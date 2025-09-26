import time

import frappe
from frappe import _
from frappe.twofactor import (
	get_otpsecret_for_,
	get_verification_method,
	two_factor_is_enabled,
)
from frappe.utils import now

from ferum_custom.ferum_custom.settings import get_setting, is_feature_enabled

try:
	import jwt  # type: ignore[import-untyped]
except Exception:
	jwt = None  # optional

try:
	import pyotp  # type: ignore[import-untyped]
except Exception:
	pyotp = None  # optional


@frappe.whitelist(allow_guest=True)
def login(username: str, password: str, otp: str | None = None) -> dict:
	"""Issue JWT for API usage (optional)."""
	_check_auth_rate_limit()
	if jwt is None:
		frappe.throw(_("pyjwt not installed on server"))
	if not is_feature_enabled("enable_jwt"):
		frappe.throw(_("JWT is disabled"))

	lm = frappe.auth.LoginManager()
	lm.authenticate(user=username, pwd=password)

	if two_factor_is_enabled(user=username):
		otp_code = (otp or "").strip()
		if not otp_code:
			frappe.throw(_("OTP code required for two-factor authentication."))
		method = get_verification_method()
		if method == "OTP App":
			if pyotp is None:
				frappe.throw(_("pyotp not installed on server"))
			secret = get_otpsecret_for_(username)
			if not pyotp.TOTP(secret).verify(otp_code):
				frappe.throw(_("Invalid OTP code."))
		else:
			frappe.throw(
				_("Two-factor method {0} is not supported via API.").format(method or "unknown"),
			)

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


def _get_client_ip() -> str:
	"""Best-effort client IP detection behind proxies."""
	try:
		# Prefer explicit proxy headers when present
		xff = frappe.get_request_header("X-Forwarded-For")
		if xff:
			return xff.split(",")[0].strip()
		real_ip = frappe.get_request_header("X-Real-IP")
		if real_ip:
			return real_ip
		# Fallback to frappe.local if provided
		ip = getattr(frappe.local, "request_ip", None)
		if ip:
			return str(ip)
	except Exception:
		pass
	return "unknown"


def _check_auth_rate_limit() -> None:
	"""Simple per-IP rate limit for auth.login, configurable in settings."""
	try:
		if not is_feature_enabled("enable_rate_limit_auth"):
			return
		limit = get_setting("rate_limit_auth_per_minute")
		try:
			limit_val = int(limit) if limit is not None else 5
		except Exception:
			limit_val = 5

		ip = _get_client_ip()
		key = f"ferum:rate:auth:{ip}"
		cache = frappe.cache()
		current = cache.get_value(key) or 0
		try:
			current_val = int(current) if current is not None else 0
		except Exception:
			current_val = 0
		current_val += 1
		cache.set_value(key, current_val, expires_in_sec=60)
		if current_val > max(1, limit_val):
			frappe.throw(_("Too many login attempts. Please try again later."))
	except Exception:
		# Never block login due to rate-limit implementation errors
		pass
