import mimetypes
import os

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue

# Conditional import for google-api-python-client and google-auth
try:
	from google.oauth2 import service_account
	from googleapiclient.discovery import build

	GOOGLE_DRIVE_INTEGRATION_ENABLED = frappe.conf.get("google_drive_integration_enabled", False)
except ImportError:
	GOOGLE_DRIVE_INTEGRATION_ENABLED = False
	frappe.log_error(
		"Google API Python Client libraries not found. Google Drive integration will be disabled.",
		"Google Drive Integration",
	)


class CustomAttachment(Document):
	def before_insert(self):
		if self.file_url and GOOGLE_DRIVE_INTEGRATION_ENABLED:
			enqueue(upload_to_google_drive, queue="long", doc_name=self.name)

	def on_trash(self):
		if self.google_drive_file_id and GOOGLE_DRIVE_INTEGRATION_ENABLED:
			enqueue(delete_from_google_drive, queue="long", doc_name=self.name)


@frappe.whitelist()
def upload_to_google_drive(doc_name):
	doc = frappe.get_doc("CustomAttachment", doc_name)
	if not doc.file_url:
		return

	service = get_drive_service()
	if not service:
		return

	file_path = frappe.get_site_path("public", doc.file_url.lstrip("/"))
	if "/private/files/" in doc.file_url:
		file_path = frappe.get_site_path("private", doc.file_url.split("/private/files/")[1])

	if not os.path.exists(file_path):
		frappe.log_error(f"File not found on server: {file_path}", "Google Drive Upload Error")
		return

	file_metadata = {
		"name": doc.file_name or os.path.basename(file_path),
		"parents": [frappe.conf.get("google_drive_folder_id")],
	}

	mime_type, _ = mimetypes.guess_type(file_path)
	media = {
		"body": open(file_path, "rb"),
		"mimeType": mime_type or "application/octet-stream",
	}

	try:
		file = (
			service.files().create(body=file_metadata, media_body=media, fields="id, webViewLink").execute()
		)
		doc.google_drive_file_id = file.get("id")
		doc.file_url = file.get("webViewLink")
		doc.save()
		frappe.msgprint(_(f"File {doc.file_name} uploaded to Google Drive."))
	except Exception as e:
		frappe.log_error(
			f"Failed to upload file {doc.file_name} to Google Drive: {e}",
			"Google Drive Integration Error",
		)


@frappe.whitelist()
def delete_from_google_drive(doc_name):
	doc = frappe.get_doc("CustomAttachment", doc_name)
	if not doc.google_drive_file_id:
		return

	service = get_drive_service()
	if not service:
		return

	try:
		service.files().delete(fileId=doc.google_drive_file_id).execute()
		frappe.msgprint(_(f"File {doc.file_name} deleted from Google Drive."))
	except Exception as e:
		frappe.log_error(
			f"Failed to delete file {doc.file_name} from Google Drive: {e}",
			"Google Drive Integration Error",
		)


def get_drive_service():
	if not GOOGLE_DRIVE_INTEGRATION_ENABLED:
		return None

	try:
		key_file_path = frappe.conf.get("google_drive_service_account_key_path")
		if not key_file_path or not os.path.exists(key_file_path):
			frappe.log_error(
				"Google Drive service account key file not found.", "Google Drive Integration Error"
			)
			return None

		credentials = service_account.Credentials.from_service_account_file(
			key_file_path, scopes=["https://www.googleapis.com/auth/drive"]
		)
		return build("drive", "v3", credentials=credentials)
	except Exception as e:
		frappe.log_error(f"Failed to get Google Drive service: {e}", "Google Drive Integration Error")
		return None
