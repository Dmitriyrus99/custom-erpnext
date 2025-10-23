from __future__ import annotations

"""Automation wrappers for scheduled jobs (monitoring, back-ups).

These functions are referenced from hooks.scheduler_events and primarily
delegate to site_ops helpers to keep logic centralized.
"""

import frappe

from ferum_custom.ferum_custom import site_ops
from ferum_custom.ferum_custom.settings import get_list_setting
from ferum_custom.ferum_custom.utils import get_users_by_roles


def send_daily_overdue_report() -> dict:
    """Daily summary of overdue Service Requests/Issues (email to PM/OM)."""
    try:
        return site_ops.daily_overdue_summary_email()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "send_daily_overdue_report failed")
        return {"status": "error"}


def send_weekly_overdue_maintenance_report() -> dict:
    """Weekly summary of overdue maintenance schedules (email to PM/OM)."""
    try:
        return site_ops.weekly_overdue_maintenance_schedules_email()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "send_weekly_overdue_maintenance_report failed")
        return {"status": "error"}


def run_nightly_backup_to_gdrive() -> dict:
    """Nightly DB backup; enqueue on 'long' queue to isolate heavy job."""
    try:
        frappe.enqueue("ferum_custom.ferum_custom.site_ops.backup_to_drive", queue="long")
        return {"status": "queued", "queue": "long"}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "run_nightly_backup_to_gdrive failed")
        return {"status": "error"}


def enqueue_weekly_full_backup() -> dict:
    """Enqueue weekly (DB+files) backup onto 'long' queue."""
    try:
        frappe.enqueue("ferum_custom.ferum_custom.site_ops.weekly_full_backup_to_drive", queue="long")
        return {"status": "queued", "queue": "long"}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "enqueue_weekly_full_backup failed")
        return {"status": "error"}


def enqueue_daily_drive_backfill_small() -> dict:
    """Enqueue incremental drive backfill onto 'long' queue."""
    try:
        frappe.enqueue("ferum_custom.ferum_custom.site_ops.daily_backfill_drive_ids_small", queue="long")
        return {"status": "queued", "queue": "long"}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "enqueue_daily_drive_backfill_small failed")
        return {"status": "error"}


def queue_healthcheck(threshold: int = 100) -> dict:
    """Check RQ queues (default/short/long) and warn when backed up."""
    try:
        from frappe.utils.background_jobs import get_queue

        names = ["default", "short", "long"]
        stats = {}
        warn = []
        for n in names:
            q = get_queue(n)
            count = q.job_count if hasattr(q, "job_count") else len(q.jobs)
            stats[n] = count
            if count > threshold:
                warn.append((n, count))
        if warn:
            frappe.logger().warning(f"RQ queues backed up: {warn}")
        return {"status": "ok", "queues": stats}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "queue_healthcheck failed")
        return {"status": "error"}


def run_permission_audit() -> dict:
    """Weekly hardening + RPPR scan and admin alert for risky entries."""
    result = {"status": "ok"}
    try:
        site_ops.harden_permissions()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "run_permission_audit: harden_permissions failed")
        result["status"] = "degraded"

    try:
        risky = _collect_risky_rppr()
        result["risky_count"] = len(risky)
        if risky:
            _email_risky_rppr(risky, subject_prefix="Weekly RPPR Audit")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "run_permission_audit: RPPR scan failed")
        result["status"] = "error"
    return result


def on_role_update_audit(doc=None, method: str | None = None) -> None:
    """Audit entry point for Role on_update to catch risky changes.

    For now, this function only logs the update and relies on weekly
    hardening to enforce stricter rules.
    """
    try:
        role_name = getattr(doc, "role_name", getattr(doc, "name", "Role")) if doc else "Role"
        frappe.logger().info(f"Role updated: {role_name}")
    except Exception:
        pass


# ------------------------------
# RPPR helpers
# ------------------------------


def _allowed_admin_roles() -> set[str]:
    roles = set(get_list_setting("admin_allowed_roles"))
    roles.add("System Manager")
    return roles


def _collect_risky_rppr() -> list[dict]:
    allowed = list(_allowed_admin_roles())
    try:
        rows = frappe.get_all(
            "Role Permission for Page and Report",
            filters={"role": ["not in", allowed]},
            fields=["name", "role", "page", "report", "owner", "modified_by", "creation", "modified"],
            order_by="modified desc",
        )
    except Exception:
        rows = []
    # Exclude rows without target (neither page nor report)
    risky = [r for r in rows if r.get("page") or r.get("report")]
    return risky


def _email_risky_rppr(rows: list[dict], subject_prefix: str = "RPPR Audit") -> None:
    recipients = list(get_users_by_roles(["System Manager"]))
    if not recipients:
        return
    lines = [
        f"- role={r.get('role')} target={'Page:' + r.get('page') if r.get('page') else 'Report:' + r.get('report')} by={r.get('owner')} modified_by={r.get('modified_by')}"
        for r in rows
    ]
    body = "\n".join(["Potentially risky Role Permission for Page and Report entries:", *lines])
    try:
        frappe.sendmail(recipients=recipients, subject=f"{subject_prefix}: {len(rows)} entries", message=body)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "RPPR audit email failed")


def on_rppr_after_insert(doc, method: str | None = None) -> None:
    """Alert on new RPPR entries created by non-admin roles or for non-admin access."""
    try:
        allowed = _allowed_admin_roles()
        # if role granted is not an allowed admin role, flag
        if getattr(doc, "role", None) not in allowed:
            _email_risky_rppr([
                {
                    "role": getattr(doc, "role", None),
                    "page": getattr(doc, "page", None),
                    "report": getattr(doc, "report", None),
                    "owner": getattr(doc, "owner", None),
                    "modified_by": getattr(doc, "modified_by", None),
                }
            ], subject_prefix="RPPR Created")
            return
        # If creator is not System Manager, still alert for visibility
        user = frappe.session.user
        if user and "System Manager" not in set(frappe.get_roles(user)):
            _email_risky_rppr([
                {
                    "role": getattr(doc, "role", None),
                    "page": getattr(doc, "page", None),
                    "report": getattr(doc, "report", None),
                    "owner": getattr(doc, "owner", None),
                    "modified_by": getattr(doc, "modified_by", None),
                }
            ], subject_prefix="RPPR Created by Non-Admin")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "on_rppr_after_insert failed")
