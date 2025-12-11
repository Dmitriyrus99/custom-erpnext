from __future__ import annotations

"""Shared helpers for Google integrations (Drive, Sheets, ...)."""

import json
import os
from collections.abc import Iterable
from functools import lru_cache
from typing import Any

import frappe

from ferum_custom.ferum_custom.settings import get_setting

try:
	from google.oauth2.service_account import Credentials  # type: ignore[import-untyped]
except Exception:  # pragma: no cover - optional dependency
	Credentials = None  # type: ignore[assignment]


# Principle of least privilege: prefer drive.file scope
SERVICE_ACCOUNT_SCOPE_DRIVE = "https://www.googleapis.com/auth/drive.file"
SERVICE_ACCOUNT_SCOPE_SHEETS = "https://www.googleapis.com/auth/spreadsheets"


@lru_cache(maxsize=1)
def _service_account_info() -> dict[str, Any] | None:
	env_b64 = os.environ.get("FERUM_GOOGLE_SERVICE_ACCOUNT_JSON_B64")
	if env_b64:
		try:
			import base64

			decoded = base64.b64decode(env_b64).decode("utf-8")
			return json.loads(decoded)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Google service account env decode failed")
			return None

	file_url = get_setting("google_service_account_json")
	if not file_url:
		return None
	try:
		file_doc = frappe.get_doc("File", {"file_url": file_url})
		if file_doc and int(getattr(file_doc, "is_private", 0)) != 1:
			file_doc.db_set("is_private", 1, commit=True)
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
