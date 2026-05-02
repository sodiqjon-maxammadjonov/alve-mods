"""
Main bot entry point — AppBot
Render.com Web Service uchun moslashtirilgan (tekin tarif)
"""

import asyncio
import logging
import os
from aiohttp import web
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


# ─── HEALTH CHECK SERVER (Render Web Service uchun MAJBURIY) ───────────

async def health_check(request):
    """Render.com bu endpointni tekshiradi — bot tirik ekanini bildiradi"""
    return web.Response(text="OK", status=200)


async def start_web_server():
    """Minimal HTTP server — faqat Render uchun port ochish"""
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)

    port = int(os.getenv("PORT", 10000))  # Render PORT env ni o'zi beradi
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health check server started on port {port} ✅")
    return runner


# ─── BOT MAIN ──────────────────────────────────────────────────────────

async def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not set!")

    DB_LINK = os.getenv("DB_LINK")
    if not DB_LINK:
        raise ValueError("DB_LINK not set!")

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

    # Web server ni paralel ishga tushiramiz (Render uchun)
    runner = await start_web_server()

    # Notify admins on startup
    admin_ids = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
    for aid in admin_ids:
        try:
            await bot.send_message(
                aid,
                f"🚀 <b>Bot ishga tushdi!</b>\n\n"
                f"🤖 @{me.username}\n"
                f"📦 Versiya: 4.1 (Render + Supabase)\n\n"
                f"/admin — Admin panel",
            )
        except Exception:
            pass

    logger.info("Starting polling...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        await runner.cleanup()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
