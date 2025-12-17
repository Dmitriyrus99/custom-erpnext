from __future__ import annotations

import frappe


def execute():
    """Backfill CustomAttachment.linked_doctype/docname for Service Report document items.

    Idempotent: only updates attachments where linked_doctype/docname differs
    or is empty. Skips rows with missing references.
    """
    updated = skipped = 0
    rows = frappe.get_all(
        "Service Report",
        fields=["name"],
        filters={},
    )
    for r in rows:
        try:
            docs = frappe.get_all(
                "Service Report Document Item",
                fields=["custom_attachment"],
                filters={"parent": r.name, "parenttype": "Service Report"},
            )
            for d in docs:
                att_name = d.custom_attachment
                if not att_name:
                    continue
                try:
                    att = frappe.get_doc("Custom Attachment", att_name)
                except Exception:
                    skipped += 1
                    continue
                if att.linked_doctype == "Service Report" and att.linked_docname == r.name:
                    skipped += 1
                    continue
                att.db_set(
                    {
                        "linked_doctype": "Service Report",
                        "linked_docname": r.name,
                    }
                )
                updated += 1
        except Exception:
            skipped += 1
            frappe.log_error(
                frappe.get_traceback(), f"sync_service_report_attachment_links failed for {r.name}"
            )
    frappe.logger().info(
        f"sync_service_report_attachment_links: updated={updated} skipped={skipped}"
    )
