from __future__ import annotations

import frappe


def _companies(user: str) -> list[str]:
    try:
        vals = frappe.get_all(
            "User Permission", filters={"user": user, "allow": "Company"}, pluck="for_value"
        )
        return vals or []
    except Exception:
        return []


def _cond(tab: str, field: str, user: str) -> str | None:
    comps = _companies(user)
    if not comps:
        return None
    esc = ", ".join(frappe.db.escape(x) for x in comps)
    return f"`{tab}`.`{field}` in ({esc})"


def invoice_pqc(user: str | None = None) -> str | None:
    user = user or frappe.session.user
    if "System Manager" in set(frappe.get_roles(user)):
        return None
    return _cond("tabInvoice", "company", user)


def payment_pqc(user: str | None = None) -> str | None:
    user = user or frappe.session.user
    if "System Manager" in set(frappe.get_roles(user)):
        return None
    return _cond("tabPayment", "company", user)


def counterparty_pqc(user: str | None = None) -> str | None:
    user = user or frappe.session.user
    if "System Manager" in set(frappe.get_roles(user)):
        return None
    return _cond("tabCounterparty", "company", user)


def contract_pqc(user: str | None = None) -> str | None:
    user = user or frappe.session.user
    if "System Manager" in set(frappe.get_roles(user)):
        return None
    return _cond("tabContract", "company", user)


def service_report_pqc(user: str | None = None) -> str | None:
    user = user or frappe.session.user
    if "System Manager" in set(frappe.get_roles(user)):
        return None
    return _cond("tabService Report", "company", user)


def service_act_pqc(user: str | None = None) -> str | None:
    user = user or frappe.session.user
    if "System Manager" in set(frappe.get_roles(user)):
        return None
    return _cond("tabService Act", "company", user)


def payment_allocation_pqc(user: str | None = None) -> str | None:
    """Scope Payment Allocation by the company of related Payment or Invoice."""
    user = user or frappe.session.user
    if "System Manager" in set(frappe.get_roles(user)):
        return None
    comps = _companies(user)
    if not comps:
        return None
    esc = ", ".join(frappe.db.escape(x) for x in comps)
    return (
        "(exists(select 1 from `tabPayment` p where p.name=`tabPayment Allocation`.payment "
        f"and p.company in ({esc})) or "
        "exists(select 1 from `tabInvoice` i where i.name=`tabPayment Allocation`.invoice "
        f"and i.company in ({esc})))"
    )


def default_has_permission(doc, user: str | None = None) -> bool:
    """Company‑scoped allow for non‑admins; fallback to owner."""
    user = user or frappe.session.user
    if "System Manager" in set(frappe.get_roles(user)):
        return True
    comps = set(_companies(user))
    if not comps:
        # If no explicit assignment, allow and let row‑level checks elsewhere constrain
        return True
    doc_comp = getattr(doc, "company", None)
    if doc_comp and doc_comp in comps:
        return True
    return getattr(doc, "owner", None) == user
