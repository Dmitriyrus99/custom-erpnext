import frappe


def execute():
	"""Point the Issue SLA link field to the correct DocType."""
	custom_field_name = "Issue-custom_sla_policy"
	target_options = "SLA Policy"

	if not frappe.db.exists("Custom Field", custom_field_name):
		return

	current_options = frappe.db.get_value("Custom Field", custom_field_name, "options")
	if current_options != target_options:
		frappe.db.set_value(
			"Custom Field",
			custom_field_name,
			"options",
			target_options,
			update_modified=False,
		)

	frappe.clear_cache(doctype="Issue")
