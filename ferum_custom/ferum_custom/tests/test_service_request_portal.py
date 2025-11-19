import frappe
from frappe.tests.utils import FrappeTestCase

from ferum_custom.ferum_custom.api.service import create_service_request
from ferum_custom.ferum_custom.tests import smoke_tools


class TestServiceRequestPortal(FrappeTestCase):
	def test_api_create_service_request_smoke(self):
		frappe.set_user("Administrator")
		smoke_tools.ensure_company()
		name = None
		try:
			result = create_service_request(
				title="Portal API Smoke", description="from test", service_object=None
			)
			name = result.get("name") if isinstance(result, dict) else str(result)
			self.assertTrue(frappe.db.exists("Service Request", name))
		finally:
			if name:
				frappe.delete_doc("Service Request", name, force=1)
