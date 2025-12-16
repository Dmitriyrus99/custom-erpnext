from __future__ import annotations

"""Unified notification dispatcher for email, Telegram and future channels.

Usage:
    from ferum_custom.notifications.dispatcher import notify

    notify(
        event_type="new_service_request",
        recipients=["user@example.com", "Administrator"],
        context={"name": "SR-0001", "title": "Printer jam", "priority": "High"},
    )

The dispatcher renders templates per channel and sends via the preferred
channel(s) per user (role-based defaults with optional user-level overrides
when custom fields exist).
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

import frappe

from ferum_custom.ferum_custom.integrations import telegram as telegram_integration
from ferum_custom.ferum_custom.settings import is_feature_enabled

# Event templates per channel. Simple Python str.format with context.
TEMPLATES: dict[str, dict[str, str]] = {
	"new_service_request": {
		"email_subject": "New Service Request {name}",
		"email_body": (
			"A new service request {name} was created.\n\n"
			"Title: {title}\nPriority: {priority}\nProject: {project}"
		),
		"telegram": "New Service Request {name}: {title} (Priority: {priority})",
	},
	"issue_assigned": {
		"email_subject": "Issue assigned: {issue}",
		"email_body": (
			"You have been assigned to issue {issue}.\n\n"
			"Subject: {subject}\nProject: {project}\nStatus: {status}"
		),
		"telegram": "Assigned to issue {issue}: {subject}",
	},
	"service_request_status_changed": {
		"email_subject": "Service Request {name} status: {status}",
		"email_body": ("Service Request {name} status changed to {status}.\n\nTitle: {title}"),
		"telegram": "SR {name} → {status}: {title}",
	},
	"sla_breach": {
		"email_subject": "SLA breached for {name}",
		"email_body": (
			"SLA breached for Service Request {name}.\n\nTitle: {title}\nPriority: {priority}\nDue: {due}"
		),
		"telegram": "SLA breached: {name} – {title} (due {due})",
	},
}


@dataclass(frozen=True)
class Rendered:
	email_subject: str
	email_body: str
	telegram_text: str


def _render(event_type: str, context: Mapping[str, Any]) -> Rendered:
	tpl = TEMPLATES.get(event_type, {})
	email_subject = tpl.get("email_subject", event_type).format(**context)
	email_body = tpl.get("email_body", "").format(**context)
	telegram_text = tpl.get("telegram", email_subject).format(**context)
	return Rendered(email_subject, email_body, telegram_text)


def _norm_user(user_or_email: str) -> str | None:
	"""Return the User.name given a user id or email; None if not found."""
	if not user_or_email:
		return None
	# If exact User exists, accept
	if frappe.db.exists("User", user_or_email):
		return user_or_email
	# Otherwise resolve by email
	try:
		rows = frappe.get_all("User", filters={"email": user_or_email}, pluck="name", limit=1)
		return rows[0] if rows else None
	except Exception:
		return None


def _user_email(user: str) -> str | None:
	try:
		return frappe.db.get_value("User", user, "email")
	except Exception:
		return None


def _user_roles(user: str) -> set[str]:
	try:
		return set(frappe.get_roles(user))
	except Exception:
		return set()


def _resolve_telegram_chat_id(user: str) -> str | None:
	# Prefer explicit mapping in Telegram User Link
	try:
		rows = frappe.get_all("Telegram User Link", filters={"user": user}, pluck="chat_id", limit=1)
		if rows and rows[0]:
			return str(rows[0])
	except Exception:
		pass
	# Fallback to custom field on User if present
	try:
		val = frappe.db.get_value("User", user, "telegram_chat_id")
		if val:
			return str(val)
	except Exception:
		pass
	return None


def _channel_prefs(user: str) -> list[str]:
	"""Return preferred channels for a user.

	Order matters. If user has custom fields `notify_via_telegram` or
	`notify_via_email`, respect them. Otherwise apply role-based defaults.
	"""
	channels: list[str] = []

	# Custom user opt-in/out fields if present
	try:
		vals = frappe.db.get_value("User", user, ["notify_via_telegram", "notify_via_email"], as_dict=True)
	except Exception:
		vals = None

	if isinstance(vals, dict):
		if vals.get("notify_via_telegram"):
			channels.append("telegram")
		if vals.get("notify_via_email"):
			channels.append("email")
		if channels:
			return channels

	roles = _user_roles(user)
	# Defaults: engineers prefer telegram, PM both, clients email
	if "Service Engineer" in roles:
		channels = ["telegram", "email"]
	elif "Project Manager" in roles:
		channels = ["email", "telegram"]
	elif "Client" in roles:
		channels = ["email"]
	else:
		channels = ["email"]
	return channels


def _send_email(user: str, subject: str, body: str) -> bool:
	email = _user_email(user)
	if not email:
		return False
	try:
		frappe.sendmail(recipients=[email], subject=subject, message=body)
		return True
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Notify: email send failed to {user}")
		return False


def _send_telegram(user: str, text: str) -> bool:
	if not is_feature_enabled("enable_telegram_notifications"):
		return False
	chat_id = _resolve_telegram_chat_id(user)
	if not chat_id or not telegram_integration.is_chat_allowed(chat_id):
		return False
	try:
		return bool(telegram_integration.send_message(text, chat_id=chat_id))
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Notify: telegram send failed to {user}")
		return False


def notify(
	event_type: str,
	recipients: Iterable[str] | None = None,
	context: Mapping[str, Any] | None = None,
	roles: Iterable[str] | None = None,
	channels_override: Iterable[str] | None = None,
) -> dict[str, Any]:
	"""Dispatch a notification to recipients (user ids or emails).

	- event_type: template key in TEMPLATES
	- recipients: iterable of user ids or emails
	- roles: optional roles to expand into users (added to recipients)
	- context: mapping for template rendering
	- channels_override: forces channels order for all users (e.g., ["email"])
	"""
	context = dict(context or {})
	rendered = _render(event_type, context)

	users: set[str] = set()
	if recipients:
		for r in recipients:
			user = _norm_user(str(r))
			if user:
				users.add(user)

	if roles:
		try:
			role_users = set(
				frappe.get_all("Has Role", filters={"role": ["in", list(roles)]}, pluck="parent")
			)
			users.update(role_users)
		except Exception:
			pass

	def _opted_out(user: str) -> bool:
		try:
			raw = frappe.db.get_value("User", user, "notify_opt_out_types")
			if not raw:
				return False
			try:
				data = frappe.parse_json(raw)
				if isinstance(data, list):
					return event_type in data
			except Exception:
				# support comma-separated list
				items = [x.strip() for x in str(raw).split(",") if x.strip()]
				return event_type in items
		except Exception:
			return False

	results = {"sent": 0, "email": 0, "telegram": 0, "skipped": 0}
	for user in users:
		if _opted_out(user):
			results["skipped"] += 1
			continue
		channels = list(channels_override) if channels_override else _channel_prefs(user)
		delivered = False
		for ch in channels:
			if ch == "email":
				delivered = _send_email(user, rendered.email_subject, rendered.email_body) or delivered
				if delivered:
					results["email"] += 1
			elif ch == "telegram":
				delivered = _send_telegram(user, rendered.telegram_text) or delivered
				if delivered:
					results["telegram"] += 1
		if delivered:
			results["sent"] += 1
		else:
			results["skipped"] += 1

	return results
