from __future__ import annotations

import frappe

DOCTYPES = [
    # Legacy / unused doctypes that are no longer referenced by code or metadata.
    "Service Act",
    "Invoice Item",
]


def execute():
    for doctype in DOCTYPES:
        try:
            if frappe.db.exists("DocType", doctype):
                frappe.delete_doc("DocType", doctype, force=1, ignore_permissions=True)
            # In some environments DocType deletion may keep the underlying table.
            frappe.db.sql(f"drop table if exists `tab{doctype}`")
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Failed to delete DocType: {doctype}")
