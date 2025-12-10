import frappe
from frappe.tests.utils import FrappeTestCase

from ferum_custom.ferum_custom.api.service import create_service_request as create_issue
from ferum_custom.ferum_custom.tests import smoke_tools


class TestIssuePortal(FrappeTestCase):
	    def test_api_create_issue_smoke(self):
	        frappe.set_user("Administrator")
	        smoke_tools.ensure_company()
	        name = None
	        try:
	            result = create_issue(
	                title="Portal API Smoke", description="from test", service_object=None
	            )
	            name = result.get("name") if isinstance(result, dict) else str(result)
	            self.assertTrue(frappe.db.exists("Issue", name))
	        finally:
	            if name:
	                frappe.delete_doc("Issue", name, force=1)
