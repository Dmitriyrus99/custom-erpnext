from __future__ import annotations

import frappe

TABLES = [
    "tabService Act",
    "tabInvoice Item",
]


def execute():
    # Defensive cleanup for environments where the DocType is deleted but the physical table remains.
    for table in TABLES:
        try:
            frappe.db.sql(f"drop table if exists `{table}`")
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Failed to drop orphan table: {table}")

