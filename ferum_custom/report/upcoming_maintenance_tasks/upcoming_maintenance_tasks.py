from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import frappe
from frappe.query_builder import DocType, functions as fn


def _date_range_from_filters(filters: dict[str, Any]) -> tuple[str, str]:
    today = date.today()
    preset = (filters.get("preset_range") or "").strip().lower()
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")

    if from_date and to_date:
        return str(from_date), str(to_date)

    if preset == "next 30 days":
        return str(today), str(today + timedelta(days=30))
    # default
    return str(today), str(today + timedelta(days=7))


def execute(filters: dict[str, Any] | None = None) -> tuple[list[dict], list[dict[str, Any]]]:
    filters = filters or {}

    from_date, to_date = _date_range_from_filters(filters)
    project = filters.get("project")
    customer = filters.get("customer")

    SMS = DocType("Service Maintenance Schedule")
    SMSI = DocType("Service Maintenance Schedule Item")
    SO = DocType("Service Object")
    Issue = DocType("Issue")

    query = (
        frappe.qb.from_(SMS)
        .join(SMSI)
        .on(SMSI.parent == SMS.name)
        .left_join(SO)
        .on(SO.name == SMSI.service_object)
        .left_join(Issue)
        .on(
            (Issue.service_maintenance_schedule == SMS.name)
            & (Issue.service_object == SMSI.service_object)
        )
        .select(
            SMS.name.as_("schedule"),
            SMS.schedule_name.as_("schedule_title"),
            SMS.service_project.as_("project"),
            fn.Coalesce(SO.customer, SMS.customer).as_("customer"),
            SMS.next_due_date.as_("due_date"),
            SMSI.service_object.as_("service_object"),
            fn.Coalesce(SMSI.description, SMS.description).as_("task_description"),
            Issue.name.as_("issue"),
            Issue.subject.as_("issue_subject"),
            Issue.status.as_("issue_status"),
            Issue.assigned_engineer.as_("assigned_engineer"),
            Issue.asset.as_("asset"),
        )
        .where(SMS.docstatus < 2)
        .where(SMS.next_due_date.between(from_date, to_date))
    )

    if project:
        query = query.where((SMS.service_project == project) | (SO.project == project))
    if customer:
        query = query.where((SMS.customer == customer) | (SO.customer == customer))

    data = query.orderby(SMS.next_due_date, SMS.name, SMSI.service_object).run(as_dict=True)

    columns = [
        {"label": "Schedule", "fieldname": "schedule", "fieldtype": "Link", "options": "Service Maintenance Schedule", "width": 160},
        {"label": "Schedule Title", "fieldname": "schedule_title", "fieldtype": "Data", "width": 180},
        {"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 110},
        {"label": "Service Object", "fieldname": "service_object", "fieldtype": "Link", "options": "Service Object", "width": 200},
        {"label": "Project", "fieldname": "project", "fieldtype": "Link", "options": "Service Project", "width": 160},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 160},
        {"label": "Task Description", "fieldname": "task_description", "fieldtype": "Data", "width": 240},
        {"label": "Issue", "fieldname": "issue", "fieldtype": "Link", "options": "Issue", "width": 130},
        {"label": "Issue Subject", "fieldname": "issue_subject", "fieldtype": "Data", "width": 220},
        {"label": "Issue Status", "fieldname": "issue_status", "fieldtype": "Data", "width": 120},
        {"label": "Assigned Engineer", "fieldname": "assigned_engineer", "fieldtype": "Link", "options": "User", "width": 160},
        {"label": "Asset", "fieldname": "asset", "fieldtype": "Link", "options": "Asset", "width": 160},
    ]

    return columns, data
