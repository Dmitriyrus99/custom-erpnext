from __future__ import annotations

from typing import Optional

from .frappe_client import FrappeClient

_CLIENT: Optional[FrappeClient] = None


def set_client(client: FrappeClient) -> None:
    global _CLIENT
    _CLIENT = client


def get_client() -> Optional[FrappeClient]:
    return _CLIENT

