from __future__ import annotations

"""Unified file synchronization helpers to Google Drive.

This module consolidates upload flows for ERP `File` and `Custom Attachment`
documents and is intended to be the single place handling folder mapping,
upload, and post-write bookkeeping (drive_file_id/web_link).

It reuses `integrations.drive.upload_bytes` for the actual API call and keeps
logic idempotent wherever possible.
"""

from collections.abc import Iterable

import frappe

from ferum_custom.ferum_custom.integrations.drive import upload_bytes
from ferum_custom.ferum_custom.settings import is_feature_enabled


def _read_file_content(file_name: str) -> tuple[bytes | None, str | None]:
	try:
		file_doc = frappe.get_doc("File", file_name)
		content = file_doc.get_content()
		name = file_doc.file_name
		if isinstance(content, bytes):
			return content, name
		if isinstance(content, str):
			return content.encode("utf-8"), name
	except Exception:
		pass
	return None, None


def _path_for_file_doc(file_doc) -> list[str]:
	# Default single bucket by doctype
	parts: list[str] = [getattr(file_doc, "attached_to_doctype", None) or "Files"]
	try:
		if file_doc.attached_to_doctype == "Project":
			proj = frappe.get_doc("Project", file_doc.attached_to_name)
			customer = getattr(proj, "customer", None) or "Customer"
			parts = [customer, proj.name, "Files"]
		elif file_doc.attached_to_doctype == "Task":
			task = frappe.get_doc("Task", file_doc.attached_to_name)
			proj = None
			customer = None
			if getattr(task, "project", None):
				proj = frappe.get_doc("Project", task.project)
				customer = getattr(proj, "customer", None)
			parts = [p for p in [customer or "Customer", (proj.name if proj else "Project"), "Task Files"]]
	except Exception:
		pass
	return parts


def _path_for_custom_attachment(att_doc) -> list[str]:
	parts: list[str] = ["Attachments"]
	try:
		if att_doc.linked_doctype and att_doc.linked_docname:
			if att_doc.linked_doctype == "Service Report":
				sr = frappe.db.get_value(
					"Service Report",
					att_doc.linked_docname,
					["service_request"],
					as_dict=True,
				)
				if sr and sr.get("service_request"):
					req = frappe.db.get_value(
						"Service Request",
						sr["service_request"],
						["customer", "project"],
						as_dict=True,
					)
					if req:
						parts = [
							p
							for p in [
								req.get("customer") or "Customer",
								req.get("project") or "Project",
								"Attachments",
							]
						]
			elif att_doc.linked_doctype == "Service Project":
				cust = frappe.db.get_value("Service Project", att_doc.linked_docname, "customer")
				parts = [p for p in [cust or "Customer", att_doc.linked_docname, "Attachments"]]
			elif att_doc.linked_doctype == "Invoice":
				proj = frappe.db.get_value("Invoice", att_doc.linked_docname, "project")
				parts = [p for p in ["Invoices", proj or "Project", "Attachments"]]
	except Exception:
		pass
	return parts


def sync_file_by_name(file_name: str) -> None:
	if not is_feature_enabled("enable_google_drive_sync"):
		return
	try:
		file_doc = frappe.get_doc("File", file_name)
		if getattr(file_doc, "drive_file_id", None):
			return
		content, filename = _read_file_content(file_name)
		if not content or not filename:
			return
		parts = _path_for_file_doc(file_doc)
		file_id = upload_bytes(parts, filename, content)
		if file_id:
			web = f"https://drive.google.com/file/d/{file_id}/view?usp=drivesdk"
			try:
				frappe.db.set_value("File", file_doc.name, {"drive_file_id": file_id, "drive_web_link": web})
			except Exception:
				pass
	except Exception:
		frappe.log_error(frappe.get_traceback(), "FileSync: sync_file_by_name failed")


def enqueue_file_sync(file_name: str) -> None:
	try:
		frappe.enqueue(
			"ferum_custom.ferum_custom.integrations.file_sync.sync_file_by_name",
			queue="short",
			file_name=file_name,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "FileSync: enqueue_file_sync failed")


def sync_custom_attachment_by_name(att_name: str) -> None:
	if not is_feature_enabled("enable_google_drive_sync"):
		return
	try:
		att = frappe.get_doc("Custom Attachment", att_name)
		if getattr(att, "drive_file_id", None):
			return
		# Only ERP-hosted files (skip external URLs)
		if not att.file_url or not str(att.file_url).startswith("/"):
			return
		# Find content by File.file_url
		try:
			file_doc = frappe.get_doc("File", {"file_url": att.file_url})
		except Exception:
			file_doc = None
		content = None
		filename = att.file_name or None
		if file_doc:
			content, _fname = _read_file_content(file_doc.name)
			filename = filename or _fname
		if not content:
			return
		parts = _path_for_custom_attachment(att)
		file_id = upload_bytes(parts, filename or f"Attachment-{att.name}", content)
		if file_id:
			try:
				web_link = f"https://drive.google.com/file/d/{file_id}/view?usp=drivesdk"
				att.db_set({"drive_file_id": file_id, "drive_web_link": web_link}, commit=True)
			except Exception:
				pass
	except Exception:
		frappe.log_error(frappe.get_traceback(), "FileSync: sync_custom_attachment_by_name failed")


def enqueue_custom_attachment_sync(att_name: str) -> None:
	try:
		frappe.enqueue(
			"ferum_custom.ferum_custom.integrations.file_sync.sync_custom_attachment_by_name",
			queue="short",
			att_name=att_name,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "FileSync: enqueue_custom_attachment_sync failed")
