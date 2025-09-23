"""Testing helpers mimicking a subset of Frappe's test utilities."""

from __future__ import annotations

import unittest

import frappe


class FrappeTestCase(unittest.TestCase):
        """TestCase base class providing a clean default session."""

        def setUp(self) -> None:  # noqa: D401 - pytest style docstring not required
                frappe.db.reset()
                frappe.set_user("Administrator")
