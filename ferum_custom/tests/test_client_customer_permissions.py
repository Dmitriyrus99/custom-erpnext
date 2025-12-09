import frappe
from frappe.tests.utils import FrappeTestCase

from ferum_custom.ferum_custom.tests import smoke_tools
from ferum_custom.ferum_custom.utils import get_allowed_customers


class TestClientCustomerPermissions(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.company = smoke_tools.ensure_company()
		self.customers = {}
		# Create client user
		if not frappe.db.exists("User", "cust1@example.com"):
			u = frappe.new_doc("User")
			u.email = "cust1@example.com"
			u.first_name = "Cust1"
			u.user_type = "Website User"
			u.insert()
		if "Client" not in frappe.get_roles("cust1@example.com"):
			frappe.get_doc("User", "cust1@example.com").add_roles("Client")
		# Customers and Service Objects
		for customer in ("Cust A", "Cust B"):
			smoke_tools.ensure_customer(customer, company=self.company)
			self.customers[customer] = frappe.db.get_value("Customer", {"customer_name": customer}, "name")
		for obj_name, customer in (("Obj-A", "Cust A"), ("Obj-B", "Cust B")):
			smoke_tools.ensure_asset(obj_name, customer=self.customers[customer], company=self.company)

		# User Permissions
		if not frappe.db.exists(
			"User Permission",
			{"user": "cust1@example.com", "allow": "Company", "for_value": self.company},
		):
			up = frappe.new_doc("User Permission")
			up.user = "cust1@example.com"
			up.allow = "Company"
			up.for_value = self.company
			up.insert(ignore_permissions=True)
		# Customer restriction
		if not frappe.db.exists(
			"User Permission",
			{"user": "cust1@example.com", "allow": "Customer", "for_value": self.customers["Cust A"]},
		):
			up = frappe.new_doc("User Permission")
			up.user = "cust1@example.com"
			up.allow = "Customer"
			up.for_value = self.customers["Cust A"]
			up.insert(ignore_permissions=True)
		frappe.clear_cache(user="cust1@example.com")

	def test_client_sees_requests_by_customer(self):
		frappe.set_user("Administrator")
		# Create two Issues under different customers; owners set to Administrator
		for title, so_obj in (("SR-A", "Obj-A"), ("SR-B", "Obj-B")):
			issue_doc = frappe.new_doc("Issue")
			issue_doc.subject = title
			issue_doc.company = self.company
			issue_doc.customer = self.customers["Cust A"] if so_obj == "Obj-A" else self.customers["Cust B"]
			issue_doc.asset = frappe.db.get_value("Asset", {"asset_name": so_obj})
			issue_doc.owner = "cust1@example.com"
			issue_doc.insert()
		issue_a = frappe.db.get_value("Issue", {"subject": "SR-A"})
		issue_b = frappe.db.get_value("Issue", {"subject": "SR-B"})

		# As client, only SR-A (Cust A) should be visible
		frappe.set_user("cust1@example.com")

		doc_a = frappe.get_doc("Issue", issue_a)
		doc_b = frappe.get_doc("Issue", issue_b)
		allowed = set(get_allowed_customers("cust1@example.com"))
		assert self.customers["Cust A"] in allowed
		doc_a.customer = self.customers["Cust A"]
		doc_b.customer = self.customers["Cust B"]
		# Permissions are now implicitly handled by the framework based on User Permissions
		# and standard Issue DocType behavior, so explicit security_pqc_rules checks are removed.
		# You would typically rely on frappe.get_list or frappe.get_doc to test permissions
		# which automatically apply the relevant PQC rules for the current user.
		# For direct testing, you might use frappe.has_permission(Issue, "read", doc_a) if needed.
		assert frappe.has_permission("Issue", ptype="read", doc=doc_a)
		assert not frappe.has_permission("Issue", ptype="read", doc=doc_b)
		frappe.set_user("Administrator")
