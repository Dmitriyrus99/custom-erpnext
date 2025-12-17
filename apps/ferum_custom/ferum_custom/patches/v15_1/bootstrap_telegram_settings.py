from __future__ import annotations

import secrets

import frappe


def execute():
    """Bootstrap Telegram-related settings if missing (idempotent)."""
    try:
        doc = frappe.get_single("Ferum Custom Settings")
    except Exception:
        return

    changed = False
    # Ensure master switch is set (default off)
    if getattr(doc, "enable_telegram_notifications", None) is None:
        frappe.db.set_single_value("Ferum Custom Settings", "enable_telegram_notifications", 0)
        changed = True

    # Generate webhook secret if empty
    secret = getattr(doc, "telegram_webhook_secret", None) or ""
    if not secret.strip():
        frappe.db.set_single_value(
            "Ferum Custom Settings",
            "telegram_webhook_secret",
            secrets.token_urlsafe(24),
        )
        changed = True

    if changed:
        frappe.logger().info("bootstrap_telegram_settings: applied defaults")
