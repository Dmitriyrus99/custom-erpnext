from __future__ import annotations

import contextlib

import frappe

from ferum_custom.patches.utils_migration import (
    _log,
    find_or_create_project,
    has_doctypes,
    migrate_attachments,
)

STATUS_MAP = {
    "Open": "Open",
    "In Progress": "Open",  # stay open until resolved
    "Completed": "Resolved",
    "Closed": "Closed",
}


def _find_issue(sr) -> str | None:
    # Attempt to find existing Issue by subject + project/customer
    cond = {"subject": sr.title}
    if getattr(sr, "project", None):
        cond["project"] = sr.project
    return frappe.db.get_value("Issue", cond, "name")


def execute():
    if not has_doctypes("Issue"):
        _log("migrate_service_request_to_issue: skipped (Issue doctype missing)")
        return
    ok = skipped = att_ok = att_skip = 0
    names = frappe.get_all("Service Request", pluck="name")
    for name in names:
        try:
            sr = frappe.get_doc("Service Request", name)
            issue_name = _find_issue(sr)
            if not issue_name:
                doc = frappe.new_doc("Issue")
                doc.subject = sr.title or sr.name
                if getattr(sr, "customer", None):
                    with contextlib.suppress(Exception):
                        doc.customer = sr.customer
                # Ensure mapped project exists
                project = getattr(sr, "project", None)
                if project:
                    # If it's a custom Service Project, find/create standard Project
                    with contextlib.suppress(Exception):
                        if frappe.db.exists("Service Project", project):
                            sp = frappe.get_doc("Service Project", project)
                            project = find_or_create_project(sp) or project
                    doc.project = project
                # Status
                doc.status = STATUS_MAP.get(sr.status, "Open")
                if getattr(sr, "service_object", None):
                    with contextlib.suppress(Exception):
                        doc.service_object = sr.service_object
                doc.insert(ignore_permissions=True)
                issue_name = doc.name
            o, s = migrate_attachments("Service Request", sr.name, "Issue", issue_name)
            att_ok += o
            att_skip += s
            ok += 1
        except Exception:
            skipped += 1
            frappe.log_error(frappe.get_traceback(), f"Service Request migration failed: {name}")
    _log(
        f"migrate_service_request_to_issue: ok={ok} skipped={skipped} attachments_ok={att_ok} attachments_skipped={att_skip}"
    )
