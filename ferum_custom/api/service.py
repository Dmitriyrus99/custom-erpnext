import typing as t

import frappe


def _paginate(start: int | None = None, page_length: int | None = None) -> tuple[int, int]:
	s = int(start) if (start is not None and str(start).isdigit()) else 0
	pl = int(page_length) if (page_length is not None and str(page_length).isdigit()) else 20
	return s, max(1, min(pl, 200))


@frappe.whitelist()
def create_service_request(
	title: str, description: str | None = None, service_object: str | None = None
) -> str:
	doc = frappe.new_doc("Service Request")
	doc.title = title
	doc.description = description
	if service_object:
		doc.service_object = service_object
	doc.insert()
	return doc.name


@frappe.whitelist()
def list_service_requests(
	status: str | None = None, start: int | None = None, page_length: int | None = None
) -> dict:
	s, pl = _paginate(start, page_length)
	filters: dict[str, t.Any] = {}
	if status:
		filters["status"] = status
	# Restrict scope for website users or clients to their own
	try:
		user = frappe.session.user
		user_type = frappe.get_cached_value("User", user, "user_type")
		roles = set(frappe.get_roles(user))
		if user_type == "Website User" or "Client" in roles:
			filters["owner"] = user
	except Exception:
		pass

	data = frappe.get_list(
		"Service Request",
		filters=filters,
		fields=["name", "title", "status", "priority", "customer", "project", "service_object", "modified"],
		start=s,
		page_length=pl,
		order_by="modified desc",
	)
	return {"data": data, "start": s, "page_length": pl}


@frappe.whitelist()
def get_service_request(name: str) -> dict:
	doc = frappe.get_doc("Service Request", name)
	return doc.as_dict()


@frappe.whitelist()
def list_service_reports(
	project: str | None = None, start: int | None = None, page_length: int | None = None
) -> dict:
	s, pl = _paginate(start, page_length)
	filters: dict[str, t.Any] = {}
	if project:
		filters["project"] = project
	data = frappe.get_list(
		"Service Report",
		filters=filters,
		fields=["name", "service_request", "status", "report_date", "total_amount", "modified"],
		start=s,
		page_length=pl,
		order_by="modified desc",
	)
	return {"data": data, "start": s, "page_length": pl}


@frappe.whitelist()
def list_invoices(
	project: str | None = None, start: int | None = None, page_length: int | None = None
) -> dict:
	s, pl = _paginate(start, page_length)
	filters: dict[str, t.Any] = {}
	if project:
		filters["project"] = project
	data = frappe.get_list(
		"Invoice",
		filters=filters,
		fields=[
			"name",
			"project",
			"counterparty_name",
			"counterparty_type",
			"status",
			"amount",
			"invoice_date",
			"sales_invoice",
			"modified",
		],
		start=s,
		page_length=pl,
		order_by="modified desc",
	)
	return {"data": data, "start": s, "page_length": pl}
