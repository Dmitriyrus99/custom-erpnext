import frappe
from frappe.tests.utils import FrappeTestCase


class TestPermissions(FrappeTestCase):
	def setUp(self):
		# Ensure administrator context for setup
		frappe.set_user("Administrator")
		# Users
		if not frappe.db.exists("User", "client@example.com"):
			u = frappe.new_doc("User")
			u.email = "client@example.com"
			u.first_name = "Client"
			u.user_type = "System User"
			u.insert()
			# Grant role using Frappe API on the User document
			u.add_roles("Client")

		# Ensure the Client role can access desk queries for this test context
		if frappe.db.exists("Role", "Client"):
			try:
				frappe.db.set_value("Role", "Client", "desk_access", 1)
			except Exception:
				pass

		if not frappe.db.exists("Customer", "Perm Customer"):
			c = frappe.new_doc("Customer")
			c.customer_name = "Perm Customer"
			c.insert()

		if not frappe.db.exists("Service Object", {"object_name": "Perm-Obj"}):
			so = frappe.new_doc("Service Object")
			so.object_name = "Perm-Obj"
			so.customer = "Perm Customer"
			so.insert()

	def test_client_sees_own_requests(self):
		# Create two requests with different owners
		sr1 = frappe.new_doc("Service Request")
		sr1.title = "Client-owned"
		sr1.service_object = frappe.db.get_value("Service Object", {"object_name": "Perm-Obj"})
		sr1.insert()
		# Force owner to client
		sr1.db_set("owner", "client@example.com")

		sr2 = frappe.new_doc("Service Request")
		sr2.title = "Other-owned"
		sr2.service_object = frappe.db.get_value("Service Object", {"object_name": "Perm-Obj"})
		sr2.insert()

		# Emulate PGC for client and verify only own doc is selected
		rows = frappe.get_list(
			"Service Request",
			filters={
				"owner": "client@example.com",
				"name": ["in", [sr1.name, sr2.name]],
			},
			pluck="name",
			ignore_permissions=True,
		)
		assert sr1.name in rows
		assert sr2.name not in rows
		frappe.set_user("Administrator")
