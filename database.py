"""
Database module — PostgreSQL with asyncpg
Tables: users, apps, channels, downloads, channel_joins
"""

import asyncpg
import os
import logging
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        db_url = os.getenv("DB_LINK")
        if not db_url:
            raise ValueError("DB_LINK environment variable is not set!")
        _pool = await asyncpg.create_pool(
            db_url,
            min_size=2,
            max_size=10,
            command_timeout=60,
        )
        logger.info("PostgreSQL connection pool created ✅")
    return _pool


async def init_db():
    """Initialize database — create all tables if not exist"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          SERIAL PRIMARY KEY,
                user_id     BIGINT UNIQUE NOT NULL,
                username    TEXT,
                full_name   TEXT,
                language    TEXT DEFAULT 'uz',
                is_blocked  SMALLINT DEFAULT 0,
                created_at  TIMESTAMPTZ DEFAULT NOW(),
                last_seen   TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS apps (
                id                SERIAL PRIMARY KEY,
                name              TEXT NOT NULL,
                description       TEXT,
                app_type          TEXT DEFAULT 'app',
                platform          TEXT DEFAULT 'android',
                app_variant       TEXT DEFAULT 'original',
                file_id           TEXT,
                file_link         TEXT,
                thumbnail_file_id TEXT,
                media_group_json  TEXT,
                src_chat_id       BIGINT,
                src_message_id    BIGINT,
                downloads         INTEGER DEFAULT 0,
                is_active         SMALLINT DEFAULT 1,
                created_by        BIGINT,
                created_at        TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id            SERIAL PRIMARY KEY,
                channel_id    TEXT UNIQUE NOT NULL,
                channel_name  TEXT NOT NULL,
                invite_link   TEXT,
                is_active     SMALLINT DEFAULT 1,
                subscribers   INTEGER DEFAULT 0,
                added_by      BIGINT,
                added_at      TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id            SERIAL PRIMARY KEY,
                user_id       BIGINT NOT NULL,
                app_id        INTEGER NOT NULL,
                downloaded_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS channel_joins (
                id          SERIAL PRIMARY KEY,
                channel_id  TEXT NOT NULL,
                user_id     BIGINT NOT NULL,
                joined_at   TIMESTAMPTZ DEFAULT NOW(),
                left_at     TIMESTAMPTZ DEFAULT NULL,
                is_active   SMALLINT DEFAULT 1,
                UNIQUE(channel_id, user_id)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS join_requests (
                id           SERIAL PRIMARY KEY,
                channel_id   TEXT NOT NULL,
                user_id      BIGINT NOT NULL,
                requested_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(channel_id, user_id)
            )
        """)
        # Migrations — yangi ustunlar qo'shish
        await conn.execute("ALTER TABLE apps ADD COLUMN IF NOT EXISTS media_group_json TEXT")
        await conn.execute("ALTER TABLE apps ADD COLUMN IF NOT EXISTS platform TEXT DEFAULT 'android'")
        await conn.execute("ALTER TABLE apps ADD COLUMN IF NOT EXISTS app_variant TEXT DEFAULT 'original'")

        # Indexes — tezlashtirish uchun
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_dl_user     ON downloads(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_dl_app      ON downloads(app_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_cj          ON channel_joins(channel_id, user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_cj_active   ON channel_joins(channel_id, is_active)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_apps_active ON apps(is_active)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_apps_date   ON apps(created_at DESC)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_date  ON users(created_at DESC)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_block ON users(is_blocked)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_jr          ON join_requests(channel_id, user_id)")
    logger.info("Database tables ready ✅")


# ─── HELPERS ───────────────────────────────────────────────────────────

def _row(record) -> Optional[dict]:
    return dict(record) if record else None

def _rows(records) -> list:
    return [dict(r) for r in records]


# ─── USER OPERATIONS ───────────────────────────────────────────────────

async def get_or_create_user(user_id: int, username: str = None, full_name: str = None) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        if not row:
            await conn.execute(
                """INSERT INTO users (user_id, username, full_name)
                   VALUES ($1, $2, $3)
                   ON CONFLICT (user_id) DO NOTHING""",
                user_id, username, full_name
            )
            row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        else:
            await conn.execute(
                "UPDATE users SET username=$1, full_name=$2, last_seen=NOW() WHERE user_id=$3",
                username, full_name, user_id
            )
        return _row(row)


async def get_user(user_id: int) -> Optional[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        return _row(row)


async def set_user_language(user_id: int, language: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET language=$1 WHERE user_id=$2", language, user_id
        )


async def get_all_users() -> list:
    """Barcha bloklangan bo'lmagan foydalanuvchilar (broadcast uchun)"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM users WHERE is_blocked = 0 ORDER BY created_at DESC"
        )
        return _rows(rows)


async def get_recent_users(limit: int = 10) -> list:
    """So'nggi N ta foydalanuvchi (statistika uchun)"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM users ORDER BY created_at DESC LIMIT $1", limit
        )
        return _rows(rows)


async def get_users_count() -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval("SELECT COUNT(*) FROM users") or 0


async def get_today_users_count() -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        today = date.today()
        return await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE created_at::date = $1", today
        ) or 0


async def block_user(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET is_blocked=1 WHERE user_id=$1", user_id
        )


# ─── APP OPERATIONS ────────────────────────────────────────────────────

async def add_app(name: str, description: str, app_type: str = "app",
                  platform: str = "android", app_variant: str = "original",
                  file_id: str = None, file_link: str = None,
                  thumbnail_file_id: str = None, created_by: int = None,
                  src_chat_id: int = None, src_message_id: int = None,
                  media_group_json: str = None) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row_id = await conn.fetchval(
            """INSERT INTO apps
               (name, description, app_type, platform, app_variant, file_id, file_link,
                thumbnail_file_id, media_group_json, src_chat_id, src_message_id, created_by)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
               RETURNING id""",
            name, description, app_type, platform, app_variant, file_id, file_link,
            thumbnail_file_id, media_group_json, src_chat_id, src_message_id, created_by
        )
        return row_id


async def search_apps(query: str) -> list:
    """Search apps by name (case-insensitive, partial match)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT * FROM apps
               WHERE is_active=1 AND name ILIKE $1
               ORDER BY downloads DESC LIMIT 20""",
            f"%{query}%"
        )
        return _rows(rows)


async def get_app(app_id: int) -> Optional[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM apps WHERE id=$1 AND is_active=1", app_id
        )
        return _row(row)


async def get_all_apps(active_only: bool = True) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        query = "SELECT * FROM apps"
        if active_only:
            query += " WHERE is_active=1"
        query += " ORDER BY created_at DESC"
        rows = await conn.fetch(query)
        return _rows(rows)


async def update_app(app_id: int, **kwargs):
    if not kwargs:
        return
    pool = await get_pool()
    async with pool.acquire() as conn:
        fields = ", ".join(f"{k}=${i+1}" for i, k in enumerate(kwargs))
        values = list(kwargs.values()) + [app_id]
        await conn.execute(
            f"UPDATE apps SET {fields} WHERE id=${len(values)}", *values
        )


async def delete_app(app_id: int):
    """
    Ilovani to'liq o'chirish — tranzaksiya ichida barcha bog'liq ma'lumotlar bilan:
    • downloads — yuklash tarixi
    • apps — ilova o'zi
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("DELETE FROM downloads    WHERE app_id=$1", app_id)
            await conn.execute("DELETE FROM apps         WHERE id=$1",     app_id)
    logger.info(f"App {app_id} and all related data deleted.")


async def increment_downloads(app_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE apps SET downloads=downloads+1 WHERE id=$1", app_id
        )


async def get_apps_count() -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval("SELECT COUNT(*) FROM apps WHERE is_active=1") or 0


async def get_total_downloads() -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval("SELECT COALESCE(SUM(downloads),0) FROM apps WHERE is_active=1") or 0


# ─── CHANNEL OPERATIONS ────────────────────────────────────────────────

async def add_channel(channel_id: str, channel_name: str,
                      invite_link: str = None, added_by: int = None) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                """INSERT INTO channels (channel_id, channel_name, invite_link, added_by)
                   VALUES ($1,$2,$3,$4)
                   ON CONFLICT (channel_id) DO UPDATE
                   SET is_active=1, channel_name=$2, invite_link=$3""",
                channel_id, channel_name, invite_link, added_by
            )
            return True
        except Exception as e:
            logger.error(f"add_channel error: {e}")
            return False


async def get_active_channels() -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM channels WHERE is_active=1 ORDER BY added_at DESC"
        )
        return _rows(rows)


async def get_all_channels() -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM channels ORDER BY added_at DESC")
        return _rows(rows)


async def remove_channel(channel_id: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE channels SET is_active=0 WHERE channel_id=$1", channel_id
        )


async def hard_delete_channel(channel_id: str):
    """
    Kanalni to'liq o'chirish — tranzaksiya ichida barcha bog'liq ma'lumotlar bilan:
    • channel_joins — a'zolik tarixi va statistikasi
    • channels — kanal o'zi
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("DELETE FROM channel_joins  WHERE channel_id=$1", channel_id)
            await conn.execute("DELETE FROM join_requests  WHERE channel_id=$1", channel_id)
            await conn.execute("DELETE FROM channels       WHERE channel_id=$1", channel_id)
    logger.info(f"Channel {channel_id} and all related data deleted.")


async def get_channels_count() -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval("SELECT COUNT(*) FROM channels WHERE is_active=1") or 0


async def update_channel_subscribers(channel_id: str, count: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE channels SET subscribers=$1 WHERE channel_id=$2", count, channel_id
        )


# ─── CHANNEL JOINS TRACKING ────────────────────────────────────────────

async def record_channel_join(channel_id: str, user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO channel_joins (channel_id, user_id, joined_at, left_at, is_active)
               VALUES ($1,$2,NOW(),NULL,1)
               ON CONFLICT (channel_id, user_id)
               DO UPDATE SET joined_at=NOW(), left_at=NULL, is_active=1""",
            channel_id, user_id
        )


async def record_channel_leave(channel_id: str, user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """UPDATE channel_joins
               SET left_at=NOW(), is_active=0
               WHERE channel_id=$1 AND user_id=$2""",
            channel_id, user_id
        )


async def get_channel_join_stats(channel_id: str) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        total    = await conn.fetchval("SELECT COUNT(*) FROM channel_joins WHERE channel_id=$1", channel_id) or 0
        active   = await conn.fetchval("SELECT COUNT(*) FROM channel_joins WHERE channel_id=$1 AND is_active=1", channel_id) or 0
        left_cnt = await conn.fetchval("SELECT COUNT(*) FROM channel_joins WHERE channel_id=$1 AND is_active=0", channel_id) or 0
    return {"total_joined": total, "currently_active": active, "left_count": left_cnt}


# ─── JOIN REQUESTS (tasdiqlashsiz so'rovlar) ───────────────────────────

async def record_join_request(channel_id: str, user_id: int):
    """Foydalanuvchi join request yuborganda qayd etish (approve qilinmaydi)"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO join_requests (channel_id, user_id)
               VALUES ($1, $2)
               ON CONFLICT (channel_id, user_id) DO NOTHING""",
            channel_id, user_id
        )


async def has_join_request(channel_id: str, user_id: int) -> bool:
    """Foydalanuvchi bu kanalga so'rov yuborganmi?"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id FROM join_requests WHERE channel_id=$1 AND user_id=$2",
            channel_id, user_id
        )
        return row is not None


async def get_join_request_count(channel_id: str) -> int:
    """Kanalga jami so'rovlar soni"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT COUNT(*) FROM join_requests WHERE channel_id=$1", channel_id
        ) or 0


async def delete_join_requests(channel_id: str):
    """Kanal o'chirilganda uning so'rovlarini ham o'chirish"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM join_requests WHERE channel_id=$1", channel_id
        )


# ─── DOWNLOAD OPERATIONS ───────────────────────────────────────────────

async def log_download(user_id: int, app_id: int):
    """Yuklab olishni qayd etish — downloads + downloads counter atomic"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "INSERT INTO downloads (user_id, app_id) VALUES ($1,$2)", user_id, app_id
            )
            await conn.execute(
                "UPDATE apps SET downloads=downloads+1 WHERE id=$1", app_id
            )


async def get_user_downloads(user_id: int) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT d.*, a.name, a.app_type
               FROM downloads d
               JOIN apps a ON d.app_id = a.id
               WHERE d.user_id=$1
               ORDER BY d.downloaded_at DESC""",
            user_id
        )
        return _rows(rows)