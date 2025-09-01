import frappe
from frappe import _
from frappe.model.document import Document


class ServiceProject(Document):
	def validate(self):
		self.check_dates_and_amount()
		self.validate_unique_objects()

	def check_dates_and_amount(self):
		if self.end_date and self.start_date and self.end_date < self.start_date:
			frappe.throw(_("End Date cannot be before Start Date."))
		if self.total_amount and self.total_amount < 0:
			frappe.throw(_("Total Amount cannot be negative."))

	def validate_unique_objects(self):
		# Check for duplicate ServiceObjects within this project
		seen_objects = set()
		for item in self.objects:
			if item.service_object in seen_objects:
				frappe.throw(_(f"Service Object {item.service_object} is duplicated in this project."))
			seen_objects.add(item.service_object)

			# Check if ServiceObject is already linked to another active project
			# Exclude current project from the check
			existing_link = frappe.db.get_value(
				"ProjectObjectItem",
				{
					"service_object": item.service_object,
					"parenttype": "ServiceProject",
					"parent": ["!=", self.name],  # Exclude current project
				},
				"parent",
			)
			if existing_link:
				frappe.throw(
					_(
						f"Service Object {item.service_object} is already linked to active project {existing_link}."
					)
				)
