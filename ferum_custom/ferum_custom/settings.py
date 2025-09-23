from __future__ import annotations

"""Helpers for accessing :doctype:`Ferum Custom Settings`."""

from functools import lru_cache
from typing import Any

import frappe

SETTINGS_DOCTYPE = "Ferum Custom Settings"


def _fetch_settings() -> Any | None:
    try:
        return frappe.get_single(SETTINGS_DOCTYPE)
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
    try:
        data = doc.as_dict()
    except AttributeError:
        data = {k: v for k, v in doc.__dict__.items() if not k.startswith("_")}
    return dict(data)


def refresh_settings_cache() -> None:
    """Invalidate the cached settings snapshot used by :func:`get_setting`."""

    try:
        _settings_snapshot.cache_clear()
    except AttributeError:  # pragma: no cover - Python <3.9
        pass


def get_setting(field: str, default: Any | None = None) -> Any | None:
    """Read a single attribute from the cached settings snapshot."""

    data = _settings_snapshot()
    if not data:
        return default
    return data.get(field, default)


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
