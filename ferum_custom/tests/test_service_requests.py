import frappe
from frappe.tests.utils import FrappeTestCase

from ferum_custom.ferum_custom.tests import smoke_tools


class TestServiceRequests(FrappeTestCase):
    def test_create_service_request_via_domain(self):
        frappe.set_user("Administrator")
        company = smoke_tools.ensure_company()
        customer = smoke_tools.ensure_customer("Perm Customer", company=company)
        doc = frappe.get_doc(
            {
                "doctype": "Service Request",
                "title": "Smoke create",
                "company": company,
                "customer": customer,
                "priority": "High",
            }
        )
        doc.insert()
        self.assertEqual(doc.status, "Open")

    def test_portal_updates(self):
        frappe.set_user("Administrator")
        company = smoke_tools.ensure_company()
        sr = frappe.get_doc(
            {
                "doctype": "Service Request",
                "title": "Portal smoke",
                "company": company,
            }
        )
        sr.insert()
        frappe.db.set_value("Service Request", sr.name, "status", "In Progress")
        updated = frappe.get_value("Service Request", sr.name, "status")
        self.assertEqual(updated, "In Progress")
