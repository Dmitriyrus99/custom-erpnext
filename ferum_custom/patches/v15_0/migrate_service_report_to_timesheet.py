from __future__ import annotations

import contextlib

import frappe

from ferum_custom.patches.utils_migration import (
	_log,
	find_or_create_project,
	has_doctypes,
	migrate_attachments,
)


def _find_timesheet(srpt) -> str | None:
	# Find by remarks tag
	return frappe.db.get_value("Timesheet", {"remarks": ["like", f"%{srpt.name}%"]}, "name")


def execute():
	if not has_doctypes("Timesheet"):
		_log("migrate_service_report_to_timesheet: skipped (Timesheet doctype missing)")
		return
	ok = skipped = att_ok = att_skip = 0
	names = frappe.get_all("Service Report", pluck="name")
	for name in names:
		try:
			srpt = frappe.get_doc("Service Report", name)
			ts_name = _find_timesheet(srpt)
			if not ts_name:
				ts = frappe.new_doc("Timesheet")
				# Date fields
				with contextlib.suppress(Exception):
					ts.start_date = srpt.report_date
					ts.end_date = srpt.report_date
				with contextlib.suppress(Exception):
					ts.company = srpt.company
				# remarks keeps migration trace
				ts.remarks = f"Migrated from Service Report {srpt.name}"

				# Map project from SR -> SRQ -> Project
				project = None
				if getattr(srpt, "service_request", None):
					project = frappe.db.get_value("Service Request", srpt.service_request, "project")
				if project:
					with contextlib.suppress(Exception):
						if frappe.db.exists("Service Project", project):
							sp = frappe.get_doc("Service Project", project)
							project = find_or_create_project(sp) or project
					ts.project = project

				# Work items → Timesheet Details
				total = 0.0
				for wi in getattr(srpt, "work_items", []) or []:
					row = ts.append("time_logs", {})
					with contextlib.suppress(Exception):
						row.employee = getattr(wi, "employee", None)
					with contextlib.suppress(Exception):
						row.hours = float(getattr(wi, "hours", 0) or 0)
						total += row.hours
					with contextlib.suppress(Exception):
						row.billing_rate = float(getattr(wi, "rate", 0) or 0)
					with contextlib.suppress(Exception):
						row.billable = 1
					with contextlib.suppress(Exception):
						row.project = project
				ts.insert(ignore_permissions=True)
				ts_name = ts.name

			o, s = migrate_attachments("Service Report", srpt.name, "Timesheet", ts_name)
			att_ok += o
			att_skip += s
			ok += 1
		except Exception:
			skipped += 1
			frappe.log_error(frappe.get_traceback(), f"Service Report migration failed: {name}")
	_log(
		f"migrate_service_report_to_timesheet: ok={ok} skipped={skipped} attachments_ok={att_ok} attachments_skipped={att_skip}"
	)
