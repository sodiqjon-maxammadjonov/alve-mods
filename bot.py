"""
Main bot entry point — AppBot
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

load_dotenv()

import database as db
from handlers import user, admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not set in .env!")

    DB_LINK = os.getenv("DB_LINK")
    if not DB_LINK:
        raise ValueError("DB_LINK not set in .env!")

    logger.info("Initializing database...")
    await db.init_db()
    logger.info("Database ready ✅")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(user.router)
    dp.include_router(admin.router)

    me = await bot.get_me()
    logger.info(f"Bot started: @{me.username} (ID: {me.id})")

    # Notify admins on startup
    admin_ids = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
    for aid in admin_ids:
        try:
            await bot.send_message(
                aid,
                f"🚀 <b>Bot ishga tushdi!</b>\n\n"
                f"🤖 @{me.username}\n"
                f"📦 Versiya: 4.0 (PostgreSQL)\n\n"
                f"/admin — Admin panel",
            )
        except Exception:
            pass

    logger.info("Starting polling...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())