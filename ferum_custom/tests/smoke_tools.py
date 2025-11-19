from __future__ import annotations

import contextlib
import json
from typing import Any

import frappe


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
		frappe.db.set_value("Global Defaults", "Global Defaults", "default_company", name)
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
			"default_currency": frappe.db.get_value("Company", company, "default_currency") or "USD",
		}
	)
	doc.insert(ignore_permissions=True)
	if doc.name != name:
		with contextlib.suppress(Exception):
			frappe.rename_doc("Customer", doc.name, name, ignore_if_exists=True, force=True)
		return name
	return doc.name


def ensure_service_object(object_name: str, customer: str | None = None, company: str | None = None) -> str:
	existing = frappe.db.get_value("Service Object", {"object_name": object_name})
	if existing:
		return existing

	company = company or ensure_company()
	customer_name = frappe.db.get_value("Customer", {"name": customer}) or frappe.db.get_value(
		"Customer", {"customer_name": customer}, "name"
	)
	if not customer_name:
		customer_name = ensure_customer(customer or "Portal Customer", company=company)
	doc = frappe.get_doc(
		{
			"doctype": "Service Object",
			"object_name": object_name,
			"customer": customer_name,
			"company": company,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def ensure_service_department(name: str, company: str | None = None) -> str:
	existing = frappe.db.exists("Service Department", name)
	if existing:
		return existing
	doc = frappe.get_doc(
		{
			"doctype": "Service Department",
			"department_name": name,
			"company": company or ensure_company(),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def ensure_service_project(name: str, customer: str, department: str) -> str:
	existing = frappe.db.get_value("Service Project", {"project_name": name}, "name")
	if existing:
		return existing
	doc = frappe.get_doc(
		{
			"doctype": "Service Project",
			"company": ensure_company(),
			"customer": customer,
			"project_name": name,
			"service_department": department,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def create_test_service_request() -> str:
	"""Create a minimal test Service Request using first available Company."""

	company = ensure_company()
	doc = frappe.get_doc(
		{
			"doctype": "Service Request",
			"company": company,
			"title": "Smoke Test Request",
			"status": "Open",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def assign_request(name: str, user: str = "Administrator") -> None:
	doc = frappe.get_doc("Service Request", name)
	doc.assigned_to = user
	doc.save(ignore_permissions=True)


def update_request_status_via_api(name: str, status: str) -> dict[str, Any]:
	from ferum_custom.ferum_custom.api.service import update_service_request_status

	return update_service_request_status(name=name, status=status)


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
