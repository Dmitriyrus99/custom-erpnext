from __future__ import annotations

import frappe

from ferum_custom.ferum_custom.domain.finance.bridge import ensure_sales_invoice_from_custom
from ferum_custom.ferum_custom.domain.finance.payments import ensure_payment_entry_from_custom


def migrate_finance_records(
    limit: int = 100, create_sales_invoices: bool = True, create_payment_entries: bool = True
) -> dict[str, int]:
    """Batch migration helper for legacy Invoice/Payment docs."""

    migrated = {"sales_invoice": 0, "payment_entry": 0, "errors": 0}

    if create_sales_invoices:
        invoices = frappe.get_all(
            "Invoice",
            filters={"docstatus": 1},
            fields=["name"],
            limit=limit,
        )
        for row in invoices:
            try:
                if ensure_sales_invoice_from_custom(row.name):
                    migrated["sales_invoice"] += 1
            except Exception:
                frappe.log_error(frappe.get_traceback(), "finance_migration.invoice")
                migrated["errors"] += 1

    if create_payment_entries:
        payments = frappe.get_all(
            "Payment",
            filters={"docstatus": 1, "direction": "in"},
            fields=["name"],
            limit=limit,
        )
        for row in payments:
            try:
                if ensure_payment_entry_from_custom(row.name):
                    migrated["payment_entry"] += 1
            except Exception:
                frappe.log_error(frappe.get_traceback(), "finance_migration.payment")
                migrated["errors"] += 1

    return migrated
