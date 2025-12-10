from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.rate_limiter import rate_limit
from frappe.desk.query_report import run as frappe_query_report_run


def _coerce_filters(filters: Any) -> tuple[dict[str, Any], bool]:
	if isinstance(filters, str):
		try:
			data = frappe.parse_json(filters) if filters else {}
		except Exception:
			data = {}
		return data, True
	if isinstance(filters, dict):
		return dict(filters), False
	return {}, True


def _apply_project_default(report_name: str, filters: Any) -> Any:
	if report_name != "Sales Invoices by Project":
		return filters

	data, needs_serialization = _coerce_filters(filters)
	if "project" not in data:
		data["project"] = None
		if needs_serialization:
			return json.dumps(data)
		return data

	if needs_serialization:
		return filters
	return data


@frappe.whitelist()
@rate_limit(limit=60, seconds=60, methods=["GET"])  # 60 calls/min per IP
def run_with_defaults(
	report_name: str,
	filters: Any | None = None,
	user: str | None = None,
	custom_columns: Any | None = None,
	is_tree: bool | None = None,
	parent_field: str | None = None,
	**kwargs: Any,
):
	filters = _apply_project_default(report_name, filters)
	return frappe_query_report_run(
		report_name,
		filters,
		user=user,
		custom_columns=custom_columns,
		is_tree=is_tree,
		parent_field=parent_field,
		**kwargs,
	)


import frappe.desk.query_report as _query_report_module

if getattr(_query_report_module.run, "__module__", "").startswith("frappe.desk.query_report"):
	_query_report_module.run = run_with_defaults
