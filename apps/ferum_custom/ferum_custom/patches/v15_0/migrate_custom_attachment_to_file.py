from __future__ import annotations

import frappe

from ferum_custom.patches.utils_migration import _log


def execute():
    """Ensure every Custom Attachment has a corresponding File document.

    Attaches Files to the same linked_doctype/docname as the original.
    Idempotent: if a File with same file_url and attachment link exists, skip.
    """
    ok = skipped = 0
    rows = frappe.get_all(
        "Custom Attachment",
        fields=["name", "file_url", "file_name", "linked_doctype", "linked_docname"],
    )
    for r in rows:
        try:
            if not r.file_url or not r.linked_doctype or not r.linked_docname:
                skipped += 1
                continue
            exists = frappe.db.exists(
                "File",
                {
                    "file_url": r.file_url,
                    "attached_to_doctype": r.linked_doctype,
                    "attached_to_name": r.linked_docname,
                },
            )
            if exists:
                skipped += 1
                continue
            doc = frappe.get_doc(
                {
                    "doctype": "File",
                    "file_name": r.file_name or r.file_url.rsplit("/", 1)[-1],
                    "file_url": r.file_url,
                    "attached_to_doctype": r.linked_doctype,
                    "attached_to_name": r.linked_docname,
                    "is_private": 0,
                }
            )
            doc.insert(ignore_permissions=True)
            ok += 1
        except Exception:
            skipped += 1
            frappe.log_error(
                frappe.get_traceback(), f"CustomAttachment to File migration failed: {r.name}"
            )
    _log(f"migrate_custom_attachment_to_file: ok={ok} skipped={skipped}")
