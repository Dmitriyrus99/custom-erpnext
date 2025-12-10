from __future__ import annotations

import frappe

from ferum_custom.ferum_custom.data_cleanup.contracts import normalize_contracts as normalize_contracts_data
from ferum_custom.ferum_custom.data_cleanup.stg_raw import cleanup_stg_raw_records


def normalize_contracts_job() -> None:
	try:
		normalize_contracts_data()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "normalize_contracts_job failed")


def cleanup_stg_raw_job() -> None:
	try:
		cleanup_stg_raw_records()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "cleanup_stg_raw_job failed")
