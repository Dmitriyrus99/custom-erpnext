from __future__ import annotations  # moved into package 'telegram_bot'

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from .. import state
from ..frappe_client import FrappeClient
from ..keyboards import request_actions

log = logging.getLogger("ferum.telegram.bot")
router = Router()


class AttachState(StatesGroup):
	"""
	Defines the states for the attachment process.

	Attributes:
		waiting_request (State): The state for waiting for a request ID.
	"""

	waiting_request = State()


@router.message(F.text.startswith("/start"))
async def cmd_start(message: Message) -> None:
	"""
	Handles the /start command.

	Args:
		message (Message): The incoming message object.
	"""
	await message.answer("Hello! Use /new <title>, /my, or send a photo with caption /attach <REQ>.")


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
			await message.answer("Service is not ready yet, please try again.")
			return
		title = message.text.split(" ", 1)[1].strip() if " " in message.text else "New Request"
		name = await client.create_request(title)
		await message.answer(f"Request created: {name}")
	except Exception as e:
		log.exception("cmd_new failed: %s", e)
		await message.answer("Failed to create request. Please try later.")


@router.message(F.text.startswith("/my"))
async def cmd_my(message: Message, client: FrappeClient | None) -> None:
	"""
	Handles the /my command to list the user's service requests.

	Args:
		message (Message): The incoming message object.
		client (FrappeClient | None): The FrappeClient instance.
	"""
	try:
		if client is None:
			client = state.get_client()
		if client is None:
			await message.answer("Service is not ready yet, please try again.")
			return
		rows = await client.list_requests()
		if not rows:
			await message.answer("No requests")
			return
		for r in rows[:10]:
			title = r.get("title") or "—"
			status = r.get("status") or "—"
			name = r.get("name") or "—"
			text = f"{name} — {title} — {status}"
			await message.answer(text, reply_markup=request_actions(name))
	except Exception as e:
		log.exception("cmd_my failed: %s", e)
		await message.answer("Failed to fetch requests. Please try later.")


@router.callback_query(F.data.startswith("req:"))
async def on_request_action(cb: CallbackQuery, client: FrappeClient | None) -> None:
	"""
	Handles callback queries for request actions (e.g., start, done).

	Args:
		cb (CallbackQuery): The incoming callback query object.
		client (FrappeClient | None): The FrappeClient instance.
	"""
	try:
		if client is None:
			client = state.get_client()
		if client is None:
			await cb.answer("Service not ready", show_alert=True)
			return
		try:
			_, name, action = cb.data.split(":", 2)
		except Exception:
			await cb.answer("Bad action", show_alert=True)
			return
		if action == "start":
			await client.update_request_status(name, "In Progress")
			await cb.message.edit_text(f"{name} — In Progress")
		elif action == "done":
			await client.update_request_status(name, "Completed")
			await cb.message.edit_text(f"{name} — Completed")
		else:
			await cb.answer("Unknown", show_alert=True)
			return
		await cb.answer("OK")
	except Exception as e:
		log.exception("on_request_action failed: %s", e)
		await cb.answer("Failed", show_alert=True)


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
			await message.answer("Service is not ready yet, please try again.")
			return
		caption = (message.caption or "").strip()
		if not caption.startswith("/attach"):
			# ignore non-command photos
			return
		if " " not in caption:
			await message.answer("Usage: send a photo with caption '/attach <REQUEST_ID>'")
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
	except Exception as e:
		log.exception("on_photo failed: %s", e)
		await message.answer("Failed to attach photo. Please try later.")


@router.message(F.text.startswith("/attach"))
async def attach_usage_text(message: Message) -> None:
	"""
	Handles the /attach command without a photo to provide usage instructions.

	Args:
		message (Message): The incoming message object.
	"""
	# Handle text-only '/attach' to guide user
	await message.answer("Usage: send a photo with caption '/attach <REQUEST_ID>'")


@router.message(F.text.regexp(r"^/"))
async def unknown_command(message: Message) -> None:
	"""
	Handles any unrecognized commands.

	Args:
		message (Message): The incoming message object.
	"""
	# Fallback for any unrecognized slash command
	await message.answer(
		"Unknown command. Available: /start, /new <title>, /my. To attach a photo: send a photo with caption '/attach <REQUEST_ID>'."
	)
