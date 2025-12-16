"""Mapping helpers from custom Invoice/Payment to ERPNext equivalents."""

from __future__ import annotations

from typing import Any

import frappe


def custom_invoice_to_sales_invoice(inv_name: str) -> str | None:
	"""Return linked Sales Invoice if present, else None."""

	return frappe.db.get_value("Invoice", inv_name, "sales_invoice")


def map_invoice_fields(inv_doc: Any) -> dict[str, Any]:
	"""Extract fields for Sales Invoice creation from custom Invoice."""

	return {
		"company": inv_doc.company,
		"customer": inv_doc.customer or inv_doc.counterparty_name,
		"posting_date": inv_doc.invoice_date,
		"project": inv_doc.project,
		"base_grand_total": inv_doc.amount,
		"cost_center": getattr(inv_doc, "cost_center", None),
	}
