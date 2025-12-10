from __future__ import annotations

"""Operational helpers for 2FA administration.

- Reset a user's 2FA (clear TOTP secret and setup flag)
- Generate, list, and consume backup recovery codes (hashed storage)
- Configure/enforce Two-Factor Authentication for roles and methods
"""

import hashlib
import secrets
from typing import Any, Iterable

import frappe
from frappe import _

try:
	# same parent/defaults namespace used by frappe.twofactor
	from frappe.twofactor import PARENT_FOR_DEFAULTS, clear_default, set_default, toggle_two_factor_auth
except Exception:  # pragma: no cover
	PARENT_FOR_DEFAULTS = "__2fa"  # fallback
	clear_default = None  # type: ignore
	toggle_two_factor_auth = None  # type: ignore


BACKUP_CODES_KEY = "{user}_2fa_backup_codes"  # default key in DefaultValue (parent=__2fa)


def _codes_key(user: str) -> str:
	return BACKUP_CODES_KEY.format(user=user)


def _hash_code(raw: str) -> str:
	# Bind to site encryption key if present for stronger secrecy
	key = (frappe.local.conf.get("encryption_key") if getattr(frappe.local, "conf", None) else "") or ""
	return hashlib.sha256((key + ":" + raw).encode("utf-8")).hexdigest()


@frappe.whitelist(methods=["POST"])
def reset_user_2fa(user: str) -> dict:
	"""Clear user's TOTP secret and setup flag so they can re-enroll.

	After reset, with method "OTP App" configured, the user will receive an email
	with QR instructions on next login and can re-bind their authenticator.
	"""
	user = frappe.utils.cstr(user).strip()
	if not user:
		frappe.throw(_("User is required"))

	# Only System Manager can reset others' 2FA
	if "System Manager" not in frappe.get_roles():
		frappe.throw(_("Not permitted"))

	# Clear 2FA defaults used by frappe.twofactor
	try:
		for suffix in ("_otpsecret", "_otplogin"):
			if clear_default:
				clear_default(user + suffix)
		# Also drop cached QR image (best-effort)
		frappe.cache.delete_value(f"qrcode:{user}")
		return {"ok": True}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "reset_user_2fa failed")
		return {"ok": False}


@frappe.whitelist(methods=["POST"])
def generate_backup_codes(user: str, count: int = 10) -> list[str]:
	"""Generate backup recovery codes for a user; returns plaintext list.

	Stores hashed codes under DefaultValue parent=__2fa so only hashes reside in DB.
	Intended for secure delivery (out-of-band) to the user. Admin should store them
	safely and provide on request.
	"""
	if "System Manager" not in frappe.get_roles():
		frappe.throw(_("Not permitted"))

	user = frappe.utils.cstr(user).strip()
	count = max(1, min(int(count or 10), 20))

	# Generate human-readable codes: groups of 4 alphanum, 2 groups
	def _one() -> str:
		return (secrets.token_hex(4).upper())[:8]

	plaintext = [f"{_one()[:4]}-{_one()[4:]}" for _ in range(count)]
	hashed = [{"h": _hash_code(c), "used": False} for c in plaintext]

	set_default(_codes_key(user), frappe.as_json(hashed))
	frappe.db.commit()
	return plaintext


def _load_backup_codes(user: str) -> list[dict[str, Any]]:
	raw = frappe.db.get_default(_codes_key(user), parent=PARENT_FOR_DEFAULTS)
	if not raw:
		return []
	try:
		data = frappe.parse_json(raw)
		return data if isinstance(data, list) else []
	except Exception:
		return []


@frappe.whitelist(methods=["GET"])  # read-only
def list_backup_codes(user: str) -> list[dict[str, Any]]:
	"""Return masked backup codes for admin review (no plaintext)."""
	if "System Manager" not in frappe.get_roles():
		frappe.throw(_("Not permitted"))
	items = _load_backup_codes(user)
	# Mask: show only tail of hash and used flag
	return [{"hash_tail": (i.get("h", "")[-6:]), "used": bool(i.get("used"))} for i in items]


@frappe.whitelist(methods=["POST"])  # state-changing
def consume_backup_code(user: str, code: str) -> dict:
	"""Verify and consume a backup code for a user (admin-assisted).

	If a valid unused code is provided, mark it used and reset user's 2FA to
	allow re-enrollment (email OTP flow will kick in on next login when method
	is set to "OTP App").
	"""
	if "System Manager" not in frappe.get_roles():
		frappe.throw(_("Not permitted"))
	user = frappe.utils.cstr(user).strip()
	code = frappe.utils.cstr(code).strip().upper()
	if not user or not code:
		frappe.throw(_("User and code are required"))

	items = _load_backup_codes(user)
	h = _hash_code(code)
	for item in items:
		if item.get("h") == h and not item.get("used"):
			item["used"] = True
			set_default(_codes_key(user), frappe.as_json(items))
			reset_user_2fa(user)
			frappe.db.commit()
			return {"ok": True, "consumed": True}
	return {"ok": False, "consumed": False}


@frappe.whitelist(methods=["POST"])  # state/config change
def configure_two_factor(method: str = "OTP App", enforce_roles: Iterable[str] | None = None) -> dict:
	"""Enable and configure 2FA globally and enforce for given roles.

	method: "OTP App" or "Email". When using "OTP App", first login triggers an email
	with QR code to set up the authenticator (fallback guidance).
	"""
	if "System Manager" not in frappe.get_roles():
		frappe.throw(_("Not permitted"))
	method = (method or "OTP App").strip()
	try:
		sys = frappe.get_single("System Settings")
		sys.enable_two_factor_auth = 1
		sys.two_factor_method = method
		if not getattr(sys, "otp_issuer_name", None):
			sys.otp_issuer_name = (
				(frappe.get_conf().host_name or frappe.utils.get_url())
				.replace("https://", "")
				.replace("http://", "")
			)
		sys.save(ignore_permissions=True)
		if enforce_roles and toggle_two_factor_auth:
			toggle_two_factor_auth(True, roles=list(enforce_roles))
		return {"ok": True}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "configure_two_factor failed")
		return {"ok": False}
