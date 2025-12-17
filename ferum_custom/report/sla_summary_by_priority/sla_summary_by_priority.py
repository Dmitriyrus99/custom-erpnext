from __future__ import annotations

from typing import Any

import frappe


def execute(filters: dict[str, Any] | None = None) -> tuple[list[dict], list[dict[str, Any]]]:
    filters = filters or {}

    company = filters.get("company")
    project = filters.get("project")
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")

    req_filters: dict[str, Any] = {
        "status": ["in", ["Completed", "Closed"]],
    }
    if company:
        req_filters["company"] = company
    if project:
        req_filters["project"] = project

    rows = frappe.get_all(
        "Service Request",
        filters=req_filters,
        fields=[
            "name",
            "priority",
            "reported_datetime",
            "actual_end_datetime",
            "sla_deadline",
        ],
    )

    from_dt = frappe.utils.get_datetime(from_date) if from_date else None
    to_dt = frappe.utils.get_datetime(to_date) if to_date else None

    stats: dict[str, dict[str, Any]] = {}
    for r in rows:
        prio = r.get("priority") or "-"
        rd = r.get("reported_datetime")
        ed = r.get("actual_end_datetime")
        sla = r.get("sla_deadline")
        if not ed or not rd:
            continue

        ed_dt = frappe.utils.get_datetime(ed)
        rd_dt = frappe.utils.get_datetime(rd)
        if from_dt and ed_dt < from_dt:
            continue
        if to_dt and ed_dt > to_dt:
            continue

        bucket = stats.setdefault(
            prio, {"priority": prio, "total": 0, "within": 0, "sum_hours": 0.0}
        )
        bucket["total"] += 1
        hours = (ed_dt - rd_dt).total_seconds() / 3600.0
        bucket["sum_hours"] += hours
        if sla:
            sla_dt = frappe.utils.get_datetime(sla)
            if ed_dt <= sla_dt:
                bucket["within"] += 1

    data: list[dict[str, Any]] = []
    for prio, s in stats.items():
        total = s["total"] or 0
        within = s["within"] or 0
        avg = (s["sum_hours"] / total) if total else 0.0
        pct = (within * 100.0 / total) if total else 0.0
        data.append(
            {
                "priority": prio,
                "total_closed": total,
                "closed_within_sla": within,
                "percent_within_sla": round(pct, 2),
                "avg_resolution_hours": round(avg, 2),
            }
        )

    columns = [
        {"label": "Priority", "fieldname": "priority", "fieldtype": "Data", "width": 120},
        {"label": "Closed", "fieldname": "total_closed", "fieldtype": "Int", "width": 100},
        {"label": "Within SLA", "fieldname": "closed_within_sla", "fieldtype": "Int", "width": 110},
        {
            "label": "% Within SLA",
            "fieldname": "percent_within_sla",
            "fieldtype": "Float",
            "width": 130,
        },
        {
            "label": "Avg Resolution (h)",
            "fieldname": "avg_resolution_hours",
            "fieldtype": "Float",
            "width": 160,
        },
    ]

    return columns, data
