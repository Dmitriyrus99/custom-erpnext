from __future__ import annotations

import frappe

SENSITIVE_ATTACH_DOCTYPES = {
	"Issue",
	"Timesheet",
	"Project",
	"Sales Invoice",
	"Purchase Invoice",
}


def on_file_validate(doc, method: str | None = None) -> None:
	"""Enforce private-by-default for sensitive attachments.

	If a file is attached to one of the SENSITIVE_ATTACH_DOCTYPES and is not marked
	private, flip it to private to avoid public exposure via static paths.
	"""
	try:
		if getattr(doc, "attached_to_doctype", None) in SENSITIVE_ATTACH_DOCTYPES:
			if int(getattr(doc, "is_private", 0)) != 1:
				doc.is_private = 1
	except Exception:
		pass
