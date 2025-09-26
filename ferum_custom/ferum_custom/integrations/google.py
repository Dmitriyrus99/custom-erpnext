from __future__ import annotations

"""Shared helpers for Google integrations (Drive, Sheets, ...)."""

import json
from collections.abc import Iterable
from functools import lru_cache
from typing import Any

import frappe

from ferum_custom.ferum_custom.settings import get_setting

try:
	from google.oauth2.service_account import Credentials  # type: ignore[import-untyped]
except Exception:  # pragma: no cover - optional dependency
	Credentials = None  # type: ignore[assignment]


SERVICE_ACCOUNT_SCOPE_DRIVE = "https://www.googleapis.com/auth/drive"
SERVICE_ACCOUNT_SCOPE_SHEETS = "https://www.googleapis.com/auth/spreadsheets"


@lru_cache(maxsize=1)
def _service_account_info() -> dict[str, Any] | None:
	file_url = get_setting("google_service_account_json")
	if not file_url:
		return None
	try:
		file_doc = frappe.get_doc("File", {"file_url": file_url})
		content = file_doc.get_content()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Google service account file load failed")
		return None

	try:
		payload = content.decode("utf-8") if isinstance(content, bytes) else content
		return json.loads(payload)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Google service account JSON invalid")
		return None


def refresh_service_account_cache() -> None:
	try:
		_service_account_info.cache_clear()
	except AttributeError:  # pragma: no cover - Python <3.9
		pass


def build_service_account_credentials(scopes: Iterable[str]) -> Any | None:
	"""Return :class:`~google.oauth2.service_account.Credentials` for the given scopes."""

	if Credentials is None:
		return None
	info = _service_account_info()
	if not info:
		return None
	try:
		return Credentials.from_service_account_info(info, scopes=list(scopes))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Google credential construction failed")
		return None
