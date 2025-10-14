from __future__ import annotations

import contextlib

import frappe

LEGACY_DOCTYPES = [
	"Service Project",
	"Service Object",
	"Service Request",
	"Service Report",
	"Invoice",
	"Custom Attachment",
]


def execute():
	"""Best-effort hide/freeze legacy doctypes after migration.

	- Restrict to a non-active domain to hide from standard Desk lists
	- Remove Create/Write/Delete perms for common roles (read-only access)
	"""
	for dt in LEGACY_DOCTYPES:
		with contextlib.suppress(Exception):
			frappe.db.set_value("DocType", dt, "restrict_to_domain", "Ferum Legacy (Hidden)")

		# Remove write/create/delete for all roles listed on DocPerm
		try:
			perms = frappe.get_all(
				"DocPerm",
				filters={"parent": dt},
				fields=["name", "role", "read", "write", "create", "delete", "submit", "cancel", "amend"],
			)  # type: ignore[list-item]
			for p in perms:
				doc = frappe.get_doc("DocPerm", p["name"])  # type: ignore[index]
				doc.read = 1
				doc.write = 0
				doc.create = 0
				doc.delete = 0
				doc.submit = 0
				doc.cancel = 0
				doc.amend = 0
				doc.save(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Freeze legacy perms failed: {dt}")
