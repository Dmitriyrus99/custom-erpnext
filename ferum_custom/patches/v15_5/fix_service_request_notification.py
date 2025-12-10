from __future__ import annotations

import frappe


def execute():
	"""Align Service Request SLA Notification condition with actual fields.

	Older fixtures referenced `response_by` which is not present on our
	custom Service Request. Replace with `sla_deadline` if the notification
	exists.
	"""

	try:
		name = frappe.db.get_value(
			"Notification",
			{"name": "Service Request SLA Breach", "document_type": "Service Request"},
			"name",
		)
		if not name:
			return
		cond = (
			"doc.sla_deadline and frappe.utils.get_datetime(doc.sla_deadline) < frappe.utils.now_datetime() and "
			"doc.status not in ('Closed','Completed','Cancelled')"
		)
		frappe.db.set_value("Notification", name, "condition", cond)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "fix_service_request_notification failed")
