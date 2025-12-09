from __future__ import annotations

"""Attachment endpoints for bots and external clients.

All methods require authentication (JWT or session) and will:
- Create an ERPNext File document attached to the target record
- Register a Custom Attachment referencing the File for Drive sync

Accepts multipart/form-data with field name 'file'.
"""

from typing import Optional
from ferum_custom.ferum_custom.integrations.antivirus import scan_bytes

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit


def _require_auth() -> None:
	"""
	Ensures that the user is authenticated.
	"""
	user = frappe.session.user
	if not user or user == "Guest":
		frappe.throw(_("Authentication required"))


def _store_file(
	*,
	doctype: str,
	docname: str,
	filename: str,
	content: bytes,
	content_type: str | None,
) -> tuple[str, str]:
	"""
	Stores a file in the system.

	Args:
		doctype (str): The doctype to attach the file to.
		docname (str): The docname to attach the file to.
		filename (str): The name of the file.
		content (bytes): The content of the file.
		content_type (str | None): The content type of the file.

	Returns:
		tuple[str, str]: The file URL and MIME type.
	"""
	# Antivirus scan (best-effort; see antivirus module for config)
	ok, signature = scan_bytes(content, filename)
	if not ok:
		frappe.throw(_(f"Upload blocked by antivirus: {signature or 'infected'}"))
	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": filename,
			"content": content,
			"is_private": 1,
			"attached_to_doctype": doctype,
			"attached_to_name": docname,
		}
	)
	file_doc.insert(ignore_permissions=True)
	mime = (content_type or "").lower().strip()
	try:
		att = frappe.get_doc(
			{
				"doctype": "Custom Attachment",
				"file_name": filename,
				"file_url": file_doc.file_url,
				"linked_doctype": doctype,
				"linked_docname": docname,
				"file_type": mime,
				"uploaded_by": frappe.session.user,
			}
		)
		att.insert(ignore_permissions=True)
	except Exception:
		# Non-fatal: File is stored; Drive sync might miss without CustomAttachment
		frappe.log_error(frappe.get_traceback(), "Create CustomAttachment via API failed")
	return file_doc.file_url, mime


@frappe.whitelist(methods=["POST"])  # multipart upload
@rate_limit(limit=30, seconds=60, methods=["POST"])  # 30 uploads/min per IP
def attach_to_issue(name: str) -> dict:
	"""Attach an uploaded file to an Issue.

	Expects a multipart/form-data request with 'file' field.
	"""
	_require_auth()
	if not frappe.db.exists("Issue", name):
		frappe.throw(_("Issue not found"))
	if not frappe.has_permission("Issue", ptype="write", doc=name):
		frappe.throw(_("Not permitted to modify this Issue"))

	f = None
	try:
		f = frappe.request.files.get("file")  # type: ignore[attr-defined]
	except Exception:
		f = None
	if not f:
		frappe.throw(_("File is required (multipart 'file')"))

	filename = getattr(f, "filename", None) or "upload.bin"
	content = f.read()
	content_type = getattr(f, "content_type", None)
	url, mime = _store_file(
		doctype="Issue",
		docname=name,
		filename=filename,
		content=content,
		content_type=content_type,
	)
	return {"ok": True, "file_url": url, "mime": mime}

@frappe.whitelist(methods=["POST"])  # multipart upload
@rate_limit(limit=30, seconds=60, methods=["POST"])  # 30 uploads/min per IP
def attach_to_timesheet(name: str) -> dict:
	"""Attach an uploaded file to a Timesheet (documents table)."""
	_require_auth()
	if not frappe.db.exists("Timesheet", name):
		frappe.throw(_("Timesheet not found"))
	if not frappe.has_permission("Timesheet", ptype="write", doc=name):
		frappe.throw(_("Not permitted to modify this Timesheet"))

	f = None
	try:
		f = frappe.request.files.get("file")  # type: ignore[attr-defined]
	except Exception:
		f = None
	if not f:
		frappe.throw(_("File is required (multipart 'file')"))

	filename = getattr(f, "filename", None) or "upload.bin"
	content = f.read()
	content_type = getattr(f, "content_type", None)
	url, mime = _store_file(
		doctype="Timesheet",
		docname=name,
		filename=filename,
		content=content,
		content_type=content_type,
	)

	return {"ok": True, "file_url": url, "mime": mime}
