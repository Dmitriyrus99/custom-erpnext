from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from prometheus_client import Counter, start_http_server
import sentry_sdk

from .config import load
from .frappe_client import FrappeClient
from .handlers import requests as requests_handlers


log = logging.getLogger("ferum.telegram.bot")

METRICS_ENABLED = True
REQ_CREATED = Counter("ferum_tg_requests_created", "Requests created via bot")
PHOTO_ATTACHED = Counter("ferum_tg_photos_attached", "Photos attached via bot")


@asynccontextmanager
async def lifespan(dp: Dispatcher):
    settings = load()
    client = FrappeClient(
        settings.frappe_base,
        settings.frappe_username,
        settings.frappe_password,
        totp_secret=settings.bot_totp_secret,
        verify_ssl=settings.verify_ssl,
    )
    dp["frappe_client"] = client
    try:
        yield
    finally:
        await client.close()


def _wire_dependencies(dp: Dispatcher):
    # Provide FrappeClient to handlers via dependency injection
    dp.workflow_data["frappe_client"] = dp["frappe_client"]

    @dp.message.middleware()
    async def inject_client(handler, event, data):  # type: ignore[no-redef]
        data["client"] = dp["frappe_client"]
        return await handler(event, data)

    @dp.callback_query.middleware()
    async def inject_client_cb(handler, event, data):  # type: ignore[no-redef]
        data["client"] = dp["frappe_client"]
        return await handler(event, data)


async def run_polling() -> None:
    settings = load()
    if settings.sentry_dsn:
        sentry_sdk.init(settings.sentry_dsn, traces_sample_rate=0.1)
    if settings.prometheus_port:
        start_http_server(settings.prometheus_port)

    bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher(lifespan=lifespan)
    dp.include_router(requests_handlers.router)
    _wire_dependencies(dp)
    await dp.start_polling(bot)


async def run_webhook() -> None:
    settings = load()
    if settings.sentry_dsn:
        sentry_sdk.init(settings.sentry_dsn, traces_sample_rate=0.1)
    if settings.prometheus_port:
        start_http_server(settings.prometheus_port)

    bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher(lifespan=lifespan)
    dp.include_router(requests_handlers.router)
    _wire_dependencies(dp)

    app = web.Application()
    webhook_path = "/tg-bot/webhook"
    handler = SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=settings.webhook_secret or None)
    handler.register(app, path=webhook_path)
    setup_application(app, dp, bot=bot)

    # Optionally: expose /healthz
    async def healthz(_: web.Request) -> web.Response:
        return web.Response(text="ok")

    app.router.add_get("/healthz", healthz)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
    await bot.set_webhook(url=settings.webhook_url, secret_token=settings.webhook_secret or None)
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
