from __future__ import annotations

from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    bot_token: str
    webhook_url: str | None
    webhook_secret: str | None
    mode: str | None
    port: int | None
    frappe_base: str
    frappe_username: str
    frappe_password: str
    bot_totp_secret: str | None
    verify_ssl: bool
    log_level: str
    prometheus_port: int | None
    sentry_dsn: str | None


def load() -> Settings:
    load_dotenv()
    return Settings(
        bot_token=os.getenv("BOT_TOKEN", ""),
        webhook_url=os.getenv("WEBHOOK_URL") or None,
        webhook_secret=os.getenv("WEBHOOK_SECRET") or None,
        mode=os.getenv("MODE") or None,
        port=int(os.getenv("PORT")) if os.getenv("PORT") else None,
        frappe_base=os.getenv("FRAPPE_BASE_URL", "").rstrip("/"),
        frappe_username=os.getenv("FRAPPE_USERNAME", ""),
        frappe_password=os.getenv("FRAPPE_PASSWORD", ""),
        bot_totp_secret=os.getenv("BOT_TOTP_SECRET") or None,
        verify_ssl=(os.getenv("VERIFY_SSL", "true").lower() in ("1", "true", "yes", "on")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        prometheus_port=int(os.getenv("PROMETHEUS_PORT")) if os.getenv("PROMETHEUS_PORT") else None,
        sentry_dsn=os.getenv("SENTRY_DSN") or None,
    )
