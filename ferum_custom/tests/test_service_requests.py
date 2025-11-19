import frappe
from frappe.tests.utils import FrappeTestCase


class TestServiceRequests(FrappeTestCase):
    def test_create_service_request_via_domain(self):
        frappe.set_user("Administrator")
        doc = frappe.get_doc(
            {
                "doctype": "Service Request",
                "title": "Smoke create",
                "company": "Ferum Co",
                "customer": "Perm Customer",
                "priority": "High",
            }
        )
        doc.insert()
        self.assertEqual(doc.status, "Open")

    def test_portal_updates(self):
        frappe.set_user("Administrator")
        name = frappe.db.get_single_value("Service Request", "name")
        if not name:
            sr = frappe.new_doc("Service Request")
            sr.title = "Portal smoke"
            sr.insert()
            name = sr.name
        doc = frappe.get_doc("Service Request", name)
        doc.status = "On Hold"
        doc.save()
        self.assertEqual(doc.status, "On Hold")
