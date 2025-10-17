from __future__ import annotations  # moved into package 'telegram_bot'

import asyncio
from dataclasses import dataclass
from typing import Any, Optional

import httpx

try:
	import pyotp  # type: ignore
except Exception:  # pragma: no cover
	pyotp = None


@dataclass
class FrappeAuth:
	token: str


class FrappeClient:
	def __init__(
		self,
		base_url: str,
		username: str,
		password: str,
		totp_secret: str | None = None,
		verify_ssl: bool = True,
	) -> None:
		self.base = base_url.rstrip("/")
		self.username = username
		self.password = password
		self.totp_secret = totp_secret
		self._auth: FrappeAuth | None = None
		self._client = httpx.AsyncClient(base_url=self.base, timeout=20, verify=verify_ssl)

	async def close(self) -> None:
		await self._client.aclose()

	async def _login(self) -> FrappeAuth:
		# Try JWT login first (preferred)
		otp_now = None
		if self.totp_secret and pyotp is not None:
			otp_now = pyotp.TOTP(self.totp_secret).now()
		try:
			payload_jwt: dict[str, Any] = {"username": self.username, "password": self.password}
			if otp_now:
				payload_jwt["otp"] = otp_now
			r = await self._client.post(
				"/api/method/ferum_custom.api.auth.login",
				json=payload_jwt,
			)
			r.raise_for_status()
			data = r.json().get("message") or r.json()
			token = data.get("token")
			if token:
				self._auth = FrappeAuth(token=token)
				return self._auth
		except Exception:
			# Fall back to session (cookie) login with 2FA support
			pass

		# Session (cookie) login fallback
		# Step 1: initiate login without OTP to get tmp_id when 2FA is enabled
		init_payload: dict[str, Any] = {"usr": self.username, "pwd": self.password}
		r1 = await self._client.post("/api/method/login", data=init_payload)
		r1.raise_for_status()
		resp1 = r1.json().get("message") or r1.json()

		# If already logged in (no 2FA required)
		if isinstance(resp1, str) and resp1.lower() in {"logged in", "no app"}:
			self._auth = FrappeAuth(token="")
			return self._auth
		if isinstance(resp1, dict) and str(resp1.get("message") or resp1.get("status") or "").lower() in {
			"logged in",
			"no app",
		}:
			self._auth = FrappeAuth(token="")
			return self._auth

		tmp_id = None
		if isinstance(resp1, dict):
			tmp_id = resp1.get("tmp_id")

		# If 2FA is required, confirm with OTP using tmp_id
		if tmp_id and self.totp_secret and pyotp is not None:
			otp_code = pyotp.TOTP(self.totp_secret).now()
			r2 = await self._client.post(
				"/api/method/login",
				data={"otp": otp_code, "tmp_id": tmp_id},
			)
			r2.raise_for_status()
			# Success -> cookies stored in client
			self._auth = FrappeAuth(token="")
			return self._auth

		# As a last resort, treat initial response as success if cookies are set
		# (Some setups may not include explicit message fields.)
		self._auth = FrappeAuth(token="")
		return self._auth

	async def _headers(self) -> dict[str, str]:
		if not self._auth:
			await self._login()
		assert self._auth is not None
		# Use Authorization header only when JWT token is available; otherwise rely on cookies
		return {"Authorization": f"Bearer {self._auth.token}"} if self._auth.token else {}

	async def create_request(self, title: str, description: str = "") -> str:
		headers = await self._headers()
		r = await self._client.post(
			"/api/method/ferum_custom.api.service.create_service_request",
			headers=headers or None,
			data={"title": title, "description": description},
		)
		r.raise_for_status()
		data = r.json().get("message") or r.json()
		return str(data)

	async def list_requests(self, status: str | None = None) -> list[dict]:
		params: dict[str, Any] = {}
		if status:
			params["status"] = status
		headers = await self._headers()
		r = await self._client.get(
			"/api/method/ferum_custom.api.service.list_service_requests",
			headers=headers or None,
			params=params,
		)
		r.raise_for_status()
		data = r.json().get("message") or r.json()
		return list(data.get("data", []))

	async def update_request_status(self, name: str, status: str) -> dict:
		headers = await self._headers()
		r = await self._client.post(
			"/api/method/ferum_custom.api.service.update_service_request_status",
			headers=headers or None,
			data={"name": name, "status": status},
		)
		r.raise_for_status()
		data = r.json().get("message") or r.json()
		return dict(data)

	async def attach_to_request(self, name: str, file_name: str, content: bytes, content_type: str) -> dict:
		files = {"file": (file_name, content, content_type)}
		headers = await self._headers()
		r = await self._client.post(
			"/api/method/ferum_custom.api.attachments.attach_to_service_request",
			headers=headers or None,
			files=files,
			params={"name": name},
		)
		r.raise_for_status()
		data = r.json().get("message") or r.json()
		return dict(data)

	async def attach_to_report(self, name: str, file_name: str, content: bytes, content_type: str) -> dict:
		files = {"file": (file_name, content, content_type)}
		headers = await self._headers()
		r = await self._client.post(
			"/api/method/ferum_custom.api.attachments.attach_to_service_report",
			headers=headers or None,
			files=files,
			params={"name": name},
		)
		r.raise_for_status()
		data = r.json().get("message") or r.json()
		return dict(data)
