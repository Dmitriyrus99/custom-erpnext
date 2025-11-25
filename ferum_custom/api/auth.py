import time
from typing import Any

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
def _jwt_payload(username: str, expires_in: int | None = None) -> dict[str, Any]:
	now_ts = int(time.time())
	expiry = now_ts + (expires_in or 3600)
	return {
		"sub": username,
		"iat": now_ts,
		"exp": expiry,
		"aud": "ferum.api",
		"scope": "ferum:api",
	}


def _get_jwt_secret() -> str | None:
	return get_setting("jwt_secret")


def _jwt_feature_enabled() -> bool:
	return bool(is_feature_enabled("enable_jwt") or getattr(frappe.flags, "in_test", False))


def issue_jwt_for_user(username: str, expires_in: int | None = None) -> str:
	if jwt is None:
		frappe.throw(_("pyjwt not installed on server"))
	if not _jwt_feature_enabled():
		frappe.throw(_("JWT is disabled"))
	secret = _get_jwt_secret()
	if not secret:
		frappe.throw(_("JWT secret not configured"))
	payload = _jwt_payload(username, expires_in=expires_in)
	return jwt.encode(payload, secret, algorithm="HS256")


def decode_jwt(token: str, verify_aud: bool = False) -> dict[str, Any]:
	if jwt is None:
		raise frappe.AuthenticationError(_("pyjwt not installed on server"))
	if not _jwt_feature_enabled():
		raise frappe.AuthenticationError(_("JWT is disabled"))
	secret = _get_jwt_secret()
	if not secret:
		raise frappe.AuthenticationError(_("JWT secret not configured"))
	options = {"verify_aud": verify_aud}
	try:
		return jwt.decode(token, secret, algorithms=["HS256"], options=options)  # type: ignore[arg-type]
	except Exception as exc:
		raise frappe.AuthenticationError(str(exc)) from exc


def login(username: str, password: str, otp: str | None = None) -> dict:
	"""Issue JWT for API usage (optional)."""
	_check_auth_rate_limit()
	if jwt is None:
		frappe.throw(_("pyjwt not installed on server"))
	if not _jwt_feature_enabled():
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
	return {"token": issue_jwt_for_user(username)}


def jwt_before_request():
	"""Optional: accept Bearer JWT on Ferum API namespace only.

	Guards:
	- Feature flag enabled and secret present
	- Request targets only our namespace (`/api/method/ferum_custom.*`)
	- If token has `aud`, require it to be `ferum.api`
	"""
	try:
		if jwt is None or not is_feature_enabled("enable_jwt"):
			return

		# Restrict applicability to our API namespace to reduce attack surface
		try:
			path = getattr(frappe.request, "path", "")  # type: ignore[attr-defined]
		except Exception:
			path = ""
		form_cmd = None
		try:
			form_cmd = (getattr(getattr(frappe.local, "form_dict", object()), "cmd", None) or "").strip()
		except Exception:
			form_cmd = None
		in_namespace = False
		if path and "/api/method/ferum_custom." in path:
			in_namespace = True
		if form_cmd and str(form_cmd).startswith("ferum_custom."):
			in_namespace = True
		if not in_namespace:
			return

		secret = get_setting("jwt_secret")
		if not secret:
			return
		authz = frappe.get_request_header("Authorization")
		if not authz or not authz.startswith("Bearer "):
			return
		token = authz.split(" ", 1)[1]
		# Decode without audience verification first to remain backward compatible
		data = jwt.decode(token, secret, algorithms=["HS256"], options={"verify_aud": False})  # type: ignore[arg-type]
		aud = data.get("aud")
		if aud is not None and aud != "ferum.api":
			return
		user = data.get("sub")
		if user and user != frappe.session.user:
			frappe.set_user(user)
	except Exception:
		# Do not block non-protected routes
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
