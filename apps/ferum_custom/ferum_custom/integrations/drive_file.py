from __future__ import annotations

import frappe

from ferum_custom.ferum_custom.integrations.antivirus import scan_bytes
from ferum_custom.ferum_custom.integrations.file_sync import enqueue_file_sync, sync_file_by_name
from ferum_custom.ferum_custom.settings import is_feature_enabled


def _read_file_content(doc) -> tuple[bytes | None, str | None]:
    """Return (content, filename) if content can be loaded for a File doc."""
    try:
        file_doc = frappe.get_doc("File", doc.name)
        content = file_doc.get_content()
        name = file_doc.file_name
        if isinstance(content, bytes):
            return content, name
        if isinstance(content, str):
            return content.encode("utf-8"), name
    except Exception:
        pass
    return None, None


def on_file_update(doc, method: str | None = None) -> None:
    """Upload new/updated ERPNext File to Google Drive via FileSyncService.

    Skips if drive_file_id already set or file is external (no stored content).
    """
    if not is_feature_enabled("enable_google_drive_sync"):
        return
    try:
        # Antivirus check for newly saved files (best-effort)
        try:
            content, _name = None, None
            file_doc = frappe.get_doc("File", doc.name)
            content = file_doc.get_content()
            if isinstance(content, bytes):
                ok, sig = scan_bytes(content, file_doc.file_name)
                if not ok:
                    frappe.throw(f"Infected file blocked (Drive sync): {sig or 'infected'}")
        except Exception:
            # Don't break Drive sync on AV implementation errors; explicit infections raise above
            pass

        if getattr(doc, "drive_file_id", None):
            return
        # For backfill we prefer synchronous to keep counters accurate.
        if method == "backfill":
            sync_file_by_name(doc.name)
        else:
            # Otherwise enqueue on the configured Drive queue (default: long)
            enqueue_file_sync(doc.name)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "File Drive upload failed (FileSync)")
