from __future__ import annotations  # moved into package 'telegram_bot'

import asyncio
import logging
import os
from contextlib import asynccontextmanager

import sentry_sdk
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from prometheus_client import Counter, start_http_server

from . import state
from .config import load
from .frappe_client import FrappeClient
from .handlers import requests as requests_handlers

log = logging.getLogger("ferum.telegram.bot")

METRICS_ENABLED = True
REQ_CREATED = Counter("ferum_tg_requests_created", "Requests created via bot")
PHOTO_ATTACHED = Counter("ferum_tg_photos_attached", "Photos attached via bot")


@asynccontextmanager
async def lifespan(dp: Dispatcher):
	"""
	An asynchronous context manager for managing the lifespan of the dispatcher.

	Note:
		This is kept for compatibility, but the client is initialized explicitly in the run_* paths.

	Args:
		dp (Dispatcher): The aiogram dispatcher instance.
	"""
	# Kept for compatibility, but we initialise client explicitly in run_* paths
	yield


def _wire_dependencies(dp: Dispatcher) -> None:
	"""
	Injects the FrappeClient into the handlers via middleware.

	This function sets up middleware to inject the FrappeClient into the data dictionary of message and callback query handlers.

	Args:
		dp (Dispatcher): The aiogram dispatcher instance.
	"""
	# Provide FrappeClient to handlers via dependency injection

	@dp.message.middleware()
	async def inject_client(handler, event, data):  # type: ignore[no-redef]
		# Retrieve client from dispatcher workflow_data where lifespan stored it
		data["client"] = dp.workflow_data.get("frappe_client")
		return await handler(event, data)

	@dp.callback_query.middleware()
	async def inject_client_cb(handler, event, data):  # type: ignore[no-redef]
		data["client"] = dp.workflow_data.get("frappe_client")
		return await handler(event, data)


async def _set_bot_commands(bot: Bot) -> None:
	"""Register bot command menu in RU (and default)."""
	commands = [
		BotCommand(command="start", description="Справка и команды"),
		BotCommand(command="new", description="Создать заявку"),
		BotCommand(command="my", description="Мои заявки"),
		BotCommand(command="objects", description="Объекты"),
	]
	try:
		await bot.set_my_commands(commands, scope=BotCommandScopeDefault(), language_code="ru")
		await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
	except Exception as e:
		log.warning("set_my_commands failed: %s", e)


async def run_polling() -> None:
	"""
	Initializes and runs the bot in polling mode.

	This function sets up Sentry and Prometheus if configured, initializes the bot and dispatcher,
	and starts polling for updates. It also ensures the FrappeClient is properly closed on exit.
	"""
	settings = load()
	if settings.sentry_dsn:
		sentry_sdk.init(settings.sentry_dsn, traces_sample_rate=0.1)
	if settings.prometheus_port:
		start_http_server(settings.prometheus_port)

	# Use plain text by default to avoid HTML parsing issues
	bot = Bot(token=settings.bot_token)
	dp = Dispatcher(lifespan=lifespan)
	dp.include_router(requests_handlers.router)
	_wire_dependencies(dp)
	# Explicitly initialise ERP client here for reliability
	settings = load()
	client = FrappeClient(
		settings.frappe_base,
		settings.frappe_username,
		settings.frappe_password,
		api_key=settings.frappe_api_key,
		api_secret=settings.frappe_api_secret,
		totp_secret=settings.bot_totp_secret,
		verify_ssl=settings.verify_ssl,
	)
	dp.workflow_data["frappe_client"] = client
	state.set_client(client)
	await _set_bot_commands(bot)
	try:
		await dp.start_polling(bot)
	finally:
		await client.close()


async def run_webhook() -> None:
	"""
	Initializes and runs the bot in webhook mode.

	This function sets up Sentry and Prometheus if configured, initializes the bot and dispatcher,
	and starts a web server to handle incoming webhooks from Telegram. It also sets up a health check endpoint.
	"""
	settings = load()
	if settings.sentry_dsn:
		sentry_sdk.init(settings.sentry_dsn, traces_sample_rate=0.1)
	if settings.prometheus_port:
		start_http_server(settings.prometheus_port)

	# Use plain text by default to avoid HTML parsing issues
	bot = Bot(token=settings.bot_token)
	dp = Dispatcher(lifespan=lifespan)
	dp.include_router(requests_handlers.router)
	_wire_dependencies(dp)
	# Explicitly initialise ERP client here for reliability
	client = FrappeClient(
		settings.frappe_base,
		settings.frappe_username,
		settings.frappe_password,
		api_key=settings.frappe_api_key,
		api_secret=settings.frappe_api_secret,
		totp_secret=settings.bot_totp_secret,
		verify_ssl=settings.verify_ssl,
	)
	dp.workflow_data["frappe_client"] = client
	state.set_client(client)
	app = web.Application()
	webhook_path = "/tg-bot/webhook"
	handler = SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=settings.webhook_secret or None)
	handler.register(app, path=webhook_path)
	setup_application(app, dp, bot=bot)

	# Optionally: expose /healthz
	async def healthz(_: web.Request) -> web.Response:
		return web.Response(text="ok")

	app.router.add_get("/healthz", healthz)
	# If Traefik doesn't strip the prefix, serve prefixed health too
	app.router.add_get("/tg-bot/healthz", healthz)

	# Ensure client closes on app shutdown (must be set before runner.setup())
	async def _close_client(_: web.Application) -> None:
		await client.close()

	app.on_cleanup.append(_close_client)

	runner = web.AppRunner(app)
	await runner.setup()
	site = web.TCPSite(runner, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
	# Best-effort webhook registration; do not crash on transient errors
	try:
		await bot.set_webhook(
			url=settings.webhook_url,
			secret_token=settings.webhook_secret or None,
			allowed_updates=["message", "edited_message", "callback_query"],
		)
		await _set_bot_commands(bot)
	except Exception as e:
		log.warning("set_webhook failed: %s", e)
	await site.start()
	log.info("Webhook server started on :%s", os.getenv("PORT", "8080"))
	# Run forever
	while True:
		await asyncio.sleep(3600)


if __name__ == "__main__":
	logging.basicConfig(level=getattr(logging, load().log_level.upper(), logging.INFO))
	mode = load().mode or os.getenv("MODE", "webhook")
	if mode == "polling":
		asyncio.run(run_polling())
	else:
		asyncio.run(run_webhook())
