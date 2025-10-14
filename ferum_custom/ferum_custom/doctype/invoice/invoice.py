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
from ferum_custom.ferum_custom.metrics import inc as metrics_inc
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
		try:
			recipients = list(get_users_by_roles(["System Manager", "Chief Accountant"]))
			if recipients:
				frappe.sendmail(
					recipients=recipients,
					subject="Google Sheets connection failed",
					message=f"Could not connect to Google Sheets: {e!s}",
				)
		except Exception:
			pass
		return None


from ferum_custom.ferum_custom.integrations.telegram import send_message as tg_send
from ferum_custom.ferum_custom.utils import (
	get_allowed_customers,
	get_users_by_roles,
	parse_names_argument,
)


class Invoice(Document):
	def validate(self):
		# Ensure company aligns with linked project if present
		try:
			if getattr(self, "project", None):
				proj_company = frappe.db.get_value("Service Project", self.project, "company")
				if proj_company:
					self.company = proj_company
		except Exception:
			pass

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
		# Resolve PM email for the project (if any) and creator email
		pm_email = None
		try:
			if getattr(doc, "project", None):
				pm_email = frappe.db.get_value(
					"Service Project", doc.project, ["project_manager", "project_manager.email"], as_dict=True
				)
				if isinstance(pm_email, dict):
					pm_email = pm_email.get("project_manager.email") or pm_email.get("project_manager")
		except Exception:
			pm_email = None

		created_by_email = None
		try:
			created_by_email = frappe.db.get_value("User", doc.owner, "email") or doc.owner
		except Exception:
			created_by_email = doc.owner

		row_data = [
			doc.name,  # A
			doc.project,  # B
			doc.counterparty_name,  # C
			doc.counterparty_type,  # D
			doc.amount,  # E
			doc.status,  # F
			doc.invoice_date,  # G
			frappe.utils.now(),  # H (synced_at)
			created_by_email,  # I
			pm_email,  # J
		]
		if cell:
			# Update existing row
			sheet.update(f"A{cell.row}", [row_data])
			frappe.msgprint(_(f"Invoice {doc.name} updated in Google Sheets."))
		else:
			# Append new row
			sheet.append_row(row_data)
			frappe.msgprint(_(f"Invoice {doc.name} added to Google Sheets."))
		_ensure_sheet_formatting(sheet)
		try:
			metrics_inc("ferum_integration_sheets_sync_total", {"result": "success"})
		except Exception:
			pass
	except Exception as e:
		frappe.log_error(
			f"Google Sheets sync failed for invoice {doc.name}: {e!s}", "Google Sheets Sync Error"
		)
		try:
			metrics_inc("ferum_integration_sheets_sync_total", {"result": "error"})
		except Exception:
			pass


def _ensure_sheet_formatting(sheet) -> None:
	"""Ensure basic conditional formatting is present (idempotent)."""
	try:
		ss = sheet.spreadsheet
		# Conditional formats:
		# 1) Status == Paid (col F=6) → green
		# 2) Status == Sent (col F=6) → blue
		# 3) Created-by != Project Manager (cols I and J) and project not in exceptions → yellow
		requests = []

		# Helper to add a rule
		def _add_rule(rule):
			requests.append({"addConditionalFormatRule": {"rule": rule, "index": 0}})

		status_range = {
			"sheetId": sheet.id,
			"startRowIndex": 1,
			"startColumnIndex": 5,
			"endColumnIndex": 6,
		}
		_add_rule(
			{
				"ranges": [status_range],
				"booleanRule": {
					"condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "Paid"}]},
					"format": {"backgroundColor": {"red": 0.8, "green": 0.95, "blue": 0.8}},
				},
			}
		)
		_add_rule(
			{
				"ranges": [status_range],
				"booleanRule": {
					"condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "Sent"}]},
					"format": {"backgroundColor": {"red": 0.85, "green": 0.9, "blue": 1}},
				},
			}
		)
		# Custom formula on columns I (9) and J (10), with project in column B (2)
		mismatch_range = {
			"sheetId": sheet.id,
			"startRowIndex": 1,
			"startColumnIndex": 9,
			"endColumnIndex": 10,
		}
		# Exclude projects: "ЗП офис", "Тендеры", "Склад", "Офис"
		formula = '=AND($B2<>"ЗП офис",$B2<>"Тендеры",$B2<>"Склад",$B2<>"Офис",$I2<>$J2)'
		_add_rule(
			{
				"ranges": [mismatch_range],
				"booleanRule": {
					"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": formula}]},
					"format": {"backgroundColor": {"red": 1.0, "green": 0.95, "blue": 0.6}},
				},
			}
		)
		if requests:
			ss.batch_update({"requests": requests})
	except Exception:
		# Best-effort: formatting is optional
		pass


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
	conds = []
	# Company restriction for internal users
	try:
		user_type = frappe.get_cached_value("User", user, "user_type")
		companies = frappe.get_all(
			"User Permission",
			filters={"user": user, "allow": "Company"},
			pluck="for_value",
		)
		if user_type != "Website User" and companies:
			vals = ", ".join(frappe.db.escape(x) for x in companies)
			conds.append(f"`tabInvoice`.company in ({vals})")
	except Exception:
		pass

	if "Office Manager" in roles or "Department Head" in roles:
		return " and ".join(f"({c})" for c in conds) if conds else None
	if "Project Manager" in roles:
		conds.append(
			"exists(select 1 from `tabService Project` sp where sp.name = `tabInvoice`.project and sp.project_manager=%(user)s)"
		)
		return " and ".join(f"({c})" for c in conds)
	# Client role: доступ к счетам запрещён
	if "Client" in roles:
		# Возвращаем фильтр, который не отдаёт строки
		base = " and ".join(f"({c})" for c in conds)
		return base + (" and 1=0" if base else "1=0")
	# Default: no rows
	base = " and ".join(f"({c})" for c in conds)
	return base + (" and 1=0" if base else "1=0")


def has_permission(doc, user: str | None = None) -> bool:
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if "System Manager" in roles or "Chief Accountant" in roles:
		return True
	if "Office Manager" in roles or "Department Head" in roles:
		return True
	if "Project Manager" in roles and doc.project:
		pm = frappe.db.get_value("Service Project", doc.project, "project_manager")
		return pm == user
	# Клиенты не имеют доступа к документам счетов
	if "Client" in roles:
		return False
	return False
