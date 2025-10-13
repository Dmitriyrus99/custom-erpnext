from __future__ import annotations

import secrets
from typing import Iterable

import frappe
from frappe import _


def _ensure_roles(user: str, roles: Iterable[str]) -> None:
    doc = frappe.get_doc("User", user)
    existing = {r.role for r in doc.get("roles", [])}
    for role in roles:
        if role not in existing:
            doc.append("roles", {"role": role})
    doc.save(ignore_permissions=True)


@frappe.whitelist()
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

