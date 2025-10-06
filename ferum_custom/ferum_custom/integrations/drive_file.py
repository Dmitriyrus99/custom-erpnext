from __future__ import annotations

import contextlib

import frappe

from ferum_custom.ferum_custom.integrations.drive import upload_bytes


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
    """Upload new/updated ERPNext File to Google Drive, store drive ids.

    Skips if drive_file_id already set or file is external (no stored content).
    """
    try:
        # If we already have a drive file id, do not re-upload here
        if getattr(doc, "drive_file_id", None):
            return
        content, filename = _read_file_content(doc)
        if not content or not filename:
            return

        # Build folder path: Customer/Project/<Doctype>
        parts: list[str] = []
        with contextlib.suppress(Exception):
            if doc.attached_to_doctype == "Project":
                proj = frappe.get_doc("Project", doc.attached_to_name)
                customer = getattr(proj, "customer", None) or "Customer"
                parts = [customer, proj.name, "Files"]
            elif doc.attached_to_doctype == "Task":
                task = frappe.get_doc("Task", doc.attached_to_name)
                proj = None
                customer = None
                if getattr(task, "project", None):
                    proj = frappe.get_doc("Project", task.project)
                    customer = getattr(proj, "customer", None)
                parts = [p for p in [customer or "Customer", (proj.name if proj else "Project"), "Task Files"]]
            else:
                parts = [doc.attached_to_doctype or "Files"]

        file_id = upload_bytes(parts, filename, content)
        if file_id:
            web = f"https://drive.google.com/file/d/{file_id}/view?usp=drivesdk"
            try:
                frappe.db.set_value("File", doc.name, {"drive_file_id": file_id, "drive_web_link": web})
            except Exception:
                pass
    except Exception:
        frappe.log_error(frappe.get_traceback(), "File Drive upload failed")

