import frappe
from frappe.tests.utils import FrappeTestCase

from ferum_custom.ferum_custom.tests import smoke_tools


class TestFinanceFlows(FrappeTestCase):
	def test_invoice_payment_cycle(self):
		frappe.set_user("Administrator")
		company = smoke_tools.ensure_company()
		counterparty = smoke_tools.ensure_customer("Perm Customer", company=company)
		inv = frappe.new_doc("Invoice")
		inv.company = company
		inv.invoice_no = "INV-001"
		inv.invoice_year = 2025
		inv.counterparty_type = "Customer"
		inv.counterparty_name = counterparty
		inv.amount = 100
		inv.insert()
		self.assertEqual(inv.status, "Draft")
		payment = frappe.new_doc("Payment")
		payment.company = company
		payment.trx_date = frappe.utils.nowdate()
		payment.direction = "in"
		payment.amount = 100
		payment.insert()
		self.assertTrue(payment.name)
