import frappe
from frappe.tests.utils import FrappeTestCase


class TestClientCustomerPermissions(FrappeTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        # Create client user
        if not frappe.db.exists("User", "cust1@example.com"):
            u = frappe.new_doc("User")
            u.email = "cust1@example.com"
            u.first_name = "Cust1"
            u.user_type = "System User"
            u.insert()
            u.add_roles("Client")
        # Customers
        for name in ("Cust A", "Cust B"):
            if not frappe.db.exists("Customer", name):
                c = frappe.new_doc("Customer")
                c.customer_name = name
                c.insert()
        # Service Objects
        for obj_name, customer in (("Obj-A", "Cust A"), ("Obj-B", "Cust B")):
            if not frappe.db.exists("Service Object", {"object_name": obj_name}):
                so = frappe.new_doc("Service Object")
                so.object_name = obj_name
                so.customer = customer
                so.insert()

        # User Permission: user -> Cust A
        if not frappe.db.exists(
            "User Permission",
            {"user": "cust1@example.com", "allow": "Customer", "for_value": "Cust A"},
        ):
            up = frappe.new_doc("User Permission")
            up.user = "cust1@example.com"
            up.allow = "Customer"
            up.for_value = "Cust A"
            up.insert(ignore_permissions=True)

    def test_client_sees_requests_by_customer(self):
        frappe.set_user("Administrator")
        # Create two SRs under different customers; owners set to Administrator
        for title, so_obj in (("SR-A", "Obj-A"), ("SR-B", "Obj-B")):
            doc = frappe.new_doc("Service Request")
            doc.title = title
            doc.service_object = frappe.db.get_value("Service Object", {"object_name": so_obj})
            doc.insert()
        sr_a = frappe.db.get_value("Service Request", {"title": "SR-A"})
        sr_b = frappe.db.get_value("Service Request", {"title": "SR-B"})

        # As client, only SR-A (Cust A) should be visible
        frappe.set_user("cust1@example.com")
        rows = frappe.get_list(
            "Service Request",
            filters={"name": ["in", [sr_a, sr_b]]},
            pluck="name",
        )
        assert sr_a in rows
        assert sr_b not in rows
        frappe.set_user("Administrator")

