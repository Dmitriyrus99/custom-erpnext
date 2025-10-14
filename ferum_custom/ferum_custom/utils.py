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


def user_roles(user: str | None = None) -> set[str]:
	"""Return a cached set of roles for the given user (defaults to session user)."""
	try:
		return set(frappe.get_roles(user))
	except Exception:
		return set()


def get_allowed_customers(user: str | None = None) -> list[str]:
	"""Return list of Customer names the user is explicitly permitted to.

	Uses User Permission records with Allow = Customer. Empty list means no
	explicit Customer restriction configured for the user.
	"""
	u = user or frappe.session.user
	try:
		return frappe.get_all(
			"User Permission",
			filters={"user": u, "allow": "Customer"},
			pluck="for_value",
		)
	except Exception:
		return []


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
