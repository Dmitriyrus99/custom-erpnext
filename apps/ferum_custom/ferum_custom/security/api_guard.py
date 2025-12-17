from __future__ import annotations

import frappe
from frappe import _


def require_post_if_http() -> None:
    """Enforce POST-only when invoked via HTTP; allow scheduler/CLI (no request)."""
    try:
        if getattr(frappe, "request", None) and frappe.request:  # type: ignore[attr-defined]
            if (frappe.request.method or "").upper() != "POST":
                frappe.throw(_("This endpoint only accepts POST requests."), frappe.PermissionError)
    except Exception:
        # If request is not present (scheduler/CLI), do nothing
        pass


def require_roles_if_http(roles: list[str]) -> None:
    """Enforce role membership when invoked via HTTP; allow scheduler/CLI."""
    try:
        if getattr(frappe, "request", None) and frappe.request:  # type: ignore[attr-defined]
            if not any(r in set(frappe.get_roles()) for r in roles):
                frappe.throw(_("Not permitted"), frappe.PermissionError)
    except Exception:
        pass
