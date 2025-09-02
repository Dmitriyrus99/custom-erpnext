# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import json

import frappe

try:
	import gspread  # type: ignore[import-untyped]
except Exception:
	gspread = None  # Optional dependency; handled at runtime
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue

try:
	from google.oauth2.service_account import Credentials  # type: ignore[import-untyped]
except Exception:
	Credentials = None  # type: ignore[assignment]

# --- Google Sheets Integration ---


def _get_settings():
	try:
		return frappe.get_single("Ferum Custom Settings")
	except Exception:
		return None


def get_google_sheet():
	"""Connects to Google Sheets and returns the worksheet object using Settings."""
	settings = _get_settings()
	if not settings or not settings.enable_google_sheets_sync or gspread is None or Credentials is None:
		return None
	try:
		sheet_name = settings.google_sheet_name or "Ferum Invoices Tracker"
		file_url = settings.google_service_account_json
		if not file_url:
			return None
		file_doc = frappe.get_doc("File", {"file_url": file_url})
		content = file_doc.get_content()
		info = json.loads(content.decode("utf-8"))
		scopes = ["https://www.googleapis.com/auth/spreadsheets"]
		creds = Credentials.from_service_account_info(info, scopes=scopes)
		client = gspread.authorize(creds)
		return client.open(sheet_name).sheet1
	except Exception as e:
		frappe.log_error(f"Google Sheets connection failed: {e!s}", "Google Sheets Connection Error")
		return None


try:
	from backend.bot.telegram_bot import send_telegram_message  # type: ignore[import-not-found]
except Exception:

	def send_telegram_message(*args, **kwargs):  # fallback no-op
		try:
			frappe.log_error(
				"Telegram bot integration unavailable. Message suppressed.",
				"Telegram Integration",
			)
		except Exception:
			pass


class Invoice(Document):
	def after_insert(self):
		self.notify_on_subcontractor_invoice()
		enqueue(
			"ferum_custom.ferum_custom.doctype.invoice.invoice.sync_to_google_sheets",
			queue="short",
			docname=self.name,
		)

	def on_update(self):
		pass  # Handled by hooks

	def notify_on_subcontractor_invoice(self):
		if self.counterparty_type == "Subcontractor":
			message = f"New subcontractor invoice created: {self.name} for {self.counterparty_name}. Amount: {self.amount}"
			send_telegram_message(message)


@frappe.whitelist()
def sync_to_google_sheets(docname: str):
	"""Syncs the invoice data to a Google Sheet."""
	sheet = get_google_sheet()
	if not sheet:
		return

	try:
		doc = frappe.get_doc("Invoice", docname)
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
		enqueue(
			"ferum_custom.ferum_custom.doctype.invoice.invoice.sync_to_google_sheets",
			queue="short",
			docname=doc.name,
		)


@frappe.whitelist()
def create_sales_invoice(invoice_name: str) -> str:
	"""Create ERPNext Sales Invoice from custom Invoice (Customer only). Returns SI name."""
	inv = frappe.get_doc("Invoice", invoice_name)
	if inv.counterparty_type != "Customer":
		frappe.throw("Sales Invoice is supported only for Customer counterparty.")

	si = frappe.new_doc("Sales Invoice")
	si.customer = inv.counterparty_name
	if getattr(inv, "project", None):
		si.project = inv.project
	if getattr(inv, "invoice_date", None):
		si.posting_date = inv.invoice_date

	settings = _get_settings()
	if settings and settings.default_item_code:
		row = si.append("items", {})
		row.item_code = settings.default_item_code
		row.qty = 1
		row.rate = inv.amount or 0
		if settings.income_account:
			row.income_account = settings.income_account
		if settings.cost_center:
			row.cost_center = settings.cost_center

	si.insert(ignore_permissions=True)
	inv.db_set("sales_invoice", si.name)
	return si.name


def get_permission_query_conditions(user: str | None = None) -> str | None:
	"""Restrict visibility based on roles and project ownership.

	- System Manager / Chief Accountant: full access
	- Project Manager: invoices linked to projects they manage
	- Office Manager: read all (operational support)
	- Others: no implicit access
	"""
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if "System Manager" in roles or "Chief Accountant" in roles:
		return None
	if "Office Manager" in roles:
		return None
	if "Project Manager" in roles:
		return "exists(select 1 from `tabService Project` sp where sp.name = `tabInvoice`.project and sp.project_manager=%(user)s)"
	# Default: no additional rows
	return "1=0"


def has_permission(doc, user: str | None = None) -> bool:
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if "System Manager" in roles or "Chief Accountant" in roles:
		return True
	if "Office Manager" in roles:
		return True
	if "Project Manager" in roles and doc.project:
		pm = frappe.db.get_value("Service Project", doc.project, "project_manager")
		return pm == user
	return False
