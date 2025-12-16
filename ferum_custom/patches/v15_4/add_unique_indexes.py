from __future__ import annotations

import frappe
from ferum_custom.ferum_custom.patches.utils_migration import _log, has_doctypes

INDEXES = [
	("idx_contract_company_normalized", "Contract", "company, contract_no_normalized", True),
	("idx_invoice_company_year_number", "Invoice", "company, invoice_year, invoice_no", True),
	("idx_payment_company_direction", "Payment", "company, direction", False),
	("idx_stg_raw_ingested_at", "Stg Raw", "ingested_at", False),
]


def _ensure_index(doctype: str, columns: str, name: str, unique: bool) -> None:
	if not has_doctypes(doctype):
		return
	fields = [field.strip().strip("`") for field in columns.split(",")]
	try:
		if unique:
			frappe.db.add_unique(doctype, fields, constraint_name=name)
		else:
			frappe.db.add_index(doctype, fields, index_name=name)
	except Exception:
		_log(f"Unable to add index {name} on {doctype}")


def execute():
	for name, table, columns, unique in INDEXES:
		_ensure_index(table, columns, name, unique)
