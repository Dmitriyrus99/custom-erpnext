from __future__ import annotations

import contextlib

import frappe

from ferum_custom.patches.utils_migration import _log


def _settings_item_and_category() -> tuple[str | None, str | None]:
    item = None
    cat = None
    with contextlib.suppress(Exception):
        item = frappe.db.get_single_value("Ferum Custom Settings", "default_item_code")
    # Try to find a default Asset Category
    with contextlib.suppress(Exception):
        cat = frappe.db.get_value("Asset Category", {"is_group": 0}, "name")
    return item, cat


def execute():
    ok = skipped = 0
    item_code, category = _settings_item_and_category()
    if not item_code or not category:
        _log(
            "migrate_service_object_to_asset: missing default_item_code or Asset Category; skipping migration"
        )
        _log(
            "Tip: set Ferum Custom Settings.default_item_code and ensure an 'Asset Category' exists"
        )
        return

    names = frappe.get_all("Service Object", pluck="name")
    for name in names:
        try:
            so = frappe.get_doc("Service Object", name)
            # Check if an Asset with same asset_name exists
            a = frappe.db.get_value("Asset", {"asset_name": so.object_name}, "name")
            if a:
                skipped += 1
                continue

            asset = frappe.new_doc("Asset")
            asset.asset_name = so.object_name or so.name
            asset.asset_category = category
            asset.item_code = item_code
            with contextlib.suppress(Exception):
                asset.company = so.company
            # for existing items, mark as available; finance fields optional
            with contextlib.suppress(Exception):
                asset.calculate_depreciation = 0
            asset.insert(ignore_permissions=True)
            ok += 1
        except Exception:
            skipped += 1
            frappe.log_error(frappe.get_traceback(), f"Service Object migration failed: {name}")

    _log(f"migrate_service_object_to_asset: ok={ok} skipped={skipped}")
