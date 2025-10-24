import frappe
from frappe.tests.utils import FrappeTestCase

from ferum_custom.ferum_custom.api.service import create_service_request


class TestServiceRequestPortal(FrappeTestCase):
	def test_api_create_service_request_smoke(self):
		frappe.set_user("Administrator")
		name = None
		try:
			name = create_service_request(
				title="Portal API Smoke", description="from test", service_object=None
			)
			self.assertTrue(frappe.db.exists("Issue", name))
		finally:
			if name:
				frappe.delete_doc("Issue", name, force=1)
