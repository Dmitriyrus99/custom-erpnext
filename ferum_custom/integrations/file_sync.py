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
from ferum_custom.ferum_custom.settings import get_setting, is_feature_enabled


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
	# Current plan leans towards a single store for simplicity.
	return [getattr(file_doc, "attached_to_doctype", None) or "Files"]


def sync_file_by_name(
	file_name: str, *, folder: Iterable[str] | None = None
) -> str | None:
	"""Upload a `File` to Google Drive and store the drive_file_id on the File doc.

	Returns the Drive file id on success.
	"""
	if not is_feature_enabled("enable_google_drive_sync"):
		return None

	try:
		file_doc = frappe.get_doc("File", file_name)
	except Exception:
		return None

	# Determine hierarchical path for Drive
	path_parts = list(folder) if folder else _path_for_file_doc(file_doc)

	# Read file bytes
	content, filename = _read_file_content(file_doc.name)
	if not content or not filename:
		return None

	mime = getattr(file_doc, "mime_type", None) or getattr(file_doc, "file_type", None) or "application/octet-stream"

	file_id = upload_bytes(path_parts, filename, content, mime_type=mime)
	if file_id:
		try:
			file_doc.db_set({"drive_file_id": file_id}, commit=False)
		except Exception:
			try:
				frappe.db.set_value("File", file_doc.name, "drive_file_id", file_id)
			except Exception:
				pass
	return file_id


def _read_custom_attachment(att) -> tuple[bytes | None, str | None]:
	"""Fetch bytes for a Custom Attachment via its linked File."""
	try:
		file_doc = frappe.get_doc("File", {"file_url": att.file_url})
		content = file_doc.get_content()
		name = att.file_name or file_doc.file_name
		if isinstance(content, bytes):
			return content, name
		if isinstance(content, str):
			return content.encode("utf-8"), name
	except Exception:
		pass
	return None, None


def sync_custom_attachment_by_name(docname: str) -> str | None:
	"""Upload a Custom Attachment to Drive and persist drive ids."""
	if not is_feature_enabled("enable_google_drive_sync"):
		return None
	try:
		att = frappe.get_doc("Custom Attachment", docname)
	except Exception:
		return None

	content, filename = _read_custom_attachment(att)
	if not content or not filename:
		return None

	path_parts: list[str] = []
	if getattr(att, "linked_doctype", None):
		path_parts.append(att.linked_doctype)
	if getattr(att, "linked_docname", None):
		path_parts.append(att.linked_docname)
	if not path_parts:
		path_parts = ["Custom Attachments"]

	mime = getattr(att, "file_type", None) or "application/octet-stream"
	file_id = upload_bytes(path_parts, filename, content, mime_type=mime)
	if file_id:
		try:
			att.db_set({"drive_file_id": file_id}, commit=False)
		except Exception:
			try:
				frappe.db.set_value("Custom Attachment", att.name, "drive_file_id", file_id)
			except Exception:
				pass
	return file_id


def enqueue_custom_attachment_sync(docname: str) -> None:
	"""Queue Custom Attachment sync to Drive."""
	try:
		frappe.enqueue(
			"ferum_custom.ferum_custom.integrations.file_sync.sync_custom_attachment_by_name",
			docname=docname,
			queue="short",
		)
	except Exception:
		# Fall back to synchronous execution to avoid silent drops during migration/testing
		sync_custom_attachment_by_name(docname)
