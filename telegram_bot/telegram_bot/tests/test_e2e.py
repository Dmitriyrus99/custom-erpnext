from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Message

from ferum_custom.telegram_bot.telegram_bot.frappe_client import FrappeClient
from ferum_custom.telegram_bot.telegram_bot.handlers import requests as requests_handlers


@pytest.fixture
def mock_frappe_client() -> FrappeClient:
    client = MagicMock(spec=FrappeClient)
    client.close = AsyncMock()
    client.create_request = AsyncMock(return_value="ISSUE-001")
    client.list_requests = AsyncMock(
        return_value=[
            {
                "name": "ISSUE-001",
                "title": "Test Issue 1",
                "status": "Open",
                "modified": "2023-01-01",
            },
            {
                "name": "ISSUE-002",
                "title": "Test Issue 2",
                "status": "In Progress",
                "modified": "2023-01-02",
            },
        ]
    )
    client.update_request_status = AsyncMock(
        return_value={"name": "ISSUE-001", "status": "In Progress"}
    )
    client.attach_to_request = AsyncMock(return_value={})
    return client


@pytest.fixture
async def setup_dispatcher_and_client(mock_frappe_client):
    dp = requests_handlers.router
    dp.workflow_data["frappe_client"] = mock_frappe_client
    with patch(
        "ferum_custom.telegram_bot.telegram_bot.state.get_client", return_value=mock_frappe_client
    ):
        yield dp, mock_frappe_client


@pytest.mark.asyncio
async def test_cmd_start(setup_dispatcher_and_client):
    dp, _ = setup_dispatcher_and_client
    message = AsyncMock(spec=Message)
    message.text = "/start"
    await dp.message.trigger(message)
    message.answer.assert_called_once()
    assert "Привет! Доступные команды:" in message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_cmd_new(setup_dispatcher_and_client):
    dp, client = setup_dispatcher_and_client
    message = AsyncMock(spec=Message)
    message.text = "/new Тестовая заявка"
    await dp.message.trigger(message)
    client.create_request.assert_called_once_with("Тестовая заявка")
    message.answer.assert_called_once_with("Заявка создана: ISSUE-001")


@pytest.mark.asyncio
async def test_cmd_my(setup_dispatcher_and_client):
    dp, client = setup_dispatcher_and_client
    message = AsyncMock(spec=Message)
    message.text = "/my"
    await dp.message.trigger(message)
    client.list_requests.assert_called_once_with(status=["Open", "Replied", "In Progress"])
    # Expecting two messages, one for each issue, with action buttons
    assert message.answer.call_count == 2
    assert "ISSUE-001" in message.answer.call_args_list[0][0][0]
    assert "ISSUE-002" in message.answer.call_args_list[1][0][0]


@pytest.mark.asyncio
async def test_cmd_start_work(setup_dispatcher_and_client):
    dp, client = setup_dispatcher_and_client
    message = AsyncMock(spec=Message)
    message.text = "/start_work ISSUE-001"
    await dp.message.trigger(message)
    client.update_request_status.assert_called_once_with("ISSUE-001", "In Progress")
    message.answer.assert_called_once_with("ISSUE-001 — В работе (In Progress)")


@pytest.mark.asyncio
async def test_cmd_done(setup_dispatcher_and_client):
    dp, client = setup_dispatcher_and_client
    message = AsyncMock(spec=Message)
    message.text = "/done ISSUE-001"
    await dp.message.trigger(message)
    client.update_request_status.assert_called_once_with("ISSUE-001", "Completed")
    message.answer.assert_called_once_with(
        "ISSUE-001 — Завершена (In Progress)"
    )  # Note: mock returns 'In Progress'


@pytest.mark.asyncio
async def test_on_photo_attach(setup_dispatcher_and_client):
    dp, client = setup_dispatcher_and_client
    message = AsyncMock(spec=Message)
    message.photo = [MagicMock(file_id="photo_id_123")]
    message.caption = "/attach ISSUE-001"
    message.bot.get_file = AsyncMock(return_value=MagicMock(file_path="photos/file.jpg"))
    message.bot.download_file = AsyncMock(return_value=MagicMock(read=lambda: b"fake_image_bytes"))

    await dp.message.trigger(message)

    message.bot.get_file.assert_called_once_with("photo_id_123")
    message.bot.download_file.assert_called_once_with("photos/file.jpg")
    client.attach_to_request.assert_called_once_with(
        "ISSUE-001", "file.jpg", b"fake_image_bytes", "image/jpeg"
    )
    message.answer.assert_called_once_with("Фото прикреплено к ISSUE-001")
