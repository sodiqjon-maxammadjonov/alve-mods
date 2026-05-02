"""
Main bot entry point — AppBot
Render.com Web Service + SQLite + avtomatik backup
"""

import asyncio
import logging
import os
from datetime import datetime, time, timedelta

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

DB_PATH = os.getenv("DB_PATH", "bot_data.db")


# ─── SELF PING ─────────────────────────────────────────

async def self_ping():
    import aiohttp

    render_url = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")

    if not render_url:
        logger.warning("RENDER_EXTERNAL_URL not set, self-ping disabled")
        return

    await asyncio.sleep(60)

    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{render_url}/health",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as r:
                    logger.info(f"Self-ping: {r.status}")
        except Exception as e:
            logger.warning(f"Self-ping error: {e}")

        await asyncio.sleep(14 * 60)


# ─── HEALTH CHECK ──────────────────────────────────────

async def health_check(request):
    return web.Response(text="OK", status=200)
    print("ishladi database yaxshiiii")  

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)

    port = int(os.getenv("PORT", 10000))

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.info(f"Health check server started on port {port} ✅")
    return runner


# ─── BACKUP ────────────────────────────────────────────

async def send_backup(bot: Bot):
    """DB faylini SECRET_GROUP_ID ga yuborish"""
    group_id = os.getenv("SECRET_GROUP_ID")

    if not group_id:
        logger.warning("SECRET_GROUP_ID not set, skipping backup")
        return

    try:
        now = datetime.now().strftime("%Y-%m-%d_%H-%M")

        with open(DB_PATH, "rb") as f:
            await bot.send_document(
                chat_id=int(group_id),
                document=f,
                filename=f"backup_{now}.db",
                caption=(
                    f"🗄 <b>Avtomatik backup</b>\n"
                    f"📅 {now}"
                ),
                parse_mode="HTML",
            )

        logger.info(f"Backup sent to {group_id}")

    except Exception as e:
        logger.error(f"Backup error: {e}")


async def daily_backup_scheduler(bot: Bot):
    """Har kuni 00:00 da backup"""
    while True:
        now = datetime.now()

        # ✅ TO‘G‘RI VA SODDA HISOB
        next_midnight = datetime.combine(now.date(), time(0, 0)) + timedelta(days=1)

        wait_seconds = (next_midnight - now).total_seconds()

        logger.info(
            f"Next backup in {int(wait_seconds // 3600)}h "
            f"{int((wait_seconds % 3600) // 60)}m"
        )

        await asyncio.sleep(wait_seconds)
        await send_backup(bot)


# ─── MAIN ──────────────────────────────────────────────

async def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")

    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not set!")

    logger.info("Initializing database...")

    try:
        await db.init_db()
        logger.info("Database ready ✅")
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(user.router)
    dp.include_router(admin.router)

    me = await bot.get_me()
    logger.info(f"Bot started: @{me.username} (ID: {me.id})")

    runner = await start_web_server()

    # ─── ADMINLARGA хабар ───
    admin_ids = [
        int(x.strip())
        for x in os.getenv("ADMIN_IDS", "").split(",")
        if x.strip()
    ]

    for aid in admin_ids:
        try:
            await bot.send_message(
                aid,
                f"🚀 <b>Bot ishga tushdi!</b>\n\n"
                f"🤖 @{me.username}\n"
                f"📦 Versiya: millioninchisi"
                f"/admin — Admin panel",
            )
        except Exception:
            pass

    # ─── BACKGROUND TASKS ───
    asyncio.create_task(daily_backup_scheduler(bot))
    asyncio.create_task(self_ping())

    logger.info("Starting polling...")

    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )
    finally:
        await bot.session.close()
        await runner.cleanup()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())