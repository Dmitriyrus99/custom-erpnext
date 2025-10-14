import frappe
from frappe.model.document import Document

from ferum_custom.ferum_custom.integrations.drive import delete_file, upload_bytes
from ferum_custom.ferum_custom.integrations.file_sync import (
	enqueue_custom_attachment_sync,
	sync_custom_attachment_by_name,
)
from ferum_custom.ferum_custom.settings import is_feature_enabled


class CustomAttachment(Document):
	def after_insert(self):
		self.enqueue_drive_upload()

	def on_update(self):
		# Upload if drive id missing and we have a local File URL
		if not getattr(self, "drive_file_id", None):
			self.enqueue_drive_upload()

	def on_trash(self):
		# Best-effort deletion from Drive if we know the file id
		try:
			if getattr(self, "drive_file_id", None):
				delete_file(self.drive_file_id)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "CustomAttachment: Drive delete on_trash failed")

	def enqueue_drive_upload(self) -> None:
		if not is_feature_enabled("enable_google_drive_sync"):
			return
		try:
			enqueue_custom_attachment_sync(self.name)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Enqueue CustomAttachment upload failed")


def _resolve_file_content(file_url: str) -> tuple[bytes | None, str | None]:
	try:
		# ERPNext File doctype stores files with file_url like /files/xyz.pdf
		file_doc = frappe.get_doc("File", {"file_url": file_url})
		content = file_doc.get_content()
		name = file_doc.file_name or file_url.rsplit("/", 1)[-1]
		if isinstance(content, bytes):
			return content, name
		if isinstance(content, str):
			return content.encode("utf-8"), name
	except Exception:
		pass
	return None, None


def _upload_to_drive(docname: str) -> None:
	# Backward-compatible entrypoint; delegate to unified sync
	sync_custom_attachment_by_name(docname)
