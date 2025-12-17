from __future__ import annotations

import contextlib

import frappe


def _add(doctype: str, fields: list[str], name: str) -> None:
    """Add an index if not present. Safe on both MariaDB and Postgres."""
    try:
        frappe.db.add_index(doctype, fields, index_name=name)
    except Exception:
        # Non-fatal: skip on errors (e.g., index already exists)
        pass


def execute():
    # Issue (ERPNext)
    with contextlib.suppress(Exception):
        _add("Issue", ["status"], "idx_issue_status")
        _add("Issue", ["project"], "idx_issue_project")
        _add("Issue", ["assigned_engineer"], "idx_issue_assigned_engineer")
        _add("Issue", ["customer"], "idx_issue_customer")
        _add("Issue", ["company"], "idx_issue_company")
        _add("Issue", ["status", "project"], "idx_issue_status_project")
        _add("Issue", ["assigned_engineer", "status"], "idx_issue_assigned_status")
        _add("Issue", ["service_maintenance_schedule"], "idx_issue_schedule")

    # Service Request (custom)
    with contextlib.suppress(Exception):
        _add("Service Request", ["status"], "idx_sr_status")
        _add("Service Request", ["assigned_to"], "idx_sr_assigned_to")
        _add("Service Request", ["project"], "idx_sr_project")
        _add("Service Request", ["customer"], "idx_sr_customer")
        _add("Service Request", ["company"], "idx_sr_company")
        _add("Service Request", ["sla_deadline"], "idx_sr_sla_deadline")
        _add("Service Request", ["status", "project"], "idx_sr_status_project")
        _add("Service Request", ["assigned_to", "status"], "idx_sr_assigned_status")

    # Project (standard)
    with contextlib.suppress(Exception):
        _add("Project", ["project_manager"], "idx_project_manager")
        _add("Project", ["customer"], "idx_project_customer")
        _add("Project", ["company"], "idx_project_company")

    # Timesheet and its child details (standard)
    with contextlib.suppress(Exception):
        _add("Timesheet", ["status"], "idx_timesheet_status")
        _add("Timesheet", ["parent_project"], "idx_timesheet_parent_project")
        _add("Timesheet Detail", ["project"], "idx_timesheet_detail_project")
