from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


def _render_details(details: dict[str, object] | None) -> str:
    if not details:
        return ""
    lines = []
    for key, value in details.items():
        label = frappe.utils.escape_html(str(key))
        val = frappe.utils.escape_html(frappe.utils.cstr(value))
        lines.append(f"<b>{label}</b>: {val}")
    return "<br>".join(lines)


class FerumCustomSettings(Document):
    def check_google_drive(self):
        from ferum_custom.ferum_custom.integrations import drive

        result = drive.healthcheck()
        status = result.get("status", "unknown")
        indicator = {"ok": "green", "disabled": "orange"}.get(status, "red")
        message = _("Google Drive status: {0}").format(status)
        detail_html = _render_details(result.get("details"))
        if detail_html:
            message += "<br>" + detail_html
        if result.get("message"):
            message += "<br>" + frappe.utils.escape_html(str(result["message"]))
        frappe.msgprint(message, indicator=indicator, alert=True)
        return result

    def validate(self):
        self._validate_integration_settings()
        self._ensure_service_account_file_private()

    def _validate_integration_settings(self):
        if self.enable_google_drive_sync and not self.google_drive_root_folder_id:
            frappe.throw(_("Drive Root Folder ID is required when Google Drive sync is enabled."))
        if self.enable_google_sheets_sync and not self.google_service_account_json:
            frappe.throw(_("Google Service Account JSON is required to sync invoices to Sheets."))
        if self.enable_telegram_notifications and not self.telegram_bot_token:
            frappe.throw(
                _("Telegram bot token must be supplied when Telegram notifications are enabled.")
            )

    def _ensure_service_account_file_private(self):
        file_url = getattr(self, "google_service_account_json", "") or ""
        if not file_url:
            return
        try:
            file_doc = frappe.get_doc("File", {"file_url": file_url})
            if file_doc and int(getattr(file_doc, "is_private", 0)) != 1:
                file_doc.db_set("is_private", 1, commit=True)
        except Exception:
            frappe.log_error(
                frappe.get_traceback(), "Failed to enforce privacy on Google service account JSON"
            )

    def check_telegram(self):
        from ferum_custom.ferum_custom.integrations import telegram

        result = telegram.healthcheck()
        status = result.get("status", "unknown")
        indicator = {"ok": "green", "disabled": "orange"}.get(status, "red")
        message = _("Telegram status: {0}").format(status)
        detail_html = _render_details(result.get("details"))
        if detail_html:
            message += "<br>" + detail_html
        if result.get("message"):
            message += "<br>" + frappe.utils.escape_html(str(result["message"]))
        frappe.msgprint(message, indicator=indicator, alert=True)
        return result
