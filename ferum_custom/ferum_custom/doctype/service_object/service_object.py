import frappe
from frappe.model.document import Document


class ServiceObject(Document):
	def validate(self):
		# Check for uniqueness of object_name (though already handled by unique:1 in JSON)
		# This provides a more user-friendly error message
		if self.is_new() or self.has_changed("object_name"):
			if (
				frappe.db.exists("Service Object", {"object_name": self.object_name})
				and frappe.db.get_value("Service Object", {"object_name": self.object_name}, "name")
				!= self.name
			):
				frappe.throw(f"Service Object with name '{self.object_name}' already exists.")

	def on_trash(self):
		# Prevent deletion if linked to an active Service Project or Service Request
		# Check Service Projects via child table Project Object Item
		parents = frappe.get_all(
			"Project Object Item", filters={"service_object": self.name}, pluck="parent"
		)
		if parents:
			active_projects = frappe.get_all(
				"Service Project",
				filters={"name": ["in", parents], "status": ["in", ["Planned", "Active"]]},
				pluck="name",
			)
			if active_projects:
				frappe.throw(
					f"Cannot delete Service Object. Linked to active Service Projects: {', '.join(active_projects)}"
				)

		active_requests = frappe.get_all(
			"Service Request",
			filters={"service_object": self.name, "status": ["in", ["Open", "In Progress"]]},
			pluck="name",
		)
		if active_requests:
			frappe.throw(
				f"Cannot delete Service Object. Linked to active Service Requests: {', '.join(active_requests)}"
			)

