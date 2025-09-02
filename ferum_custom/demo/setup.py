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


def _get_or_create_service_object(name: str, customer: str, project: str | None = None) -> str:
	if frappe.db.exists("Service Object", {"object_name": name}):
		return frappe.db.get_value("Service Object", {"object_name": name}, "name")
	doc = frappe.new_doc("Service Object")
	doc.object_name = name
	doc.customer = customer
	if project:
		doc.project = project
	doc.address = "Demo Address"
	doc.insert(ignore_permissions=True)
	return doc.name


def _get_or_create_project(customer: str, project_name: str, objects: list[str]) -> str:
	# Use project_name as the unique key
	exists = frappe.db.exists("Service Project", {"project_name": project_name})
	if exists:
		return exists
	proj = frappe.new_doc("Service Project")
	proj.customer = customer
	proj.project_name = project_name
	proj.status = "Active"
	for so in objects:
		proj.append("objects", {"service_object": so})
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


def _get_or_create_service_request(title: str, service_object: str) -> str:
	exists = frappe.db.exists("Service Request", {"title": title})
	if exists:
		return exists
	so = frappe.get_doc("Service Object", service_object)
	req = frappe.new_doc("Service Request")
	req.title = title
	req.type = "Routine Maintenance"
	req.priority = "High"
	req.service_object = service_object
	req.customer = so.customer
	req.project = so.project
	req.status = "Open"
	req.reported_datetime = frappe.utils.now()
	req.insert(ignore_permissions=True)
	return req.name


def _get_or_create_service_report(request_name: str, attachment_name: str) -> str:
	exists = frappe.db.exists("Service Report", {"service_request": request_name})
	if exists:
		return exists
	rep = frappe.new_doc("Service Report")
	rep.service_request = request_name
	rep.report_date = nowdate()
	rep.status = "Draft"
	rep.append("work_items", {"description": "Inspection", "hours": 1.0, "rate": 100})
	rep.append("documents", {"custom_attachment": attachment_name})
	rep.insert(ignore_permissions=True)
	return rep.name


def _get_or_create_maintenance_schedule(customer: str, project: str, service_object: str) -> str:
	key = f"MS-{project}"
	exists = frappe.db.exists("Service Maintenance Schedule", {"schedule_name": key})
	if exists:
		return exists
	ms = frappe.new_doc("Service Maintenance Schedule")
	ms.schedule_name = key
	ms.customer = customer
	ms.service_project = project
	ms.frequency = "Daily"
	ms.start_date = nowdate()
	ms.next_due_date = nowdate()
	ms.append("items", {"service_object": service_object, "description": "Daily health check"})
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
	project = _get_or_create_project(customer, "Maintenance Contract 2025", [])
	service_object = _get_or_create_service_object("Pump-1001", customer, project)

	# Ensure object listed in project child table
	if not any(
		so.service_object == service_object for so in frappe.get_doc("Service Project", project).objects
	):
		proj = frappe.get_doc("Service Project", project)
		proj.append("objects", {"service_object": service_object})
		proj.save(ignore_permissions=True)

	attachment = _get_or_create_custom_attachment("demo_doc.pdf", "https://example.com/demo_doc.pdf")
	request = _get_or_create_service_request("Replace filter", service_object)
	report = _get_or_create_service_report(request, attachment)
	# Skip creating Maintenance Schedule to avoid conflicts with similarly named ERPNext DocType
	ms = None
	invoice = _get_or_create_invoice(project, "Ferum LLC", 1000)

	return {
		"customer": customer,
		"project": project,
		"service_object": service_object,
		"service_request": request,
		"service_report": report,
		"maintenance_schedule": ms,
		"invoice": invoice,
	}
