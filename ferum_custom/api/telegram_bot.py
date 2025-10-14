"""Telegram bot webhook endpoint for Ferum Custom.

This module keeps the public surface (`handle_update`) identical while
splitting the previous monolithic implementation into smaller helpers.
The refactor improves readability, makes individual commands easier to
extend and provides light-weight abstractions for replying back to
Telegram chats.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import frappe
from frappe import _

from ferum_custom.ferum_custom.integrations import telegram as telegram_integration
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
		telegram_integration.send_message(text, chat_id=str(chat_id))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Telegram reply failed")


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


def _ensure_argument(ctx: TelegramContext, usage: str) -> str:
	if ctx.argument:
		return ctx.argument
	raise CommandError(_("Usage: {0}").format(usage))


def _cmd_new_request(ctx: TelegramContext) -> None:
	title = ctx.argument or _("New Request")
	name = frappe.call("ferum_custom.api.service.create_service_request", title=title)
	ctx.reply(_("Request created: {0}").format(name))


def _cmd_my_requests(ctx: TelegramContext) -> None:
	res = frappe.call(
		"ferum_custom.api.service.list_service_requests",
		start=0,
		page_length=10,
	)
	lines = [f"{x['name']} - {x['title']} - {x['status']}" for x in res.get("data", [])]
	ctx.reply("\n".join(lines) or _("No requests"))


def _cmd_start_work(ctx: TelegramContext) -> None:
	req = _ensure_argument(ctx, "/start_work <request_name>")
	doc = frappe.get_doc("Service Request", req)
	doc.status = "In Progress"
	doc.save(ignore_permissions=True)
	ctx.reply(_("Marked as In Progress: {0}").format(req))


def _cmd_done(ctx: TelegramContext) -> None:
	req = _ensure_argument(ctx, "/done <request_name>")
	doc = frappe.get_doc("Service Request", req)
	if not getattr(doc, "linked_report", None):
		raise CommandError(_("Please attach a Service Report before completing."))
	doc.status = "Completed"
	doc.save(ignore_permissions=True)
	ctx.reply(_("Marked as Completed: {0}").format(req))


def _cmd_close(ctx: TelegramContext) -> None:
	if "System Manager" not in frappe.get_roles():
		raise CommandError(_("Not permitted"))
	req = _ensure_argument(ctx, "/close <request_name>")
	doc = frappe.get_doc("Service Request", req)
	doc.status = "Closed"
	doc.save(ignore_permissions=True)
	ctx.reply(_("Closed: {0}").format(req))


def _cmd_analytics(ctx: TelegramContext) -> None:
	open_count = frappe.db.count(
		"Service Request",
		{"status": ["not in", ["Completed", "Closed"]]},
	)
	paid = frappe.db.count("Invoice", {"status": "Paid"})
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
	"/new_request": _cmd_new_request,
	"/my_requests": _cmd_my_requests,
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


def _attach_photo(ctx: TelegramContext, request_name: str) -> None:
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

	try:
		file_doc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": file_name,
				"content": content,
				"is_private": 0,
				"attached_to_doctype": "Service Request",
				"attached_to_name": request_name,
			}
		)
		file_doc.insert(ignore_permissions=True)

		# Register as Custom Attachment for unified handling and Drive sync
		try:
			att = frappe.get_doc(
				{
					"doctype": "Custom Attachment",
					"file_name": file_name,
					"file_url": file_doc.file_url,
					"linked_doctype": "Service Request",
					"linked_docname": request_name,
					"file_type": "image",
				}
			)
			att.insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Create CustomAttachment from Telegram failed")

		# Keep existing photo table for backward compatibility in UI
		request_doc = frappe.get_doc("Service Request", request_name)
		request_doc.append("photos", {"photo": file_doc.file_url, "description": "bot"})
		# Also reflect in generic attachments table
		try:
			request_doc.append("attachments", {"attachment": file_doc.file_url, "description": "bot"})
		except Exception:
			pass
		request_doc.save(ignore_permissions=True)
	except CommandError:
		raise
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), "Telegram photo attach failed")
		raise CommandError(_("Failed to attach photo")) from exc

	ctx.reply(_("Photo attached to {0}").format(request_name))


def _handle_photo_payload(ctx: TelegramContext) -> bool:
	if not ctx.has_photo:
		return False

	caption = ctx.caption
	if not caption.startswith("/attach") or " " not in caption:
		return False

	request_name = caption.split(" ", 1)[1].strip()
	if not request_name:
		raise CommandError(_("Usage: /attach <request_name>"))

	_attach_photo(ctx, request_name)
	return True


def _dispatch_command(ctx: TelegramContext) -> None:
	if not ctx.command:
		return

	handler = COMMANDS.get(ctx.command)
	if handler is None:
		ctx.reply(_("Unknown command"))
		return

	if ctx.command in ADMIN_COMMANDS and not telegram_integration.is_admin(ctx.user):
		ctx.reply(_("Not permitted"))
		return

	handler(ctx)


def _verify_secret(query_secret: str | None) -> None:
	"""Verify webhook authenticity via Telegram secret token.

	Prefers the official header "X-Telegram-Bot-Api-Secret-Token" if present
	(set via setWebhook secret_token). Falls back to the "secret" query param
	for backward compatibility.
	"""
	configured = (get_setting("telegram_webhook_secret") or "").strip()
	# Read header if available (recommended)
	header_secret = None
	try:
		header_secret = (frappe.request.headers.get("X-Telegram-Bot-Api-Secret-Token") or "").strip()
	except Exception:
		header_secret = None

	candidate = (header_secret or (query_secret or "")).strip()
	if not configured or candidate != configured:
		frappe.throw(_("Invalid secret"))


@frappe.whitelist(allow_guest=True)
def handle_update(secret: str | None = None, update: str | dict[str, Any] | None = None) -> dict[str, Any]:
	"""Process Telegram webhook updates with simple chat commands."""

	_verify_secret(secret)
	payload = frappe.parse_json(update) if isinstance(update, str) else (update or {})
	ctx = _build_context(payload)

	if not is_feature_enabled("enable_telegram_notifications"):
		frappe.logger().warning("Telegram webhook hit while notifications disabled.")
		return {"ok": False, "error": "telegram-disabled"}

	if not telegram_integration.is_chat_allowed(ctx.chat_id):
		frappe.logger().warning("Telegram chat %s not in allowlist", ctx.chat_id)
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
	except Exception:
		pass

	if not ctx.text and not ctx.has_photo:
		return {"ok": True}

	try:
		if _handle_photo_payload(ctx):
			return {"ok": True}
		_dispatch_command(ctx)
	except CommandError as exc:
		ctx.reply(exc.message)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Telegram bot update failed")
		ctx.reply(_("Error processing command"))

	return {"ok": True}
