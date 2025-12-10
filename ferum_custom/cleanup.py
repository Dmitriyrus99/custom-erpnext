from __future__ import annotations

import frappe

from ferum_custom.ferum_custom.integrations.drive import delete_file


def on_file_trash(doc, method=None):
	"""On File deletion, attempt to delete corresponding Drive file."""
	try:
		if not getattr(doc, "drive_file_id", None):
			return
		try:
			delete_file(doc.drive_file_id)  # best effort
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Drive delete from File on_trash failed")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "on_file_trash handler failed")
