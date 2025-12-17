from __future__ import annotations  # moved into package 'telegram_bot'

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    bot_token: str
    webhook_url: str | None
    webhook_secret: str | None
    mode: str | None
    port: int | None
    frappe_base: str
    frappe_api_key: str | None
    frappe_api_secret: str | None
    frappe_username: str
    frappe_password: str
    bot_totp_secret: str | None
    verify_ssl: bool
    log_level: str
    prometheus_port: int | None
    sentry_dsn: str | None


def load() -> Settings:
    # Best-effort: load shared bench env files first, then fallback to local .env
    _load_integrations_env()
    load_dotenv()
    return Settings(
        bot_token=_get_env(
            "BOT_TOKEN",
            ["FERUM_TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT_TOKEN"],
            default="",
        ),
        webhook_url=_get_env("WEBHOOK_URL", ["FERUM_TELEGRAM_WEBHOOK_URL"]),
        webhook_secret=_get_env("WEBHOOK_SECRET", ["FERUM_TELEGRAM_WEBHOOK_SECRET"]),
        mode=_get_env("MODE", ["FERUM_BOT_MODE"]),
        port=int(_get_env("PORT", ["FERUM_BOT_PORT"]) or 0) or None,
        frappe_base=_get_env("FRAPPE_BASE_URL", ["FERUM_FRAPPE_BASE_URL"], default="").rstrip("/"),
        frappe_api_key=_get_env("FRAPPE_API_KEY", ["FERUM_FRAPPE_API_KEY"]),
        frappe_api_secret=_get_env("FRAPPE_API_SECRET", ["FERUM_FRAPPE_API_SECRET"]),
        frappe_username=_get_env("FRAPPE_USERNAME", ["FERUM_FRAPPE_USERNAME"], default=""),
        frappe_password=_get_env("FRAPPE_PASSWORD", ["FERUM_FRAPPE_PASSWORD"], default=""),
        bot_totp_secret=_get_env("BOT_TOTP_SECRET", ["FERUM_BOT_TOTP_SECRET"]),
        verify_ssl=(
            (_get_env("VERIFY_SSL", ["FERUM_VERIFY_SSL"], default="true").lower())
            in ("1", "true", "yes", "on")
        ),
        log_level=_get_env("LOG_LEVEL", ["FERUM_LOG_LEVEL"], default="INFO"),
        prometheus_port=int(_get_env("PROMETHEUS_PORT", ["FERUM_PROMETHEUS_PORT"]) or 0) or None,
        sentry_dsn=_get_env("SENTRY_DSN", ["FERUM_SENTRY_DSN"]),
    )


def _get_env(
    primary: str, fallbacks: list[str] | None = None, default: str | None = None
) -> str | None:
    """Read env var by primary name, then from fallback names, else default.

    Returns None if nothing is set and default is None.
    """
    val = os.getenv(primary)
    if val is not None and str(val) != "":
        return val
    if fallbacks:
        for k in fallbacks:
            v = os.getenv(k)
            if v is not None and str(v) != "":
                return v
    return default


def _load_integrations_env() -> None:
    """Load bench-level integration env files into process env (non-overriding).

    Files (if exist, in order):
    - config/.env.local.integrations
    - config/.env.integrations

    This allows centralising bot/server secrets in one place.
    """
    try:
        here = Path(__file__).resolve()
        # Find bench root (directory that contains 'sites' and 'apps')
        bench_root = None
        for parent in [here.parents[i] for i in range(min(7, len(here.parents)))]:
            if (parent / "sites").exists() and (parent / "apps").exists():
                bench_root = parent
                break
        if bench_root is None:
            bench_root = here.parents[5] if len(here.parents) > 5 else Path.cwd()

        def _parse_line(line: str) -> tuple[str, str] | None:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                return None
            k, v = line.split("=", 1)
            key = k.strip()
            val = v.strip().strip('"').strip("'")
            if not key:
                return None
            return key, val

        for rel in ("config/.env.local.integrations", "config/.env.integrations"):
            path = bench_root / rel
            if not path.exists():
                continue
            try:
                for raw in path.read_text(encoding="utf-8").splitlines():
                    pair = _parse_line(raw)
                    if not pair:
                        continue
                    key, val = pair
                    # Don't override explicitly provided env
                    if key not in os.environ:
                        os.environ[key] = val
            except Exception:
                # Non-fatal: if file unreadable, ignore
                pass
    except Exception:
        # Best-effort only
        pass
