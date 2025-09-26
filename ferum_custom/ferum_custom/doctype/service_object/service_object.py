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

		# Default company from linked project or customer when missing
		try:
			if not getattr(self, "company", None):
				if getattr(self, "project", None):
					self.company = frappe.db.get_value("Service Project", self.project, "company")
				elif getattr(self, "customer", None):
					self.company = frappe.db.get_value("Customer", self.customer, "company")
		except Exception:
			pass

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

	# Company restriction for internal users
	try:
		user_type = frappe.get_cached_value("User", user, "user_type")
		company_vals = frappe.get_all(
			"User Permission",
			filters={"user": user, "allow": "Company"},
			pluck="for_value",
		)
		company_cond = None
		if user_type != "Website User" and company_vals:
			company_list = ", ".join(frappe.db.escape(x) for x in company_vals)
			company_cond = f"`tabService Object`.company in ({company_list})"
	except Exception:
		company_cond = None

	conds = []
	if company_cond:
		conds.append(company_cond)
	if "Project Manager" in roles:
		conds.append(
			"exists(select 1 from `tabProject Object Item` poi join `tabService Project` sp on sp.name=poi.parent where poi.service_object=`tabService Object`.name and sp.project_manager=%(user)s)"
		)
	# Allow owners to see their created objects
	conds.append("`tabService Object`.owner=%(user)s")
	return " and ".join(f"({c})" for c in conds) if conds else None


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
