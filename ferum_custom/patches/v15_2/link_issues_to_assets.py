from __future__ import annotations

import contextlib

import frappe

from ferum_custom.patches.utils_migration import _log


def execute():
    """Post-migration helper: link migrated Issues with corresponding Assets.

    Strategy:
    - For each legacy Service Request, find its migrated Issue by subject = sr.title
    - Resolve Asset by matching Service Object.object_name -> Asset.asset_name
    - Add a comment on Issue with a reference to the Asset (keeps traceability)
    """
    ok = skipped = 0
    if not frappe.db.exists("DocType", "Service Request"):
        _log("link_issues_to_assets: skipped (no Service Request doctype)")
        return
    srs = frappe.get_all("Service Request", fields=["name", "title", "service_object"])
    for sr in srs:
        try:
            # Find Issue by subject
            issue = frappe.db.get_value("Issue", {"subject": sr["title"]}, "name")
            if not issue:
                skipped += 1
                continue
            asset_name = None
            # Resolve Asset via Service Object.object_name
            so = sr.get("service_object")
            if so:
                with contextlib.suppress(Exception):
                    obj_name = frappe.db.get_value("Service Object", so, "object_name")
                    if obj_name:
                        asset_name = frappe.db.get_value("Asset", {"asset_name": obj_name}, "name")
            if asset_name:
                msg = frappe._("Linked Asset: {0}").format(asset_name)
                try:
                    frappe.get_doc("Issue", issue).add_comment("Info", msg)
                except Exception:
                    pass
                ok += 1
            else:
                skipped += 1
        except Exception:
            skipped += 1
            frappe.log_error(frappe.get_traceback(), f"link_issues_to_assets failed for SR {sr['name']}")
    _log(f"link_issues_to_assets: ok={ok} skipped={skipped}")

