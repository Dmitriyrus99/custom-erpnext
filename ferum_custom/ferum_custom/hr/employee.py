from __future__ import annotations

"""Employee-related helpers."""

import frappe


def ensure_unique_middle_name_for_tests(doc, _):
	"""Populate ``middle_name`` with a unique value during automated tests.

	Customer deployments set :class:`User`'s ``middle_name`` field to ``unique``.
	Frappe's stock test records leave the field empty, which would violate that
	constraint. During the test runner we fill the field with the employee's
	document name, keeping behaviour consistent while avoiding duplicate values.
	"""

	if not (
		frappe.flags.in_test
		or (getattr(doc, "name", "") or "").startswith("_T-")
		or (getattr(doc, "user_id", "") or "").startswith("test")
	):
		return

	if getattr(doc, "middle_name", None):
		return

	# doc.name is already assigned before before_save hooks run
	doc.middle_name = doc.name or frappe.generate_hash(length=10)


def sync_user_middle_name(doc, _):
	"""Ensure linked user's ``middle_name`` mirrors the employee during tests."""

	if not getattr(doc, "user_id", None):
		return

	if not (
		frappe.flags.in_test
		or (getattr(doc, "name", "") or "").startswith("_T-")
		or (doc.user_id or "").startswith("test")
	):
		return

	frappe.db.set_value("User", doc.user_id, "middle_name", doc.middle_name, update_modified=False)
