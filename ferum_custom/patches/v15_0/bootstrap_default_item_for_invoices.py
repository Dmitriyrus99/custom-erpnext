from __future__ import annotations

import contextlib

import frappe

from ferum_custom.patches.utils_migration import _log, has_doctypes


def _find_any_item() -> str | None:
    with contextlib.suppress(Exception):
        # Prefer a non-disabled service-like item if available
        name = frappe.db.get_value("Item", {"disabled": 0}, "name")
        return name
    return None


def _find_default_item_group() -> str | None:
    with contextlib.suppress(Exception):
        # Try common English root first
        root = frappe.db.get_value("Item Group", {"is_group": 1}, "name", order_by="lft asc")
        return root
    return None


def _find_default_uom() -> str | None:
    with contextlib.suppress(Exception):
        # Pick any existing UOM
        return frappe.db.sql("SELECT name FROM `tabUOM` ORDER BY name LIMIT 1")[0][0]
    return None


def _create_placeholder_item() -> str | None:
    try:
        item = frappe.new_doc("Item")
        item.item_code = "FERUM-SERVICE"
        item.item_name = "Ferum Service"
        item.is_stock_item = 0
        with contextlib.suppress(Exception):
            item.item_group = _find_default_item_group()
        with contextlib.suppress(Exception):
            item.stock_uom = _find_default_uom()
        with contextlib.suppress(Exception):
            item.is_sales_item = 1
            item.is_purchase_item = 1
        item.insert(ignore_permissions=True)
        return item.name
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Create placeholder Item failed")
        return None


def execute():
    """Ensure Ferum Custom Settings.default_item_code is set to allow invoice migration.

    Idempotent: if already set, skip. Attempts to reuse any existing Item, otherwise
    creates a simple non-stock service Item (FERUM-SERVICE).
    """
    if not has_doctypes("Item"):
        _log("bootstrap_default_item_for_invoices: skipped (Item doctype missing)")
        return

    try:
        current = frappe.db.get_single_value("Ferum Custom Settings", "default_item_code")
    except Exception:
        current = None

    if current:
        _log("bootstrap_default_item_for_invoices: default_item_code already set; skipping")
        return

    item = _find_any_item() or _create_placeholder_item()
    if not item:
        _log("bootstrap_default_item_for_invoices: could not provision an Item; invoice migration will be skipped")
        return

    try:
        frappe.db.set_single_value("Ferum Custom Settings", "default_item_code", item)
        _log(f"bootstrap_default_item_for_invoices: default_item_code set to {item}")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Set default_item_code failed")
