from __future__ import annotations

# Thin wrapper to re-run invoice migration after provisioning default item
from ferum_custom.patches.v15_0.migrate_invoice_to_erpnext import execute as run


def execute():
    try:
        run()
    except Exception:
        import frappe

        frappe.log_error(frappe.get_traceback(), "migrate_invoice_to_erpnext_retry failed")
