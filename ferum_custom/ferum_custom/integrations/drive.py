from __future__ import annotations

from typing import Optional

import frappe

try:
	from google.oauth2.service_account import Credentials  # type: ignore[import-untyped]
	from googleapiclient.discovery import build  # type: ignore[import-untyped]
	from googleapiclient.http import MediaInMemoryUpload  # type: ignore[import-untyped]
except Exception:  # pragma: no cover
	Credentials = None  # type: ignore[assignment]
	build = None  # type: ignore[assignment]
	MediaInMemoryUpload = None  # type: ignore[assignment]


def _get_settings():
	try:
		return frappe.get_single("Ferum Custom Settings")
	except Exception:
		return None


def _drive_service():
	settings = _get_settings()
	if not settings or Credentials is None or build is None:
		return None
	try:
		file_url = settings.google_service_account_json
		if not file_url:
			return None
		file_doc = frappe.get_doc("File", {"file_url": file_url})
		content = file_doc.get_content()
		info = frappe.parse_json(content.decode("utf-8"))
		scopes = ["https://www.googleapis.com/auth/drive"]
		creds = Credentials.from_service_account_info(info, scopes=scopes)
		return build("drive", "v3", credentials=creds)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Drive service init failed")
		return None


def _ensure_folder(drive, name: str, parent_id: str | None) -> str | None:
	escaped_name = name.replace("'", "\'")
	q = f"mimeType='application/vnd.google-apps.folder' and name='{escaped_name}'"
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

	settings = _get_settings()
	parent = getattr(settings, "google_drive_root_folder_id", None)
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
