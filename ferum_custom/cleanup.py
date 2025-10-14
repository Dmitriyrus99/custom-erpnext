from __future__ import annotations

import frappe

from ferum_custom.ferum_custom.integrations.drive import delete_file


def on_file_trash(doc, method=None):
	"""On File deletion, attempt to delete corresponding Drive files for any linked CustomAttachment.

	We match CustomAttachment by exact `file_url` to avoid overly aggressive deletions.
	"""
	try:
		if not getattr(doc, "file_url", None):
			return
		atts = frappe.get_all(
			"Custom Attachment", filters={"file_url": doc.file_url}, fields=["name", "drive_file_id"]
		)
		for a in atts:
			if a.get("drive_file_id"):
				try:
					delete_file(a["drive_file_id"])  # best effort
				except Exception:
					frappe.log_error(frappe.get_traceback(), "Drive delete from File on_trash failed")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "on_file_trash handler failed")
