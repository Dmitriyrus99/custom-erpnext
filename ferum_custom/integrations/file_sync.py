from __future__ import annotations

"""Unified file synchronization helpers to Google Drive.

This module consolidates upload flows for ERP `File` and `Custom Attachment`
documents and is intended to be the single place handling folder mapping,
upload, and post-write bookkeeping (drive_file_id/web_link).

It reuses `integrations.drive.upload_bytes` for the actual API call and keeps
logic idempotent wherever possible.
"""

from collections.abc import Iterable

import frappe

from ferum_custom.ferum_custom.integrations.drive import upload_bytes
from ferum_custom.ferum_custom.settings import get_setting, is_feature_enabled


def _read_file_content(file_name: str) -> tuple[bytes | None, str | None]:
	try:
		file_doc = frappe.get_doc("File", file_name)
		content = file_doc.get_content()
		name = file_doc.file_name
		if isinstance(content, bytes):
			return content, name
		if isinstance(content, str):
			return content.encode("utf-8"), name
	except Exception:
		pass
	return None, None


def _path_for_file_doc(file_doc) -> list[str]:
	# Current plan leans towards a single store for simplicity.
	return [getattr(file_doc, "attached_to_doctype", None) or "Files"]
