import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import nowdate


class TestServiceMaintenanceSchedule(FrappeTestCase):
	def test_insert_schedule_smoke(self):
		frappe.set_user("Administrator")
		company = frappe.get_all("Company", pluck="name", limit=1)[0]
		customer = frappe.get_all("Customer", pluck="name", limit=1)
		self.assertTrue(company)
		if not customer:
			# create a minimal customer for test
			c = frappe.new_doc("Customer")
			c.customer_name = "Test Customer SMS"
			c.save()
			customer = [c.name]
		name = None
		try:
			doc = frappe.new_doc("Service Maintenance Schedule")
			doc.company = company
			doc.schedule_name = "TEST-SMS"
			doc.customer = customer[0]
			doc.frequency = "Monthly"
			doc.start_date = nowdate()
			doc.next_due_date = nowdate()
			doc.save()
			name = doc.name
			self.assertTrue(frappe.db.exists("Service Maintenance Schedule", name))
		finally:
			if name:
				frappe.delete_doc("Service Maintenance Schedule", name, force=1)
