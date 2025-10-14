import contextlib

import frappe
from frappe.utils import add_days, add_months, add_years, getdate, nowdate

try:
	# optional helper to map custom Service Project -> standard Project
	from ferum_custom.patches.utils_migration import find_or_create_project  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional in CI
	find_or_create_project = None  # type: ignore[assignment]


def generate_service_requests_from_schedule():
	"""Generate standard ERPNext Issues instead of custom Service Requests.

	For each due schedule item, create an Issue with subject/description,
	set company/customer/project, and try to assign to default engineer
	from Service Object, falling back to Service Project default.
	"""

	today = nowdate()
	schedules = frappe.get_list(
		"Service Maintenance Schedule",
		filters={"next_due_date": ["<=", today], "docstatus": 0},
		fields=["name"],
	)

	for row in schedules:
		try:
			schedule = frappe.get_doc("Service Maintenance Schedule", row.name)
			if schedule.end_date and getdate(schedule.end_date) < getdate(today):
				continue

			# Resolve company and standard Project
			company = getattr(schedule, "company", None)
			std_project = None
			with contextlib.suppress(Exception):
				if not company and getattr(schedule, "service_project", None):
					company = frappe.db.get_value("Service Project", schedule.service_project, "company")
			if getattr(schedule, "service_project", None) and find_or_create_project:
				with contextlib.suppress(Exception):
					sp = frappe.get_doc("Service Project", schedule.service_project)
					std_project = find_or_create_project(sp)

			for item in schedule.items:
				try:
					subj = f"Scheduled Maintenance: {item.service_object} ({schedule.schedule_name})"
					desc = item.description or f"Routine maintenance as per schedule {schedule.schedule_name}"

					issue = frappe.get_doc(
						{
							"doctype": "Issue",
							"subject": subj,
							"description": desc,
							"status": "Open",
							"company": company,
							"customer": getattr(schedule, "customer", None),
							"project": std_project,
						}
					)
					issue.insert(ignore_permissions=True)

					# Best-effort assignment to engineer
					engineer = None
					with contextlib.suppress(Exception):
						if getattr(item, "service_object", None):
							engineer = frappe.db.get_value(
								"Service Object", item.service_object, "default_engineer"
							)
						if not engineer and getattr(schedule, "service_project", None):
							engineer = frappe.db.get_value(
								"Service Project", schedule.service_project, "default_engineer"
							)
					if engineer:
						try:
							from frappe.desk.form.assign_to import (
								add as add_assignment,  # type: ignore[import-not-found]
							)

							add_assignment(
								{
									"assign_to": [engineer],
									"doctype": "Issue",
									"name": issue.name,
									"description": subj,
								}
							)
						except Exception:
							pass

					frappe.logger().info(
						f"Issue {issue.name} created from Service Maintenance Schedule {schedule.name}"
					)
				except Exception:
					frappe.log_error(
						frappe.get_traceback(),
						f"Failed creating Issue from schedule {schedule.name}",
					)

			# Bump next due date
			if schedule.frequency == "Daily":
				schedule.next_due_date = add_days(schedule.next_due_date, 1)
			elif schedule.frequency == "Weekly":
				schedule.next_due_date = add_days(schedule.next_due_date, 7)
			elif schedule.frequency == "Monthly":
				schedule.next_due_date = add_months(schedule.next_due_date, 1)
			elif schedule.frequency == "Annually":
				schedule.next_due_date = add_years(schedule.next_due_date, 1)
			schedule.save()
		except Exception as e:
			frappe.log_error(
				f"Failed to process Service Maintenance Schedule {row.name}: {e}",
				"Maintenance schedule generation failed",
			)
