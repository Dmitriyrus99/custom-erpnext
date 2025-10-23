import typing as t

import frappe
from frappe import _

from ferum_custom.ferum_custom.settings import get_setting, is_feature_enabled

try:
	import erpnext  # type: ignore
except Exception:  # pragma: no cover - erpnext always present in this bench
	erpnext = None  # fallback safety
from ferum_custom.ferum_custom.utils import get_allowed_customers


def _paginate(start: int | None = None, page_length: int | None = None) -> tuple[int, int]:
	s = int(start) if (start is not None and str(start).isdigit()) else 0
	pl = int(page_length) if (page_length is not None and str(page_length).isdigit()) else 20
	return s, max(1, min(pl, 200))


@frappe.whitelist(methods=["POST"])  # API used by bot/portal: POST only
def create_service_request(
	title: str, description: str | None = None, service_object: str | None = None
) -> str:
	"""Create a standard ERPNext Issue (backward-compatible API name).

	- Maps title → Issue.subject, description → Issue.description
	- Tries to populate company from defaults
	- If a Service Object is provided, appends its name to description for context
	"""
	_check_new_request_rate_limit()
	issue = frappe.new_doc("Issue")
	issue.subject = title
	if description:
		issue.description = description
	# Company default
	try:
		default_company = None
		if erpnext is not None and hasattr(erpnext, "get_default_company"):
			default_company = erpnext.get_default_company()
		if not default_company:
			default_company = frappe.db.get_single_value("Global Defaults", "default_company")
		if not default_company:
			companies = frappe.get_all("Company", pluck="name", limit=1)
			if companies:
				default_company = companies[0]
		if default_company:
			issue.company = default_company
	except Exception:
		pass
	# Try to enrich customer/project from Service Object
	if service_object:
		obj_name = service_object
		if not frappe.db.exists("Service Object", obj_name):
			try:
				val = frappe.db.get_value("Service Object", {"object_name": obj_name}, "name")
				if val:
					obj_name = val
			except Exception:
				pass
		if frappe.db.exists("Service Object", obj_name):
			try:
				so = frappe.get_doc("Service Object", obj_name)
				issue.customer = getattr(so, "customer", None)
				if getattr(so, "project", None):
					issue.project = so.project
				note = f"\n\nService Object: {obj_name}"
				issue.description = (issue.description or "") + note
			except Exception:
				pass
	issue.insert()
	return issue.name


@frappe.whitelist(methods=["GET"])  # Listing is idempotent
def list_service_requests(
	status: str | None = None, start: int | None = None, page_length: int | None = None
) -> dict:
	s, pl = _paginate(start, page_length)
	filters: dict[str, t.Any] = {}
	if status:
		filters["status"] = status
	# Restrict scope for website users or clients to their Customer
	try:
		user = frappe.session.user
		user_type = frappe.get_cached_value("User", user, "user_type")
		roles = set(frappe.get_roles(user))
		if user_type == "Website User" or "Client" in roles:
			allowed = get_allowed_customers(user)
			if allowed:
				filters["customer"] = ["in", allowed]
			else:
				# fallback: owner when no explicit customer permission
				filters["owner"] = user
	except Exception:
		pass

	# Provide Issue data compatible with portal (title alias)
	data = frappe.get_list(
		"Issue",
		filters=filters,
		fields=[
			"name",
			"subject as title",
			"status",
			"priority",
			"customer",
			"project",
			"modified",
		],
		start=s,
		page_length=pl,
		order_by="modified desc",
	)
	return {"data": data, "start": s, "page_length": pl}


@frappe.whitelist(methods=["GET"])  # Read-only fetch
def get_service_request(name: str) -> dict:
	"""Return Issue as a dict with a title alias for portal compatibility."""
	doc = frappe.get_doc("Issue", name)
	d = doc.as_dict()
	if "title" not in d:
		d["title"] = d.get("subject")
	# Do not leak sensitive fields to website users
	try:
		user = frappe.session.user
		user_type = frappe.get_cached_value("User", user, "user_type")
		roles = set(frappe.get_roles(user))
		if user_type == "Website User" or "Client" in roles:
			# Strip common sensitive custom fields if present
			for fld in ("financial_details",):
				d.pop(fld, None)
	except Exception:
		pass
	return d


@frappe.whitelist(methods=["POST"])  # State change
def update_service_request_status(name: str, status: str) -> dict:
	"""Update Service Request status with server-side validation.

	Requires authentication; relies on DocType validations and permission checks.
	"""
	doc = frappe.get_doc("Issue", name)
	# Map basic statuses if needed
	allowed = {"Open", "Replied", "On Hold", "Resolved", "Closed"}
	doc.status = status if status in allowed else "Open"
	doc.save()  # will trigger workflow and validations
	return {"ok": True, "name": doc.name, "status": doc.status}


@frappe.whitelist()
def list_service_reports(
	project: str | None = None, start: int | None = None, page_length: int | None = None
) -> dict:
	s, pl = _paginate(start, page_length)
	filters: dict[str, t.Any] = {}
	if project:
		filters["project"] = project
	try:
		user = frappe.session.user
		user_type = frappe.get_cached_value("User", user, "user_type")
		roles = set(frappe.get_roles(user))
		if user_type == "Website User" or "Client" in roles:
			# No direct customer link on Timesheet; restrict only if project provided
			if not project:
				return {"data": [], "start": 0, "page_length": pl}
	except Exception:
		pass

		# Timesheet replacement (no customer link by default)
	data = frappe.get_list(
		"Timesheet",
		filters=filters,
		fields=["name", "start_date", "end_date", "total_hours", "company", "modified"],
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
	try:
		user = frappe.session.user
		user_type = frappe.get_cached_value("User", user, "user_type")
		roles = set(frappe.get_roles(user))
		if user_type == "Website User" or "Client" in roles:
			allowed = get_allowed_customers(user)
			if allowed:
				filters["counterparty_type"] = "Customer"
				filters["counterparty_name"] = ["in", allowed]
	except Exception:
		pass

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


@frappe.whitelist()
def confirm_service_request(name: str) -> None:
	"""Allow a Client to confirm completion of a Service Request by adding a comment."""
	doc = frappe.get_doc("Issue", name)
	# Permission check performed by Frappe via get_doc; add comment
	try:
		doc.add_comment("Comment", _("Client confirmed completion via portal."))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Client confirm SR failed")


@frappe.whitelist()
def confirm_service_report(name: str) -> None:
	"""Allow a Client to confirm a Service Report via a comment."""
	doc = frappe.get_doc("Timesheet", name)
	try:
		doc.add_comment("Comment", _("Client confirmed Service Report via portal."))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Client confirm report failed")
