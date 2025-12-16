from __future__ import annotations  # moved into package 'telegram_bot'

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
import httpx

from .. import state
from ..frappe_client import FrappeClient
from ..keyboards import request_actions
from ferum_custom.ferum_custom.constants import statuses as status_consts

log = logging.getLogger("ferum.telegram.bot")
router = Router()

ACTIVE_STATUSES = status_consts.ACTIVE_STATUSES


class AttachState(StatesGroup):
    """
    Defines the states for the attachment process.

    Attributes:
            waiting_request (State): The state for waiting for a request ID.
    """

    waiting_request = State()


@router.message(F.text.regexp(r"^/start(?:\s|$)"))
async def cmd_start(message: Message) -> None:
    """Handles the /start command."""
    await message.answer(
        "Привет! Доступные команды:\n"
        "• /new <текст> — создать заявку\n"
        "• /my — актуальные заявки (новые/в работе)\n"
        "• /open — открытые\n"
        "• /inwork — в работе\n"
        "• /archive — закрытые\n"
        "• /start_work <ID> — взять в работу\n"
        "• /done <ID> — завершить заявку\n"
        "• Отправьте фото с подписью /attach <ID> чтобы прикрепить к заявке\n"
        "• /objects — список объектов (заготовка)"
    )


@router.message(F.text.startswith("/new"))
async def cmd_new(message: Message, client: FrappeClient | None) -> None:
    """
    Handles the /new command to create a new service request.

    Args:
            message (Message): The incoming message object.
            client (FrappeClient | None): The FrappeClient instance.
    """
    try:
        if client is None:
            client = state.get_client()
        if client is None:
            await message.answer("Сервис пока не готов, попробуйте позже.")
            return
        title = message.text.split(" ", 1)[1].strip() if " " in message.text else "Новая заявка"
        name = await client.create_request(title)
        await message.answer(f"Заявка создана: {name}")
    except Exception as e:
        log.exception("cmd_new failed: %s", e)
        await message.answer("Не удалось создать заявку, попробуйте позже.")


def _is_final_status(status: str | None) -> bool:
    return str(status) in status_consts.FINAL_STATUSES


async def _send_requests_list(
    message: Message,
    client: FrappeClient,
    heading: str,
    statuses: list[str] | None = None,
    limit: int = 15,
    with_actions: bool = True,
) -> None:
    """Fetch and render a compact list of issues with optional action buttons.

    - Merges multiple status buckets without duplicates.
    - Sorts by modified desc to show the freshest items first.
    - Splits into chunks to avoid Telegram 409/413 errors.
    """

    rows: list[dict] = []
    try:
        if not statuses:
            rows = await client.list_requests()
        else:
            seen = set()
            for st in statuses:
                subset = await client.list_requests(status=st)
                for item in subset:
                    name = item.get("name")
                    if name and name in seen:
                        continue
                    seen.add(name)
                    rows.append(item)
        rows.sort(key=lambda x: x.get("modified", ""), reverse=True)
        rows = rows[:limit]
    except Exception:
        log.exception("list_requests failed (statuses=%s)", statuses)
        await message.answer("Не удалось получить список заявок, попробуйте позже.")
        return

    # Safety: drop final statuses when показываем активные/с кнопками
    if with_actions or statuses == list(ACTIVE_STATUSES):
        rows = [r for r in rows if not _is_final_status(r.get("status"))]

    if not rows:
        await message.answer(f"{heading}: заявок нет")
        return

    # Build text in a single message but respect Telegram limits
    lines: list[str] = []
    for idx, r in enumerate(rows, start=1):
        title = (r.get("title") or "—").strip()
        status = r.get("status") or "—"
        name = r.get("name") or "—"
        title_short = title[:90] + ("…" if len(title) > 90 else "")
        lines.append(f"{idx}. {name} — {title_short} — {status}")

    text = f"{heading} (первые {len(lines)}):\n" + "\n".join(lines)

    # Inline actions only for non-final statuses and only when enabled
    keyboard = None
    if with_actions:
        # Show per-line inline actions for each active item (Open/Replied/In Progress)
        keyboard = None  # we send separate messages with per-row buttons below

    # Telegram max text ~4096; split if needed
    chunk_size = 3800
    if with_actions:
        # Send each item separately with inline buttons when actionable, to keep actions per-row
        for r in rows:
            name = r.get("name") or "—"
            title = (r.get("title") or "—").strip()
            status = r.get("status") or "—"
            row_text = f"{name} — {title} — {status}"
            reply_kb = request_actions(name) if not _is_final_status(status) else None
            await message.answer(row_text, reply_markup=reply_kb)
    else:
        for i in range(0, len(text), chunk_size):
            slice_text = text[i : i + chunk_size]
            await message.answer(slice_text)


