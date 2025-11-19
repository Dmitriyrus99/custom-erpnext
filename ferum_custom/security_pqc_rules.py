from __future__ import annotations

import frappe

from ferum_custom.ferum_custom.utils import get_allowed_customers

SYSTEM_ROLE = "System Manager"
SECURITY_ROLE = "Security Engineer"


def _roles(user: str) -> set[str]:
    return set(frappe.get_roles(user))


def _is_admin(user: str) -> bool:
    return SYSTEM_ROLE in _roles(user)


def _companies(user: str) -> list[str]:
    try:
        vals = frappe.get_all(
            "User Permission", filters={"user": user, "allow": "Company"}, pluck="for_value"
        )
        return vals or []
    except Exception:
        return []


def _company_condition(tab: str, field: str, user: str) -> str | None:
    comps = _companies(user)
    if not comps:
        return None
    esc = ", ".join(frappe.db.escape(x) for x in comps)
    return f"`{tab}`.`{field}` in ({esc})"


def _customers_condition(user: str) -> str | None:
    customers = get_allowed_customers(user)
    if not customers:
        return None
    esc = ", ".join(frappe.db.escape(x) for x in customers)
    return f"`tabService Request`.customer IN ({esc})"


def _engineer_condition(user: str) -> str:
    return f"`tabService Request`.assigned_to = {frappe.db.escape(user)}"


def invoice_pqc(user: str | None = None) -> str | None:
    user = user or frappe.session.user
    if _is_admin(user):
        return None
    return _company_condition("tabInvoice", "company", user)


def payment_pqc(user: str | None = None) -> str | None:
    user = user or frappe.session.user
    if _is_admin(user):
        return None
    return _company_condition("tabPayment", "company", user)


def counterparty_pqc(user: str | None = None) -> str | None:
    user = user or frappe.session.user
    if _is_admin(user):
        return None
    return _company_condition("tabCounterparty", "company", user)


def contract_pqc(user: str | None = None) -> str | None:
    user = user or frappe.session.user
    if _is_admin(user):
        return None
    return _company_condition("tabContract", "company", user)


def service_request_pqc(user: str | None = None) -> str | None:
    user = user or frappe.session.user
    if _is_admin(user):
        return None
    conds: list[str] = []
    company_cond = _company_condition("tabService Request", "company", user)
    if company_cond:
        conds.append(company_cond)
    if "Service Engineer" in _roles(user):
        conds.append(_engineer_condition(user))
    customer_cond = _customers_condition(user)
    if customer_cond:
        conds.append(customer_cond)
    return " and ".join(f"({c})" for c in conds) if conds else None


def service_report_pqc(user: str | None = None) -> str | None:
    user = user or frappe.session.user
    if _is_admin(user):
        return None
    company_cond = _company_condition("tabService Report", "company", user)
    return company_cond


def service_act_pqc(user: str | None = None) -> str | None:
    user = user or frappe.session.user
    if _is_admin(user):
        return None
    company_cond = _company_condition("tabService Act", "company", user)
    return company_cond


def payment_allocation_pqc(user: str | None = None) -> str | None:
    user = user or frappe.session.user
    if _is_admin(user):
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


def data_issue_pqc(user: str | None = None) -> str | None:
    user = user or frappe.session.user
    roles = _roles(user)
    if _is_admin(user) or SECURITY_ROLE in roles:
        return None
    return "FALSE"


def service_request_has_permission(doc, user: str | None = None) -> bool:
    user = user or frappe.session.user
    if _is_admin(user):
        return True
    if getattr(doc, "assigned_to", None) == user:
        return True
    allowed_customers = set(get_allowed_customers(user))
    if allowed_customers and getattr(doc, "customer", None) in allowed_customers:
        return True
    return False


def default_has_permission(doc, user: str | None = None) -> bool:
    """Company‑scoped allow for non‑admins; fallback to owner."""
    user = user or frappe.session.user
    if _is_admin(user):
        return True
    comps = set(_companies(user))
    if not comps:
        return True
    doc_comp = getattr(doc, "company", None)
    if doc_comp and doc_comp in comps:
        return True
    return getattr(doc, "owner", None) == user
