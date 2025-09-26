from __future__ import annotations

import pytest

from ferum_custom.api import telegram_bot as bot


def test_split_command_extracts_command_and_argument():
	command, argument = bot._split_command("/new_request Title")
	assert command == "/new_request"
	assert argument == "Title"


def test_split_command_without_prefix_returns_none():
	command, argument = bot._split_command("hello world")
	assert command is None
	assert argument == "hello world"


def test_handle_photo_payload_invokes_attachment(monkeypatch):
	called = {}
	ctx = bot.TelegramContext(
		payload={"message": {"photo": [{}], "caption": "/attach REQ-1"}},
		chat_id="1",
		text="",
		command=None,
		argument="",
		user=None,
	)

	monkeypatch.setattr(bot, "_attach_photo", lambda context, req: called.setdefault("req", req))

	assert bot._handle_photo_payload(ctx) is True
	assert called["req"] == "REQ-1"


def test_handle_photo_payload_requires_request_name():
	ctx = bot.TelegramContext(
		payload={"message": {"photo": [{}], "caption": "/attach"}},
		chat_id="1",
		text="",
		command=None,
		argument="",
		user=None,
	)

	with pytest.raises(bot.CommandError):
		bot._handle_photo_payload(ctx)


def test_dispatch_unknown_command_replies(monkeypatch):
	messages: list[str] = []
	monkeypatch.setattr(bot, "_reply", lambda chat_id, text: messages.append(text))
	ctx = bot.TelegramContext(
		payload={},
		chat_id="1",
		text="/unknown",
		command="/unknown",
		argument="",
		user=None,
	)

	bot._dispatch_command(ctx)
	assert messages, "reply should be sent for unknown command"
