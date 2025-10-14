from __future__ import annotations

import time
from typing import Any

import frappe

from ferum_custom.ferum_custom.integrations.google import (
	SERVICE_ACCOUNT_SCOPE_DRIVE,
	build_service_account_credentials,
)
from ferum_custom.ferum_custom.metrics import inc as metrics_inc
from ferum_custom.ferum_custom.settings import get_setting, is_feature_enabled
from ferum_custom.ferum_custom.utils import get_users_by_roles

try:
	from googleapiclient.discovery import build  # type: ignore[import-untyped]
	from googleapiclient.errors import HttpError  # type: ignore[import-untyped]
	from googleapiclient.http import MediaInMemoryUpload  # type: ignore[import-untyped]
except Exception:  # pragma: no cover
	build = None  # type: ignore[assignment]
	MediaInMemoryUpload = None  # type: ignore[assignment]
	HttpError = None  # type: ignore[assignment]

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
FATAL_STATUS_CODES = {401, 403, 404}


def _notify_admins(subject: str, message: str) -> None:
	try:
		recipients = list(get_users_by_roles(["System Manager", "Chief Accountant"]))
		if recipients:
			frappe.sendmail(recipients=recipients, subject=subject, message=message)
	except Exception:
		pass


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
		_notify_admins(
			"Drive service init failed",
			"Google Drive service initialization failed. Check Ferum Custom settings and credentials.",
		)
		return None


def _http_status(exc: Exception) -> int | None:
	if HttpError and isinstance(exc, HttpError):
		resp = getattr(exc, "resp", None)
		if resp:
			return getattr(resp, "status", None)
	return None


def _classify_failure(exc: Exception) -> tuple[str, str]:
	status = _http_status(exc)
	if status in RETRYABLE_STATUS_CODES:
		return "retry", f"HTTP {status}"
	if status in FATAL_STATUS_CODES:
		return "fatal", f"HTTP {status}"
	return "unknown", str(exc)


def _ensure_folder(drive, name: str, parent_id: str | None) -> str | None:
	query = "mimeType='application/vnd.google-apps.folder' and name='" + name.replace("'", "\\'") + "'"
	if parent_id:
		query += f" and '{parent_id}' in parents"
	try:
		res = drive.files().list(q=query, fields="files(id,name)").execute()
		files = res.get("files", [])
		if files:
			return files[0]["id"]
		body = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
		if parent_id:
			body["parents"] = [parent_id]
		file = drive.files().create(body=body, fields="id").execute()
		return file.get("id")
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Drive ensure folder failed: {name}")
		return None


def upload_bytes(
	path_parts: list[str], filename: str, data: bytes, mime_type: str = "application/pdf"
) -> str | None:
	"""Upload bytes to Drive under the given hierarchical path.

	Returns file id on success.
	"""

	if not is_feature_enabled("enable_google_drive_sync"):
		return None
	if MediaInMemoryUpload is None:
		frappe.log_error("google-api-python-client missing", "Drive upload skipped")
		return None

	service = _drive_service()
	if not service:
		return None

	root_folder = get_setting("google_drive_root_folder_id")
	if not root_folder:
		frappe.log_error("Google Drive root folder ID not configured.", "Drive upload skipped")
		return None

	try:
		media = MediaInMemoryUpload(data, mimetype=mime_type, resumable=False)
	except Exception as exc:  # pragma: no cover - dependency-specific
		frappe.log_error(frappe.get_traceback(), "Drive upload init failed")
		_notify_admins("Drive upload failed", f"Failed to initialise upload for {filename}: {exc}")
		return None

	max_attempts = 3
	delay = 2.0
	last_error: Exception | None = None

	for attempt in range(1, max_attempts + 1):
		try:
			current_parent = root_folder
			for part in (p for p in path_parts if p):
				current_parent = _ensure_folder(service, part, current_parent)
				if not current_parent:
					raise RuntimeError(f"Failed to ensure folder {part}")

			existing_id = None
			try:
				query = (
					"name='" + filename.replace("'", "\\'") + "' and "
					"mimeType!='application/vnd.google-apps.folder'"
				)
				if current_parent:
					query += f" and '{current_parent}' in parents"
				res = service.files().list(q=query, fields="files(id,name,modifiedTime)").execute()
				files = res.get("files", [])
				if files:
					existing_id = files[0]["id"]
			except Exception:
				existing_id = None

			if existing_id:
				file = service.files().update(fileId=existing_id, media_body=media, fields="id").execute()
			else:
				body = {"name": filename}
				if current_parent:
					body["parents"] = [current_parent]
				file = service.files().create(body=body, media_body=media, fields="id").execute()

			file_id = file.get("id")
			try:
				metrics_inc("ferum_integration_drive_upload_total", {"result": "success"})
			except Exception:
				pass
			return file_id
		except Exception as exc:
			last_error = exc
			category, context = _classify_failure(exc)
			frappe.log_error(frappe.get_traceback(), f"Drive upload attempt {attempt} failed: {context}")

			if category != "retry" or attempt == max_attempts:
				break

			time.sleep(delay)
			delay = min(delay * 2, 10.0)

	if last_error:
		_notify_admins(
			"Drive upload failed",
			f"Failed to upload {filename} to Google Drive. Error: {_classify_failure(last_error)[1]}",
		)
		try:
			category, _ = _classify_failure(last_error)
			metrics_inc("ferum_integration_drive_upload_total", {"result": "error", "category": category})
		except Exception:
			pass
	return None


def delete_file(file_id: str) -> bool:
	"""Delete a file from Google Drive by id. Returns True on success."""

	if not is_feature_enabled("enable_google_drive_sync"):
		return False

	service = _drive_service()
	if not service:
		return False

	try:
		service.files().delete(fileId=file_id).execute()
		try:
			metrics_inc("ferum_integration_drive_delete_total", {"result": "success"})
		except Exception:
			pass
		return True
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), "Drive delete failed")
		category, context = _classify_failure(exc)
		if category != "fatal":
			_notify_admins(
				"Drive delete failed",
				f"Failed to delete Drive file {file_id}: {context}",
			)
		try:
			metrics_inc("ferum_integration_drive_delete_total", {"result": "error", "category": category})
		except Exception:
			pass
		return False


def healthcheck() -> dict[str, Any]:
	"""Return basic health information for the Drive integration."""

	if not is_feature_enabled("enable_google_drive_sync"):
		return {"status": "disabled", "message": "Drive sync feature flag disabled"}

	if build is None or MediaInMemoryUpload is None:
		return {"status": "error", "message": "google-api-python-client is not installed"}

	root = get_setting("google_drive_root_folder_id")
	if not root:
		return {"status": "error", "message": "Drive root folder ID is not configured"}

	service = _drive_service()
	if not service:
		return {"status": "error", "message": "Failed to initialise Drive client"}

	try:
		meta = (
			service.files()
			.get(fileId=root, fields="id,name,trashed,webViewLink,owners(displayName)")
			.execute()
		)
		owner = (meta.get("owners") or [{}])[0].get("displayName")
		return {
			"status": "ok",
			"details": {
				"id": meta.get("id"),
				"name": meta.get("name"),
				"trashed": meta.get("trashed"),
				"owner": owner,
				"link": meta.get("webViewLink"),
			},
		}
	except Exception as exc:
		category, context = _classify_failure(exc)
		return {
			"status": "error",
			"message": f"Unable to access root folder ({context})",
			"category": category,
		}
