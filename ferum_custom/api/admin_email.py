from __future__ import annotations

import re

import frappe
from frappe import _


def _clean_app_password(pwd: str) -> str:
    # Gmail app passwords often come with spaces; strip spaces and NULs
    return re.sub(r"\s+", "", (pwd or "").replace("\x00", ""))


@frappe.whitelist()
def setup_outgoing(
    *,
    account_name: str,
    email_address: str,
    login_id: str,
    app_password: str,
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int | str = 587,
    use_tls: int | bool = 1,
) -> dict:
    """Create or update a Default Outgoing Email Account for SMTP.

    Defaults are tuned for Google Workspace (Gmail) via STARTTLS on 587.
    """
    frappe.only_for(("System Manager",))

    doc = None
    if frappe.db.exists("Email Account", account_name):
        doc = frappe.get_doc("Email Account", account_name)
    else:
        # Try locate by email_id
        name_by_email = frappe.db.get_value("Email Account", {"email_id": email_address})
        if name_by_email:
            doc = frappe.get_doc("Email Account", name_by_email)

    if not doc:
        doc = frappe.new_doc("Email Account")

    doc.email_account_name = account_name
    doc.email_id = email_address
    # Outgoing only
    doc.enable_outgoing = 1
    doc.default_outgoing = 1
    # SMTP settings
    doc.smtp_server = smtp_server
    doc.smtp_port = str(smtp_port)
    doc.use_tls = 1 if str(use_tls) in ("1", "True", "true", "yes", "on") else 0
    doc.use_ssl_for_outgoing = 0
    doc.no_smtp_authentication = 0
    # Login differs from email
    doc.login_id_is_different = 1 if login_id and login_id != email_address else 0
    doc.login_id = login_id if doc.login_id_is_different else None
    # Sender handling
    doc.always_use_account_email_id_as_sender = 1
    # Auth
    doc.awaiting_password = 0
    doc.password = _clean_app_password(app_password)
    # Service hint (optional)
    if (smtp_server or "").lower().startswith("smtp.gmail"):
        doc.service = "GMail"

    if doc.name:
        doc.save(ignore_permissions=True)
    else:
        doc.insert(ignore_permissions=True)

    frappe.db.commit()
    return {
        "name": doc.name,
        "email_id": doc.email_id,
        "smtp_server": doc.smtp_server,
        "smtp_port": doc.smtp_port,
        "default_outgoing": bool(doc.default_outgoing),
    }

