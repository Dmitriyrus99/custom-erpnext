from __future__ import annotations

from datetime import datetime

import frappe
from frappe.utils import add_days, now_datetime

DEFAULT_RETENTION_DAYS = 30


def cleanup_stg_raw_records(retention_days: int = DEFAULT_RETENTION_DAYS) -> int:
	"""Delete staging rows older than the retention threshold."""
	if not frappe.db.table_exists("Stg Raw"):
		return 0

	threshold = add_days(now_datetime(), -retention_days)
	count = frappe.db.count("Stg Raw", filters={"ingested_at": ("<", threshold)})
	if not count:
		return 0

	frappe.db.sql(
		"""
        DELETE FROM `tabStg Raw`
        WHERE ingested_at < %s
        """,
		(threshold,),
	)
	return count
