from __future__ import annotations

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from ..frappe_client import FrappeClient
from ..keyboards import request_actions


router = Router()


class AttachState(StatesGroup):
    waiting_request = State()


@router.message(F.text.startswith("/start"))
async def cmd_start(message: Message) -> None:
    await message.answer("Hello! Use /new <title>, /my, or send a photo with caption /attach <REQ>.")


@router.message(F.text.startswith("/new"))
async def cmd_new(message: Message, client: FrappeClient) -> None:
    title = message.text.split(" ", 1)[1].strip() if " " in message.text else "New Request"
    name = await client.create_request(title)
    await message.answer(f"Request created: {name}")


@router.message(F.text.startswith("/my"))
async def cmd_my(message: Message, client: FrappeClient) -> None:
    rows = await client.list_requests()
    if not rows:
        await message.answer("No requests")
        return
    for r in rows[:10]:
        text = f"{r['name']} — {r['title']} — {r['status']}"
        await message.answer(text, reply_markup=request_actions(r["name"]))


@router.callback_query(F.data.startswith("req:"))
async def on_request_action(cb: CallbackQuery, client: FrappeClient) -> None:
    try:
        _, name, action = cb.data.split(":", 2)
    except Exception:
        await cb.answer("Bad action", show_alert=True)
        return
    if action == "start":
        res = await client.update_request_status(name, "In Progress")
        await cb.message.edit_text(f"{name} — In Progress")
    elif action == "done":
        res = await client.update_request_status(name, "Completed")
        await cb.message.edit_text(f"{name} — Completed")
    else:
        await cb.answer("Unknown", show_alert=True)
        return
    await cb.answer("OK")


@router.message(F.photo)
async def on_photo(message: Message, client: FrappeClient) -> None:
    caption = (message.caption or "").strip()
    if not caption.startswith("/attach") or " " not in caption:
        # ignore non-command photos
        return
    req = caption.split(" ", 1)[1].strip()
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    # Download via Bot API
    content = await message.bot.download_file(file.file_path)
    content_bytes = content.read()
    file_name = file.file_path.split("/")[-1]
    await client.attach_to_request(req, file_name, content_bytes, "image/jpeg")
    await message.answer(f"Photo attached to {req}")

