import time
import typing as t

import frappe
from frappe import _

try:
	import jwt  # type: ignore[import-untyped]
except Exception:
	jwt = None  # optional


def _get_settings():
	try:
		return frappe.get_single("Ferum Custom Settings")
	except Exception:
		return None


@frappe.whitelist(allow_guest=True)
def login(username: str, password: str) -> dict:
	"""Issue JWT for API usage (optional)."""
	settings = _get_settings()
	if not settings or not settings.enable_jwt:
		frappe.throw(_("JWT is disabled"))
	if jwt is None:
		frappe.throw(_("pyjwt not installed on server"))

	lm = frappe.auth.LoginManager()
	lm.authenticate(user=username, pwd=password)
	lm.post_login()

	secret = settings.jwt_secret
	if not secret:
		frappe.throw(_("JWT secret not configured"))
	payload = {"sub": username, "iat": int(time.time()), "exp": int(time.time()) + 3600}
	token = jwt.encode(payload, secret, algorithm="HS256")
	return {"token": token}


def jwt_before_request():
	"""Optional: accept Bearer JWT on API calls under our namespace."""
	try:
		settings = _get_settings()
		if not settings or not settings.enable_jwt or jwt is None:
			return
		authz = frappe.get_request_header("Authorization")
		if not authz or not authz.startswith("Bearer "):
			return
		token = authz.split(" ", 1)[1]
		data = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])  # type: ignore[arg-type]
		user = data.get("sub")
		if user and user != frappe.session.user:
			frappe.set_user(user)
	except Exception:
		# Do not block non-protected routes silently
		pass
