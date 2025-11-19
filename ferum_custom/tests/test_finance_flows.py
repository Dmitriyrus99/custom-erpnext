import frappe
from frappe.tests.utils import FrappeTestCase


class TestFinanceFlows(FrappeTestCase):
    def test_invoice_payment_cycle(self):
        frappe.set_user("Administrator")
        inv = frappe.new_doc("Invoice")
        inv.company = "Ferum Co"
        inv.posting_date = frappe.utils.nowdate()
        inv.due_date = frappe.utils.nowdate()
        inv.counterparty_name = "Perm Customer"
        inv.append("items", {"item_name": "Service", "amount": 100})
        inv.insert()
        inv.submit()
        self.assertEqual(inv.status, "Submitted")
        payment = frappe.new_doc("Payment")
        payment.company = "Ferum Co"
        payment.reference_doctype = "Invoice"
        payment.reference_name = inv.name
        payment.amount = 100
        payment.insert()
        self.assertTrue(payment.name)
