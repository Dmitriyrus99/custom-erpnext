"""Helpers for creating Payment Entry from custom Payment + Allocation."""

from __future__ import annotations

import frappe

from ferum_custom.ferum_custom.domain.finance import standard_finance_enabled
from ferum_custom.ferum_custom.domain.finance.bridge import (
    custom_invoice_to_sales_invoice,
    ensure_sales_invoice_from_custom,
)


def _parse_payment_entry_ref(doc_ref: str | None) -> str | None:
    if not doc_ref:
        return None
    parts = str(doc_ref).split()
    if len(parts) >= 3 and parts[0] == "Payment" and parts[1] == "Entry":
        return parts[2]
    return None


def ensure_payment_entry_from_custom(payment_name: str) -> str | None:
    """Create Payment Entry when the standard finance flag is on and return its name."""

    if not standard_finance_enabled():
        return None

    pay = frappe.get_doc("Payment", payment_name)
    existing = _parse_payment_entry_ref(getattr(pay, "doc_ref", None))
    if existing and frappe.db.exists("Payment Entry", existing):
        return existing

    if pay.direction != "in":
        return None

    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = "Receive"
    pe.company = pay.company
    pe.party_type = "Customer"
    pe.party = pay.customer or _default_customer(pay)
    pe.posting_date = pay.trx_date
    pe.paid_amount = pay.amount
    pe.received_amount = pay.amount

    allocations = frappe.get_all(
        "Payment Allocation",
        filters={"payment": pay.name},
        fields=["invoice", "amount"],
    )
    for alloc in allocations:
        si = alloc.invoice and _resolve_sales_invoice(alloc.invoice)
        if not si and getattr(pay, "sales_invoice", None):
            si = pay.sales_invoice
        if si:
            row = pe.append("references", {})
            row.reference_doctype = "Sales Invoice"
            row.reference_name = si
            row.total_amount = frappe.db.get_value("Sales Invoice", si, "grand_total") or 0
            row.allocated_amount = alloc.amount or pay.amount

    if not pe.references:
        si = pay.sales_invoice
        if si:
            row = pe.append("references", {})
            row.reference_doctype = "Sales Invoice"
            row.reference_name = si
            row.total_amount = frappe.db.get_value("Sales Invoice", si, "grand_total") or 0
            row.allocated_amount = pay.amount

    pe.insert(ignore_permissions=True)
    pe.submit()
    pay.db_set("doc_ref", f"Payment Entry {pe.name}", update_modified=False)
    return pe.name


def _resolve_sales_invoice(inv_name: str) -> str | None:
    return ensure_sales_invoice_from_custom(inv_name) or custom_invoice_to_sales_invoice(inv_name)


def _default_customer(pay: frappe.Document) -> str | None:
    return getattr(pay, "customer", None)
