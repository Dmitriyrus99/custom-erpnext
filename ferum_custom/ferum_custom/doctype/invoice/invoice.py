# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

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

from ferum_custom.ferum_custom.integrations.google import (
	SERVICE_ACCOUNT_SCOPE_SHEETS,
	build_service_account_credentials,
)
from ferum_custom.ferum_custom.settings import get_setting, is_feature_enabled

# --- Google Sheets Integration ---


def get_google_sheet():
	"""Connects to Google Sheets and returns the worksheet object using Settings."""
	if gspread is None or not is_feature_enabled("enable_google_sheets_sync"):
		return None
	try:
		creds = build_service_account_credentials([SERVICE_ACCOUNT_SCOPE_SHEETS])
		if not creds:
			return None
		sheet_name = get_setting("google_sheet_name") or "Ferum Invoices Tracker"
		client = gspread.authorize(creds)
		return client.open(sheet_name).sheet1
	except Exception as e:
		frappe.log_error(f"Google Sheets connection failed: {e!s}", "Google Sheets Connection Error")
		return None


from ferum_custom.ferum_custom.integrations.telegram import send_message as tg_send
from ferum_custom.ferum_custom.utils import get_users_by_roles, parse_names_argument


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
			# try Telegram (default chat)
			try:
				tg_send(message)
			except Exception:
				frappe.log_error(frappe.get_traceback(), "Telegram Notification Failed")

			recipients: set[str] = set()
			configured_roles = get_setting("invoice_notification_roles") or []
			roles: list[str] = []
			for row in configured_roles:
				if isinstance(row, dict):
					role = row.get("link_name") or row.get("value")
				else:
					role = str(row)
				if role:
					roles.append(role)
			if not roles:
				roles = ["Chief Accountant", "System Manager"]

			recipients.update(get_users_by_roles(roles))
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
			frappe.log_error(
				frappe.get_traceback(),
				f"Project Financial Update Failed for {doc.project}",
			)

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

	# Optional: auto create ERPNext Sales Invoice for Customer invoices when enabled
	try:
		if (
			is_feature_enabled("enable_auto_create_sales_invoice")
			and doc.counterparty_type == "Customer"
			and not doc.sales_invoice
			and doc.status in ("Sent", "Paid")
		):
			# create and link SI; ignore permissions to allow server-side automation
			name = create_sales_invoice(doc.name)
			frappe.msgprint(_(f"Sales Invoice {name} created for {doc.name}"))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Auto-create Sales Invoice failed")


@frappe.whitelist()
def bulk_mark_sent(names: list[str] | str) -> dict:
	"""Bulk mark selected Invoices as 'Sent'.

	- Validates roles (System Manager, Project Manager, Office Manager, Chief Accountant)
	- Skips invoices already Paid or Cancelled
	- Returns a summary dict with updated and skipped lists
	"""
	names_list = parse_names_argument(names)
	if not names_list:
		return {"updated": [], "skipped": ["<empty>"]}

	roles = set(frappe.get_roles())
	allowed_roles = {"System Manager", "Project Manager", "Office Manager", "Chief Accountant"}
	if not roles.intersection(allowed_roles):
		frappe.throw(_("Not permitted to change invoice status."))

	updated: list[str] = []
	skipped: list[str] = []

	for name in names_list:
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
	names_list = parse_names_argument(names)
	if not names_list:
		return {"updated": [], "skipped": ["<empty>"]}

	roles = set(frappe.get_roles())
	allowed_roles = {"Chief Accountant", "System Manager"}
	if not roles.intersection(allowed_roles):
		frappe.throw(_("Not permitted to mark invoices as Paid."))

	updated: list[str] = []
	skipped: list[str] = []

	for name in names_list:
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

	item_code = get_setting("default_item_code")
	if item_code:
		row = si.append("items", {})
		row.item_code = item_code
		row.qty = 1
		row.rate = inv.amount or 0
		income_account = get_setting("income_account")
		if income_account:
			row.income_account = income_account
		cost_center = get_setting("cost_center")
		if cost_center:
			row.cost_center = cost_center

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
