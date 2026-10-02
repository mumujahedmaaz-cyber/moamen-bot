from __future__ import annotations

import logging

from dotenv import load_dotenv
from telegram.ext import Application

from bot.config import load_settings
from bot.handlers import register_handlers
from bot.logging_config import configure_logging
from bot.storage import Storage


def run() -> None:
    load_dotenv()
    settings = load_settings()
    configure_logging(settings.log_level)

    logger = logging.getLogger(__name__)
    logger.info("Starting bot")

    storage = Storage(settings.database_path)

    application = Application.builder().token(settings.bot_token).build()
    application.bot_data["storage"] = storage
    application.bot_data["admin_ids"] = settings.admin_ids

    register_handlers(application)
    application.run_polling(close_loop=False)
