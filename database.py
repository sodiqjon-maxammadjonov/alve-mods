"""
Database module — SQLite with aiosqlite
Tashqi server shart emas, fayl sifatida saqlanadi.
"""

import aiosqlite
import os
import logging
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "bot_data.db")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER UNIQUE NOT NULL,
                username    TEXT,
                full_name   TEXT,
                language    TEXT DEFAULT 'uz',
                is_blocked  INTEGER DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now')),
                last_seen   TEXT DEFAULT (datetime('now'))
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS apps (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                name              TEXT NOT NULL,
                description       TEXT,
                app_type          TEXT DEFAULT 'app',
                platform          TEXT DEFAULT 'android',
                app_variant       TEXT DEFAULT 'original',
                file_id           TEXT,
                file_link         TEXT,
                thumbnail_file_id TEXT,
                media_group_json  TEXT,
                src_chat_id       INTEGER,
                src_message_id    INTEGER,
                downloads         INTEGER DEFAULT 0,
                is_active         INTEGER DEFAULT 1,
                created_by        INTEGER,
                created_at        TEXT DEFAULT (datetime('now'))
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id    TEXT UNIQUE NOT NULL,
                channel_name  TEXT NOT NULL,
                invite_link   TEXT,
                is_active     INTEGER DEFAULT 1,
                subscribers   INTEGER DEFAULT 0,
                added_by      INTEGER,
                added_at      TEXT DEFAULT (datetime('now'))
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL,
                app_id        INTEGER NOT NULL,
                downloaded_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS channel_joins (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id  TEXT NOT NULL,
                user_id     INTEGER NOT NULL,
                joined_at   TEXT DEFAULT (datetime('now')),
                left_at     TEXT DEFAULT NULL,
                is_active   INTEGER DEFAULT 1,
                UNIQUE(channel_id, user_id)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS join_requests (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id   TEXT NOT NULL,
                user_id      INTEGER NOT NULL,
                requested_at TEXT DEFAULT (datetime('now')),
                UNIQUE(channel_id, user_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_dl_user ON downloads(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_dl_app  ON downloads(app_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_cj      ON channel_joins(channel_id, user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_apps    ON apps(is_active)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_jr      ON join_requests(channel_id, user_id)")
        await conn.commit()
    logger.info("SQLite database ready ✅")


def _row(record) -> Optional[dict]:
    return dict(record) if record else None

def _rows(records) -> list:
    return [dict(r) for r in records]


# ─── USERS ─────────────────────────────────────────────────────────────

async def get_or_create_user(user_id: int, username: str = None, full_name: str = None) -> dict:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        row = await (await conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,))).fetchone()
        if not row:
            await conn.execute(
                "INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?,?,?)",
                (user_id, username, full_name)
            )
            await conn.commit()
            row = await (await conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,))).fetchone()
        else:
            await conn.execute(
                "UPDATE users SET username=?, full_name=?, last_seen=datetime('now') WHERE user_id=?",
                (username, full_name, user_id)
            )
            await conn.commit()
        return _row(row)


async def get_user(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        row = await (await conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,))).fetchone()
        return _row(row)


async def set_user_language(user_id: int, language: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("UPDATE users SET language=? WHERE user_id=?", (language, user_id))
        await conn.commit()


async def get_all_users() -> list:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        rows = await (await conn.execute(
            "SELECT * FROM users WHERE is_blocked=0 ORDER BY created_at DESC"
        )).fetchall()
        return _rows(rows)


async def get_recent_users(limit: int = 10) -> list:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        rows = await (await conn.execute(
            "SELECT * FROM users ORDER BY created_at DESC LIMIT ?", (limit,)
        )).fetchall()
        return _rows(rows)


async def get_users_count() -> int:
    async with aiosqlite.connect(DB_PATH) as conn:
        row = await (await conn.execute("SELECT COUNT(*) FROM users")).fetchone()
        return row[0] if row else 0


async def get_today_users_count() -> int:
    async with aiosqlite.connect(DB_PATH) as conn:
        today = date.today().isoformat()
        row = await (await conn.execute(
            "SELECT COUNT(*) FROM users WHERE date(created_at)=?", (today,)
        )).fetchone()
        return row[0] if row else 0


async def block_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("UPDATE users SET is_blocked=1 WHERE user_id=?", (user_id,))
        await conn.commit()


# ─── APPS ──────────────────────────────────────────────────────────────

async def add_app(name, description, app_type="app", platform="android",
                  app_variant="original", file_id=None, file_link=None,
                  thumbnail_file_id=None, created_by=None,
                  src_chat_id=None, src_message_id=None, media_group_json=None) -> int:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute(
            """INSERT INTO apps (name,description,app_type,platform,app_variant,
               file_id,file_link,thumbnail_file_id,media_group_json,
               src_chat_id,src_message_id,created_by)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (name, description, app_type, platform, app_variant,
             file_id, file_link, thumbnail_file_id, media_group_json,
             src_chat_id, src_message_id, created_by)
        )
        await conn.commit()
        return cur.lastrowid


async def search_apps(query: str) -> list:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        rows = await (await conn.execute(
            "SELECT * FROM apps WHERE is_active=1 AND name LIKE ? ORDER BY downloads DESC LIMIT 20",
            (f"%{query}%",)
        )).fetchall()
        return _rows(rows)


async def get_app(app_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        row = await (await conn.execute(
            "SELECT * FROM apps WHERE id=? AND is_active=1", (app_id,)
        )).fetchone()
        return _row(row)


async def get_all_apps(active_only: bool = True) -> list:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        q = "SELECT * FROM apps" + (" WHERE is_active=1" if active_only else "") + " ORDER BY created_at DESC"
        rows = await (await conn.execute(q)).fetchall()
        return _rows(rows)


async def update_app(app_id: int, **kwargs):
    if not kwargs:
        return
    async with aiosqlite.connect(DB_PATH) as conn:
        fields = ", ".join(f"{k}=?" for k in kwargs)
        values = list(kwargs.values()) + [app_id]
        await conn.execute(f"UPDATE apps SET {fields} WHERE id=?", values)
        await conn.commit()


async def delete_app(app_id: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("DELETE FROM downloads WHERE app_id=?", (app_id,))
        await conn.execute("DELETE FROM apps WHERE id=?", (app_id,))
        await conn.commit()


async def get_apps_count() -> int:
    async with aiosqlite.connect(DB_PATH) as conn:
        row = await (await conn.execute("SELECT COUNT(*) FROM apps WHERE is_active=1")).fetchone()
        return row[0] if row else 0


async def get_total_downloads() -> int:
    async with aiosqlite.connect(DB_PATH) as conn:
        row = await (await conn.execute(
            "SELECT COALESCE(SUM(downloads),0) FROM apps WHERE is_active=1"
        )).fetchone()
        return row[0] if row else 0


# ─── CHANNELS ──────────────────────────────────────────────────────────

async def add_channel(channel_id: str, channel_name: str,
                      invite_link: str = None, added_by: int = None) -> bool:
    async with aiosqlite.connect(DB_PATH) as conn:
        try:
            await conn.execute(
                """INSERT INTO channels (channel_id,channel_name,invite_link,added_by)
                   VALUES (?,?,?,?)
                   ON CONFLICT(channel_id) DO UPDATE
                   SET is_active=1, channel_name=excluded.channel_name, invite_link=excluded.invite_link""",
                (channel_id, channel_name, invite_link, added_by)
            )
            await conn.commit()
            return True
        except Exception as e:
            logger.error(f"add_channel error: {e}")
            return False


async def get_active_channels() -> list:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        rows = await (await conn.execute(
            "SELECT * FROM channels WHERE is_active=1 ORDER BY added_at DESC"
        )).fetchall()
        return _rows(rows)


async def get_all_channels() -> list:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        rows = await (await conn.execute("SELECT * FROM channels ORDER BY added_at DESC")).fetchall()
        return _rows(rows)


async def remove_channel(channel_id: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("UPDATE channels SET is_active=0 WHERE channel_id=?", (channel_id,))
        await conn.commit()


async def hard_delete_channel(channel_id: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("DELETE FROM channel_joins WHERE channel_id=?", (channel_id,))
        await conn.execute("DELETE FROM join_requests WHERE channel_id=?", (channel_id,))
        await conn.execute("DELETE FROM channels WHERE channel_id=?", (channel_id,))
        await conn.commit()


async def get_channels_count() -> int:
    async with aiosqlite.connect(DB_PATH) as conn:
        row = await (await conn.execute("SELECT COUNT(*) FROM channels WHERE is_active=1")).fetchone()
        return row[0] if row else 0


async def update_channel_subscribers(channel_id: str, count: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("UPDATE channels SET subscribers=? WHERE channel_id=?", (count, channel_id))
        await conn.commit()


# ─── CHANNEL JOINS ─────────────────────────────────────────────────────

async def record_channel_join(channel_id: str, user_id: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            """INSERT INTO channel_joins (channel_id,user_id,joined_at,left_at,is_active)
               VALUES (?,?,datetime('now'),NULL,1)
               ON CONFLICT(channel_id,user_id)
               DO UPDATE SET joined_at=datetime('now'), left_at=NULL, is_active=1""",
            (channel_id, user_id)
        )
        await conn.commit()


async def record_channel_leave(channel_id: str, user_id: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE channel_joins SET left_at=datetime('now'), is_active=0 WHERE channel_id=? AND user_id=?",
            (channel_id, user_id)
        )
        await conn.commit()


async def get_channel_join_stats(channel_id: str) -> dict:
    async with aiosqlite.connect(DB_PATH) as conn:
        total  = (await (await conn.execute("SELECT COUNT(*) FROM channel_joins WHERE channel_id=?", (channel_id,))).fetchone())[0]
        active = (await (await conn.execute("SELECT COUNT(*) FROM channel_joins WHERE channel_id=? AND is_active=1", (channel_id,))).fetchone())[0]
        left   = (await (await conn.execute("SELECT COUNT(*) FROM channel_joins WHERE channel_id=? AND is_active=0", (channel_id,))).fetchone())[0]
    return {"total_joined": total, "currently_active": active, "left_count": left}


async def get_join_request_count(channel_id: str) -> int:
    async with aiosqlite.connect(DB_PATH) as conn:
        row = await (await conn.execute(
            "SELECT COUNT(*) FROM join_requests WHERE channel_id=?", (channel_id,)
        )).fetchone()
        return row[0] if row else 0


# ─── JOIN REQUESTS ─────────────────────────────────────────────────────

async def record_join_request(channel_id: str, user_id: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "INSERT OR IGNORE INTO join_requests (channel_id,user_id) VALUES (?,?)",
            (channel_id, user_id)
        )
        await conn.commit()


async def has_join_request(channel_id: str, user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as conn:
        row = await (await conn.execute(
            "SELECT id FROM join_requests WHERE channel_id=? AND user_id=?",
            (channel_id, user_id)
        )).fetchone()
        return row is not None


async def delete_join_requests(channel_id: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("DELETE FROM join_requests WHERE channel_id=?", (channel_id,))
        await conn.commit()


# ─── DOWNLOADS ─────────────────────────────────────────────────────────

async def log_download(user_id: int, app_id: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("INSERT INTO downloads (user_id,app_id) VALUES (?,?)", (user_id, app_id))
        await conn.execute("UPDATE apps SET downloads=downloads+1 WHERE id=?", (app_id,))
        await conn.commit()


async def get_user_downloads(user_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        rows = await (await conn.execute(
            """SELECT d.*, a.name, a.app_type
               FROM downloads d JOIN apps a ON d.app_id=a.id
               WHERE d.user_id=? ORDER BY d.downloaded_at DESC""",
            (user_id,)
        )).fetchall()
        return _rows(rows)
