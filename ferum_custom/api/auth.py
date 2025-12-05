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
	"""
	Generates the payload for a JWT token.

	Args:
		username (str): The username to include in the token.
		expires_in (int | None, optional): The token's expiration time in seconds. Defaults to None.

	Returns:
		dict[str, Any]: The JWT payload.
	"""
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
	"""
	Retrieves the JWT secret from the settings.

	Returns:
		str | None: The JWT secret, or None if not configured.
	"""
	return get_setting("jwt_secret")


def _jwt_feature_enabled() -> bool:
	"""
	Checks if the JWT feature is enabled.

	Returns:
		bool: True if the JWT feature is enabled, False otherwise.
	"""
	return bool(is_feature_enabled("enable_jwt") or getattr(frappe.flags, "in_test", False))


def issue_jwt_for_user(username: str, expires_in: int | None = None) -> str:
	"""
	Issues a JWT token for a user.

	Args:
		username (str): The user to issue the token for.
		expires_in (int | None, optional): The token's expiration time in seconds. Defaults to None.

	Returns:
		str: The JWT token.
	"""
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
	"""
	Decodes a JWT token.

	Args:
		token (str): The JWT token to decode.
		verify_aud (bool, optional): Whether to verify the token's audience. Defaults to False.

	Returns:
		dict[str, Any]: The decoded token payload.
	"""
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
	"""
	Authenticates a user and issues a JWT token for API usage.

	Args:
		username (str): The user's username.
		password (str): The user's password.
		otp (str | None, optional): The one-time password for 2FA. Defaults to None.

	Returns:
		dict: A dictionary containing the JWT token.
	"""
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


def jwt_before_request() -> None:
	"""
	A hook to authenticate requests using a Bearer JWT token.

	This function is intended to be used as a `before_request` hook. It checks for a
	Bearer token in the Authorization header and, if present and valid, sets the user
	for the current request.

	Guards:
	- The JWT feature must be enabled and a secret key configured.
	- The request path must be within the `/api/method/ferum_custom.*` namespace.
	- If the token has an `aud` (audience) claim, it must be `ferum.api`.
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
	"""
	Retrieves the client's IP address from the request headers.

	This is a best-effort detection that checks for common proxy headers.

	Returns:
		str: The client's IP address.
	"""
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
	"""
	Checks and enforces the rate limit for authentication requests.
	"""
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
