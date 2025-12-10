from __future__ import annotations

from typing import Any

import frappe


def log_event(
    *,
    event_type: str,
    ref_doctype: str | None = None,
    ref_docname: str | None = None,
    message: str | None = None,
    user: str | None = None,
    details: dict[str, Any] | None = None,
) -> str | None:
    """Create an Audit Event with structured details.

    Returns the created document name or None on failure.
    """
    try:
        doc = frappe.get_doc(
            {
                "doctype": "Audit Event",
                "event_type": event_type,
                "ref_doctype": ref_doctype,
                "ref_docname": ref_docname,
                "message": message,
                "details_json": details or {},
            }
        )
        if user:
            doc.user = user
        else:
            try:
                doc.user = frappe.session.user
            except Exception:
                pass
        doc.insert(ignore_permissions=True)
        return doc.name
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Audit log failed: {event_type}")
        return None