@router.message(F.text.startswith("/my"))
async def cmd_my(message: Message, client: FrappeClient | None) -> None:
    """List only active requests (Open/Replied/In Progress)."""
    if client is None:
        client = state.get_client()
    if client is None:
        await message.answer("Сервис пока не готов, попробуйте позже.")
        return
    await _send_requests_list(message, client, "Мои заявки", list(ACTIVE_STATUSES), with_actions=True)


@router.message(F.text.startswith("/open"))
async def cmd_open(message: Message, client: FrappeClient | None) -> None:
    """List open requests."""
    if client is None:
        client = state.get_client()
    if client is None:
        await message.answer("Сервис пока не готов, попробуйте позже.")
        return
    await _send_requests_list(message, client, "Открытые", ["Open"])


@router.message(F.text.regexp(r"^/(inwork|in_progress|work)"))
async def cmd_in_work(message: Message, client: FrappeClient | None) -> None:
    """List requests that находятся в работе (Issue=Replied)."""
    if client is None:
        client = state.get_client()
    if client is None:
        await message.answer("Сервис пока не готов, попробуйте позже.")
        return
    await _send_requests_list(message, client, "В работе", ["Replied", "In Progress"])


@router.message(F.text.regexp(r"^/(archive|done|closed)"))
async def cmd_archive(message: Message, client: FrappeClient | None) -> None:
    """List завершённые/закрытые заявки."""
    if client is None:
        client = state.get_client()
    if client is None:
        await message.answer("Сервис пока не готов, попробуйте позже.")
        return
    await _send_requests_list(message, client, "Архив", ["Resolved", "Closed", "Completed"])


@router.message(F.text.startswith("/objects"))
async def cmd_objects(message: Message) -> None:
    """Placeholder for future objects list."""
    await message.answer("Список объектов пока недоступен. Скоро добавим.")


async def _ensure_client_or_reply(message: Message, client: FrappeClient | None) -> FrappeClient | None:
    if client is None:
        client = state.get_client()
    if client is None:
        await message.answer("Сервис пока не готов, попробуйте позже.")
    return client


@router.message(F.text.regexp(r"^/start_work\b"))
async def cmd_start_work(message: Message, client: FrappeClient | None) -> None:
    """Take request/issue into work."""
    client = await _ensure_client_or_reply(message, client)
    if client is None:
        return
    parts = message.text.split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("Используйте: /start_work <ID_ЗАЯВКИ>")
        return
    name = parts[1].strip()
    try:
        resp = await client.update_request_status(name, "In Progress")
        await message.answer(f"{name} — В работе ({resp.get('status')})")
    except Exception as e:
        log.exception("cmd_start_work failed: %s", e)
        await message.answer("Не удалось изменить статус, попробуйте позже.")


@router.message(F.text.regexp(r"^/done\b"))
async def cmd_done(message: Message, client: FrappeClient | None) -> None:
    """Mark request/issue as completed."""
    client = await _ensure_client_or_reply(message, client)
    if client is None:
        return
    parts = message.text.split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("Используйте: /done <ID_ЗАЯВКИ>")
        return
    name = parts[1].strip()
    try:
        resp = await client.update_request_status(name, "Completed")
        await message.answer(f"{name} — Завершена ({resp.get('status')})")
    except Exception as e:
        log.exception("cmd_done failed: %s", e)
        await message.answer("Не удалось изменить статус, попробуйте позже.")


