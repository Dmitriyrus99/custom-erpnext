from __future__ import annotations

from unittest import mock

import frappe
from frappe.tests.utils import FrappeTestCase

from ferum_custom.api import service as service_api


class TestJWTAuthentication(FrappeTestCase):
    def test_requires_token(self):
        monkeypatch_get_header = mock.patch("frappe.get_request_header", return_value=None)
        monkeypatch_feature = mock.patch.object(
            service_api, "is_feature_enabled", return_value=True
        )

        with monkeypatch_get_header, monkeypatch_feature:
            frappe.set_user("Guest")
            with self.assertRaises(frappe.AuthenticationError):
                service_api._require_jwt_authentication()
