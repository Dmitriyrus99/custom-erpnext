import frappe
from frappe import _
from frappe.model.document import Document


class ServiceProject(Document):
	def validate(self):
		self.ensure_company_defaults()
		self.check_dates_and_amount()
		self.validate_unique_objects()

	def on_update(self):
		# Audit: log status changes
		try:
			if self.has_value_changed("status"):
				self.add_comment(
					"Info",
					_("Status changed to {status}").format(status=self.status or "-"),
				)
		except Exception:
			pass

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
				"Project Object Item",
				{
					"service_object": item.service_object,
					"parenttype": "Service Project",
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

		# Ensure all listed objects reference this project and inherit company
		for item in self.objects:
			try:
				obj = frappe.get_doc("Service Object", item.service_object)
				updated = False
				if obj.project != self.name:
					obj.project = self.name
					updated = True
				if not getattr(obj, "company", None) and getattr(self, "company", None):
					obj.company = self.company
					updated = True
				if updated:
					obj.save(ignore_permissions=True)
			except Exception:
				pass

	def ensure_company_defaults(self):
		# When customer has a preferred company, prefill
		try:
			if not getattr(self, "company", None) and getattr(self, "customer", None):
				cust_company = frappe.db.get_value("Customer", self.customer, "company")
				if cust_company:
					self.company = cust_company
		except Exception:
			pass



def get_permission_query_conditions(user: str | None = None) -> str | None:
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if "System Manager" in roles:
		return None

	conds = []
	# Company restriction for internal users
	try:
		user_type = frappe.get_cached_value("User", user, "user_type")
		companies = frappe.get_all(
			"User Permission",
			filters={"user": user, "allow": "Company"},
			pluck="for_value",
		)
		if user_type != "Website User" and companies:
			vals = ", ".join(frappe.db.escape(x) for x in companies)
			conds.append(f"`tabService Project`.company in ({vals})")
	except Exception:
		pass

	# Office Manager and Department Head: broad access within companies
	if "Office Manager" in roles:
		return " and ".join(f"({c})" for c in conds) if conds else None
	if "Department Head" in roles:
		depts = frappe.get_all(
			"User Permission", filters={"user": user, "allow": "Service Department"}, pluck="for_value"
		)
		if depts:
			vals = ", ".join(frappe.db.escape(x) for x in depts)
			conds.append(f"`tabService Project`.service_department in ({vals})")
			return " and ".join(f"({c})" for c in conds)
		return " and ".join(f"({c})" for c in conds) if conds else None

	if "Project Manager" in roles:
		conds.append("`tabService Project`.project_manager=%(user)s")
	# Client access by Customer user permission
	if "Client" in roles:
		customers = frappe.get_all(
			"User Permission",
			filters={"user": user, "allow": "Customer"},
			pluck="for_value",
		)
		if customers:
			vals = ", ".join(frappe.db.escape(x) for x in customers)
			conds.append(f"`tabService Project`.customer in ({vals})")
		else:
			# fallback to owner if no explicit permission configured
			conds.append("`tabService Project`.owner=%(user)s")
	else:
		conds.append("`tabService Project`.owner=%(user)s")
	return " and ".join(f"({c})" for c in conds)


def has_permission(doc, user: str | None = None) -> bool:
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if "System Manager" in roles or "Office Manager" in roles:
		return True
	if "Department Head" in roles:
		allowed = set(
			frappe.get_all(
				"User Permission", filters={"user": user, "allow": "Service Department"}, pluck="for_value"
			)
		)
		if allowed:
			if getattr(doc, "service_department", None) in allowed:
				return True
		else:
			return True
	if doc.project_manager == user:
		return True
	if "Client" in roles:
		customers = frappe.get_all(
			"User Permission", filters={"user": user, "allow": "Customer"}, pluck="for_value"
		)
		if customers and getattr(doc, "customer", None) in set(customers):
			return True
	if doc.owner == user:
		return True
	return False


def update_project_financials(project: str) -> None:
	"""Recalculate and store financial totals for the given Service Project."""
	if not project:
		return

	totals = frappe.db.get_all(
		"Invoice",
		filters={"project": project, "docstatus": 1, "status": "Paid"},
		fields=["counterparty_type", "sum(amount) as total"],
		group_by="counterparty_type",
	)

	totals_map = {row.counterparty_type: row.get("total") or 0 for row in totals}
	income = totals_map.get("Customer", 0.0)
	expenses = totals_map.get("Subcontractor", 0.0)

	frappe.db.set_value(
		"Service Project",
		project,
		{
			"income_amount": income,
			"expense_amount": expenses,
			"profit_amount": income - expenses,
		},
	)
