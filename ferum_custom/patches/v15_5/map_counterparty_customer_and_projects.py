import frappe


def execute():
	"""
	Link Counterparty -> Customer and Service Project -> Project where possible, without creating new docs.
	- Counterparty.customer: match by exact name_short, fallback to name_full.
	- Service Project.erp_project: match Project.name == project_name (or same as Service Project name) and company.
	"""

	# Counterparty -> Customer
	for cp in frappe.get_all(
		"Counterparty",
		fields=["name", "name_short", "name_full", "customer"],
	):
		if cp.customer:
			continue
		candidate = None
		for key in (cp.name_short, cp.name_full):
			if not key:
				continue
			candidate = frappe.db.get_value("Customer", {"customer_name": key})
			if candidate:
				break
		if candidate:
			frappe.db.set_value("Counterparty", cp.name, "customer", candidate, update_modified=False)

	# Service Project -> Project
	for sp in frappe.get_all(
		"Service Project",
		fields=["name", "project_name", "company", "erp_project"],
	):
		if sp.erp_project:
			continue
		project = None
		# Try match by name then project_name
		for key in (sp.name, sp.project_name):
			if not key:
				continue
			project = frappe.db.get_value(
				"Project",
				{"project_name": key, "company": sp.company} if sp.company else {"project_name": key},
			) or frappe.db.get_value("Project", {"name": key})
			if project:
				break
		if project:
			frappe.db.set_value("Service Project", sp.name, "erp_project", project, update_modified=False)
