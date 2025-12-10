import frappe
from frappe.utils import nowdate


def _ensure_customer_group_and_territory() -> tuple[str, str]:
	# Customer Group
	cg = frappe.get_all("Customer Group", pluck="name")
	if cg:
		customer_group = cg[0]
	else:
		# Create a minimal tree: root + leaf
		if not frappe.db.exists("Customer Group", "All Customer Groups"):
			root = frappe.new_doc("Customer Group")
			root.customer_group_name = "All Customer Groups"
			root.is_group = 1
			root.insert(ignore_permissions=True)
		leaf = frappe.new_doc("Customer Group")
		leaf.customer_group_name = "General"
		leaf.parent_customer_group = "All Customer Groups"
		leaf.is_group = 0
		leaf.insert(ignore_permissions=True)
		customer_group = leaf.name

	# Territory
	tr = frappe.get_all("Territory", pluck="name")
	if tr:
		territory = tr[0]
	else:
		if not frappe.db.exists("Territory", "All Territories"):
			troot = frappe.new_doc("Territory")
			troot.territory_name = "All Territories"
			troot.is_group = 1
			troot.insert(ignore_permissions=True)
		tleaf = frappe.new_doc("Territory")
		tleaf.territory_name = "Rest of the World"
		tleaf.parent_territory = "All Territories"
		tleaf.is_group = 0
		tleaf.insert(ignore_permissions=True)
		territory = tleaf.name

	return customer_group, territory


def _get_or_create_customer(name: str) -> str:
	if frappe.db.exists("Customer", name):
		return name
	customer_group, territory = _ensure_customer_group_and_territory()
	doc = frappe.new_doc("Customer")
	doc.customer_name = name
	doc.customer_group = customer_group
	doc.territory = territory
	doc.insert(ignore_permissions=True)
	return doc.name


def _get_or_create_asset(name: str, customer: str, project: str | None = None) -> str:
	if frappe.db.exists("Asset", {"asset_name": name}):
		return frappe.db.get_value("Asset", {"asset_name": name}, "name")
	doc = frappe.new_doc("Asset")
	doc.asset_name = name
	doc.customer = customer
	doc.address = "Demo Address"
	doc.insert(ignore_permissions=True)
	return doc.name


def _get_or_create_project_doc(customer: str, project_name: str) -> str:
	# Use project_name as the unique key
	exists = frappe.db.exists("Project", {"project_name": project_name})
	if exists:
		return exists
	proj = frappe.new_doc("Project")
	proj.customer = customer
	proj.project_name = project_name
	proj.status = "Active"
	proj.insert(ignore_permissions=True)
	return proj.name


def _get_or_create_custom_attachment(file_name: str, url: str) -> str:
	exists = frappe.db.exists("Custom Attachment", {"file_name": file_name, "file_url": url})
	if exists:
		return exists
	att = frappe.new_doc("Custom Attachment")
	att.file_name = file_name
	att.file_url = url
	att.file_type = "url"
	try:
		att.uploaded_by = frappe.session.user or "Administrator"
	except Exception:
		att.uploaded_by = "Administrator"
	att.uploaded_on = frappe.utils.now_datetime()
	att.insert(ignore_permissions=True)
	return att.name


def _get_or_create_issue(title: str, asset_name: str) -> str:
	exists = frappe.db.exists("Issue", {"subject": title})
	if exists:
		return exists
	asset_doc = frappe.get_doc("Asset", asset_name)
	issue_doc = frappe.new_doc("Issue")
	issue_doc.subject = title
	issue_doc.issue_type = "Routine Maintenance"
	issue_doc.priority = "High"
	issue_doc.asset = asset_name
	issue_doc.customer = asset_doc.customer
	issue_doc.project = asset_doc.project  # Project link is via asset's project if available
	issue_doc.status = "Open"
	issue_doc.creation = frappe.utils.now_datetime()
	issue_doc.insert(ignore_permissions=True)
	return issue_doc.name


def _get_or_create_timesheet(issue_name: str, attachment_name: str) -> str:
	exists = frappe.db.exists("Timesheet", {"issue": issue_name})
	if exists:
		return exists
	timesheet_doc = frappe.new_doc("Timesheet")
	timesheet_doc.issue = issue_name
	timesheet_doc.start_date = nowdate()
	timesheet_doc.status = "Draft"
	timesheet_doc.append(
		"time_logs", {"activity_type": "Maintenance", "hours": 1.0, "description": "Inspection"}
	)
	timesheet_doc.insert(ignore_permissions=True)
	return timesheet_doc.name


def _get_or_create_maintenance_schedule(customer: str, project: str, asset_name: str) -> str:
	key = f"MS-{project}"
	exists = frappe.db.exists("Service Maintenance Schedule", {"schedule_name": key})
	if exists:
		return exists
	ms = frappe.new_doc("Service Maintenance Schedule")
	ms.schedule_name = key
	ms.customer = customer
	ms.project = project
	ms.frequency = "Daily"
	ms.start_date = nowdate()
	ms.next_due_date = nowdate()
	ms.append("items", {"asset": asset_name, "description": "Daily health check"})
	ms.insert(ignore_permissions=True)
	return ms.name


def _get_or_create_invoice(project: str, counterparty_name: str, amount: float) -> str:
	exists = frappe.db.exists("Invoice", {"project": project, "counterparty_name": counterparty_name})
	if exists:
		return exists
	inv = frappe.new_doc("Invoice")
	inv.project = project
	inv.counterparty_type = "Customer"
	inv.counterparty_name = counterparty_name
	inv.status = "Draft"
	inv.invoice_date = nowdate()
	inv.amount = amount
	inv.insert(ignore_permissions=True)
	return inv.name


def create_demo_data() -> dict:
	"""Create demo master and transactional records for quick smoke tests.

	Returns keys of created/found documents.
	"""
	frappe.only_for("Administrator")

	customer = _get_or_create_customer("Ferum LLC")
	project = _get_or_create_project_doc(customer, "Maintenance Contract 2025")
	asset = _get_or_create_asset("Pump-1001", customer, None)

	attachment = _get_or_create_custom_attachment("demo_doc.pdf", "https://example.com/demo_doc.pdf")
	issue = _get_or_create_issue("Replace filter", asset)
	timesheet = _get_or_create_timesheet(issue, attachment)
	ms = _get_or_create_maintenance_schedule(customer, project, asset)
	invoice = _get_or_create_invoice(project, "Ferum LLC", 1000)

	return {
		"customer": customer,
		"project": project,
		"asset": asset,
		"issue": issue,
		"timesheet": timesheet,
		"maintenance_schedule": ms,
		"invoice": invoice,
	}
