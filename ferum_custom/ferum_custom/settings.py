from __future__ import annotations

"""Helpers for accessing :doctype:`Ferum Custom Settings`."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import frappe

SETTINGS_DOCTYPE = "Ferum Custom Settings"
ENV_PREFIX = "FERUM_"

_ENV_FILES = (
	# Local overrides first (highest precedence among files)
	"config/.env.local.integrations",
	# Team-shared defaults next
	"config/.env.integrations",
)

ENV_PRIORITY_FIELDS = {
	"jwt_secret",
	"telegram_bot_token",
	"telegram_webhook_secret",
	"google_service_account_json",
}


def _load_env_files() -> None:
	"""Best-effort load of integration env files into process env.

	- Only sets variables that are not already present in os.environ.
	- Supports simple KEY=VALUE lines with optional quotes and comments.
	- Relative paths are resolved from the Bench root (…/frappe-bench).
	"""
	try:
		here = Path(__file__).resolve()
		# Bench root: apps/…/ferum_custom/ferum_custom/ferum_custom/settings.py -> bench root is parent of 'apps'
		bench_root = here.parents[4]
	except Exception:
		bench_root = Path.cwd()

	def _parse_line(line: str) -> tuple[str, str] | None:
		line = line.strip()
		if not line or line.startswith("#"):
			return None
		if "=" not in line:
			return None
		k, v = line.split("=", 1)
		key = k.strip()
		val = v.strip().strip("'\"")
		if not key:
			return None
		return key, val

	for rel in _ENV_FILES:
		try:
			path = bench_root / rel
			if not path.exists():
				continue
			for raw in path.read_text(encoding="utf-8").splitlines():
				pair = _parse_line(raw)
				if not pair:
					continue
				key, val = pair
				# Only export FERUM_* keys; don't override explicit env
				if key.startswith(ENV_PREFIX) and key not in os.environ:
					os.environ[key] = val
		except Exception:
			# Non-fatal: env files are optional
			pass


# Load env files early so get_setting() sees them
_load_env_files()


def _fetch_settings() -> Any | None:
    """Fetch settings document.

    Primary path uses frappe.get_single which constructs a proper Document.
    Some environments exhibit issues resolving Singles via get_single (e.g.
    legacy schemas or partial migrations). In that case, fall back to reading
    raw rows from `tabSingles` and return a mapping-like object.
    """
    try:
        return frappe.get_single(SETTINGS_DOCTYPE)
    except Exception:
        # Fallback: construct dict from Singles rows via raw SQL (Singles has no DocType)
        try:
            rows = frappe.db.sql(
                """select `field`, `value` from `tabSingles` where `doctype`=%s""",
                (SETTINGS_DOCTYPE,),
                as_dict=True,
            )
            return frappe._dict({r["field"]: r["value"] for r in rows})
        except Exception:
            return None


def get_settings(*, refresh: bool = False) -> Any | None:
	"""Return the live settings document or ``None`` when unavailable."""

	if refresh:
		refresh_settings_cache()
	return _fetch_settings()


@lru_cache(maxsize=1)
def _settings_snapshot() -> dict[str, Any] | None:
    doc = _fetch_settings()
    if not doc:
        return None
    # Support Document, frappe._dict or plain dict
    try:
        data = doc.as_dict()  # type: ignore[attr-defined]
        return dict(data)
    except Exception:
        try:
            # frappe._dict or plain object with __dict__
            if isinstance(doc, dict):
                return dict(doc)
            return {k: v for k, v in doc.__dict__.items() if not k.startswith("_")}
        except Exception:
            return None


def refresh_settings_cache() -> None:
	"""Invalidate the cached settings snapshot used by :func:`get_setting`."""

	try:
		_settings_snapshot.cache_clear()
	except AttributeError:  # pragma: no cover - Python <3.9
		pass


def _value_is_set(value: Any | None) -> bool:
	if value is None:
		return False
	if isinstance(value, str):
		return bool(value.strip())
	if isinstance(value, (tuple, list, set, dict)):
		return bool(value)
	return True


def _get_from_site_config(field: str) -> Any | None:
	try:
		conf = getattr(frappe.local, "conf", None) or getattr(frappe, "conf", None)
		if conf and field in conf:
			return conf.get(field)
	except Exception:
		pass
	return None


def _get_from_env(field: str) -> Any | None:
	env_key = f"{ENV_PREFIX}{field.upper()}"
	return os.getenv(env_key)


def _get_env_priority(field: str) -> Any | None:
	try:
		if field in ENV_PRIORITY_FIELDS:
			value = _get_from_env(field)
			if _value_is_set(value):
				return value
	except Exception:
		pass
	return None


def get_setting(field: str, default: Any | None = None) -> Any | None:
	"""Read a single attribute from settings, falling back to site config/env."""

	env_value = _get_env_priority(field)
	if env_value is not None:
		return env_value

	data = _settings_snapshot()
	if data and _value_is_set(data.get(field)):
		return data.get(field)

	site_conf_value = _get_from_site_config(field)
	if _value_is_set(site_conf_value):
		return site_conf_value

	env_value = _get_from_env(field)
	if _value_is_set(env_value):
		return env_value

	return default


def is_feature_enabled(flag: str) -> bool:
	"""Return ``True`` when the configured feature flag evaluates to truthy."""

	value = get_setting(flag)
	if isinstance(value, bool):
		return value
	if isinstance(value, (int, float)):
		return bool(value)
	if isinstance(value, str):
		return value.strip().lower() in {"1", "true", "yes", "on"}
	return False


def get_list_setting(field: str) -> list[str]:
	"""Return a normalised list of strings for multi-value settings (comma or newline separated)."""

	raw = get_setting(field)
	if raw is None:
		return []
	if isinstance(raw, (list, tuple, set)):
		iterable = raw
	else:
		iterable = str(raw).replace(",", "\n").splitlines()
	return [str(item).strip() for item in iterable if str(item).strip()]
