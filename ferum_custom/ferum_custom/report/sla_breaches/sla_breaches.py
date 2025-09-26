from __future__ import annotations

import datetime as dt
from typing import Any

import frappe


def execute(filters: dict[str, Any] | None = None) -> tuple[list[dict], list[dict[str, Any]]]:
	filters = filters or {}

	company = filters.get("company")
	project = filters.get("project")
	priority = filters.get("priority")
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")

	now = dt.datetime.now()

	req_filters: dict[str, Any] = {
		"status": ["not in", ["Completed", "Closed"]],
	}
	if company:
		req_filters["company"] = company
	if project:
		req_filters["project"] = project
	if priority:
		req_filters["priority"] = priority
	if from_date:
		req_filters["reported_datetime"] = [">=", from_date]
	if to_date:
		req_filters.setdefault("reported_datetime", [">=", dt.date(1970, 1, 1)])
		# Add upper bound by additional filter via manual post-filtering if needed

	rows = frappe.get_all(
		"Service Request",
		filters=req_filters,
		fields=[
			"name",
			"title",
			"customer",
			"project",
			"type",
			"priority",
			"reported_datetime",
			"sla_deadline",
			"status",
		],
		order_by="sla_deadline asc",
	)

	data: list[dict[str, Any]] = []
	for r in rows:
		sla_deadline = r.get("sla_deadline")
		if not sla_deadline:
			continue
		try:
			sla_dt = frappe.utils.get_datetime(sla_deadline)
		except Exception:
			continue
		# breach only if past deadline
		if sla_dt and sla_dt < now:
			overdue_hours = round((now - sla_dt).total_seconds() / 3600.0, 2)
			if to_date:
				# ensure reported_datetime <= to_date if provided
				rd = r.get("reported_datetime")
				if rd and str(rd) > str(to_date):
					continue
			r["overdue_hours"] = overdue_hours
			data.append(r)

	columns = [
		{
			"label": "Name",
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Service Request",
			"width": 150,
		},
		{"label": "Title", "fieldname": "title", "fieldtype": "Data", "width": 220},
		{
			"label": "Customer",
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 160,
		},
		{
			"label": "Project",
			"fieldname": "project",
			"fieldtype": "Link",
			"options": "Service Project",
			"width": 160,
		},
		{"label": "Type", "fieldname": "type", "fieldtype": "Data", "width": 110},
		{"label": "Priority", "fieldname": "priority", "fieldtype": "Data", "width": 110},
		{"label": "Reported", "fieldname": "reported_datetime", "fieldtype": "Datetime", "width": 160},
		{"label": "SLA Deadline", "fieldname": "sla_deadline", "fieldtype": "Datetime", "width": 160},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 110},
		{"label": "Overdue (h)", "fieldname": "overdue_hours", "fieldtype": "Float", "width": 120},
	]

	return columns, data
