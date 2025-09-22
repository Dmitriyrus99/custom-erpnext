import frappe


@frappe.whitelist()
def save_integrations(telegram_chat_id: str | None = None,
                      telegram_token: str | None = None,
                      drive_root_id: str | None = None) -> dict:
    """Persist integration settings into Ferum Custom Settings singleton.

    Only updates provided fields. Returns the saved subset.
    """
    settings = frappe.get_single("Ferum Custom Settings")
    updated: dict[str, str] = {}

    if telegram_chat_id:
        settings.telegram_default_chat_id = telegram_chat_id
        updated["telegram_default_chat_id"] = telegram_chat_id

    if telegram_token:
        settings.telegram_bot_token = telegram_token
        # do not include token in response

    if drive_root_id:
        settings.google_drive_root_folder_id = drive_root_id
        updated["google_drive_root_folder_id"] = drive_root_id

    settings.save(ignore_permissions=True)
    frappe.db.commit()
    return updated

