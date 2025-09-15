# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _

try:
	import gspread  # type: ignore[import-untyped]
except Exception:
	gspread = None  # Optional dependency; handled at runtime
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue

try:
	from frappe.model.workflow import apply_workflow  # type: ignore[import-not-found]
except Exception:
	apply_workflow = None  # type: ignore[assignment]

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

	TELEGRAM_AVAILABLE = True
except Exception:
	TELEGRAM_AVAILABLE = False

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
			if TELEGRAM_AVAILABLE:
				try:
					send_telegram_message(message)
					return
				except Exception:
					frappe.log_error(frappe.get_traceback(), "Telegram Notification Failed")

			recipients: set[str] = set()
			settings = _get_settings()
			roles = ["Chief Accountant", "System Manager"]
			if settings and getattr(settings, "invoice_notification_roles", None):
				roles = [r.role for r in settings.invoice_notification_roles]

			if roles:
				user_ids = frappe.get_all(
					"Has Role",
					filters={"role": ["in", roles], "parenttype": "User"},
					pluck="parent",
				)
				if user_ids:
					for u in frappe.db.get_all(
						"User",
						filters={"name": ["in", user_ids]},
						fields=["name", "email"],
					):
						recipients.add(u.email or u.name)
			if recipients:
				frappe.sendmail(
					recipients=list(recipients),
					subject=_("New subcontractor invoice {0}").format(self.name),
					message=message,
				)
			else:
				frappe.log_error(message, "Subcontractor Invoice Notification")


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
			frappe.msgprint(_(f"Invoice {doc.name} updated in Google Sheets."))
		else:
			# Append new row
			sheet.append_row(row_data)
			frappe.msgprint(_(f"Invoice {doc.name} added to Google Sheets."))
	except Exception as e:
		frappe.log_error(
			f"Google Sheets sync failed for invoice {doc.name}: {e!s}", "Google Sheets Sync Error"
		)


def on_invoice_update(doc, method):
	if doc.project:
		try:
			from ferum_custom.ferum_custom.doctype.service_project.service_project import (
				update_project_financials,
			)

			update_project_financials(doc.project)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Project Financial Update Failed")

	if doc.docstatus == 1 and doc.status == "Paid":  # Submitted and Paid
		enqueue(
			"ferum_custom.ferum_custom.doctype.invoice.invoice.sync_to_google_sheets",
			queue="short",
			docname=doc.name,
		)
	elif doc.docstatus == 2:  # Cancelled
		enqueue(
			"ferum_custom.ferum_custom.doctype.invoice.invoice.sync_to_google_sheets",
			queue="short",
			docname=doc.name,
		)


@frappe.whitelist()
def bulk_mark_sent(names: list[str] | str) -> dict:
	"""Bulk mark selected Invoices as 'Sent'.

	- Validates roles (System Manager, Project Manager, Office Manager, Chief Accountant)
	- Skips invoices already Paid or Cancelled
	- Returns a summary dict with updated and skipped lists
	"""
	# Parse names when called from JS (stringified JSON or CSV)
	if isinstance(names, str):
		try:
			names = frappe.parse_json(names)  # type: ignore[assignment]
		except Exception:
			names = [n.strip() for n in names.split(",") if n.strip()]

	if not names:
		return {"updated": [], "skipped": ["<empty>"]}

	roles = set(frappe.get_roles())
	allowed_roles = {"System Manager", "Project Manager", "Office Manager", "Chief Accountant"}
	if not roles.intersection(allowed_roles):
		frappe.throw(_("Not permitted to change invoice status."))

	updated: list[str] = []
	skipped: list[str] = []

	for name in names:  # type: ignore[assignment]
		try:
			doc = frappe.get_doc("Invoice", name)
			if doc.status in ("Paid", "Cancelled"):
				skipped.append(name)
				continue
			if doc.status == "Sent":
				skipped.append(name)
				continue
			# Prefer workflow transition if configured
			transitioned = False
			if apply_workflow:
				try:
					apply_workflow(doc, "Send")
					transitioned = True
				except Exception:
					transitioned = False
			if not transitioned:
				doc.db_set("status", "Sent")
			updated.append(name)
		except Exception:
			skipped.append(name)

	return {"updated": updated, "skipped": skipped}


@frappe.whitelist()
def bulk_mark_paid(names: list[str] | str) -> dict:
	"""Bulk mark selected Invoices as 'Paid' using Workflow when available.

	- Only Chief Accountant (and System Manager) may perform this action
	- Requires invoices to not be Cancelled; prefers current status 'Sent'
	- Uses workflow action 'Mark Paid' if configured; otherwise submits + sets status
	- Returns a summary dict with updated and skipped lists
	"""
	# Parse names when called from JS
	if isinstance(names, str):
		try:
			names = frappe.parse_json(names)  # type: ignore[assignment]
		except Exception:
			names = [n.strip() for n in names.split(",") if n.strip()]

	if not names:
		return {"updated": [], "skipped": ["<empty>"]}

	roles = set(frappe.get_roles())
	allowed_roles = {"Chief Accountant", "System Manager"}
	if not roles.intersection(allowed_roles):
		frappe.throw(_("Not permitted to mark invoices as Paid."))

	updated: list[str] = []
	skipped: list[str] = []

	for name in names:  # type: ignore[assignment]
		try:
			doc = frappe.get_doc("Invoice", name)
			if doc.status in ("Paid", "Cancelled"):
				skipped.append(name)
				continue

			# Prefer workflow transition if configured
			transitioned = False
			if apply_workflow:
				try:
					apply_workflow(doc, "Mark Paid")
					transitioned = True
				except Exception:
					transitioned = False

			if not transitioned:
				# Fallback: ensure submitted + set status
				if doc.docstatus == 0:
					doc.status = "Paid"
					doc.submit()  # triggers on_update hooks
				elif doc.docstatus == 1:
					doc.status = "Paid"
					doc.save()
				else:
					skipped.append(name)
					continue

			updated.append(name)
		except Exception:
			skipped.append(name)

	return {"updated": updated, "skipped": skipped}


@frappe.whitelist()
def create_sales_invoice(invoice_name: str) -> str:
	"""Create ERPNext Sales Invoice from custom Invoice (Customer only). Returns SI name."""
	inv = frappe.get_doc("Invoice", invoice_name)
	if inv.counterparty_type != "Customer":
		frappe.throw(_("Sales Invoice is supported only for Customer counterparty."))

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
