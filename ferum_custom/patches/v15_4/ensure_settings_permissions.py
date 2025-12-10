from __future__ import annotations

import frappe


def execute():
	if not frappe.db.exists("DocType", "Ferum Custom Settings"):
		return

	perms = frappe.get_all(
		"DocPerm",
		filters={"parent": "Ferum Custom Settings", "parenttype": "DocType"},
		fields=["name", "role"],
	)

	found = False
	for perm in perms:
		role = (perm.get("role") or "").strip()
		if role in {"System Manager", "Менеджер системы"}:
			if role != "System Manager":
				frappe.db.set_value("DocPerm", perm["name"], "role", "System Manager")
			found = True

	if not found:
		doc = frappe.get_doc("DocType", "Ferum Custom Settings")
		doc.append(
			"permissions",
			{
				"role": "System Manager",
				"read": 1,
				"write": 1,
				"create": 1,
				"delete": 1,
			},
		)
		doc.save()
