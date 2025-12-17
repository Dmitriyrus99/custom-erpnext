from __future__ import annotations

import frappe

DOCTYPES = [
    # Legacy / unused doctypes that must not be present in a v15 ERPNext-based deployment.
    "Service Act",
    "Invoice Item",
]


def execute() -> None:
    for doctype in DOCTYPES:
        if not frappe.db.exists("DocType", doctype):
            continue

        # If there is data, do not delete silently.
        try:
            count = frappe.db.count(doctype)
        except Exception as exc:
            frappe.throw(f"Failed to count {doctype}: {exc}")

        if count:
            frappe.throw(
                f"Refusing to delete DocType {doctype}: it still has {count} record(s). "
                "Please migrate/archive data first."
            )

        frappe.delete_doc("DocType", doctype, force=True, ignore_permissions=True)

        # In some setups DocType deletion may keep the underlying table.
        table = f"tab{doctype}"
        frappe.db.sql(f"DROP TABLE IF EXISTS `{table}`")
