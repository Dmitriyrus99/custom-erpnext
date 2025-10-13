from __future__ import annotations

import time
from typing import Any, Set

import frappe

from ferum_custom.ferum_custom.settings import (
	get_list_setting,
	get_setting,
	is_feature_enabled,
)

try:
	import requests  # type: ignore[import-untyped]
except Exception:  # pragma: no cover
	requests = None  # type: ignore[assignment]

API_BASE = "https://api.telegram.org"


def _normalise(value: str | int | None) -> str | None:
	if value is None:
		return None
	text = str(value).strip()
	return text or None


def _allowed_chats() -> Set[str]:
    chats = {chat for chat in get_list_setting("telegram_allowed_chat_ids") if chat}
    default_chat = _normalise(get_setting("telegram_default_chat_id"))
    if default_chat:
        chats.add(default_chat)
    # Also include mapped chat IDs from Telegram User Link
    try:
        mapped = frappe.get_all("Telegram User Link", pluck="chat_id")
        chats.update({_normalise(x) for x in mapped if _normalise(x)})
    except Exception:
        pass
    # Include chat IDs from User custom fields if present
    try:
        user_chats = frappe.get_all("User", filters={"enabled": 1}, pluck="telegram_chat_id")
        chats.update({_normalise(x) for x in user_chats if _normalise(x)})
    except Exception:
        pass
    return {chat for chat in chats if chat}


def _admin_usernames() -> Set[str]:
    names = {username.lower() for username in get_list_setting("telegram_admin_usernames")}
    # Users flagged as admin in mapping are also treated as Telegram admins
    try:
        rows = frappe.get_all(
            "Telegram User Link",
            filters={"is_admin": 1},
            fields=["telegram_username"],
        )
        for r in rows:
            if r.get("telegram_username"):
                names.add(str(r["telegram_username"]).lower())
    except Exception:
        pass
    return names


def is_chat_allowed(chat_id: str | None) -> bool:
    allowed = _allowed_chats()
    if not allowed:
        return True
    normalised = _normalise(chat_id)
    return bool(normalised and normalised in allowed)


def is_admin(username: str | None) -> bool:
	if not username:
		return False
	admins = _admin_usernames()
	if not admins:
		return False
	return username.lower() in admins


def send_message(text: str, chat_id: str | None = None, max_retries: int = 3) -> bool:
	"""Send Telegram message using Bot API with simple retry and fallback logging."""

	if not is_feature_enabled("enable_telegram_notifications"):
		return False

	token = get_setting("telegram_bot_token")
	chat = _normalise(chat_id or get_setting("telegram_default_chat_id"))

	if not token or not chat or requests is None:
		try:
			frappe.logger().warning("Telegram not configured or requests missing. Message suppressed.")
		except Exception:
			pass
		return False

	if not is_chat_allowed(chat):
		frappe.logger().warning("Telegram chat %s is not in the allowlist; message suppressed.", chat)
		return False

    url = f"{API_BASE}/bot{token}/sendMessage"
    payload = {"chat_id": chat, "text": text}

	delay = 1.0
	for attempt in range(1, max_retries + 1):
		try:
			response = requests.post(url, json=payload, timeout=10)
			if response.ok:
				data = response.json()
				if data.get("ok"):
					return True
				frappe.logger().warning(
					"Telegram send failed (attempt %s): %s",
					attempt,
					data,
				)
			else:
				frappe.logger().warning(
					"Telegram send HTTP failure (attempt %s): %s",
					attempt,
					response.text,
				)
		except Exception as exc:  # pragma: no cover
			try:
				frappe.logger().exception(f"Telegram send exception (attempt {attempt}): {exc}")
			except Exception:
				pass
		time.sleep(delay)
		delay = min(delay * 2, 8.0)
    return False


def send_to_roles(text: str, roles: list[str]) -> int:
    """Send a message to all mapped users holding any of the given roles.

    Returns number of successful deliveries. Respects allowlist and feature flag.
    """
    if not is_feature_enabled("enable_telegram_notifications"):
        return 0
    try:
        # Find users with roles then resolve their mapped chat_ids
        users = set()
        for role in roles:
            rows = frappe.get_all("Has Role", filters={"role": role}, pluck="parent")
            users.update(rows)
        if not users:
            return 0
        mappings = frappe.get_all(
            "Telegram User Link",
            filters={"user": ["in", list(users)]},
            fields=["chat_id"],
        )
        count = 0
        for m in mappings:
            chat = _normalise(m.get("chat_id"))
            if not chat or not is_chat_allowed(chat):
                continue
            if send_message(text, chat_id=chat):
                count += 1
        return count
    except Exception:
        try:
            frappe.logger().exception("send_to_roles failed")
        except Exception:
            pass
        return 0


def healthcheck() -> dict[str, Any]:
	"""Perform a lightweight connectivity check against the Telegram Bot API."""

	if not is_feature_enabled("enable_telegram_notifications"):
		return {"status": "disabled", "message": "Telegram notifications feature flag disabled"}

	if requests is None:
		return {"status": "error", "message": "requests package is not available"}

	token = get_setting("telegram_bot_token")
	if not token:
		return {"status": "error", "message": "Telegram bot token is not configured"}

	try:
		response = requests.get(f"{API_BASE}/bot{token}/getMe", timeout=10)
		if not response.ok:
			return {"status": "error", "message": f"HTTP {response.status_code}", "details": {"response": response.text}}
		data = response.json()
		if not data.get("ok"):
			return {"status": "error", "message": "Bot API returned error", "details": data}
		result = data.get("result") or {}
		return {
			"status": "ok",
			"details": {
				"username": result.get("username"),
				"bot_id": result.get("id"),
				"can_join_groups": result.get("can_join_groups"),
				"allowlist": sorted(_allowed_chats()),
			},
		}
	except Exception as exc:  # pragma: no cover - network errors
		return {"status": "error", "message": str(exc)}
