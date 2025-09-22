import time
from typing import Optional

import frappe

try:
    import requests  # type: ignore[import-untyped]
except Exception:  # pragma: no cover
    requests = None  # type: ignore[assignment]


def get_settings():
    try:
        return frappe.get_single("Ferum Custom Settings")
    except Exception:
        return None


def send_message(text: str, chat_id: Optional[str] = None, max_retries: int = 3) -> bool:
    """Send Telegram message using Bot API with simple retry and fallback logging.

    Reads token/default chat from Ferum Custom Settings. Returns True on success.
    """
    settings = get_settings()
    token = getattr(settings, "telegram_bot_token", None) if settings else None
    chat = chat_id or (getattr(settings, "telegram_default_chat_id", None) if settings else None)

    if not token or not chat or requests is None:
        # Fallback: log and return False; callers may try email fallback
        try:
            frappe.logger().warning("Telegram not configured or requests missing. Message suppressed.")
        except Exception:
            pass
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat, "text": text}

    delay = 1.0
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.post(url, json=payload, timeout=10)
            if r.ok and r.json().get("ok"):
                return True
            frappe.logger().warning(f"Telegram send failed (attempt {attempt}): {r.text}")
        except Exception as e:  # pragma: no cover
            try:
                frappe.logger().exception(f"Telegram send exception (attempt {attempt}): {e}")
            except Exception:
                pass
        time.sleep(delay)
        delay = min(delay * 2, 8)
    return False

