import typing as t

import frappe
from frappe import _

from ferum_custom.api import auth as auth_api
from ferum_custom.ferum_custom.domain.service import application as service_app
from ferum_custom.ferum_custom.settings import get_setting, is_feature_enabled

try:
	import erpnext  # type: ignore
except Exception:  # pragma: no cover - erpnext always present in this bench
	erpnext = None  # fallback safety
from ferum_custom.ferum_custom.utils import get_allowed_customers


def _paginate(start: int | None = None, page_length: int | None = None) -> tuple[int, int]:
	"""
	Paginates the request.

	Args:
		start (int | None, optional): The starting index. Defaults to None.
		page_length (int | None, optional): The length of the page. Defaults to None.

	Returns:
		tuple[int, int]: The start index and page length.
	"""
	s = int(start) if (start is not None and str(start).isdigit()) else 0
	pl = int(page_length) if (page_length is not None and str(page_length).isdigit()) else 20
	return s, max(1, min(pl, 200))


def _response_ok(**payload: t.Any) -> dict[str, t.Any]:
	"""
	Creates a successful response.

	Args:
		**payload (t.Any): The payload to include in the response.

	Returns:
		dict[str, t.Any]: The successful response.
	"""
	return {"status": "ok", **payload}


def _get_bearer_token() -> str | None:
	"""
	Retrieves the bearer token from the request headers.

	Returns:
		str | None: The bearer token, or None if not found.
	"""
	authz = frappe.get_request_header("Authorization")
	if authz and authz.startswith("Bearer "):
		return authz.split(" ", 1)[1]
	return None


def _require_jwt_authentication() -> None:
	"""
	Ensures that the request is authenticated with a valid JWT token.
	"""
	if not is_feature_enabled("enable_jwt"):
		return
	token = _get_bearer_token()
	if not token:
		frappe.throw(_("Authorization token required"), frappe.AuthenticationError)
	try:
		payload = auth_api.decode_jwt(token)
	except Exception as exc:
		frappe.throw(_("Invalid JWT token: {0}").format(str(exc)), frappe.AuthenticationError)
	user_from_token = payload.get("sub")
	if user_from_token:
		frappe.set_user(user_from_token)


def _rate_limit_key(scope: str, identifier: str) -> str:
	"""
	Generates a key for rate limiting.

	Args:
		scope (str): The scope of the rate limit.
		identifier (str): The identifier for the rate limit.

	Returns:
		str: The rate limit key.
	"""
	return f"ferum:rate:{scope}:{identifier}"


def _enforce_rate_limit(scope: str, identifier: str | None, limit: int) -> None:
	"""
	Enforces a rate limit.

	Args:
		scope (str): The scope of the rate limit.
		identifier (str | None): The identifier for the rate limit.
		limit (int): The rate limit.
	"""
	if not identifier:
		return
	cache = frappe.cache()
	key = _rate_limit_key(scope, identifier)
	current = cache.get_value(key) or 0
	try:
		current_val = int(current)
	except Exception:
		current_val = 0
	current_val += 1
	cache.set_value(key, current_val, expires_in_sec=60)
	if current_val > limit:
		frappe.throw(_("Too many requests. Please try again later."))


@frappe.whitelist(methods=["POST"])  # API used by bot/portal: POST only
def create_service_request(
	title: str, description: str | None = None, service_object: str | None = None
) -> dict[str, t.Any]:
	"""
	Creates a new service request.

	This function creates a standard ERPNext Issue, mapping the title and description accordingly.
	It also tries to populate the company from defaults and link the service object if provided.

	Args:
		title (str): The title of the service request.
		description (str | None, optional): The description of the service request. Defaults to None.
		service_object (str | None, optional): The service object to link to the request. Defaults to None.

	Returns:
		dict[str, t.Any]: A dictionary containing the name of the created service request.
	"""
	_require_jwt_authentication()
	_check_new_request_rate_limit()
	company = None
	project = None
	customer = None
	try:
		default_company = frappe.db.get_single_value("Global Defaults", "default_company")
		if not default_company and erpnext is not None and hasattr(erpnext, "get_default_company"):
			default_company = erpnext.get_default_company()
		if not default_company:
			companies = frappe.get_all("Company", pluck="name", limit=1)
			if companies:
				default_company = companies[0]
		company = default_company
	except Exception:
		pass

	if service_object:
		obj_name = service_object
		if not frappe.db.exists("Asset", obj_name):
			obj_name = frappe.db.get_value("Asset", {"asset_name": obj_name}, "name") or service_object
		if frappe.db.exists("Asset", obj_name):
			so = frappe.get_doc("Asset", obj_name)
			customer = getattr(so, "customer", None)
			project = getattr(so, "project", None)
			company = company or getattr(so, "company", None)

	name = service_app.create_service_request(
		title=title,
		description=description,
		service_object=service_object,
		company=company,
		project=project,
		customer=customer,
	)
	return _response_ok(name=name, data={"name": name})


