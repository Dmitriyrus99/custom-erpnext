import frappe
from frappe.model.document import Document

from ferum_custom.ferum_custom.integrations.drive import upload_bytes


class CustomAttachment(Document):
	def after_insert(self):
		self.enqueue_drive_upload()

	def on_update(self):
		# Upload if drive id missing and we have a local File URL
		if not getattr(self, "drive_file_id", None):
			self.enqueue_drive_upload()

	def enqueue_drive_upload(self) -> None:
		try:
			frappe.enqueue(
				"ferum_custom.ferum_custom.doctype.custom_attachment.custom_attachment._upload_to_drive",
				queue="short",
				docname=self.name,
			)
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
	doc = frappe.get_doc("Custom Attachment", docname)
	if doc.drive_file_id:
		return
	# Only handle ERP-managed files; skip external URLs
	if not doc.file_url or not doc.file_url.startswith("/"):
		return
	data, filename = _resolve_file_content(doc.file_url)
	if not data:
		return
	# Build path based on linked document if available
	parts: list[str] = ["Attachments"]
	try:
		if doc.linked_doctype and doc.linked_docname:
			# Try customer/project context
			if doc.linked_doctype == "Service Report":
				sr = frappe.db.get_value(
					"Service Report",
					doc.linked_docname,
					["service_request"],
					as_dict=True,
				)
				if sr and sr.service_request:
					cust, proj = frappe.db.get_value(
						"Service Request",
						sr.service_request,
						["customer", "project"],
						as_dict=True,
					).values()
					parts = [p for p in [cust or "Customer", proj or "Project", "Attachments"]]
			elif doc.linked_doctype == "Service Project":
				cust = frappe.db.get_value("Service Project", doc.linked_docname, "customer")
				parts = [p for p in [cust or "Customer", doc.linked_docname, "Attachments"]]
			elif doc.linked_doctype == "Invoice":
				(proj,) = frappe.db.get_value("Invoice", doc.linked_docname, ["project"]) or (None,)
				parts = [p for p in ["Invoices", proj or "Project", "Attachments"]]
	except Exception:
		pass

	file_id = upload_bytes(parts, filename or f"Attachment-{doc.name}", data)
	if file_id:
		try:
			web_link = f"https://drive.google.com/file/d/{file_id}/view?usp=drivesdk"
			doc.db_set({"drive_file_id": file_id, "drive_web_link": web_link}, commit=True)
		except Exception:
			pass
