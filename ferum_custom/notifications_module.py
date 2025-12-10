from __future__ import annotations

import frappe
from frappe import _

from ferum_custom.notifications.dispatcher import notify


def on_issue_after_insert(doc, method=None):  # New Issue created
	try:
		ctx = {
			"name": doc.name,
			"title": getattr(doc, "subject", ""),
			"priority": getattr(doc, "priority", ""),
			"project": getattr(doc, "project", ""),
		}
		notify(
			event_type="new_issue",
			roles=["Project Manager", "Office Manager"],
			context=ctx,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Notify on_issue_after_insert failed")


def on_invoice_after_insert(doc, method=None):
	try:
		ctx = {
			"name": doc.name,
			"amount": getattr(doc, "amount", 0),
			"invoice_date": getattr(doc, "invoice_date", ""),
			"project": getattr(doc, "project", ""),
		}
		notify(
			event_type="new_invoice",
			roles=["Chief Accountant", "Project Manager"],
			context=ctx,
			channels_override=["email"],
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Notify on_invoice_after_insert failed")


@frappe.whitelist()
def test_notify(kind: str = "ping") -> dict:
	ctx = {"name": kind, "title": kind, "priority": "Low", "project": ""}
	return notify("new_issue", recipients=[frappe.session.user], context=ctx)
