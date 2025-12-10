from __future__ import annotations

import frappe


# -------------------------- Helpers --------------------------


def _company_cond(user: str) -> str | None:
	try:
		user_type = frappe.get_cached_value("User", user, "user_type")
		if user_type == "Website User":
			return None
		companies = frappe.get_all(
			"User Permission", filters={"user": user, "allow": "Company"}, pluck="for_value"
		)
		if companies:
			vals = ", ".join(frappe.db.escape(x) for x in companies)
			return f"company in ({vals})"
	except Exception:
		return None
	return None


# -------------------------- Project --------------------------


def project_get_permission_query_conditions(user: str | None = None) -> str | None:
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if "System Manager" in roles:
		return None

	conds: list[str] = []
	comp = _company_cond(user)
	if comp:
		conds.append(f"`tabProject`.{comp}")

	# Project Manager: own projects
	if "Project Manager" in roles:
		conds.append("`tabProject`.project_manager=%(user)s")

	# Client / Website User: projects for allowed customers
	try:
		user_type = frappe.get_cached_value("User", user, "user_type")
		if user_type == "Website User" or "Client" in roles:
			customers = frappe.get_all(
				"User Permission", filters={"user": user, "allow": "Customer"}, pluck="for_value"
			)
			if customers:
				vals = ", ".join(frappe.db.escape(x) for x in customers)
				conds.append(f"`tabProject`.customer in ({vals})")
			else:
				conds.append("`tabProject`.owner=%(user)s")
	except Exception:
		pass

	return " and ".join(f"({c})" for c in conds) if conds else None


def project_has_permission(doc, user: str | None = None) -> bool:
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if "System Manager" in roles:
		return True
	# PM: owns the project
	if getattr(doc, "project_manager", None) == user:
		return True
	# Office/Dept Head: within allowed companies
	if "Office Manager" in roles or "Department Head" in roles:
		try:
			companies = set(
				frappe.get_all(
					"User Permission", filters={"user": user, "allow": "Company"}, pluck="for_value"
				)
			)
			return not companies or getattr(doc, "company", None) in companies
		except Exception:
			return True
	# Client: by allowed customers (requires Project.customer)
	if "Client" in roles:
		try:
			customers = set(
				frappe.get_all(
					"User Permission", filters={"user": user, "allow": "Customer"}, pluck="for_value"
				)
			)
			cust = getattr(doc, "customer", None)
			if customers and cust in customers:
				return True
		except Exception:
			pass
	# Owner fallback
	return getattr(doc, "owner", None) == user


# -------------------------- Timesheet --------------------------


def timesheet_get_permission_query_conditions(user: str | None = None) -> str | None:
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if "System Manager" in roles:
		return None

	conds: list[str] = []
	comp = _company_cond(user)
	if comp:
		conds.append(f"`tabTimesheet`.{comp}")

	# Owner can see own timesheets
	conds.append("`tabTimesheet`.owner=%(user)s")

	# Project Manager: by project
	if "Project Manager" in roles:
		conds.append(
			"exists(select 1 from `tabProject` p where p.name=`tabTimesheet`.project and p.project_manager=%(user)s)"
		)

	# Client / Website User: typically no access to Timesheets; keep strict
	try:
		user_type = frappe.get_cached_value("User", user, "user_type")
		if user_type == "Website User" or "Client" in roles:
			# no additional allowances; rely on None/owner fallback
			pass
	except Exception:
		pass

	return " or ".join(f"({c})" for c in conds) if conds else None


def timesheet_has_permission(doc, user: str | None = None) -> bool:
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if "System Manager" in roles:
		return True
	# Owner
	if getattr(doc, "owner", None) == user:
		return True
	# PM: by project
	try:
		if getattr(doc, "project", None):
			pm = frappe.db.get_value("Project", doc.project, "project_manager")
			if pm == user:
				return True
	except Exception:
		pass
	# Office Manager / Dept Head: company scope
	if "Office Manager" in roles or "Department Head" in roles:
		try:
			companies = set(
				frappe.get_all(
					"User Permission", filters={"user": user, "allow": "Company"}, pluck="for_value"
				)
			)
			return not companies or getattr(doc, "company", None) in companies
		except Exception:
			return True
	# Client: deny unless the project's customer matches allowed (optional)
	if "Client" in roles:
		try:
			if getattr(doc, "project", None):
				cust = frappe.db.get_value("Project", doc.project, "customer")
				allowed = set(
					frappe.get_all(
						"User Permission", filters={"user": user, "allow": "Customer"}, pluck="for_value"
					)
				)
				if allowed and cust in allowed:
					return True
		except Exception:
			pass
	return False
