import frappe
from frappe.model.document import Document


class ServiceObject(Document):
	def validate(self):
		# Check for uniqueness of object_name (though already handled by unique:1 in JSON)
		# This provides a more user-friendly error message
		if self.is_new() or self.has_changed("object_name"):
			if (
				frappe.db.exists("ServiceObject", {"object_name": self.object_name})
				and frappe.db.get_value("ServiceObject", {"object_name": self.object_name}, "name")
				!= self.name
			):
				frappe.throw(f"Service Object with name '{self.object_name}' already exists.")

	def on_trash(self):
		# Prevent deletion if the ServiceObject is linked to an active ServiceProject
		# or any active ServiceRequest
		active_projects = frappe.get_all(
			"ServiceProject",
			filters={"objects.service_object": self.name, "status": ["in", ["Planned", "Active"]]},
			pluck="name",
		)
		if active_projects:
			frappe.throw(
				f"Cannot delete Service Object. It is linked to active Service Projects: {', '.join(active_projects)}"
			)

		active_requests = frappe.get_all(
			"ServiceRequest",
			filters={"service_object": self.name, "status": ["in", ["Open", "In Progress"]]},
			pluck="name",
		)
		if active_requests:
			frappe.throw(
				f"Cannot delete Service Object. It is linked to active Service Requests: {', '.join(active_requests)}"
			)
