from __future__ import annotations

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """Add Telegram fields on User doctype (idempotent)."""
    fields = {
        "User": [
            {
                "fieldname": "telegram_username",
                "label": "Telegram Username",
                "fieldtype": "Data",
                "insert_after": "mobile_no",
            },
            {
                "fieldname": "telegram_chat_id",
                "label": "Telegram Chat ID",
                "fieldtype": "Data",
                "insert_after": "telegram_username",
            },
        ]
    }
    create_custom_fields(fields, ignore_validate=True)
