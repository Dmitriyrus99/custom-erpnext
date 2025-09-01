import frappe
from frappe.utils import add_days, add_months, add_years, getdate, nowdate


def generate_service_requests_from_schedule():
	today = nowdate()
	maintenance_schedules = frappe.get_list(
		"MaintenanceSchedule",
		filters={
			"next_due_date": ["<=", today],
			"docstatus": 0,  # Draft or active schedules
		},
		fields=["name"],
	)

	for schedule_data in maintenance_schedules:
		try:
			schedule = frappe.get_doc("MaintenanceSchedule", schedule_data.name)
			if schedule.end_date and getdate(schedule.end_date) < getdate(today):
				# Schedule has ended, skip it
				continue

			for item in schedule.items:
				service_request = frappe.new_doc("ServiceRequest")
				service_request.customer = schedule.customer
				service_request.service_project = schedule.service_project
				service_request.service_object = item.service_object
				service_request.subject = (
					f"Scheduled Maintenance for {item.service_object} ({schedule.schedule_name})"
				)
				service_request.description = (
					item.description or f"Routine maintenance as per schedule {schedule.schedule_name}"
				)
				service_request.status = "Open"
				service_request.save()
				frappe.log_by_activity(
					doctype="ServiceRequest",
					name=service_request.name,
					text=f"Created from Maintenance Schedule {schedule.name}",
					status="Success",
				)

			# Update next_due_date for the schedule
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
			frappe.log_error(f"Failed to process Maintenance Schedule {schedule_data.name}: {e}")
