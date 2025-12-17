import frappe


def execute() -> None:
    """Fix broken System Settings where mandatory `language` is empty.

    Without this value, saving System Settings (including changing time zone) fails with
    MandatoryError: [System Settings, System Settings]: language
    """

    language = frappe.db.get_single_value("System Settings", "language")
    if language:
        return

    # Prefer ru when available (bench is RU-centric), fallback to en.
    for candidate in ("ru", "en"):
        if frappe.db.exists("Language", candidate):
            enabled = frappe.db.get_value("Language", candidate, "enabled")
            if enabled:
                frappe.db.set_single_value("System Settings", "language", candidate)
                frappe.db.commit()
                return
