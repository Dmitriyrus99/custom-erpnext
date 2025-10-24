import frappe
from frappe.tests.utils import FrappeTestCase


class TestRolesPermissionsMatrix(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		# Create customers and objects
		for cust in ("Perm C1", "Perm C2"):
			if not frappe.db.exists("Customer", cust):
				c = frappe.new_doc("Customer")
				c.customer_name = cust
				c.insert()
		if not frappe.db.exists("Service Object", {"object_name": "Obj-C1"}):
			so = frappe.new_doc("Service Object")
			so.object_name = "Obj-C1"
			so.customer = "Perm C1"
			so.insert()
		if not frappe.db.exists("Service Object", {"object_name": "Obj-C2"}):
			so = frappe.new_doc("Service Object")
			so.object_name = "Obj-C2"
			so.customer = "Perm C2"
			so.insert()

		# Departments
		for dept in ("SD-A", "SD-B"):
			if not frappe.db.exists("Service Department", dept):
				d = frappe.new_doc("Service Department")
				d.department_name = dept
				d.insert()

		# Projects per department
		for proj, cust, _obj, dept in (
			("SP-A", "Perm C1", "Obj-C1", "SD-A"),
			("SP-B", "Perm C2", "Obj-C2", "SD-B"),
		):
			if not frappe.db.exists("Service Project", proj):
				p = frappe.new_doc("Service Project")
				p.project_name = proj
				p.customer = cust
				p.service_department = dept
				p.insert()

		# Service Requests under projects
		for title, obj, proj in (("SR-A", "Obj-C1", "SP-A"), ("SR-B", "Obj-C2", "SP-B")):
			if not frappe.db.exists("Service Request", {"title": title}):
				sr = frappe.new_doc("Service Request")
				sr.title = title
				sr.service_object = frappe.db.get_value("Service Object", {"object_name": obj})
				sr.project = frappe.db.get_value("Service Project", {"project_name": proj}, "name")
				sr.insert()

		# Users
		if not frappe.db.exists("User", "om@example.com"):
			u = frappe.new_doc("User")
			u.email = "om@example.com"
			u.first_name = "OM"
			u.user_type = "System User"
			u.insert()
		if "Office Manager" not in frappe.get_roles("om@example.com"):
			frappe.get_doc("User", "om@example.com").add_roles("Office Manager")
		if not frappe.db.exists("User", "dh@example.com"):
			u = frappe.new_doc("User")
			u.email = "dh@example.com"
			u.first_name = "DH"
			u.user_type = "System User"
			u.insert()
		if "Department Head" not in frappe.get_roles("dh@example.com"):
			frappe.get_doc("User", "dh@example.com").add_roles("Department Head")

		# User Permission: DH -> SD-A only
		if not frappe.db.exists(
			"User Permission",
			{"user": "dh@example.com", "allow": "Service Department", "for_value": "SD-A"},
		):
			up = frappe.new_doc("User Permission")
			up.user = "dh@example.com"
			up.allow = "Service Department"
			up.for_value = "SD-A"
			up.insert(ignore_permissions=True)

	def test_office_manager_reads_all_requests(self):
		frappe.set_user("om@example.com")
		names = frappe.get_list("Service Request", pluck="name")
		# Should see at least the two created
		assert len(names) >= 2
		frappe.set_user("Administrator")

	def test_department_head_sees_only_own_department(self):
		frappe.set_user("dh@example.com")
		rows = frappe.get_list("Service Request", fields=["name", "project", "service_department"])
		depts = {row.service_department for row in rows}
		assert depts.issubset({"SD-A"})
		frappe.set_user("Administrator")
