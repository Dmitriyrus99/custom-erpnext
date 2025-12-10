"""Seed minimal standard ERPNext masters required for tests.

Run via:

    bench --site <site> execute ferum_custom.ferum_custom.scripts.test_bootstrap.run

This is idempotent and safe to re-run.
"""

from __future__ import annotations

import contextlib
import frappe


def _insert(doc: "frappe.model.document.Document") -> str:
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_tree(doctype: str, root_name: str, root_field: str) -> str:
	existing = frappe.db.exists(doctype, root_name)
	if existing:
		return root_name
	doc = frappe.new_doc(doctype)
	doc.set(root_field, root_name)
	doc.is_group = 1
	return _insert(doc)


def _ensure_child(doctype: str, name_field: str, name: str, parent_field: str, parent_value: str) -> str:
	existing = frappe.db.exists(doctype, name)
	if existing:
		return existing
	doc = frappe.new_doc(doctype)
	doc.set(name_field, name)
	doc.set(parent_field, parent_value)
	doc.is_group = 0
	return _insert(doc)


def _ensure_company(name: str = "Ferum Co") -> str:
	if frappe.db.exists("Company", name):
		return name
	# Minimal company
	doc = frappe.new_doc("Company")
	doc.company_name = name
	abbr = ("".join(p[0] for p in name.split() if p) or name[:3]).upper()
	doc.abbr = abbr[:5]
	doc.default_currency = "USD"
	with contextlib.suppress(Exception):
		if not frappe.db.exists("Currency", "USD"):
			cur = frappe.new_doc("Currency")
			cur.currency_name = "US Dollar"
			cur.name = "USD"
			_insert(cur)
	_insert(doc)
	# Set as default company if not set
	with contextlib.suppress(Exception):
		frappe.db.set_value("Global Defaults", "Global Defaults", "default_company", name)
	return name


def run() -> dict[str, str]:
	out: dict[str, str] = {}
	# Company
	out["company"] = _ensure_company("Ferum Co")

	# Territories
	root = _ensure_tree("Territory", "All Territories", "territory_name")
	out["territory_root"] = root
	out["_Test Territory"] = _ensure_child(
		"Territory", "territory_name", "_Test Territory", "parent_territory", root
	)

	# Customer Groups
	cg_root = _ensure_tree("Customer Group", "All Customer Groups", "customer_group_name")
	out["customer_group_root"] = cg_root
	out["_Test Customer Group"] = _ensure_child(
		"Customer Group", "customer_group_name", "_Test Customer Group", "parent_customer_group", cg_root
	)

	# Item Groups
	ig_root = _ensure_tree("Item Group", "All Item Groups", "item_group_name")
	out["item_group_root"] = ig_root
	out["_Test Item Group"] = _ensure_child(
		"Item Group", "item_group_name", "_Test Item Group", "parent_item_group", ig_root
	)

	return out