@router.callback_query(F.data.startswith("req:"))
async def on_request_action(cb: CallbackQuery, client: FrappeClient | None) -> None:
    """
    Handles callback queries for request actions (e.g., start, done).

    Args:
            cb (CallbackQuery): The incoming callback query object.
            client (FrappeClient | None): The FrappeClient instance.
    """
    try:
        log.info("callback data=%s from user=%s", cb.data, cb.from_user.id if cb.from_user else "-")
        if client is None:
            client = state.get_client()
        if client is None:
            await cb.answer("Сервис не готов", show_alert=True)
            return
        try:
            _, name, action = cb.data.split(":", 2)
        except Exception:
            await cb.answer("Неверное действие", show_alert=True)
            return
        if action == "start":
            resp = await client.update_request_status(name, "In Progress")
            await cb.message.edit_text(f"{name} — В работе ({resp.get('status')})")
        elif action == "done":
            resp = await client.update_request_status(name, "Completed")
            await cb.message.edit_text(f"{name} — Завершена ({resp.get('status')})")
        else:
            await cb.answer("Неизвестное действие", show_alert=True)
            return
        await cb.answer("OK")
    except Exception as e:
        log.exception("on_request_action failed: %s", e)
        try:
            await cb.answer("Ошибка", show_alert=True)
        except Exception:
            pass
        try:
            await cb.message.reply("Не удалось выполнить действие, попробуйте позже.")
        except Exception:
            pass


@router.message(F.photo)
async def on_photo(message: Message, client: FrappeClient | None) -> None:
    """
    Handles incoming photos and attaches them to a service request.

    Args:
            message (Message): The incoming message object containing the photo.
            client (FrappeClient | None): The FrappeClient instance.
    """
    try:
        if client is None:
            client = state.get_client()
        if client is None:
            await message.answer("Сервис пока не готов, попробуйте позже.")
            return
        caption = (message.caption or "").strip()
        if not caption.startswith("/attach"):
            # ignore non-command photos
            return
        if " " not in caption:
            await message.answer("Используйте: пришлите фото с подписью '/attach <ID_ЗАЯВКИ>'")
            return
        req = caption.split(" ", 1)[1].strip()
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        # Download via Bot API
        content = await message.bot.download_file(file.file_path)
        content_bytes = content.read()
        file_name = file.file_path.split("/")[-1]
        await client.attach_to_request(req, file_name, content_bytes, "image/jpeg")
        await message.answer(f"Фото прикреплено к {req}")
    except httpx.HTTPStatusError as e:
        # Provide clearer feedback when backend rejects the upload
        msg = ""
        try:
            payload = e.response.json()
            msg = payload.get("message") or payload.get("exc") or ""
        except Exception:
            msg = str(e)
        log.exception("on_photo failed (HTTP %s): %s", e.response.status_code, msg)
        hint = f" ({msg})" if msg else ""
        await message.answer(f"Не удалось прикрепить фото{hint}")
    except Exception as e:
        log.exception("on_photo failed: %s", e)
        await message.answer("Не удалось прикрепить фото. Попробуйте позже.")


@router.message(F.text.startswith("/attach"))
async def attach_usage_text(message: Message) -> None:
    """
    Handles the /attach command without a photo to provide usage instructions.

    Args:
            message (Message): The incoming message object.
    """
    # Handle text-only '/attach' to guide user
    await message.answer("Пришлите фото с подписью '/attach <ID_ЗАЯВКИ>'")


@router.message(F.text.regexp(r"^/"))
async def unknown_command(message: Message) -> None:
    """
    Handles any unrecognized commands.

    Args:
            message (Message): The incoming message object.
    """
    # Fallback for any unrecognized slash command
    await message.answer(
        "Неизвестная команда. Доступно: /start, /new <текст>, /my, /open, /inwork, /archive, "
        "/start_work <ID>, /done <ID>. Фото: отправьте фото с подписью '/attach <ID_ЗАЯВКИ>'."
    )
