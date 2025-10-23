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
def attach_to_service_request(name: str) -> dict:
	"""Attach an uploaded file to a Service Request.

	Expects a multipart/form-data request with 'file' field.
	"""
	_require_auth()
	if not frappe.db.exists("Service Request", name):
		frappe.throw(_("Service Request not found"))
	if not frappe.has_permission("Service Request", ptype="write", doc=name):
		frappe.throw(_("Not permitted to modify this Service Request"))

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
		doctype="Service Request",
		docname=name,
		filename=filename,
		content=content,
		content_type=content_type,
	)

	# Back-compat: append to child tables if they exist
	try:
		req = frappe.get_doc("Service Request", name)
		req.append("photos", {"photo": url, "description": "bot"})
		req.append("attachments", {"attachment": url, "description": "bot"})
		req.save(ignore_permissions=True)
	except Exception:
		pass

	return {"ok": True, "file_url": url, "mime": mime}


@frappe.whitelist(methods=["POST"])  # multipart upload
@rate_limit(limit=30, seconds=60, methods=["POST"])  # 30 uploads/min per IP
def attach_to_service_report(name: str) -> dict:
	"""Attach an uploaded file to a Service Report (documents table).

	Expects a multipart/form-data request with 'file' field.
	Registers a Custom Attachment and adds a row to Service Report Document Item.
	"""
	_require_auth()
	if not frappe.db.exists("Service Report", name):
		frappe.throw(_("Service Report not found"))
	if not frappe.has_permission("Service Report", ptype="write", doc=name):
		frappe.throw(_("Not permitted to modify this Service Report"))

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
		doctype="Service Report",
		docname=name,
		filename=filename,
		content=content,
		content_type=content_type,
	)

	# Add to documents child table
	try:
		# Find the Custom Attachment we just inserted by file_url
		att_name = frappe.db.get_value(
			"Custom Attachment",
			{"linked_doctype": "Service Report", "linked_docname": name, "file_url": url},
			"name",
		)
		if att_name:
			sr = frappe.get_doc("Service Report", name)
			sr.append("documents", {"custom_attachment": att_name})
			sr.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Attach to Service Report child table failed")

	return {"ok": True, "file_url": url, "mime": mime}
