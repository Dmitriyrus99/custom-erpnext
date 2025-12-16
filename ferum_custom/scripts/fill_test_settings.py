import json
import os

import frappe


def _load_service_account_payload() -> str | None:
	env_payload = os.getenv("FERUM_GOOGLE_SERVICE_ACCOUNT_JSON")
	if env_payload and env_payload.strip().startswith("{"):
		return env_payload
	path = os.path.join(os.path.dirname(__file__), "creds.json")
	try:
		if os.path.exists(path):
			with open(path, encoding="utf-8") as fh:
				data = json.load(fh)
			return json.dumps(data, indent=2)
	except Exception:
		pass
	return None


def run():
	frappe.set_user("Administrator")

	payload = _load_service_account_payload()

	file_url = None
	if payload:
		existing = frappe.db.exists(
			"File",
			{
				"attached_to_doctype": "Ferum Custom Settings",
				"attached_to_name": "Ferum Custom Settings",
				"file_name": "ferum-service-account.json",
			},
		)
		if existing:
			frappe.delete_doc("File", existing, ignore_permissions=True)

		file_doc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "ferum-service-account.json",
				"content": payload,
				"is_private": 1,
			}
		).insert(ignore_permissions=True)
		file_url = file_doc.file_url
		frappe.db.set_single_value("Ferum Custom Settings", "google_service_account_json", file_url)

	frappe.db.set_single_value("Ferum Custom Settings", "enable_google_drive_sync", 1)
	frappe.db.set_single_value("Ferum Custom Settings", "enable_google_sheets_sync", 1)
	if not frappe.db.get_single_value("Ferum Custom Settings", "google_drive_root_folder_id"):
		frappe.db.set_single_value("Ferum Custom Settings", "google_drive_root_folder_id", "")
	frappe.db.set_single_value("Ferum Custom Settings", "enable_jwt", 1)
	if not frappe.db.get_single_value("Ferum Custom Settings", "jwt_secret"):
		frappe.db.set_single_value("Ferum Custom Settings", "jwt_secret", "test-jwt-secret")

	frappe.db.commit()
	return {"file_url": file_url}
