import frappe


def execute():
    """Restrict legacy custom DocTypes (Service Request/Report) to read-only System Manager.

    - Remove all permissions except System Manager (read only)
    - Hide from "New" by setting read_only and disallow on_submit, etc.
    """
    targets = ["Service Request", "Service Report"]
    for dt in targets:
        if not frappe.db.exists("DocType", dt):
            continue
        try:
            doc = frappe.get_doc("DocType", dt)
            # Clear and re-add minimal perms
            doc.permissions = []  # type: ignore[assignment]
            p = doc.append("permissions", {})  # type: ignore[attr-defined]
            p.role = "System Manager"
            p.read = 1
            p.create = 0
            p.write = 0
            p.delete = 0
            p.export = 0
            p.email = 0
            p.print = 0
            p.report = 0
            # Hard disable mutations
            doc.is_submittable = 0
            doc.read_only = 1
            doc.save(ignore_permissions=True)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"hide legacy doctype failed: {dt}")
