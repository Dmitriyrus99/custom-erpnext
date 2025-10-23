from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import frappe


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

    # Build SQL with robust left join on new custom fields; include fallback by subject match
    sql = """
        SELECT
            sms.name AS schedule,
            sms.schedule_name AS schedule_title,
            sms.service_project AS project,
            COALESCE(so.customer, sms.customer) AS customer,
            sms.next_due_date AS due_date,
            smsi.service_object AS service_object,
            COALESCE(smsi.description, sms.description) AS task_description,
            i.name AS issue,
            i.subject AS issue_subject,
            i.status AS issue_status,
            i.assigned_engineer AS assigned_engineer,
            i.asset AS asset
        FROM `tabService Maintenance Schedule` sms
        JOIN `tabService Maintenance Schedule Item` smsi ON smsi.parent = sms.name
        LEFT JOIN `tabService Object` so ON so.name = smsi.service_object
        LEFT JOIN `tabIssue` i ON (
            (i.service_maintenance_schedule = sms.name AND i.service_object = smsi.service_object)
            OR (
                i.subject LIKE CONCAT('Scheduled Maintenance: ', smsi.service_object, ' (', sms.schedule_name, '%')
            )
        )
        WHERE sms.docstatus < 2
          AND sms.next_due_date BETWEEN %(from_date)s AND %(to_date)s
          AND (%(project)s IS NULL OR sms.service_project = %(project)s OR so.project = %(project)s)
          AND (%(customer)s IS NULL OR sms.customer = %(customer)s OR so.customer = %(customer)s)
        ORDER BY sms.next_due_date, sms.name, smsi.service_object
    """

    params = {"from_date": from_date, "to_date": to_date, "project": project, "customer": customer}
    data = frappe.db.sql(sql, params, as_dict=True)

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
