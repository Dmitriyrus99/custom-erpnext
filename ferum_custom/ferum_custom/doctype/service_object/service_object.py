import frappe
from frappe import _
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
				frappe.throw(_(f"Service Object with name '{self.object_name}' already exists."))

	def on_trash(self):
		# Prevent deletion if linked to an active Service Project or Service Request
		# Check Service Projects via child table Project Object Item
		parents = frappe.get_all("Project Object Item", filters={"service_object": self.name}, pluck="parent")
		if parents:
			active_projects = frappe.get_all(
				"Service Project",
				filters={"name": ["in", parents], "status": ["in", ["Planned", "Active"]]},
				pluck="name",
			)
			if active_projects:
				frappe.throw(
					_("Cannot delete Service Object. Linked to active Service Projects: {projects}").format(
						projects=", ".join(active_projects)
					)
				)

		active_requests = frappe.get_all(
			"Service Request",
			filters={"service_object": self.name, "status": ["in", ["Open", "In Progress"]]},
			pluck="name",
		)
		if active_requests:
			frappe.throw(
				_("Cannot delete Service Object. Linked to active Service Requests: {requests}").format(
					requests=", ".join(active_requests)
				)
			)


def get_permission_query_conditions(user: str | None = None) -> str | None:
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if "System Manager" in roles:
		return None
	if "Project Manager" in roles:
		return "exists(select 1 from `tabProject Object Item` poi join `tabService Project` sp on sp.name=poi.parent where poi.service_object=`tabService Object`.name and sp.project_manager=%(user)s)"
	# Allow owners to see their created objects
	return "`tabService Object`.owner=%(user)s"


def has_permission(doc, user: str | None = None) -> bool:
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if "System Manager" in roles:
		return True
	if doc.owner == user:
		return True
	if "Project Manager" in roles:
		parents = frappe.db.sql(
			"""
			select sp.project_manager
			from `tabProject Object Item` poi
			left join `tabService Project` sp on sp.name = poi.parent
			where poi.service_object=%s limit 1
			""",
			(doc.name,),
		)
		return bool(parents and parents[0][0] == user)
	return False
