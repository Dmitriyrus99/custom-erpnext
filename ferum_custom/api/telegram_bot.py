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

from ferum_custom.ferum_custom.settings import get_setting

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
	from ferum_custom.ferum_custom.integrations.telegram import send_message

	try:
		send_message(text, chat_id=str(chat_id))
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


CommandHandler = Callable[[TelegramContext], None]


COMMANDS: dict[str, CommandHandler] = {
	"/new_request": _cmd_new_request,
	"/my_requests": _cmd_my_requests,
	"/start_work": _cmd_start_work,
	"/done": _cmd_done,
	"/close": _cmd_close,
	"/analytics": _cmd_analytics,
}


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

		request_doc = frappe.get_doc("Service Request", request_name)
		request_doc.append("photos", {"photo": file_doc.file_url, "description": "bot"})
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

	handler(ctx)


def _verify_secret(secret: str) -> None:
	configured = get_setting("telegram_webhook_secret") or ""
	if secret != configured:
		frappe.throw(_("Invalid secret"))


@frappe.whitelist(allow_guest=True)
def handle_update(secret: str, update: str | dict[str, Any]) -> dict[str, Any]:
	"""Process Telegram webhook updates with simple chat commands."""

	_verify_secret(secret)
	payload = frappe.parse_json(update) if isinstance(update, str) else update
	ctx = _build_context(payload)

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
