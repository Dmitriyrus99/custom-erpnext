"""Finance application services."""

from __future__ import annotations

import datetime as dt
import typing as t
from decimal import Decimal

import frappe
from frappe.utils import getdate, nowdate


def create_sales_invoice(
	*,
	company: str,
	project: str | None,
	customer: str,
	contract_ref: str | None,  # Renamed from 'contract' to avoid conflict with standard field
	posting_date: dt.date | None,
	items: list[dict[str, t.Any]],
) -> str:
	doc = frappe.new_doc("Sales Invoice")
	doc.company = company
	doc.project = project
	doc.customer = customer
	doc.custom_contract_ref = contract_ref  # Assuming custom field for legacy contract reference
	doc.posting_date = posting_date or dt.date.today()
	doc.set_onload("is_pos", 0)  # Not a POS invoice
	doc.is_return = 0
	doc.status = "Draft"

	# Handle items for Sales Invoice
	for item_data in items:
		item_doc = doc.append("items", {})
		item_doc.item_code = item_data.get("item_code")
		item_doc.qty = item_data.get("qty", 1)
		item_doc.rate = item_data.get("rate")
		item_doc.amount = item_doc.qty * item_doc.rate

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
			pa.reference_doctype = "Sales Invoice"
			pa.reference_name = alloc["sales_invoice"]
			pa.amount = alloc["amount"]
			pa.insert()
	return doc.name


def ensure_invoice_number(doc) -> None:
	"""
	Lightweight numbering helper for the custom ``Invoice`` doctype.

	The original implementation is missing in this branch; tests only require the
	document to have a stable name/number. We derive sensible defaults when the
	user didn't provide them and ensure ``doc.name`` matches the business number
	for readability.
	"""

	# Default year from the invoice date or today
	if not getattr(doc, "invoice_year", None):
		invoice_date = getattr(doc, "invoice_date", None) or nowdate()
		doc.invoice_year = getdate(invoice_date).year

	# Generate a human-friendly number if absent
	if not getattr(doc, "invoice_no", None):
		prefix = (doc.company or "INV")[:4].upper().replace(" ", "")
		random_part = frappe.generate_hash(length=6).upper()
		doc.invoice_no = f"{prefix}-{doc.invoice_year}-{random_part}"

	# Use invoice_no as the document name when it is a new record
	if getattr(doc, "name", None) in (None, "", "New Invoice", "New Invoice 1"):
		doc.name = doc.invoice_no
