import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_to_date


class TestWorkflows(FrappeTestCase):
	def setUp(self):
		# Ensure administrator context for setup
		frappe.set_user("Administrator")
		# Ensure a minimal customer and service object exist
		if not frappe.db.exists("Customer", "Test Customer"):
			c = frappe.new_doc("Customer")
			c.customer_name = "Test Customer"
			c.insert()
		if not frappe.db.exists("Service Object", {"object_name": "Obj-1"}):
			so = frappe.new_doc("Service Object")
			so.object_name = "Obj-1"
			so.customer = "Test Customer"
			so.insert()

	def test_sla_deadline_calculation(self):
		# Emergency / High → +4 hours
		sr = frappe.new_doc("Service Request")
		sr.title = "Test SLA"
		sr.type = "Emergency"
		sr.priority = "High"
		sr.service_object = frappe.db.get_value("Service Object", {"object_name": "Obj-1"})
		sr.insert()
		sr.reload()
		assert sr.sla_deadline, "SLA deadline should be set"
		assert sr.sla_deadline == add_to_date(sr.creation, hours=4)

	def test_status_requires_assigned(self):
		sr = frappe.new_doc("Service Request")
		sr.title = "Need engineer"
		sr.type = "Routine Maintenance"
		sr.priority = "Low"
		sr.service_object = frappe.db.get_value("Service Object", {"object_name": "Obj-1"})
		sr.insert()
		sr.status = "In Progress"
		with self.assertRaises(frappe.ValidationError):
			sr.save()

	def test_service_report_submit_updates_request(self):
		# Create request
		sr = frappe.new_doc("Service Request")
		sr.title = "Finish with report"
		sr.type = "Routine Maintenance"
		sr.priority = "High"
		sr.service_object = frappe.db.get_value("Service Object", {"object_name": "Obj-1"})
		sr.insert()

		# Prepare a minimal Custom Attachment for report document
		att = frappe.new_doc("Custom Attachment")
		att.file_name = "report.pdf"
		att.file_url = "https://example.com/report.pdf"
		att.insert()

		# Create Service Report with one work item and one document
		rep = frappe.new_doc("Service Report")
		rep.service_request = sr.name
		rep.report_date = frappe.utils.nowdate()
		rep.append("work_items", {"description": "Work", "hours": 1.0, "rate": 100})
		rep.append("documents", {"custom_attachment": att.name})
		rep.insert()
		rep.submit()
		sr.reload()
		assert sr.status == "Completed"
		assert sr.linked_report == rep.name
