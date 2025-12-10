import json
import frappe


def run():
	with open("apps/ferum_custom/ferum_custom/scripts/creds.json") as fh:
		data = json.load(fh)
	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": "ferum-service-account.json",
			"content": json.dumps(data, indent=2),
			"is_private": 1,
		}
	).insert(ignore_permissions=True)
	frappe.db.set_single_value("Ferum Custom Settings", "google_service_account_json", file_doc.file_url)
	frappe.db.set_single_value(
		"Ferum Custom Settings",
		"google_sheet_name",
		"https://docs.google.com/spreadsheets/d/19WNE5JT25PuLz2mAphtHteZC0SpGE6vhLghmqq2vLoc/edit?usp=drivesdk",
	)
	frappe.db.set_single_value(
		"Ferum Custom Settings", "google_drive_root_folder_id", "1QH1o_V9NmpMawgVS8gLC3N3zFb4ejtT8"
	)
