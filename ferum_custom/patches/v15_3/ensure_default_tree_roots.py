from __future__ import annotations

"""Provide English root nodes for ERPNext tree doctypes used by tests."""

import frappe


def execute() -> None:
	for doctype, parent_field, title_field, root_name in (
		("Customer Group", "parent_customer_group", "customer_group_name", "All Customer Groups"),
		("Supplier Group", "parent_supplier_group", "supplier_group_name", "All Supplier Groups"),
		("Item Group", "parent_item_group", "item_group_name", "All Item Groups"),
		("Territory", "parent_territory", "territory_name", "All Territories"),
		("Sales Person", "parent_sales_person", "sales_person_name", "Sales Team"),
	):
		ensure_translated_group(doctype, parent_field, title_field, root_name)

	ensure_department_root()


def ensure_translated_group(doctype: str, parent_field: str, title_field: str, root_name: str) -> None:
	if frappe.db.exists(doctype, root_name):
		return

	root = frappe.db.get_value(
		doctype,
		{"is_group": 1, parent_field: ["in", [None, ""]]},
		"name",
	)

	doc = frappe.get_doc(
		{
			"doctype": doctype,
			"name": root_name,
			title_field: root_name,
			"is_group": 1,
			parent_field: root or "",
		}
	)

	doc.insert(ignore_permissions=True)


def ensure_department_root() -> None:
	target = "All Departments"
	if frappe.db.exists("Department", target):
		return

	root = frappe.db.get_value(
		"Department",
		{"is_group": 1, "parent_department": ["in", [None, ""]]},
		"name",
	)

	defaults = frappe.defaults.get_defaults() or {}
	company = defaults.get("company") or frappe.db.get_value("Company", {}, "name")
	if not company:
		return

	from erpnext.setup.doctype.department.department import Department

	original_autoname = Department.autoname

	def autoname_override(self):
		if self.department_name == target:
			self.name = target
		else:
			original_autoname(self)

	Department.autoname = autoname_override

	try:
		doc = frappe.get_doc(
			{
				"doctype": "Department",
				"department_name": target,
				"company": company,
				"is_group": 1,
				"parent_department": root or "",
			}
		)
		doc.insert(ignore_permissions=True)
	finally:
		Department.autoname = original_autoname
