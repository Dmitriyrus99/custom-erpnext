import frappe
from frappe.tests.utils import FrappeTestCase
from unittest import mock

from ferum_custom.api.service import portal_token
from ferum_custom.ferum_custom.api import service as portal_service


class TestPortalAPI(FrappeTestCase):
    def test_portal_token_requires_login(self):
        frappe.set_user("Guest")
        with self.assertRaises(frappe.AuthenticationError):
            portal_token()

    def test_require_jwt_authentication_requires_token(self):
        with mock.patch.object(portal_service, "is_feature_enabled", return_value=True), \
             mock.patch("frappe.get_request_header", return_value=None):
            frappe.set_user("Guest")
            with self.assertRaises(frappe.AuthenticationError):
                portal_service._require_jwt_authentication()

    def test_check_new_request_rate_limit_calls_tracker(self):
        calls = []

        def fake_enforce(scope, identifier, limit):
            calls.append((scope, identifier, limit))

        def fake_get_setting(field, default=None):
            return "1" if field == "rate_limit_create_request_per_minute" else default

        with mock.patch.object(portal_service, "is_feature_enabled", return_value=True), \
             mock.patch.object(portal_service, "get_setting", side_effect=fake_get_setting), \
             mock.patch.object(portal_service, "_get_client_ip", return_value="1.2.3.4"), \
             mock.patch.object(portal_service, "_enforce_rate_limit", fake_enforce):
            frappe.set_user("Test User")
            portal_service._check_new_request_rate_limit()

        scopes = {item[0] for item in calls}
        self.assertIn("new_request_ip", scopes)
        self.assertIn("new_request_user", scopes)
