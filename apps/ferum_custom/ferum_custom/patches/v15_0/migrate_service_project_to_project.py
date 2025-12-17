from __future__ import annotations

import frappe

from ferum_custom.patches.utils_migration import (
    _log,
    find_or_create_project,
    has_doctypes,
    migrate_attachments,
)


def execute():
    if not has_doctypes("Project"):
        _log("migrate_service_project_to_project: skipped (Project doctype missing)")
        return
    """Migrate Service Project records to standard Project.

    - Idempotent: finds Project by (project_name, customer) before creating
    - Logs counts; continues on errors
    - Moves CustomAttachment to Project File links
    """
    ok = skipped = att_ok = att_skip = 0
    names = frappe.get_all("Service Project", pluck="name")
    for name in names:
        try:
            sp = frappe.get_doc("Service Project", name)
            proj_name = find_or_create_project(sp)
            if not proj_name:
                skipped += 1
                continue
            o, s = migrate_attachments("Service Project", sp.name, "Project", proj_name)
            att_ok += o
            att_skip += s
            ok += 1
        except Exception:
            skipped += 1
            frappe.log_error(frappe.get_traceback(), f"Service Project migration failed: {name}")

    _log(
        f"migrate_service_project_to_project: ok={ok} skipped={skipped} attachments_ok={att_ok} attachments_skipped={att_skip}"
    )
