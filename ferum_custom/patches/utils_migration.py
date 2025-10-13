from __future__ import annotations

import contextlib
from typing import Any

import frappe


def _log(msg: str) -> None:
    try:
        frappe.logger("ferum_migration").info(msg)
    except Exception:
        print(msg)


def _warn(msg: str) -> None:
    try:
        frappe.logger("ferum_migration").warning(msg)
    except Exception:
        print("WARN:", msg)


def find_or_create_project(sp: Any) -> str | None:
    """Return Project name for given Service Project doc, creating if absent.

    Idempotent: tries to find Project by exact project_name + customer.
    """
    # Try exact match by project_name and customer
    name = frappe.db.get_value(
        "Project",
        {"project_name": sp.project_name, "customer": getattr(sp, "customer", None)},
        "name",
    )
    if name:
        return name

    # Create a new Project with essential fields
    try:
        doc = frappe.new_doc("Project")
        doc.project_name = sp.project_name or sp.name
        if getattr(sp, "customer", None):
            doc.customer = sp.customer
        if getattr(sp, "company", None):
            doc.company = sp.company
        with contextlib.suppress(Exception):
            if getattr(sp, "project_manager", None):
                doc.append("users", {"user": sp.project_manager})
        doc.insert(ignore_permissions=True)
        return doc.name
    except Exception:  # log and skip
        frappe.log_error(frappe.get_traceback(), "Project migration failed (Service Project)")
        return None


def migrate_attachments(from_dt: str, from_name: str, to_dt: str, to_name: str) -> tuple[int, int]:
    """Copy attachments from Custom Attachment/File linked to `from_dt/from_name` onto `to_dt/to_name`.

    Returns (ok, skipped).
    """
    ok = skipped = 0
    # Prefer Custom Attachment table if present
    rows = frappe.get_all(
        "Custom Attachment",
        filters={"linked_doctype": from_dt, "linked_docname": from_name},
        fields=["name", "file_url", "file_name"],
    )
    for r in rows:
        try:
            if not r.file_url:
                skipped += 1
                continue
            # Ensure File exists and is attached to the new doc
            file_doc = frappe.get_doc({
                "doctype": "File",
                "file_name": r.file_name or r.file_url.rsplit("/", 1)[-1],
                "file_url": r.file_url,
                "attached_to_doctype": to_dt,
                "attached_to_name": to_name,
                "is_private": 0,
            })
            file_doc.insert(ignore_permissions=True)
            ok += 1
        except Exception:
            skipped += 1
            frappe.log_error(frappe.get_traceback(), f"Attachment migration failed: {from_dt} {from_name}")
    return ok, skipped


def has_doctypes(*names: str) -> bool:
    """Return True only if all given DocTypes (tables) exist in the site.

    Helps make patches no-op when ERPNext is not installed (CI/dev).
    """
    try:
        for n in names:
            if not frappe.db.table_exists(f"tab{n}"):
                _warn(f"Patch skipped: missing doctype {n}")
                return False
        return True
    except Exception:
        return False
