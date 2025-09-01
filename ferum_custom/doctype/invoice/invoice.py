# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
import gspread
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue
from google.oauth2.service_account import Credentials

# --- Google Sheets Integration ---

GOOGLE_SHEETS_INTEGRATION_ENABLED = frappe.conf.get("google_sheets_integration_enabled", False)
GOOGLE_SHEETS_CREDENTIALS_PATH = frappe.conf.get("google_sheets_credentials_path")
GOOGLE_SHEET_NAME = "Ferum Invoices Tracker"


def get_google_sheet():
	"""Connects to Google Sheets and returns the worksheet object."""
	if not GOOGLE_SHEETS_INTEGRATION_ENABLED or not GOOGLE_SHEETS_CREDENTIALS_PATH:
		return None
	try:
		scopes = ["https://www.googleapis.com/auth/spreadsheets"]
		creds = Credentials.from_service_account_file(GOOGLE_SHEETS_CREDENTIALS_PATH, scopes=scopes)
		client = gspread.authorize(creds)
		sheet = client.open(GOOGLE_SHEET_NAME).sheet1
		return sheet
	except Exception as e:
		frappe.log_error(f"Google Sheets connection failed: {e!s}", "Google Sheets Connection Error")
		return None


from backend.bot.telegram_bot import send_telegram_message


class Invoice(Document):
	def after_insert(self):
		self.notify_on_subcontractor_invoice()
		enqueue("ferum_custom.doctype.invoice.invoice.sync_to_google_sheets", queue="short", doc=self)

	def on_update(self):
		pass  # Handled by hooks

	def notify_on_subcontractor_invoice(self):
		if self.counterparty_type == "Subcontractor":
			message = f"New subcontractor invoice created: {self.name} for {self.counterparty_name}. Amount: {self.amount}"
			send_telegram_message(message)


@frappe.whitelist()
def sync_to_google_sheets(doc):
	"""Syncs the invoice data to a Google Sheet."""
	sheet = get_google_sheet()
	if not sheet:
		return

	try:
		# Check if invoice already exists
		cell = sheet.find(doc.name)
		row_data = [
			doc.name,
			doc.project,
			doc.counterparty_name,
			doc.counterparty_type,
			doc.amount,
			doc.status,
			doc.invoice_date,
			frappe.utils.now(),
		]
		if cell:
			# Update existing row
			sheet.update(f"A{cell.row}", [row_data])
			frappe.msgprint(f"Invoice {doc.name} updated in Google Sheets.")
		else:
			# Append new row
			sheet.append_row(row_data)
			frappe.msgprint(f"Invoice {doc.name} added to Google Sheets.")
	except Exception as e:
		frappe.log_error(
			f"Google Sheets sync failed for invoice {doc.name}: {e!s}", "Google Sheets Sync Error"
		)


def on_invoice_update(doc, method):
	if doc.docstatus == 1 and doc.status == "Paid":  # Submitted and Paid
		enqueue("ferum_custom.doctype.invoice.invoice.sync_to_google_sheets", queue="short", doc=doc)
