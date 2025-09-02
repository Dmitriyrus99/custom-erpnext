import frappe
from frappe.utils import add_days, add_months, add_years, getdate, nowdate


def generate_service_requests_from_schedule():
	today = nowdate()
	maintenance_schedules = frappe.get_list(
		"Service Maintenance Schedule",
		filters={"next_due_date": ["<=", today], "docstatus": 0},
		fields=["name"],
	)

	for schedule_data in maintenance_schedules:
		try:
			schedule = frappe.get_doc("Service Maintenance Schedule", schedule_data.name)
			if schedule.end_date and getdate(schedule.end_date) < getdate(today):
				continue
			for item in schedule.items:
				service_request = frappe.new_doc("Service Request")
				service_request.customer = schedule.customer
				service_request.project = schedule.service_project
				service_request.service_object = item.service_object
				service_request.title = (
					f"Scheduled Maintenance for {item.service_object} ({schedule.schedule_name})"
				)
				service_request.description = item.description or (
					f"Routine maintenance as per schedule {schedule.schedule_name}"
				)
				service_request.status = "Open"
				service_request.insert()
				frappe.logger().info(
					f"Service Request {service_request.name} created from Service Maintenance Schedule {schedule.name}"
				)

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
			frappe.log_error(f"Failed to process Service Maintenance Schedule {schedule_data.name}: {e}")
