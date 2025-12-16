"""Telegram bot webhook endpoint for Ferum Custom.

This module keeps the public surface (`handle_update`) identical while
splitting the previous monolithic implementation into smaller helpers.
The refactor improves readability, makes individual commands easier to
extend and provides light-weight abstractions for replying back to
Telegram chats.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit

from ferum_custom.ferum_custom.integrations import telegram as telegram_integration
from ferum_custom.ferum_custom.metrics import inc as metrics_inc
from ferum_custom.ferum_custom.settings import get_setting, is_feature_enabled

try:  # pragma: no cover - optional dependency, exercised in production
	import requests  # type: ignore[import-untyped]
except Exception:  # pragma: no cover
	requests = None  # type: ignore[assignment]


class CommandError(Exception):
	"""Exception raised when a user-facing error should be reported."""

	def __init__(self, message: str) -> None:
		super().__init__(message)
		self.message = message


def _reply(chat_id: int | str | None, text: str) -> None:
	if chat_id is None:
		return
	try:
		ok = telegram_integration.send_message(text, chat_id=str(chat_id), max_retries=5)
		if not ok:
			frappe.log_error(
				f"Telegram reply send failed after retries to chat={chat_id}",
				"Telegram reply failed",
			)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Telegram reply failed")


# ------------------------------
# Idempotency helpers
# ------------------------------


def _idempotency_key(update: dict[str, Any]) -> str | None:
	try:
		if update.get("update_id") is not None:
			return f"telegram:update:{update['update_id']}"
	except Exception:
		pass
	try:
		msg = update.get("message") or {}
		mid = msg.get("message_id")
		chat = (msg.get("chat") or {}).get("id")
		if mid is not None and chat is not None:
			return f"telegram:message:{chat}:{mid}"
	except Exception:
		pass
	return None


def _already_processed(update: dict[str, Any]) -> bool:
	key = _idempotency_key(update)
	if not key:
		return False
	try:
		return bool(frappe.cache().get_value(key, expires=True) is not None)
	except Exception:
		return False


def _mark_processed(update: dict[str, Any], ttl_seconds: int = 7 * 24 * 60 * 60) -> None:
	key = _idempotency_key(update)
	if not key:
		return
	try:
		frappe.cache().set_value(key, 1, expires_in_sec=ttl_seconds)
	except Exception:
		pass


def _user_from_update(update: dict[str, Any]) -> str | None:
	try:
		return str(update["message"]["from"]["username"])  # type: ignore[index]
	except Exception:
		return None


def _chat_id(update: dict[str, Any]) -> str | None:
	try:
		return str(update["message"]["chat"]["id"])  # type: ignore[index]
	except Exception:
		return None


def _split_command(text: str) -> tuple[str | None, str]:
	if not text.startswith("/"):
		return None, text
	parts = text.split(" ", 1)
	command = parts[0].strip()
	argument = parts[1].strip() if len(parts) > 1 else ""
	return command, argument


@dataclass(slots=True)
class TelegramContext:
	payload: dict[str, Any]
	chat_id: str | None
	text: str
	command: str | None
	argument: str
	user: str | None
	erp_user: str | None = None

	def reply(self, message: str) -> None:
		_reply(self.chat_id, message)

	@property
	def has_photo(self) -> bool:
		try:
			return bool(self.payload.get("message", {}).get("photo"))
		except Exception:
			return False

	@property
	def caption(self) -> str:
		try:
			return str(self.payload.get("message", {}).get("caption") or "").strip()
		except Exception:
			return ""


def _build_context(update: dict[str, Any]) -> TelegramContext:
	message = update.get("message") or {}
	text = str(message.get("text") or "").strip()
	command, argument = _split_command(text) if text else (None, "")
	return TelegramContext(
		payload=update,
		chat_id=_chat_id(update),
		text=text,
		command=command,
		argument=argument,
		user=_user_from_update(update),
	)


def _enforce_command_rate_limit(ctx: TelegramContext, limit: int = 30, seconds: int = 60) -> None:
	"""Per-chat per-command throttle to reduce spam and accidental loops."""
	if not ctx.command or not ctx.chat_id:
		return
	try:
		key = f"tg:cmd:{ctx.chat_id}:{ctx.command}"
		cache = frappe.cache()
		count = cache.incr(key)
		if count == 1:
			cache.expire(key, seconds)
		if count > limit:
			try:
				metrics_inc(
					"ferum_integration_telegram_command_total",
					{"command": ctx.command, "result": "throttled"},
				)
			except Exception:
				pass
			raise CommandError(_("Too many requests, slow down."))
	except CommandError:
		raise
	except Exception:
		# On cache issues, fail open to avoid blocking users
		return


def _has_admin_role(ctx: TelegramContext) -> bool:
	"""Admin commands require mapped ERP user with System Manager or Telegram Admin role."""
	roles = set(frappe.get_roles())
	return bool({"System Manager", "Telegram Admin"} & roles)


def _user_has_roles(ctx: TelegramContext, required: set[str]) -> bool:
	"""Check that the mapped ERP user (or session user) has any of the required roles."""
	try:
		roles = set(frappe.get_roles())
		return bool(roles & required)
	except Exception:
		return False


def _ensure_argument(ctx: TelegramContext, usage: str) -> str:
	if ctx.argument:
		return ctx.argument
	raise CommandError(_("Usage: {0}").format(usage))


def _cmd_new_issue(ctx: TelegramContext) -> None:
	title = ctx.argument or _("New Request")
	name = frappe.call("ferum_custom.api.service.create_issue", title=title)
	ctx.reply(_("Request created: {0}").format(name))


def _load_request(req: str):
	"""Resolve request name to Service Request or Issue."""
	if frappe.db.exists("Service Request", req):
		return frappe.get_doc("Service Request", req)
	if frappe.db.exists("Issue", req):
		return frappe.get_doc("Issue", req)
	raise CommandError(_("Request {0} not found").format(req))


def _cmd_my_issues(ctx: TelegramContext) -> None:
	res = frappe.call(
		"ferum_custom.api.service.list_issues",
		start=0,
		page_length=10,
	)
	lines = [f"{x['name']} - {x['title']} - {x['status']}" for x in res.get("data", [])]
	ctx.reply("\n".join(lines) or _("No requests"))


def _cmd_start_work(ctx: TelegramContext) -> None:
	req = _ensure_argument(ctx, "/start_work <issue_name>")
	if not _user_has_roles(ctx, {"Engineer", "Support Team", "System Manager"}):
		raise CommandError(_("Only engineers/support may start work"))
	doc = _load_request(req)
	user = frappe.session.user

	if doc.doctype == "Service Request":
		if doc.status not in ("Open", "In Progress"):
			raise CommandError(_("Service Request must be Open to start work."))
		if not getattr(doc, "assigned_to", None):
			doc.assigned_to = user
		if doc.status != "In Progress":
			doc.status = "In Progress"
		doc.save(ignore_permissions=True)
		ctx.reply(_("Service Request {0} accepted, status: In Progress").format(doc.name))
	else:
		# Standard Issue uses allowed statuses: Open/Replied/Resolved/Closed
		if doc.status == "Closed":
			raise CommandError(_("Issue is already Closed."))
		if doc.status == "Resolved":
			ctx.reply(_("Issue {0} is already Resolved.").format(doc.name))
			return
		if hasattr(doc, "assigned_engineer") and not getattr(doc, "assigned_engineer", None):
			doc.assigned_engineer = user
		# Replied is the closest allowed value to "in progress" in Issue workflow
		if doc.status != "Replied":
			doc.status = "Replied"
		doc.save(ignore_permissions=True)
		ctx.reply(_("Issue {0} accepted, status: Replied").format(doc.name))


def _cmd_done(ctx: TelegramContext) -> None:
	req = _ensure_argument(ctx, "/done <issue_name>")
	if not _user_has_roles(ctx, {"Engineer", "Support Team", "System Manager"}):
		raise CommandError(_("Only engineers/support may resolve issues"))
	doc = _load_request(req)
	if doc.doctype == "Service Request":
		if doc.status in ("Closed", "Cancelled"):
			ctx.reply(_("Service Request {0} already closed.").format(doc.name))
			return
		doc.status = "Completed"
		doc.save(ignore_permissions=True)
		ctx.reply(_("Service Request {0} marked as Completed").format(doc.name))
	else:
		if doc.status == "Closed":
			ctx.reply(_("Issue {0} already Closed.").format(doc.name))
			return
		if doc.status == "Resolved":
			ctx.reply(_("Issue {0} already Resolved.").format(doc.name))
			return
		doc.status = "Resolved"
		doc.save(ignore_permissions=True)
		ctx.reply(_("Issue {0} marked as Resolved").format(doc.name))


def _cmd_close(ctx: TelegramContext) -> None:
	if "System Manager" not in frappe.get_roles():
		raise CommandError(_("Not permitted"))
	req = _ensure_argument(ctx, "/close <issue_name>")
	doc = frappe.get_doc("Issue", req)
	doc.status = "Closed"
	doc.save(ignore_permissions=True)
	ctx.reply(_("Closed: {0}").format(req))


def _cmd_analytics(ctx: TelegramContext) -> None:
	open_count = frappe.db.count(
		"Issue",
		{"status": ["not in", ["Resolved", "Closed"]]},
	)
	paid = frappe.db.count("Sales Invoice", {"status": "Paid"})
	ctx.reply(_("Open requests: {0}\nPaid invoices: {1}").format(open_count, paid))


def _cmd_ping(ctx: TelegramContext) -> None:
	result = telegram_integration.healthcheck()
	status = result.get("status", "unknown")
	if status == "ok":
		details = result.get("details") or {}
		ctx.reply(_("Telegram OK (bot: {0})").format(details.get("username") or details.get("bot_id") or "-"))
	else:
		message = result.get("message") or _("See error logs for details.")
		ctx.reply(_("Telegram not ready: {0} — {1}").format(status, message))


CommandHandler = Callable[[TelegramContext], None]


COMMANDS: dict[str, CommandHandler] = {
	"/new_issue": _cmd_new_issue,
	"/my_issues": _cmd_my_issues,
	"/start_work": _cmd_start_work,
	"/done": _cmd_done,
	"/close": _cmd_close,
	"/analytics": _cmd_analytics,
	"/ping": _cmd_ping,
}

ADMIN_COMMANDS = {"/close", "/analytics", "/ping"}


def _cmd_whoami(ctx: TelegramContext) -> None:
	username = ctx.user or "-"
	ctx.reply(_(f"You are @{username}, chat_id={ctx.chat_id}"))


# Register publicly available helper
COMMANDS["/whoami"] = _cmd_whoami


def _download_photo(token: str, file_id: str) -> tuple[str, bytes]:
	if requests is None:
		raise CommandError(_("Photo handling requires the 'requests' package."))

	try:
		response = requests.get(  # type: ignore[call-overload]
			f"https://api.telegram.org/bot{token}/getFile",
			params={"file_id": file_id},
			timeout=10,
		)
		response.raise_for_status()
		file_path = response.json()["result"]["file_path"]

		download = requests.get(  # type: ignore[call-overload]
			f"https://api.telegram.org/file/bot{token}/{file_path}",
			timeout=20,
		)
		download.raise_for_status()
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), "Telegram photo download failed")
		raise CommandError(_("Failed to download photo from Telegram.")) from exc

	return file_path, download.content


def _attach_photo(ctx: TelegramContext, issue_name: str) -> None:
	token = get_setting("telegram_bot_token")
	if not token:
		raise CommandError(_("Telegram bot token is not configured."))

	try:
		photos = ctx.payload["message"]["photo"]  # type: ignore[index]
		file_id = photos[-1]["file_id"]  # highest resolution item
	except Exception as exc:  # pragma: no cover - defensive; depends on payload
		raise CommandError(_("No photo data provided.")) from exc

	file_path, content = _download_photo(token, file_id)
	file_name = file_path.split("/")[-1]
	if len(content) > 7_000_000:
		raise CommandError(_("File too large (max 7 MB)."))

	try:
		file_doc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": file_name,
				"content": content,
				"is_private": 0,
				"attached_to_doctype": "Issue",
				"attached_to_name": issue_name,
			}
		)
		file_doc.insert(ignore_permissions=True)

	except CommandError:
		raise
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), "Telegram photo attach failed")
		raise CommandError(_("Failed to attach photo")) from exc

	ctx.reply(_("Photo attached to {0}").format(issue_name))


def _handle_photo_payload(ctx: TelegramContext) -> bool:
	if not ctx.has_photo:
		return False

	caption = ctx.caption
	if not caption.startswith("/attach"):
		return False

	if " " not in caption:
		raise CommandError(_("Usage: /attach <issue_name>"))

	issue_name = caption.split(" ", 1)[1].strip()
	if not issue_name:
		raise CommandError(_("Usage: /attach <issue_name>"))

	_attach_photo(ctx, issue_name)
	return True


def _dispatch_command(ctx: TelegramContext) -> None:
	if not ctx.command:
		return

	handler = COMMANDS.get(ctx.command)
	if handler is None:
		try:
			metrics_inc("ferum_integration_telegram_command_total", {"command": "unknown", "result": "blocked"})
		except Exception:
			pass
		ctx.reply(_("Unknown command"))
		return

	# Lightweight per-chat/command throttle to reduce spam
	_enforce_command_rate_limit(ctx)

	if ctx.command in ADMIN_COMMANDS:
		if not telegram_integration.is_admin(ctx.user):
			try:
				metrics_inc("ferum_integration_telegram_command_total", {"command": ctx.command, "result": "blocked"})
			except Exception:
				pass
			ctx.reply(_("Not permitted"))
			return
		if not _has_admin_role(ctx):
			try:
				metrics_inc("ferum_integration_telegram_command_total", {"command": ctx.command, "result": "blocked"})
			except Exception:
				pass
			ctx.reply(_("Admin mapping required. Ask admin to link your Telegram to an ERP user with System Manager or Telegram Admin role."))
			return

	handler(ctx)
	try:
		metrics_inc("ferum_integration_telegram_command_total", {"command": ctx.command, "result": "success"})
	except Exception:
		pass


def _verify_secret() -> None:
	"""Verify webhook authenticity via Telegram secret token header only.

	We no longer accept the legacy ?secret=... query parameter to avoid easy leakage.
	"""
	configured = (get_setting("telegram_webhook_secret") or "").strip()
	if not configured:
		frappe.throw(_("Configure telegram_webhook_secret in settings"))

	header_secret = None
	try:
		header_secret = (frappe.request.headers.get("X-Telegram-Bot-Api-Secret-Token") or "").strip()
	except Exception:
		header_secret = None

	if not header_secret or header_secret != configured:
		frappe.throw(_("Invalid secret"))


def _verify_ip_allowlist() -> None:
	"""Optional IP allowlist for Telegram webhook, configured via env TELEGRAM_IP_ALLOWLIST (comma-separated)."""
	allowlist = (frappe.local.conf.get("telegram_ip_allowlist") if hasattr(frappe.local, "conf") else None) or \
		os.environ.get("TELEGRAM_IP_ALLOWLIST", "")
	allowlist = [ip.strip() for ip in allowlist.split(",") if ip.strip()]
	if not allowlist:
		return
	request_ip = getattr(frappe.local, "request_ip", None) or frappe.request.remote_addr
	if request_ip not in allowlist:
		frappe.throw(_("IP not allowed"), frappe.PermissionError)


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=120, seconds=60, methods=["POST"])  # 120 updates/min per IP
def handle_update(secret: str | None = None, update: str | dict[str, Any] | None = None) -> dict[str, Any]:
	"""Process Telegram webhook updates with simple chat commands."""

	_verify_secret()
	_verify_ip_allowlist()
	payload = frappe.parse_json(update) if isinstance(update, str) else (update or {})
	# Idempotency check
	if _already_processed(payload):
		try:
			metrics_inc("ferum_integration_telegram_webhook_total", {"result": "duplicate"})
		except Exception:
			pass
		return {"ok": True, "duplicate": True}
	ctx = _build_context(payload)

	if not is_feature_enabled("enable_telegram_notifications"):
		frappe.logger().warning("Telegram webhook hit while notifications disabled.")
		try:
			metrics_inc("ferum_integration_telegram_webhook_total", {"result": "disabled"})
		except Exception:
			pass
		return {"ok": False, "error": "telegram-disabled"}

	if not telegram_integration.is_chat_allowed(ctx.chat_id):
		frappe.logger().warning("Telegram chat %s not in allowlist", ctx.chat_id)
		try:
			metrics_inc("ferum_integration_telegram_webhook_total", {"result": "not_allowed"})
		except Exception:
			pass
		return {"ok": False, "error": "chat-not-allowed"}

	# Identify mapped ERPNext user by chat_id or username and switch context
	try:
		target_user: str | None = None
		# 1) Prefer explicit mapping via Telegram User Link
		rows = frappe.get_all(
			"Telegram User Link",
			filters={"chat_id": str(ctx.chat_id) if ctx.chat_id else "__none__"},
			fields=["user"],
			limit=1,
		)
		if rows and rows[0].get("user"):
			target_user = rows[0]["user"]
		# 2) Fallback to mapping by Telegram username
		if not target_user and ctx.user:
			rows = frappe.get_all(
				"Telegram User Link",
				filters={"telegram_username": ctx.user},
				fields=["user"],
				limit=1,
			)
			if rows and rows[0].get("user"):
				target_user = rows[0]["user"]
		# 3) Fallback to User custom fields (telegram_chat_id / telegram_username)
		if not target_user and ctx.chat_id:
			u = frappe.get_all("User", filters={"telegram_chat_id": str(ctx.chat_id)}, pluck="name", limit=1)
			if u:
				target_user = u[0]
		if not target_user and ctx.user:
			u = frappe.get_all("User", filters={"telegram_username": ctx.user}, pluck="name", limit=1)
			if u:
				target_user = u[0]

		if target_user and target_user != frappe.session.user:
			frappe.set_user(target_user)
			ctx.erp_user = target_user
	except Exception:
		pass

	if not ctx.text and not ctx.has_photo:
		return {"ok": True}

	try:
		if _handle_photo_payload(ctx):
			try:
				metrics_inc("ferum_integration_telegram_webhook_total", {"result": "success", "type": "photo"})
			except Exception:
				pass
			return {"ok": True}
		_dispatch_command(ctx)
	except CommandError as exc:
		try:
			metrics_inc("ferum_integration_telegram_webhook_total", {"result": "error", "reason": "command"})
		except Exception:
			pass
		ctx.reply(exc.message)
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), "Telegram bot update failed")
		try:
			if get_setting("telegram_alert_admin_on_failure"):
				subject = "Telegram bot update processing failed"
				body = f"Exception: {exc}\n\nPayload: {frappe.safe_encode(frappe.as_json(payload))[:8000]}\n"
				# Reuse email notifier from integration module
				from ferum_custom.ferum_custom.integrations.telegram import (
					_notify_admins_email,  # type: ignore
				)

				_notify_admins_email(subject, body)
		except Exception:
			pass
		ctx.reply(_("Error processing command"))
		try:
			metrics_inc("ferum_integration_telegram_webhook_total", {"result": "error", "reason": "exception"})
		except Exception:
			pass

	# Mark processed on successful path (no raised exceptions)
	_mark_processed(payload)
	try:
		metrics_inc("ferum_integration_telegram_webhook_total", {"result": "success", "type": "text" if ctx.text else "other"})
	except Exception:
		pass
	return {"ok": True}


# ------------------------------
# Webhook utilities (optional, for switching from polling)
# ------------------------------


@frappe.whitelist()
def set_webhook(base_url: str | None = None, secret: str | None = None) -> dict[str, Any]:
	"""Configure Telegram to deliver updates to this site via webhook.

	Requires System Manager permission. Provide base_url (e.g., https://your.site)
	if not configured in settings as site_url. Uses the same secret as handle_update.
	"""
	if not frappe.has_permission(doctype=None, ptype="write", user=frappe.session.user):
		frappe.throw(_("Not permitted"))

	token = get_setting("telegram_bot_token")
	if not token:
		frappe.throw(_("Telegram bot token not configured"))

	site = base_url or (get_setting("site_url") or "").strip()
	if not site:
		frappe.throw(_("Provide base_url or configure site_url in settings"))

	secret = (secret or get_setting("telegram_webhook_secret") or "").strip()
	if not secret:
		frappe.throw(_("Configure telegram_webhook_secret in settings"))

	# Rely solely on header secret_token; no query parameter.
	endpoint = f"{site.rstrip('/')}/api/method/ferum_custom.api.telegram_bot.handle_update"

	try:
		import requests  # type: ignore

		url = f"{telegram_integration.API_BASE}/bot{token}/setWebhook"
		resp = requests.post(
			url,
			json={
				"url": endpoint,
				"secret_token": secret,
				"allowed_updates": ["message", "edited_message"],
				"max_connections": 40,
				# keep certificate defaults (let Telegram fetch via public HTTPS)
			},
			timeout=15,
		)
		data = (
			resp.json()
			if resp.headers.get("content-type", "").startswith("application/json")
			else {"http": resp.text}
		)
		if not resp.ok or not data.get("ok"):
			frappe.throw(_("Failed to set webhook: {0}").format(data))
		return {"ok": True, "result": data.get("result")}
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), "Telegram set_webhook failed")
		frappe.throw(_("Error setting webhook: {0}").format(str(exc)))


@frappe.whitelist()
def delete_webhook() -> dict[str, Any]:
	token = get_setting("telegram_bot_token")
	if not token:
		frappe.throw(_("Telegram bot token not configured"))
	try:
		import requests  # type: ignore

		url = f"{telegram_integration.API_BASE}/bot{token}/deleteWebhook"
		resp = requests.post(url, timeout=15)
		data = (
			resp.json()
			if resp.headers.get("content-type", "").startswith("application/json")
			else {"http": resp.text}
		)
		if not resp.ok or not data.get("ok"):
			frappe.throw(_("Failed to delete webhook: {0}").format(data))
		return {"ok": True, "result": data.get("result")}
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), "Telegram delete_webhook failed")
		frappe.throw(_("Error deleting webhook: {0}").format(str(exc)))


@frappe.whitelist(allow_guest=True)
def health() -> dict[str, Any]:
	return telegram_integration.healthcheck()
