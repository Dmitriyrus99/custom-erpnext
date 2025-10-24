from __future__ import annotations

"""Ensure the English root Customer Group exists for test fixtures."""

import frappe


def execute() -> None:
	"""Create a group named `All Customer Groups` if it is missing.

	This keeps the ERPNext test fixtures working on sites where the default
	root customer group was translated (e.g. Russian deployments).
	"""

	if frappe.db.exists("Customer Group", "All Customer Groups"):
		return

	root_customer_group = frappe.db.get_value(
		"Customer Group",
		{"is_group": 1, "parent_customer_group": ["in", [None, ""]]},
		"name",
	)

	doc = frappe.get_doc(
		{
			"doctype": "Customer Group",
			"customer_group_name": "All Customer Groups",
			"is_group": 1,
			"parent_customer_group": root_customer_group or "",
		}
	)
	doc.insert(ignore_permissions=True)
