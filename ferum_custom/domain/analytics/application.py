"""Analytics application services (materialized view refresh)."""

from __future__ import annotations

import frappe

MATERIALIZED_VIEWS = [
	"mv_invoice_balance",
	"mv_contract_overview",
	"mv_cashflow_daily",
]


def refresh_view(view: str) -> None:
	try:
		frappe.db.sql(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}")
	except Exception:
		try:
			frappe.db.sql(f"REFRESH MATERIALIZED VIEW {view}")
		except Exception:
			frappe.log_error(f"Materialized view refresh failed: {view}")


def refresh_all_materialized_views() -> None:
	for view in MATERIALIZED_VIEWS:
		refresh_view(view)
