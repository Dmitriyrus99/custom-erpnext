import frappe


def execute():
    """Ensure Client has no Desk access; internal roles have Desk access.

    Does not fail the migration if roles are missing.
    """
    updates = {
        "Client": 0,
        "Project Manager": 1,
        "Office Manager": 1,
        "Service Engineer": 1,
        "Chief Accountant": 1,
    }

    for role, desk in updates.items():
        try:
            if frappe.db.exists("Role", role):
                frappe.db.set_value("Role", role, "desk_access", int(desk))
        except Exception:
            # best-effort; ignore errors on old versions/permissions
            pass
