from __future__ import annotations

import contextlib

import frappe

from ferum_custom.patches.utils_migration import (
	_log,
	find_or_create_project,
	has_doctypes,
	migrate_attachments,
)


def _default_item_code() -> str | None:
	with contextlib.suppress(Exception):
		return frappe.db.get_single_value("Ferum Custom Settings", "default_item_code")
	return None


def execute():
	if not has_doctypes("Sales Invoice", "Purchase Invoice"):
		_log("migrate_invoice_to_erpnext: skipped (Sales/Purchase Invoice doctypes missing)")
		return
	ok = skipped = att_ok = att_skip = 0
	item_code = _default_item_code()
	if not item_code:
		_log("migrate_invoice_to_erpnext: default_item_code not set; customer invoices will be skipped")

	names = frappe.get_all("Invoice", pluck="name")
	for name in names:
		try:
			inv = frappe.get_doc("Invoice", name)
			if inv.counterparty_type == "Customer":
				# try to find existing SI created earlier
				if getattr(inv, "sales_invoice", None) and frappe.db.exists(
					"Sales Invoice", inv.sales_invoice
				):
					si_name = inv.sales_invoice
				else:
					if not item_code:
						skipped += 1
						continue
					si = frappe.new_doc("Sales Invoice")
					with contextlib.suppress(Exception):
						si.customer = inv.counterparty_name
					with contextlib.suppress(Exception):
						si.posting_date = inv.invoice_date
					project = getattr(inv, "project", None)
					if project and frappe.db.exists("Project", project):
						sp = frappe.get_doc("Project", project)
						project = find_or_create_project(sp) or project
					with contextlib.suppress(Exception):
						if project:
							si.project = project
					# item row
					row = si.append("items", {})
					row.item_code = item_code
					with contextlib.suppress(Exception):
						row.qty = 1
						row.rate = float(getattr(inv, "amount", 0) or 0)
					si.insert(ignore_permissions=True)
					si_name = si.name
					with contextlib.suppress(Exception):
						inv.db_set("sales_invoice", si_name)
				# Attachments
				o, s = migrate_attachments("Invoice", inv.name, "Sales Invoice", si_name)
				att_ok += o
				att_skip += s
				ok += 1
			else:
				# Subcontractor → Purchase Invoice
				# Requires Supplier; if not exists, skip
				supplier = getattr(inv, "counterparty_name", None)
				if supplier and not frappe.db.exists("Supplier", supplier):
					with contextlib.suppress(Exception):
						sup = frappe.new_doc("Supplier")
						sup.supplier_name = supplier
						sup.insert(ignore_permissions=True)
				if not frappe.db.exists("Supplier", supplier or ""):
					skipped += 1
					continue
				pi = frappe.new_doc("Purchase Invoice")
				pi.supplier = supplier
				with contextlib.suppress(Exception):
					pi.posting_date = inv.invoice_date
				# Fallback item code
				if not item_code:
					skipped += 1
					continue
				row = pi.append("items", {})
				row.item_code = item_code
				row.qty = 1
				with contextlib.suppress(Exception):
					row.rate = float(getattr(inv, "amount", 0) or 0)
				with contextlib.suppress(Exception):
					project = getattr(inv, "project", None)
					if project and frappe.db.exists("Project", project):
						sp = frappe.get_doc("Project", project)
						project = find_or_create_project(sp) or project
					if project:
						pi.project = project
				pi.insert(ignore_permissions=True)
				o, s = migrate_attachments("Invoice", inv.name, "Purchase Invoice", pi.name)
				att_ok += o
				att_skip += s
				ok += 1
		except Exception:
			skipped += 1
			frappe.log_error(frappe.get_traceback(), f"Invoice migration failed: {name}")
	_log(
		f"migrate_invoice_to_erpnext: ok={ok} skipped={skipped} attachments_ok={att_ok} attachments_skipped={att_skip}"
	)
