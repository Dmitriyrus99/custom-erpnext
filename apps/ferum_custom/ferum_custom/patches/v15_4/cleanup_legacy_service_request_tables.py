from __future__ import annotations

import frappe

LEGACY_TABLES = [
    "tabService Request Legacy",
    "tabService Request Legacy Attachments",
    "tabService Report Legacy",
    "tabService Report Legacy Attachments",
    "tabLegacy Service Request Attachments",
    "tabLegacy Service Report Work Items",
]


def execute():
    """Drop legacy tables that remain from the pre-ERPNext migration."""
    for table in LEGACY_TABLES:
        try:
            frappe.db.sql(f"drop table if exists `{table}`")
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Failed to drop legacy table {table}")
