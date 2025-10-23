import frappe


def execute():
    """Hide/lock legacy master doctypes used before migration (Service Object, Invoice)."""
    targets = ["Service Object", "Invoice"]
    for dt in targets:
        if not frappe.db.exists("DocType", dt):
            continue
        try:
            doc = frappe.get_doc("DocType", dt)
            # Minimal read-only access for System Manager
            doc.permissions = []  # type: ignore[assignment]
            p = doc.append("permissions", {})  # type: ignore[attr-defined]
            p.role = "System Manager"
            p.read = 1
            for f in ("create", "write", "delete", "export", "email", "print", "report"):
                setattr(p, f, 0)
            doc.is_submittable = 0
            doc.read_only = 1
            doc.save(ignore_permissions=True)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"hide_legacy_master_doctypes failed: {dt}")

