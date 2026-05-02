"""
database.py — AppBot (alve-mods)
PostgreSQL (asyncpg) — Render Internal Database URL ishlatiladi.
"""

import asyncpg
import os
import logging
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            os.getenv("DB_LINK"),
            min_size=2,
            max_size=10,
        )
    return _pool


async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          SERIAL PRIMARY KEY,
                user_id     BIGINT UNIQUE NOT NULL,
                username    TEXT,
                full_name   TEXT,
                language    TEXT DEFAULT 'uz',
                is_blocked  INTEGER DEFAULT 0,
                created_at  TIMESTAMP DEFAULT NOW(),
                last_seen   TIMESTAMP DEFAULT NOW()
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
                is_active         INTEGER DEFAULT 1,
                created_by        BIGINT,
                created_at        TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id            SERIAL PRIMARY KEY,
                channel_id    TEXT UNIQUE NOT NULL,
                channel_name  TEXT NOT NULL,
                invite_link   TEXT,
                is_active     INTEGER DEFAULT 1,
                subscribers   INTEGER DEFAULT 0,
                added_by      BIGINT,
                added_at      TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id            SERIAL PRIMARY KEY,
                user_id       BIGINT NOT NULL,
                app_id        INTEGER NOT NULL,
                downloaded_at TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS channel_joins (
                id          SERIAL PRIMARY KEY,
                channel_id  TEXT NOT NULL,
                user_id     BIGINT NOT NULL,
                joined_at   TIMESTAMP DEFAULT NOW(),
                left_at     TIMESTAMP DEFAULT NULL,
                is_active   INTEGER DEFAULT 1,
                UNIQUE(channel_id, user_id)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS join_requests (
                id           SERIAL PRIMARY KEY,
                channel_id   TEXT NOT NULL,
                user_id      BIGINT NOT NULL,
                requested_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(channel_id, user_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_dl_user ON downloads(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_dl_app  ON downloads(app_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_cj      ON channel_joins(channel_id, user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_jr      ON join_requests(channel_id, user_id)")
    logger.info("PostgreSQL database ready ✅")


def _row(r) -> Optional[dict]:
    return dict(r) if r else None

def _rows(rs) -> list:
    return [dict(r) for r in rs]


# ─── USERS ─────────────────────────────────────────────────────

async def get_or_create_user(user_id: int, username: str = None, full_name: str = None) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE user_id=$1", user_id)
        if not row:
            await conn.execute(
                "INSERT INTO users (user_id, username, full_name) VALUES ($1,$2,$3) ON CONFLICT DO NOTHING",
                user_id, username, full_name
            )
            row = await conn.fetchrow("SELECT * FROM users WHERE user_id=$1", user_id)
        else:
            await conn.execute(
                "UPDATE users SET username=$1, full_name=$2, last_seen=NOW() WHERE user_id=$3",
                username, full_name, user_id
            )
        return _row(row)


async def get_user(user_id: int) -> Optional[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return _row(await conn.fetchrow("SELECT * FROM users WHERE user_id=$1", user_id))


async def set_user_language(user_id: int, language: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET language=$1 WHERE user_id=$2", language, user_id)


async def get_all_users() -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return _rows(await conn.fetch("SELECT * FROM users WHERE is_blocked=0 ORDER BY created_at DESC"))


async def get_users_count() -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return (await conn.fetchrow("SELECT COUNT(*) AS cnt FROM users"))["cnt"]


async def get_today_users_count() -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return (await conn.fetchrow(
            "SELECT COUNT(*) AS cnt FROM users WHERE date(created_at)=current_date"
        ))["cnt"]


async def block_user(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET is_blocked=1 WHERE user_id=$1", user_id)


# ─── APPS ──────────────────────────────────────────────────────

async def add_app(name, description, app_type="app", platform="android",
                  app_variant="original", file_id=None, file_link=None,
                  thumbnail_file_id=None, created_by=None,
                  src_chat_id=None, src_message_id=None, media_group_json=None) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO apps (name,description,app_type,platform,app_variant,
               file_id,file_link,thumbnail_file_id,media_group_json,
               src_chat_id,src_message_id,created_by)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12) RETURNING id""",
            name, description, app_type, platform, app_variant,
            file_id, file_link, thumbnail_file_id, media_group_json,
            src_chat_id, src_message_id, created_by
        )
        return row["id"]


async def search_apps(query: str) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return _rows(await conn.fetch(
            "SELECT * FROM apps WHERE is_active=1 AND name ILIKE $1 ORDER BY downloads DESC LIMIT 20",
            f"%{query}%"
        ))


async def get_app(app_id: int) -> Optional[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return _row(await conn.fetchrow("SELECT * FROM apps WHERE id=$1 AND is_active=1", app_id))


async def get_all_apps(active_only: bool = True) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        q = "SELECT * FROM apps" + (" WHERE is_active=1" if active_only else "") + " ORDER BY created_at DESC"
        return _rows(await conn.fetch(q))


async def update_app(app_id: int, **kwargs):
    if not kwargs:
        return
    pool = await get_pool()
    async with pool.acquire() as conn:
        fields = ", ".join(f"{k}=${i+1}" for i, k in enumerate(kwargs))
        values = list(kwargs.values()) + [app_id]
        await conn.execute(f"UPDATE apps SET {fields} WHERE id=${len(values)}", *values)


async def delete_app(app_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM downloads WHERE app_id=$1", app_id)
        await conn.execute("DELETE FROM apps WHERE id=$1", app_id)


async def get_apps_count() -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return (await conn.fetchrow("SELECT COUNT(*) AS cnt FROM apps WHERE is_active=1"))["cnt"]


async def get_total_downloads() -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return (await conn.fetchrow("SELECT COALESCE(SUM(downloads),0) AS s FROM apps WHERE is_active=1"))["s"]


# ─── CHANNELS ──────────────────────────────────────────────────

async def add_channel(channel_id: str, channel_name: str,
                      invite_link: str = None, added_by: int = None) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                """INSERT INTO channels (channel_id,channel_name,invite_link,added_by)
                   VALUES ($1,$2,$3,$4)
                   ON CONFLICT(channel_id) DO UPDATE
                   SET is_active=1, channel_name=EXCLUDED.channel_name, invite_link=EXCLUDED.invite_link""",
                channel_id, channel_name, invite_link, added_by
            )
            return True
        except Exception as e:
            logger.error(f"add_channel error: {e}")
            return False


async def get_active_channels() -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return _rows(await conn.fetch("SELECT * FROM channels WHERE is_active=1 ORDER BY added_at DESC"))


async def get_all_channels() -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return _rows(await conn.fetch("SELECT * FROM channels ORDER BY added_at DESC"))


async def remove_channel(channel_id: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE channels SET is_active=0 WHERE channel_id=$1", channel_id)


async def hard_delete_channel(channel_id: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM channel_joins WHERE channel_id=$1", channel_id)
        await conn.execute("DELETE FROM join_requests WHERE channel_id=$1", channel_id)
        await conn.execute("DELETE FROM channels WHERE channel_id=$1", channel_id)


async def get_channels_count() -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return (await conn.fetchrow("SELECT COUNT(*) AS cnt FROM channels WHERE is_active=1"))["cnt"]


async def update_channel_subscribers(channel_id: str, count: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE channels SET subscribers=$1 WHERE channel_id=$2", count, channel_id)


# ─── CHANNEL JOINS ─────────────────────────────────────────────

async def record_channel_join(channel_id: str, user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO channel_joins (channel_id,user_id,joined_at,left_at,is_active)
               VALUES ($1,$2,NOW(),NULL,1)
               ON CONFLICT(channel_id,user_id)
               DO UPDATE SET joined_at=NOW(), left_at=NULL, is_active=1""",
            channel_id, user_id
        )


async def record_channel_leave(channel_id: str, user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE channel_joins SET left_at=NOW(), is_active=0 WHERE channel_id=$1 AND user_id=$2",
            channel_id, user_id
        )


async def get_channel_join_stats(channel_id: str) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        total  = (await conn.fetchrow("SELECT COUNT(*) AS cnt FROM channel_joins WHERE channel_id=$1", channel_id))["cnt"]
        active = (await conn.fetchrow("SELECT COUNT(*) AS cnt FROM channel_joins WHERE channel_id=$1 AND is_active=1", channel_id))["cnt"]
        left   = (await conn.fetchrow("SELECT COUNT(*) AS cnt FROM channel_joins WHERE channel_id=$1 AND is_active=0", channel_id))["cnt"]
    return {"total_joined": total, "currently_active": active, "left_count": left}


# ─── JOIN REQUESTS ─────────────────────────────────────────────

async def record_join_request(channel_id: str, user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO join_requests (channel_id,user_id) VALUES ($1,$2) ON CONFLICT DO NOTHING",
            channel_id, user_id
        )


async def has_join_request(channel_id: str, user_id: int) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return bool(await conn.fetchrow(
            "SELECT id FROM join_requests WHERE channel_id=$1 AND user_id=$2",
            channel_id, user_id
        ))


async def get_join_request_count(channel_id: str) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return (await conn.fetchrow("SELECT COUNT(*) AS cnt FROM join_requests WHERE channel_id=$1", channel_id))["cnt"]


async def delete_join_requests(channel_id: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM join_requests WHERE channel_id=$1", channel_id)


# ─── DOWNLOADS ─────────────────────────────────────────────────

async def log_download(user_id: int, app_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO downloads (user_id,app_id) VALUES ($1,$2)", user_id, app_id)
        await conn.execute("UPDATE apps SET downloads=downloads+1 WHERE id=$1", app_id)


async def get_user_downloads(user_id: int) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return _rows(await conn.fetch(
            """SELECT d.*, a.name, a.app_type
               FROM downloads d JOIN apps a ON d.app_id=a.id
               WHERE d.user_id=$1 ORDER BY d.downloaded_at DESC""",
            user_id
        ))