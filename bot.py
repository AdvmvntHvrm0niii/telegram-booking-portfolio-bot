"""Entry point: Booking Assistant Telegram bot (long polling)."""

from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError, TelegramUnauthorizedError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent

import config as cfg
from config import ConfigError, load_settings
from database import Database
from handlers import register_routers

logger = logging.getLogger("bot")


async def on_error(event: ErrorEvent) -> bool:
    """Log unexpected errors and tell the user something went wrong."""
    logger.error("Unhandled error: %s", event.exception, exc_info=event.exception)
    update = event.update
    try:
        if update.callback_query:
            await update.callback_query.answer(cfg.TEXT_ERROR, show_alert=True)
        elif update.message:
            await update.message.answer(cfg.TEXT_ERROR)
    except TelegramAPIError:
        logger.warning("Could not deliver the error message to the user")
    return True


async def main() -> None:
    """Configure and run the bot."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    try:
        settings = load_settings()
    except ConfigError as exc:
        logger.error("Configuration error: %s", exc)
        sys.exit(1)

    db = Database(settings.database_path)
    await db.init()

    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage(), db=db, settings=settings)
    dp.errors.register(on_error)
    register_routers(dp)

    try:
        me = await bot.get_me()
        logger.info("Starting long polling as @%s", me.username)
        await bot.delete_webhook(drop_pending_updates=False)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except TelegramUnauthorizedError:
        logger.error("Telegram rejected the bot token. Check BOT_TOKEN in your .env file.")
        sys.exit(1)
    except TelegramAPIError as exc:
        logger.error("Telegram API error on startup: %s", type(exc).__name__)
        sys.exit(1)
    finally:
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped by user")
