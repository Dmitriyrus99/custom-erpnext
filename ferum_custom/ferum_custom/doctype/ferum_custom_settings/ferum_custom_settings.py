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
