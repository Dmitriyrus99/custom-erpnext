import frappe
from frappe.tests.utils import FrappeTestCase

from ferum_custom.ferum_custom.api import service as service_api
from ferum_custom.ferum_custom.tests import smoke_tools


class TestIssuePortal(FrappeTestCase):
	def test_api_create_issue_smoke(self):
		frappe.set_user("Administrator")
		smoke_tools.ensure_company()
		name = None
		try:
			result = service_api.create_issue(title="Portal API Smoke", description="from test", asset=None)
			name = result.get("name") if isinstance(result, dict) else str(result)
			self.assertTrue(frappe.db.exists("Issue", name))
		finally:
			if name:
				frappe.delete_doc("Issue", name, force=1)
