from __future__ import annotations

from unittest import mock

import frappe
from frappe.tests.utils import FrappeTestCase

from ferum_custom.ferum_custom.doctype.invoice import invoice as invoice_module


class _DummySheet:
	def __init__(self):
		self.rows: list[list[object]] = []

	def find(self, value):
		raise invoice_module.CellNotFound

	def append_row(self, row):
		self.rows.append(row)


class TestGoogleSheetsSync(FrappeTestCase):
	def test_append_row_on_missing_cell(self):
		company = frappe.get_all("Company", filters={"name": "Ferum Co"}, pluck="name")
		if not company:
			frappe.get_doc({"doctype": "Company", "company_name": "Ferum Co"}).insert()

		doc = frappe.get_doc(
			{
				"doctype": "Invoice",
				"company": "Ferum Co",
				"counterparty_type": "Customer",
				"counterparty_name": "Dummy Client",
				"amount": 100,
			}
		)
		doc.insert()

		sheet = _DummySheet()
		with mock.patch.object(
			invoice_module,
			"get_google_sheet",
			return_value=sheet,
		), mock.patch.object(invoice_module, "metrics_inc", lambda *args, **kwargs: None):
			invoice_module.sync_to_google_sheets(doc.name)

		self.assertEqual(sheet.rows[0][0], doc.name)
		doc.delete()
