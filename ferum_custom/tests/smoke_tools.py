from __future__ import annotations

import contextlib
import json
from typing import Any

import frappe


def _ensure_module_registered() -> None:
    """Make sure custom DocTypes resolve even if module map cache is stale."""

    if (
        not getattr(frappe.local, "module_app", None)
        or "ferum_custom" not in frappe.local.module_app
    ):
        # Flush potentially stale module maps so custom doctypes import cleanly
        frappe.cache().delete_value("app_modules")
        frappe.cache().delete_value("installed_app_modules")
        frappe.local.app_modules = None
        frappe.local.module_app = None
        frappe.setup_module_map(include_all_apps=True)


def _ensure_currency(name: str) -> str:
    if frappe.db.exists("Currency", name):
        return name
    doc = frappe.get_doc(
        {
            "doctype": "Currency",
            "currency_name": name,
            "fraction": "Cent",
            "fraction_units": 100,
            "symbol": "$" if name == "USD" else name[:1].upper(),
            "number_format": "#,###.##",
        }
    )
    doc.insert(ignore_permissions=True)
    return name


def ensure_company(name: str = "Ferum Co", currency: str = "USD") -> str:
    """Ensure a minimal Company exists and set it as the default."""

    _ensure_module_registered()
    if frappe.db.exists("Company", name):
        return name

    currency = _ensure_currency(currency)
    abbr = "".join(part[0] for part in name.split() if part).upper() or name[:3].upper()
    doc = frappe.get_doc(
        {
            "doctype": "Company",
            "company_name": name,
            "abbr": abbr[:5],
            "default_currency": currency,
            "country": "Russia",
        }
    )
    doc.insert(ignore_permissions=True)
    with contextlib.suppress(Exception):
        frappe.db.set_single_value("Global Defaults", "default_company", name)
    return name


def _ensure_customer_group(name: str = "Ferum Customers") -> str:
    root = "Ferum Customer Groups"
    if not frappe.db.exists("Customer Group", root):
        frappe.get_doc(
            {
                "doctype": "Customer Group",
                "customer_group_name": root,
                "is_group": 1,
            }
        ).insert(ignore_permissions=True)
    if not frappe.db.exists("Customer Group", name):
        frappe.get_doc(
            {
                "doctype": "Customer Group",
                "customer_group_name": name,
                "parent_customer_group": root,
                "is_group": 0,
            }
        ).insert(ignore_permissions=True)
    return name


def _ensure_territory(name: str = "Domestic") -> str:
    root = "Ferum Territories"
    if not frappe.db.exists("Territory", root):
        frappe.get_doc(
            {
                "doctype": "Territory",
                "territory_name": root,
                "is_group": 1,
            }
        ).insert(ignore_permissions=True)
    if not frappe.db.exists("Territory", name):
        frappe.get_doc(
            {
                "doctype": "Territory",
                "territory_name": name,
                "parent_territory": root,
                "is_group": 0,
            }
        ).insert(ignore_permissions=True)
    return name


def ensure_customer(name: str = "Perm Customer", company: str | None = None) -> str:
    """Create or reuse a Customer with the bare minimum master data."""

    existing = frappe.db.exists("Customer", name) or frappe.db.get_value(
        "Customer", {"customer_name": name}, "name"
    )
    if existing:
        return existing

    company = company or ensure_company()
    customer_group = _ensure_customer_group()
    territory = _ensure_territory()

    doc = frappe.get_doc(
        {
            "doctype": "Customer",
            "customer_name": name,
            "customer_type": "Company",
            "customer_group": customer_group,
            "territory": territory,
            "default_currency": frappe.db.get_value("Company", company, "default_currency")
            or "USD",
        }
    )
    doc.insert(ignore_permissions=True)
    if doc.name != name:
        with contextlib.suppress(Exception):
            frappe.rename_doc("Customer", doc.name, name, ignore_if_exists=True, force=True)
        return name
    return doc.name


def _ensure_asset_category(name: str = "Test Category") -> str:
    existing = frappe.get_all("Asset Category", limit=1, pluck="name")
    if existing:
        return existing[0]

    doc = frappe.new_doc("Asset Category")
    doc.asset_category_name = name
    doc.flags.ignore_mandatory = True
    doc.insert(ignore_permissions=True)
    return name


def _ensure_item(name: str = "Test Asset Item") -> str:
    if frappe.db.exists("Item", name):
        return name
    cat = _ensure_asset_category()
    item = frappe.new_doc("Item")
    item.item_code = name
    item.item_group = "All Item Groups"
    item.stock_uom = "Nos"
    item.is_stock_item = 0
    item.is_fixed_asset = 1
    item.asset_category = cat
    item.insert(ignore_permissions=True)
    return name


