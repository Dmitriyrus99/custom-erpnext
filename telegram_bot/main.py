"""Entrypoint shim so systemd ExecStart can run `-m apps.ferum_custom.telegram_bot.main`.

The real bot code lives in `apps/ferum_custom/telegram_bot/telegram_bot/main.py`.
"""

from __future__ import annotations

import asyncio
import logging
import os

from .telegram_bot import main as bot_main


def _run() -> None:
	logging.basicConfig(level=getattr(logging, bot_main.load().log_level.upper(), logging.INFO))
	mode = bot_main.load().mode or os.getenv("MODE", "webhook")
	if mode == "polling":
		asyncio.run(bot_main.run_polling())
	else:
		asyncio.run(bot_main.run_webhook())


if __name__ == "__main__":
	_run()
