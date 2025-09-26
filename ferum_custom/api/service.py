import typing as t

import frappe
from frappe import _

from ferum_custom.ferum_custom.settings import get_setting, is_feature_enabled


def _paginate(start: int | None = None, page_length: int | None = None) -> tuple[int, int]:
	s = int(start) if (start is not None and str(start).isdigit()) else 0
	pl = int(page_length) if (page_length is not None and str(page_length).isdigit()) else 20
	return s, max(1, min(pl, 200))


@frappe.whitelist()
def create_service_request(
	title: str, description: str | None = None, service_object: str | None = None
) -> str:
	_check_new_request_rate_limit()
	doc = frappe.new_doc("Service Request")
	doc.title = title
	doc.description = description
	if service_object:
		# Accept either a docname or a human-friendly object_name
		obj_name = service_object
		if not frappe.db.exists("Service Object", obj_name):
			try:
				val = frappe.db.get_value("Service Object", {"object_name": obj_name}, "name")
				if val:
					obj_name = val
			except Exception:
				pass
		if frappe.db.exists("Service Object", obj_name):
			doc.service_object = obj_name
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


def _get_client_ip() -> str:
	try:
		xff = frappe.get_request_header("X-Forwarded-For")
		if xff:
			return xff.split(",")[0].strip()
		real_ip = frappe.get_request_header("X-Real-IP")
		if real_ip:
			return real_ip
		ip = getattr(frappe.local, "request_ip", None)
		if ip:
			return str(ip)
	except Exception:
		pass
	return "unknown"


def _check_new_request_rate_limit() -> None:
	try:
		if not is_feature_enabled("enable_rate_limit_create_request"):
			return
		limit = get_setting("rate_limit_create_request_per_minute")
		try:
			limit_val = int(limit) if limit is not None else 10
		except Exception:
			limit_val = 10
		ip = _get_client_ip()
		key = f"ferum:rate:new_request:{ip}"
		cache = frappe.cache()
		current = cache.get_value(key) or 0
		try:
			current_val = int(current) if current is not None else 0
		except Exception:
			current_val = 0
		current_val += 1
		cache.set_value(key, current_val, expires_in_sec=60)
		if current_val > max(1, limit_val):
			frappe.throw(_("Too many new requests. Please try again later."))
	except Exception:
		# Never block due to rate-limit implementation errors
		pass


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
