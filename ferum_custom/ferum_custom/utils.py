from collections.abc import Iterable

import frappe


def get_users_by_roles(roles: list[str]) -> set[str]:
	"""Fetch email addresses of users with the given roles."""
	users = frappe.get_all(
		"Has Role",
		filters={"role": ["in", roles], "parenttype": "User"},
		pluck="parent",
	)
	recipients: set[str] = set()
	if users:
		for u in frappe.db.get_all(
			"User",
			filters={"name": ["in", users]},
			fields=["email"],
		):
			if u.email:
				recipients.add(u.email)
	return recipients


def parse_names_argument(names: Iterable[str] | str | None) -> list[str]:
	"""Return a clean list of names from RPC inputs (list, JSON string or CSV)."""

	if names is None:
		return []
	if isinstance(names, str):
		try:
			parsed = frappe.parse_json(names)
		except Exception:
			parsed = None
		if isinstance(parsed, list | tuple):
			names_iter = parsed
		else:
			names_iter = [part.strip() for part in names.split(",")]
	else:
		names_iter = names

	result: list[str] = []
	for item in names_iter:
		text = str(item).strip()
		if text:
			result.append(text)
	return result
