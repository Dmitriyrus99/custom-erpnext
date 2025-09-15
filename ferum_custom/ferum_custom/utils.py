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
