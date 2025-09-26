import frappe

from ferum_custom.ferum_custom.integrations.google import refresh_service_account_cache
from ferum_custom.ferum_custom.settings import refresh_settings_cache


@frappe.whitelist()
def save_integrations(
	telegram_chat_id: str | None = None,
	telegram_token: str | None = None,
	drive_root_id: str | None = None,
) -> dict:
	"""Persist integration settings into Ferum Custom Settings singleton.

	Only updates provided fields. Returns the saved subset.
	"""
	frappe.only_for("System Manager")

	settings = frappe.get_single("Ferum Custom Settings")
	updated: dict[str, str] = {}

	if telegram_chat_id is not None:
		settings.telegram_default_chat_id = telegram_chat_id
		updated["telegram_default_chat_id"] = telegram_chat_id

	if telegram_token is not None:
		settings.telegram_bot_token = telegram_token
		# do not include token in response

	if drive_root_id is not None:
		settings.google_drive_root_folder_id = drive_root_id
		updated["google_drive_root_folder_id"] = drive_root_id

	settings.save(ignore_permissions=True)
	frappe.db.commit()
	refresh_settings_cache()
	refresh_service_account_cache()
	return updated


@frappe.whitelist()
def add_user_company_permission(user: str, company: str) -> dict:
	"""Create (idempotent) User Permission mapping a user to a Company.

	Returns the created/ensured record name.
	"""
	frappe.only_for("System Manager")
	if not frappe.db.exists("Company", company):
		raise frappe.DoesNotExistError(f"Company not found: {company}")
	# Check existing
	exists = frappe.get_all(
		"User Permission",
		filters={"user": user, "allow": "Company", "for_value": company},
		pluck="name",
	)
	if exists:
		return {"name": exists[0]}
	up = frappe.new_doc("User Permission")
	up.user = user
	up.allow = "Company"
	up.for_value = company
	up.apply_to_all_doctypes = 1
	up.insert(ignore_permissions=True)
	return {"name": up.name}


@frappe.whitelist()
def bulk_add_user_company_permissions(pairs: list[dict] | str) -> dict:
	"""Bulk mapping of users to companies.

	Accepts a list of {user, company} or a JSON string.
	Returns count of created/ensured mappings.
	"""
	frappe.only_for("System Manager")
	try:
		items = frappe.parse_json(pairs) if isinstance(pairs, str) else pairs
	except Exception:
		raise frappe.ValidationError("Invalid payload: expected list of {user, company}")
	count = 0
	for it in items or []:
		user = it.get("user")
		company = it.get("company")
		if not user or not company:
			continue
		add_user_company_permission(user, company)
		count += 1
	return {"count": count}
