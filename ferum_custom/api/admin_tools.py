from __future__ import annotations

import secrets
from collections.abc import Iterable

import frappe
from frappe import _

from ferum_custom.ferum_custom.integrations.file_sync import enqueue_file_sync


def _ensure_roles(user: str, roles: Iterable[str]) -> None:
    doc = frappe.get_doc("User", user)
    existing = {r.role for r in doc.get("roles", [])}
    for role in roles:
        if role not in existing:
            doc.append("roles", {"role": role})
    doc.save(ignore_permissions=True)


@frappe.whitelist(methods=["POST"])
def create_telegram_bot_user(
    email: str = "telegram.bot@ferumrus.ru",
    full_name: str = "Telegram Bot",
    roles: str = "Office Manager,Service Engineer",
) -> dict:
    """Create or update a dedicated ERPNext user for the Telegram bot.

    - Ensures System User type
    - Assigns roles (comma-separated string)
    - Generates a strong random password if user is new
    Returns: {"name": <user>, "password": <generated or None>}
    """
    frappe.only_for("System Manager")
    generated: str | None = None
    if frappe.db.exists("User", email):
        user = frappe.get_doc("User", email)
    else:
        generated = secrets.token_urlsafe(16)
        user = frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": full_name,
                "user_type": "System User",
                "send_welcome_email": 0,
                "enabled": 1,
                "new_password": generated,
            }
        )
        user.insert(ignore_permissions=True)

    # Ensure roles
    role_list = [r.strip() for r in (roles or "").split(",") if r.strip()]
    if role_list:
        _ensure_roles(user.name, role_list)

    # Avoid forcing 2FA on the bot user; if globally enforced, set TOTP secret and supply OTP in bot env
    return {"name": user.name, "password": generated}


@frappe.whitelist(methods=["GET"])  # read-only; enforces doc permissions below
def get_file_sync_status(doctype: str, name: str) -> dict:
    if doctype != "File":
        frappe.throw(_("Unsupported doctype. Use 'File'."))
    # Respect read permissions on the document
    if not frappe.has_permission(doctype, ptype="read", doc=name):
        frappe.throw(_("Not permitted"))
    doc = frappe.get_doc(doctype, name)
    status: dict[str, object] = {
        "doctype": doctype,
        "name": doc.name,
        "drive_file_id": getattr(doc, "drive_file_id", None),
        "drive_web_link": getattr(doc, "drive_web_link", None),
        "sync_needed": not bool(getattr(doc, "drive_file_id", None)),
    }
    return status


@frappe.whitelist(methods=["POST"])  # enqueues a job
def trigger_file_sync(doctype: str, name: str) -> dict:
    """Enqueue Drive sync for a File or Custom Attachment via FileSyncService."""
    doctype = (doctype or "").strip()
    if doctype != "File":
        frappe.throw(_("Unsupported doctype. Use 'File'."))
    frappe.only_for("System Manager")
    enqueue_file_sync(name)
    return {"ok": True, "queued": True}


@frappe.whitelist(methods=["GET"])  # admin diagnostics
def list_unsynced_attachments(limit: int | None = 200) -> dict:
    """Return lists of Custom Attachments and Files missing Drive ID.

    Meant for admin diagnostics; consider paging with `limit`.
    """
    frappe.only_for("System Manager")
    lim = int(limit) if (limit is not None and str(limit).isdigit()) else 200
    files = frappe.get_all(
        "File",
        filters={"drive_file_id": ["in", ["", None]], "is_private": 0},
        fields=["name", "file_name", "attached_to_doctype", "attached_to_name"],
        limit=lim,
    )
    return {"files": files, "limit": lim}