@frappe.whitelist(methods=["GET"])  # Listing is idempotent
def list_service_requests(
	status: str | None = None, start: int | None = None, page_length: int | None = None
) -> dict:
	"""
	Lists service requests.

	Args:
		status (str | None, optional): The status to filter by. Defaults to None.
		start (int | None, optional): The starting index for pagination. Defaults to None.
		page_length (int | None, optional): The number of items per page. Defaults to None.

	Returns:
		dict: A dictionary containing the list of service requests.
	"""
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

	data = service_app.list_service_requests(filters=filters, start=s, page_length=pl)
	return _response_ok(data=data, start=s, page_length=pl)


@frappe.whitelist(methods=["GET"])  # Read-only fetch
def get_service_request(name: str) -> dict:
	"""
	Retrieves a service request by name.

	Args:
		name (str): The name of the service request to retrieve.

	Returns:
		dict: A dictionary containing the service request data.
	"""
	data = service_app.fetch_service_request(name)
	try:
		user = frappe.session.user
		user_type = frappe.get_cached_value("User", user, "user_type")
		roles = set(frappe.get_roles(user))
		if user_type == "Website User" or "Client" in roles:
			allowed = get_allowed_customers(user)
			if allowed and data.get("customer") not in allowed:
				frappe.throw(_("Not permitted"))
	except Exception:
		pass
	return _response_ok(data=data)


@frappe.whitelist()
def portal_token() -> dict[str, t.Any]:
	"""
	Issues a JWT token for the currently logged-in user.

	Returns:
		dict[str, t.Any]: A dictionary containing the JWT token and the username.
	"""
	if not is_feature_enabled("enable_jwt"):
		frappe.throw(_("JWT is disabled"))
	user = frappe.session.user
	if not user or user == "Guest":
		frappe.throw(_("Login required for portal token"))
	token = auth_api.issue_jwt_for_user(user)
	return _response_ok(token=token, user=user)


@frappe.whitelist(methods=["POST"])  # State change
def update_issue_status(name: str, status: str) -> dict:
	"""
	Updates the status of an issue.

	This function updates the status of an issue with server-side validation.
	It requires authentication and relies on DocType validations and permission checks.

	Args:
		name (str): The name of the issue to update.
		status (str): The new status for the issue.

	Returns:
		dict: A dictionary containing the name and updated status of the issue.
	"""
	_require_jwt_authentication()
	doc = frappe.get_doc("Issue", name)
	# Map basic statuses if needed
	allowed = {"Open", "Replied", "On Hold", "Resolved", "Closed"}
	doc.status = status if status in allowed else "Open"
	doc.save()  # will trigger workflow and validations
	return _response_ok(name=doc.name, status=doc.status)


@frappe.whitelist()
def list_service_reports(
	project: str | None = None, start: int | None = None, page_length: int | None = None
) -> dict:
	"""
	Lists service reports.

	Args:
		project (str | None, optional): The project to filter by. Defaults to None.
		start (int | None, optional): The starting index for pagination. Defaults to None.
		page_length (int | None, optional): The number of items per page. Defaults to None.

	Returns:
		dict: A dictionary containing the list of service reports.
	"""
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
				return _response_ok(data=[], start=0, page_length=pl)
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
	return _response_ok(data=data, start=s, page_length=pl)


def _get_client_ip() -> str:
	"""
	Retrieves the client's IP address from the request headers.

	Returns:
		str: The client's IP address.
	"""
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
	"""
	Checks and enforces the rate limit for creating new service requests.
	"""
	try:
		if not is_feature_enabled("enable_rate_limit_create_request"):
			return
		limit = get_setting("rate_limit_create_request_per_minute")
		try:
			limit_val = int(limit) if limit is not None else 10
		except Exception:
			limit_val = 10
		ip = _get_client_ip()
		_enforce_rate_limit("new_request_ip", ip, max(1, limit_val))
		user = frappe.session.user
		if user and user not in {"Guest", "Administrator"}:
			_enforce_rate_limit("new_request_user", user, max(1, limit_val))
	except Exception:
		# Never block due to rate-limit implementation errors
		pass


@frappe.whitelist()
def list_invoices(
	project: str | None = None, start: int | None = None, page_length: int | None = None
) -> dict:
	"""
	Lists invoices.

	Args:
		project (str | None, optional): The project to filter by. Defaults to None.
		start (int | None, optional): The starting index for pagination. Defaults to None.
		page_length (int | None, optional): The number of items per page. Defaults to None.

	Returns:
		dict: A dictionary containing the list of invoices.
	"""
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
	return _response_ok(data=data, start=s, page_length=pl)


@frappe.whitelist()
def confirm_issue_completion(name: str) -> None:
	"""Allow a Client to confirm completion of an Issue by adding a comment."""
	service_app.confirm_service_request(name)


@frappe.whitelist()
def confirm_timesheet_report(name: str) -> None:
	"""Allow a Client to confirm a Timesheet Report via a comment."""
	service_app.confirm_timesheet_report(name)
