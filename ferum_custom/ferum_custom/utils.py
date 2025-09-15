from collections.abc import Sequence

import frappe


def get_emails_by_roles(roles: Sequence[str]) -> list[str]:
	"""Return user emails for any of the given roles.

	If a user has no email set, their username is used instead.
	"""
	if not roles:
		return []
	user_ids = frappe.get_all(
		"Has Role",
		filters={"role": ["in", list(roles)], "parenttype": "User"},
		pluck="parent",
	)
	if not user_ids:
		return []
	users = frappe.get_all(
		"User",
		filters={"name": ["in", user_ids]},
		fields=["name", "email"],
	)
	return [u.get("email") or u["name"] for u in users]
