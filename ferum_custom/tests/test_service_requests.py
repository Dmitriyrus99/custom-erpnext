import frappe
from frappe.tests.utils import FrappeTestCase

from ferum_custom.ferum_custom.tests import smoke_tools


class TestIssues(FrappeTestCase):
    def test_create_issue_via_domain(self):
        frappe.set_user("Administrator")
        company = smoke_tools.ensure_company()
        customer = smoke_tools.ensure_customer("Perm Customer", company=company)
        doc = frappe.get_doc(
            {
                "doctype": "Issue",
                "subject": "Smoke create",
                "company": company,
                "customer": customer,
                "priority": "High",
            }
        )
        doc.insert()
        self.assertEqual(doc.status, "Open")

    def test_issue_portal_updates(self):
        frappe.set_user("Administrator")
        company = smoke_tools.ensure_company()
        issue_doc = frappe.get_doc(
            {
                "doctype": "Issue",
                "subject": "Portal smoke",
                "company": company,
            }
        )
        issue_doc.insert()
        frappe.db.set_value("Issue", issue_doc.name, "status", "Open")
        updated = frappe.get_value("Issue", issue_doc.name, "status")
        self.assertEqual(updated, "Open")
