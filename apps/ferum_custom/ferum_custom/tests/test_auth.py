from __future__ import annotations

import types

import pytest

from ferum_custom.api import auth


@pytest.fixture(autouse=True)
def _no_rate_limit(monkeypatch):
    monkeypatch.setattr(auth, "_check_auth_rate_limit", lambda: None)


@pytest.fixture
def dummy_login_manager(monkeypatch):
    calls: dict[str, object] = {}

    class _DummyLoginManager:
        def __init__(self):
            calls.setdefault("init", 0)
            calls["init"] += 1

        def authenticate(self, user: str, pwd: str) -> None:
            calls["auth"] = (user, pwd)

        def post_login(self) -> None:
            calls["post_login"] = True

    monkeypatch.setattr(auth.frappe, "auth", types.SimpleNamespace(LoginManager=_DummyLoginManager))
    return calls


def test_login_requires_otp_when_two_factor_enabled(monkeypatch, dummy_login_manager):
    monkeypatch.setattr(auth, "two_factor_is_enabled", lambda user: True)
    monkeypatch.setattr(auth, "get_verification_method", lambda: "OTP App")
    monkeypatch.setattr(auth, "get_otpsecret_for_", lambda user: "SECRET")
    monkeypatch.setattr(
        auth,
        "pyotp",
        types.SimpleNamespace(TOTP=lambda secret: types.SimpleNamespace(verify=lambda _: True)),
    )
    monkeypatch.setattr(
        auth, "jwt", types.SimpleNamespace(encode=lambda payload, secret, algorithm=None: "token")
    )
    monkeypatch.setattr(auth, "get_setting", lambda key: "secret" if key == "jwt_secret" else None)

    with pytest.raises(auth.frappe.ValidationError):
        auth.login("user@example.com", "pass")

    assert dummy_login_manager["auth"] == ("user@example.com", "pass")
    assert "post_login" not in dummy_login_manager


def test_login_with_valid_otp(monkeypatch, dummy_login_manager):
    monkeypatch.setattr(auth, "two_factor_is_enabled", lambda user: True)
    monkeypatch.setattr(auth, "get_verification_method", lambda: "OTP App")
    monkeypatch.setattr(auth, "get_otpsecret_for_", lambda user: "SECRET")

    class _FakeTotp:
        def __init__(self, secret: str) -> None:
            self.secret = secret

        def verify(self, code: str) -> bool:
            return self.secret == "SECRET" and code == "123456"

    monkeypatch.setattr(auth, "pyotp", types.SimpleNamespace(TOTP=_FakeTotp))
    monkeypatch.setattr(
        auth,
        "jwt",
        types.SimpleNamespace(
            encode=lambda payload, secret, algorithm=None: f"jwt::{payload['sub']}"
        ),
    )
    monkeypatch.setattr(
        auth, "get_setting", lambda key: "shared-secret" if key == "jwt_secret" else None
    )

    result = auth.login("user@example.com", "pass", otp="123456")

    assert result == {"token": "jwt::user@example.com"}
    assert dummy_login_manager["post_login"] is True


def test_login_rejects_unsupported_two_factor_method(monkeypatch, dummy_login_manager):
    monkeypatch.setattr(auth, "two_factor_is_enabled", lambda user: True)
    monkeypatch.setattr(auth, "get_verification_method", lambda: "Email")
    monkeypatch.setattr(auth, "get_otpsecret_for_", lambda user: "SECRET")
    monkeypatch.setattr(
        auth, "jwt", types.SimpleNamespace(encode=lambda payload, secret, algorithm=None: "token")
    )
    monkeypatch.setattr(auth, "get_setting", lambda key: "secret" if key == "jwt_secret" else None)

    with pytest.raises(auth.frappe.ValidationError):
        auth.login("user@example.com", "pass", otp="123456")

    assert "post_login" not in dummy_login_manager
