from __future__ import annotations

import frappe
from ferum_custom.ferum_custom.data_cleanup.contracts import normalize_contracts as _normalize_contracts


def execute():
	"""Normalize contract numbers and statuses, logging Data Issues for duplicates."""
	try:
		_normalize_contracts()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "normalize_contracts failed")
