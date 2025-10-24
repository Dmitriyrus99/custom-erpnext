"""Finance application services."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
import typing as t

import frappe


def ensure_invoice_number(doc) -> None:
    if not getattr(doc, "invoice_year", None):
        doc.invoice_year = (doc.invoice_date or dt.date.today()).year
    if not getattr(doc, "invoice_no", None):
        doc.invoice_no = doc.name


def create_invoice(
    *,
    company: str,
    project: str | None,
    customer: str,
    contract: str | None,
    invoice_date: dt.date | None,
    items: list[dict[str, t.Any]],
) -> str:
    doc = frappe.new_doc("Invoice")
    doc.company = company
    doc.project = project
    doc.customer = customer
    doc.contract = contract
    doc.invoice_date = invoice_date or dt.date.today()
    doc.status = "Draft"
    doc.amount = sum(Decimal(str(item.get("amount") or 0)) for item in items)
    doc.extend("items", items)
    ensure_invoice_number(doc)
    doc.insert()
    return doc.name


def record_payment(
    *,
    company: str,
    trx_date: dt.date,
    amount: float,
    direction: str,
    article: str | None,
    counterparty: str | None,
    allocations: list[dict[str, t.Any]] | None = None,
) -> str:
    doc = frappe.new_doc("Payment")
    doc.company = company
    doc.trx_date = trx_date
    doc.amount = amount
    doc.direction = direction
    doc.article = article
    doc.counterparty = counterparty
    doc.insert()
    if allocations:
        for alloc in allocations:
            pa = frappe.new_doc("Payment Allocation")
            pa.payment = doc.name
            pa.invoice = alloc["invoice"]
            pa.amount = alloc["amount"]
            pa.insert()
    return doc.name
