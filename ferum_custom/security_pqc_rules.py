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
			"User Permission",
			filters={"user": user, "allow": "Company"},
			pluck="for_value",
			ignore_permissions=True,
		)
		return vals or []
	except Exception:
		return []


def _departments(user: str) -> list[str]:
	try:
		vals = frappe.get_all(
			"User Permission",
			filters={"user": user, "allow": "Service Department"},
			pluck="for_value",
			ignore_permissions=True,
		)
		return vals or []
	except Exception:
		return []


def _company_condition(tab: str, field: str, user: str) -> str | None:
	comps = _companies(user)
	if not comps:
		return None
	esc = ", ".join(frappe.db.escape(x) for x in comps)
	return f"`{tab}`.{field} in ({esc})"


def sales_invoice_pqc(user: str | None = None) -> str | None:
	user = user or frappe.session.user
	if _is_admin(user):
		return None
	return _company_condition("tabSales Invoice", "company", user)


def invoice_pqc(user: str | None = None) -> str | None:
	"""Permission query condition for custom Invoice (ferum_custom)."""
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


def project_pqc(user: str | None = None) -> str | None:
	user = user or frappe.session.user
	if _is_admin(user):
		return None
	return _company_condition("tabProject", "company", user)


def timesheet_pqc(user: str | None = None) -> str | None:
	user = user or frappe.session.user
	if _is_admin(user):
		return None
	company_cond = _company_condition("tabTimesheet", "company", user)
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
		f"and exists(select 1 from `tabSales Invoice` i where i.name=`tabPayment Allocation`.invoice "
		f"and i.company in ({esc})))"
	)


def data_issue_pqc(user: str | None = None) -> str | None:
	user = user or frappe.session.user
	roles = _roles(user)
	if _is_admin(user) or SECURITY_ROLE in roles:
		return None
	return "FALSE"


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
