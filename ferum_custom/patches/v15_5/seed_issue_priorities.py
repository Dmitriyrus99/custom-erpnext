"""Ensure default Issue Priority records exist.

During recent migrations the built-in Issue Priority rows (Low/Medium/High)
were dropped, which makes `Issue.priority` link validation fail when the bot
tries to update statuses. This patch recreates the defaults idempotently so
API writes from the Telegram bot and desk form edits succeed again.
"""

from __future__ import annotations

import frappe


def execute() -> None:
	priorities = [
		("Low", "Low priority"),
		("Medium", "Medium priority"),
		("High", "High priority"),
	]

	for name, description in priorities:
		if frappe.db.exists("Issue Priority", name):
			continue
		doc = frappe.new_doc("Issue Priority")
		doc.name = name
		doc.description = description
		doc.insert(ignore_permissions=True, ignore_if_duplicate=True)

	# Ensure data is flushed to the DB when running via bench execute
	frappe.db.commit()

	# Normalise any issues that carry stale priority values pointing to missing rows
	valid = tuple(p[0] for p in priorities)
	placeholders = ", ".join(["%s"] * len(valid))
	frappe.db.sql(
		f"""
			update `tabIssue`
			set priority = NULL
			where coalesce(priority, '') != '' and priority not in ({placeholders})
		""",
		valid,
	)
