import time
import frappe
from frappe import _

from ferum_custom.ferum_custom.settings import get_setting, is_feature_enabled

try:
	import jwt  # type: ignore[import-untyped]
except Exception:
	jwt = None  # optional


@frappe.whitelist(allow_guest=True)
def login(username: str, password: str) -> dict:
	"""Issue JWT for API usage (optional)."""
	if jwt is None:
		frappe.throw(_("pyjwt not installed on server"))
	if not is_feature_enabled("enable_jwt"):
		frappe.throw(_("JWT is disabled"))

	lm = frappe.auth.LoginManager()
	lm.authenticate(user=username, pwd=password)
	lm.post_login()

	secret = get_setting("jwt_secret")
	if not secret:
		frappe.throw(_("JWT secret not configured"))
	payload = {"sub": username, "iat": int(time.time()), "exp": int(time.time()) + 3600}
	token = jwt.encode(payload, secret, algorithm="HS256")
	return {"token": token}


def jwt_before_request():
	"""Optional: accept Bearer JWT on API calls under our namespace."""
	try:
		if jwt is None or not is_feature_enabled("enable_jwt"):
			return
		secret = get_setting("jwt_secret")
		if not secret:
			return
		authz = frappe.get_request_header("Authorization")
		if not authz or not authz.startswith("Bearer "):
			return
		token = authz.split(" ", 1)[1]
		data = jwt.decode(token, secret, algorithms=["HS256"])  # type: ignore[arg-type]
		user = data.get("sub")
		if user and user != frappe.session.user:
			frappe.set_user(user)
	except Exception:
		# Do not block non-protected routes silently
		pass
