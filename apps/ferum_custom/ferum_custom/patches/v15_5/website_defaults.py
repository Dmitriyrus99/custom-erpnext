from __future__ import annotations

import frappe


def execute():
    # Ensure brand/logo and basic website fields are set to avoid missing assets on Desk/Website
    try:
        ws = frappe.get_doc("Website Settings")
    except Exception:
        return

    changed = False
    # Fallback brand HTML when empty
    if not (ws.brand_html or "").strip():
        ws.brand_html = "Ferum"
        changed = True

    # If no logo set, try to reuse site identicon
    if not (ws.brand_image or "").strip():
        with frappe.local.flags.ignore_permissions:  # type: ignore[attr-defined]
            try:
                file_url = "/assets/frappe/images/frappe-framework-logo.svg"
                ws.brand_image = file_url
                changed = True
            except Exception:
                pass

    if changed:
        try:
            ws.save(ignore_permissions=True)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Website defaults patch failed to save")

    # Make sure scheduler is enabled on this site to process background jobs
    try:
        frappe.db.set_value("System Settings", None, "enable_scheduler", 1)
    except Exception:
        pass
