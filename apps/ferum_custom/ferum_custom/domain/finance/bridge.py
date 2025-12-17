"""Bridge utilities to create Sales Invoice / Payment Entry from custom docs."""

from __future__ import annotations

import frappe

from ferum_custom.ferum_custom.domain.finance import standard_finance_enabled
from ferum_custom.ferum_custom.domain.finance.mappers import map_invoice_fields


def custom_invoice_to_sales_invoice(inv_name: str) -> str | None:
    """Return linked Sales Invoice if already created."""

    return frappe.db.get_value("Invoice", inv_name, "sales_invoice")


def ensure_sales_invoice_from_custom(inv_name: str) -> str | None:
    """Create Sales Invoice from custom Invoice if flag is on; return SI name."""

    if not standard_finance_enabled():
        return None

    inv = frappe.get_doc("Invoice", inv_name)
    if inv.sales_invoice:
        return inv.sales_invoice

    fields = map_invoice_fields(inv)
    si = frappe.new_doc("Sales Invoice")
    for k, v in fields.items():
        if v is not None:
            setattr(si, k, v)
    # Minimal line item to satisfy mandatory requirements
    si.append(
        "items",
        {
            "item_name": inv.invoice_no or "Service",
            "qty": 1,
            "rate": inv.amount or 0,
        },
    )
    si.insert(ignore_permissions=True)
    si.submit()
    inv.db_set("sales_invoice", si.name, update_modified=False)
    return si.name
