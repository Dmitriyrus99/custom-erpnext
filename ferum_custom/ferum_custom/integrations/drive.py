from __future__ import annotations

import frappe

from ferum_custom.ferum_custom.integrations.google import (
	SERVICE_ACCOUNT_SCOPE_DRIVE,
	build_service_account_credentials,
)
from ferum_custom.ferum_custom.settings import get_setting
from ferum_custom.ferum_custom.utils import get_users_by_roles

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
		try:
			recipients = list(get_users_by_roles(["System Manager", "Chief Accountant"]))
			if recipients:
				frappe.sendmail(
					recipients=recipients,
					subject="Drive service init failed",
					message="Google Drive service initialization failed. Check Ferum Custom settings and credentials.",
				)
		except Exception:
			pass
		return None


def _ensure_folder(drive, name: str, parent_id: str | None) -> str | None:
	q = "mimeType='application/vnd.google-apps.folder' and name='" + name.replace("'", "\\'") + "'"
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
		# Ensure folder structure exists
		for part in path_parts:
			parent = _ensure_folder(drive, part, parent)
			if not parent:
				return None

		media = MediaInMemoryUpload(data, mimetype=mime_type, resumable=False)

		# Try update existing file with the same name in the target parent
		existing_id = None
		try:
			q = (
				"name='" + filename.replace("'", "\\'") + "' and "
				"mimeType!='application/vnd.google-apps.folder'"
			)
			if parent:
				q += f" and '{parent}' in parents"
			res = drive.files().list(q=q, fields="files(id,name,modifiedTime)").execute()
			files = res.get("files", [])
			if files:
				existing_id = files[0]["id"]
		except Exception:
			existing_id = None

		if existing_id:
			file = drive.files().update(fileId=existing_id, media_body=media, fields="id").execute()
		else:
			body = {"name": filename}
			if parent:
				body["parents"] = [parent]
			file = drive.files().create(body=body, media_body=media, fields="id").execute()

		return file.get("id")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Drive upload failed")
		try:
			recipients = list(get_users_by_roles(["System Manager", "Chief Accountant"]))
			if recipients:
				frappe.sendmail(
					recipients=recipients,
					subject="Drive upload failed",
					message=f"Failed to upload {filename} to Google Drive.",
				)
		except Exception:
			pass
		return None


def delete_file(file_id: str) -> bool:
	"""Delete a file from Google Drive by id. Returns True on success."""
	drive = _drive_service()
	if not drive:
		return False
	try:
		drive.files().delete(fileId=file_id).execute()
		return True
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Drive delete failed")
		try:
			recipients = list(get_users_by_roles(["System Manager", "Chief Accountant"]))
			if recipients:
				frappe.sendmail(
					recipients=recipients,
					subject="Drive delete failed",
					message=f"Failed to delete Drive file: {file_id}",
				)
		except Exception:
			pass
		return False
