from __future__ import annotations

from ferum_custom.ferum_custom.api import telegram_bot as telegram_api
from ferum_custom.ferum_custom.integrations import telegram


def test_send_message_disabled(monkeypatch):
	monkeypatch.setattr(telegram, "is_feature_enabled", lambda flag: False)
	assert telegram.send_message("hi", chat_id="123") is False


def test_is_chat_allowed_with_allowlist(monkeypatch):
	monkeypatch.setattr(telegram, "get_list_setting", lambda key: ["111"])
	monkeypatch.setattr(
		telegram,
		"get_setting",
		lambda key, default=None: "111" if key == "telegram_default_chat_id" else None,
	)
	assert telegram.is_chat_allowed("111") is True
	assert telegram.is_chat_allowed("222") is False


def test_is_admin_with_config(monkeypatch):
	monkeypatch.setattr(
		telegram, "get_list_setting", lambda key: ["Boss"] if key == "telegram_admin_usernames" else []
	)
	assert telegram.is_admin("Boss") is True
	assert telegram.is_admin("boss") is True
	assert telegram.is_admin("other") is False


def test_send_message_respects_allowlist(monkeypatch):
	monkeypatch.setattr(telegram, "is_feature_enabled", lambda flag: True)
	monkeypatch.setattr(
		telegram,
		"get_setting",
		lambda key, default=None: {
			"telegram_bot_token": "token",
			"telegram_default_chat_id": "999",
		}.get(key),
	)
	monkeypatch.setattr(telegram, "get_list_setting", lambda key: ["999"])

	class StubRequests:
		def __init__(self):
			self.calls = 0

		def post(self, *args, **kwargs):
			self.calls += 1

			class Resp:
				ok = True

				def json(self):
					return {"ok": True}

			return Resp()

	stub = StubRequests()
	monkeypatch.setattr(telegram, "requests", stub)

	assert telegram.send_message("ping", chat_id="888") is False
	assert stub.calls == 0


def test_send_message_success(monkeypatch):
	monkeypatch.setattr(telegram, "is_feature_enabled", lambda flag: True)
	monkeypatch.setattr(
		telegram,
		"get_setting",
		lambda key, default=None: {
			"telegram_bot_token": "token",
			"telegram_default_chat_id": "123",
		}.get(key),
	)
	monkeypatch.setattr(telegram, "get_list_setting", lambda key: [])

	class StubRequests:
		def __init__(self):
			self.calls = 0

		def post(self, *args, **kwargs):
			self.calls += 1

			class Resp:
				ok = True

				def json(self_inner):
					return {"ok": True}

			return Resp()

	stub = StubRequests()
	monkeypatch.setattr(telegram, "requests", stub)

	assert telegram.send_message("hello", chat_id="123") is True
	assert stub.calls == 1


def test_telegram_healthcheck_success(monkeypatch):
	monkeypatch.setattr(telegram, "is_feature_enabled", lambda flag: True)
	monkeypatch.setattr(telegram, "get_list_setting", lambda key: [])

	class FakeResponse:
		ok = True

		def json(self):
			return {"ok": True, "result": {"username": "ferum_bot", "id": 42}}

	class FakeRequests:
		def get(self, url, timeout):
			assert "getMe" in url
			return FakeResponse()

	monkeypatch.setattr(telegram, "requests", FakeRequests())
	monkeypatch.setattr(
		telegram,
		"get_setting",
		lambda key, default=None: {
			"telegram_bot_token": "token",
			"telegram_default_chat_id": "123",
		}.get(key),
	)

	result = telegram.healthcheck()
	assert result["status"] == "ok"
	assert result["details"]["username"] == "ferum_bot"


def test_telegram_healthcheck_missing_token(monkeypatch):
	monkeypatch.setattr(telegram, "is_feature_enabled", lambda flag: True)
	monkeypatch.setattr(telegram, "requests", object())
	monkeypatch.setattr(
		telegram,
		"get_setting",
		lambda key, default=None: None,
	)
	result = telegram.healthcheck()
	assert result["status"] == "error"
	assert "token" in result["message"].lower()


def test_telegram_api_health(monkeypatch):
	monkeypatch.setattr(telegram, "healthcheck", lambda: {"status": "ok", "details": {"username": "bot"}})
	result = telegram_api.health()
	assert result["status"] == "ok"
	assert result["details"]["username"] == "bot"
