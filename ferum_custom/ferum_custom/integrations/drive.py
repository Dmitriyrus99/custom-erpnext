from __future__ import annotations

import frappe

from ferum_custom.ferum_custom.integrations.google import (
	SERVICE_ACCOUNT_SCOPE_DRIVE,
	build_service_account_credentials,
)
from ferum_custom.ferum_custom.settings import get_setting

try:
	from googleapiclient.discovery import build  # type: ignore[import-untyped]
	from googleapiclient.http import MediaInMemoryUpload  # type: ignore[import-untyped]
except Exception:  # pragma: no cover
	build = None  # type: ignore[assignment]
	MediaInMemoryUpload = None  # type: ignore[assignment]


def _drive_service():
	if build is None:
		return None
	try:
		creds = build_service_account_credentials([SERVICE_ACCOUNT_SCOPE_DRIVE])
		if not creds:
			return None
		return build("drive", "v3", credentials=creds)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Drive service init failed")
		return None


def _ensure_folder(drive, name: str, parent_id: str | None) -> str | None:
	q = f"mimeType='application/vnd.google-apps.folder' and name='{name.replace("'", "\\'")}'"
	if parent_id:
		q += f" and '{parent_id}' in parents"
	try:
		res = drive.files().list(q=q, fields="files(id,name)").execute()
		files = res.get("files", [])
		if files:
			return files[0]["id"]
		body = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
		if parent_id:
			body["parents"] = [parent_id]
		file = drive.files().create(body=body, fields="id").execute()
		return file.get("id")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Drive ensure folder failed")
		return None


def upload_bytes(
	path_parts: list[str], filename: str, data: bytes, mime_type: str = "application/pdf"
) -> str | None:
	"""Upload bytes to Drive under the given hierarchical path.

	Returns file id on success.
	"""
	drive = _drive_service()
	if not drive or MediaInMemoryUpload is None:
		return None

	parent = get_setting("google_drive_root_folder_id")
	try:
		for part in path_parts:
			parent = _ensure_folder(drive, part, parent)
			if not parent:
				return None

		media = MediaInMemoryUpload(data, mimetype=mime_type, resumable=False)
		body = {"name": filename}
		if parent:
			body["parents"] = [parent]
		file = drive.files().create(body=body, media_body=media, fields="id").execute()
		return file.get("id")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Drive upload failed")
		return None
