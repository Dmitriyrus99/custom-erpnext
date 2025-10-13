from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
try:
    import pyotp  # type: ignore
except Exception:  # pragma: no cover
    pyotp = None


@dataclass
class FrappeAuth:
    token: str


class FrappeClient:
    def __init__(self, base_url: str, username: str, password: str, totp_secret: str | None = None, verify_ssl: bool = True) -> None:
        self.base = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.totp_secret = totp_secret
        self._auth: Optional[FrappeAuth] = None
        self._client = httpx.AsyncClient(base_url=self.base, timeout=20, verify=verify_ssl)

    async def close(self) -> None:
        await self._client.aclose()

    async def _login(self) -> FrappeAuth:
        payload: Dict[str, Any] = {"username": self.username, "password": self.password}
        if self.totp_secret and pyotp is not None:
            payload["otp"] = pyotp.TOTP(self.totp_secret).now()
        r = await self._client.post(
            "/api/method/ferum_custom.api.auth.login",
            data=payload,
        )
        r.raise_for_status()
        data = r.json().get("message") or r.json()
        token = data.get("token")
        if not token:
            raise RuntimeError("No JWT token from auth.login")
        self._auth = FrappeAuth(token=token)
        return self._auth

    async def _headers(self) -> Dict[str, str]:
        if not self._auth:
            await self._login()
        assert self._auth is not None
        return {"Authorization": f"Bearer {self._auth.token}"}

    async def create_request(self, title: str, description: str = "") -> str:
        r = await self._client.post(
            "/api/method/ferum_custom.api.service.create_service_request",
            headers=await self._headers(),
            data={"title": title, "description": description},
        )
        r.raise_for_status()
        data = r.json().get("message") or r.json()
        return str(data)

    async def list_requests(self, status: Optional[str] = None) -> list[dict]:
        params: Dict[str, Any] = {}
        if status:
            params["status"] = status
        r = await self._client.get(
            "/api/method/ferum_custom.api.service.list_service_requests",
            headers=await self._headers(),
            params=params,
        )
        r.raise_for_status()
        data = r.json().get("message") or r.json()
        return list(data.get("data", []))

    async def update_request_status(self, name: str, status: str) -> dict:
        r = await self._client.post(
            "/api/method/ferum_custom.api.service.update_service_request_status",
            headers=await self._headers(),
            data={"name": name, "status": status},
        )
        r.raise_for_status()
        data = r.json().get("message") or r.json()
        return dict(data)

    async def attach_to_request(self, name: str, file_name: str, content: bytes, content_type: str) -> dict:
        files = {"file": (file_name, content, content_type)}
        r = await self._client.post(
            "/api/method/ferum_custom.api.attachments.attach_to_service_request",
            headers=await self._headers(),
            files=files,
            params={"name": name},
        )
        r.raise_for_status()
        data = r.json().get("message") or r.json()
        return dict(data)

    async def attach_to_report(self, name: str, file_name: str, content: bytes, content_type: str) -> dict:
        files = {"file": (file_name, content, content_type)}
        r = await self._client.post(
            "/api/method/ferum_custom.api.attachments.attach_to_service_report",
            headers=await self._headers(),
            files=files,
            params={"name": name},
        )
        r.raise_for_status()
        data = r.json().get("message") or r.json()
        return dict(data)