def _ensure_location(name: str = "Test Location") -> str:
    if frappe.db.exists("Location", name):
        return name
    doc = frappe.new_doc("Location")
    doc.location_name = name
    doc.insert(ignore_permissions=True)
    return name


def ensure_asset(object_name: str, customer: str | None = None, company: str | None = None) -> str:
    _ensure_module_registered()
    existing = frappe.db.get_value("Asset", {"asset_name": object_name})
    if existing:
        return existing

    company = company or ensure_company()
    customer_name = frappe.db.get_value("Customer", {"name": customer}) or frappe.db.get_value(
        "Customer", {"customer_name": customer}, "name"
    )
    if not customer_name:
        customer_name = ensure_customer(customer or "Portal Customer", company=company)

    item_code = _ensure_item()
    location = _ensure_location()
    doc = frappe.get_doc(
        {
            "doctype": "Asset",
            "asset_name": object_name,
            "item_code": item_code,
            "location": location,
            "customer": customer_name,
            "company": company,
            "gross_purchase_amount": 1000,
            "purchase_date": frappe.utils.today(),
            "calculate_depreciation": 0,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def ensure_service_department(name: str, company: str | None = None) -> str:
    _ensure_module_registered()
    company = company or ensure_company()
    existing = frappe.db.get_value(
        "Service Department", {"department_name": name}, "name"
    ) or frappe.db.get_value("Service Department", {"name": name}, "name")
    if existing:
        return existing
    doc = frappe.get_doc(
        {
            "doctype": "Service Department",
            "department_name": name,
            "company": company,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def ensure_project_doc(name: str, customer: str) -> str:
    _ensure_module_registered()
    # Resolve customer name (accept customer_name or name) and create if missing
    resolved_customer = frappe.db.get_value(
        "Customer", {"name": customer}, "name"
    ) or frappe.db.get_value("Customer", {"customer_name": customer}, "name")
    if not resolved_customer:
        resolved_customer = ensure_customer(customer)
    customer = resolved_customer
    existing = frappe.db.get_value("Project", {"project_name": name}, "name")
    if existing:
        return existing
    doc = frappe.get_doc(
        {
            "doctype": "Project",
            "company": ensure_company(),
            "customer": customer,
            "project_name": name,
            "code": name,
        }
    )
    # In tests, bypass link validation to reduce fixture coupling
    doc.flags.ignore_links = True
    doc.insert(ignore_permissions=True)
    return doc.name


def create_test_issue() -> str:
    """Create a minimal test Issue using first available Company."""

    _ensure_module_registered()
    company = ensure_company()
    doc = frappe.get_doc(
        {
            "doctype": "Issue",
            "company": company,
            "subject": "Smoke Test Issue",
            "status": "Open",
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def assign_issue(name: str, user: str = "Administrator") -> None:
    doc = frappe.get_doc("Issue", name)
    doc.assigned_to = user
    doc.save(ignore_permissions=True)


def update_issue_status_via_api(name: str, status: str) -> dict[str, Any]:
    from ferum_custom.ferum_custom.api.service import update_issue_status

    return update_issue_status(name=name, status=status)


def _ensure_activity_type(name: str = "Maintenance") -> str:
    if frappe.db.exists("Activity Type", name):
        return name
    doc = frappe.new_doc("Activity Type")
    doc.activity_type = name
    doc.insert(ignore_permissions=True)
    return name


def _get_or_create_timesheet(issue_name: str, attachment_name: str) -> str:
    exists = frappe.db.exists("Timesheet", {"issue": issue_name})
    if exists:
        return exists

    activity_type = _ensure_activity_type()
    timesheet_doc = frappe.new_doc("Timesheet")
    timesheet_doc.issue = issue_name
    timesheet_doc.start_date = frappe.utils.nowdate()
    timesheet_doc.status = "Draft"
    timesheet_doc.append(
        "time_logs", {"activity_type": activity_type, "hours": 1.0, "description": "Inspection"}
    )
    timesheet_doc.insert(ignore_permissions=True)
    return timesheet_doc.name


def get_telegram_secret() -> str:
    from ferum_custom.ferum_custom.settings import get_setting

    return (get_setting("telegram_webhook_secret") or "").strip()


def call_webhook_with_secret(secret: str) -> dict[str, Any]:
    from ferum_custom.ferum_custom.api.telegram_bot import handle_update

    # minimal update payload that should be rejected by allowlist but processed
    update = {
        "message": {
            "text": "/ping",
            "from": {"username": "smoke_user"},
            "chat": {"id": "0"},
        }
    }
    return handle_update(secret=secret, update=json.dumps(update))
