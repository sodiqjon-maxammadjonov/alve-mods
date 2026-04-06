"""
Keyboards — all inline and reply keyboards
"""

from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from locales import t, LANG_FLAGS


# ─── LANGUAGE ──────────────────────────────────────────────────────────

def lang_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, label in LANG_FLAGS.items():
        builder.button(text=label, callback_data=f"lang:{code}")
    builder.adjust(2)
    return builder.as_markup()


# ─── USER MENUS ────────────────────────────────────────────────────────

def main_menu(lang: str) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=t(lang, "all_apps"))
    builder.button(text=t(lang, "my_requests"))
    builder.button(text=t(lang, "contact_admin"))
    builder.button(text=t(lang, "settings"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def cancel_keyboard(lang: str) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=t(lang, "cancel"))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


# ─── ADMIN MENU ────────────────────────────────────────────────────────
# Admin panel always in Uzbek

def admin_menu() -> ReplyKeyboardMarkup:
    """Admin panel keyboard — always Uzbek"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="📦 Ilovalar boshqaruvi")
    builder.button(text="📢 Kanallar boshqaruvi")
    builder.button(text="👥 Foydalanuvchilar")
    builder.button(text="📊 Statistika")
    builder.button(text="📣 Xabar yuborish")
    builder.button(text="🏠 Asosiy menyu")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def admin_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Cancel keyboard for admin — always Uzbek"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Bekor qilish")
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


# ─── SUBSCRIPTION ──────────────────────────────────────────────────────

def subscribe_keyboard(lang: str, channels: list, app_id: int) -> InlineKeyboardMarkup:
    channel_labels = {
        "uz": "Kanal", "ru": "Канал", "en": "Channel",
        "tr": "Kanal", "hi": "चैनल",
    }
    label = channel_labels.get(lang, "Kanal")
    builder = InlineKeyboardBuilder()
    for i, ch in enumerate(channels):
        # Support join request links (https://t.me/+xxx) stored as channel_id
        ch_id = ch.get("channel_id", "")
        if ch_id.startswith("https://"):
            link = ch_id
        else:
            link = ch.get("invite_link") or f"https://t.me/{ch_id.lstrip('@')}"
        builder.button(text=f"📢 {label} {i+1}", url=link)
    builder.button(
        text=t(lang, "check_subscription"),
        callback_data=f"check_sub:{app_id}"
    )
    builder.adjust(1)
    return builder.as_markup()


# ─── APPS ──────────────────────────────────────────────────────────────

def apps_list_keyboard(lang: str, apps: list, page: int = 0, page_size: int = 8) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    start = page * page_size
    end   = start + page_size
    page_apps = apps[start:end]

    for app in page_apps:
        emoji = "🎮" if app.get("app_type") == "game" else "📱"
        builder.button(
            text=f"{emoji} {app['name']}",
            callback_data=f"app:{app['id']}"
        )

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"apps_page:{page-1}"))
    if end < len(apps):
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"apps_page:{page+1}"))
    if nav:
        builder.row(*nav)

    builder.row(InlineKeyboardButton(text=t(lang, "close"), callback_data="close"))
    builder.adjust(1)
    return builder.as_markup()


def app_detail_keyboard(lang: str, app_id: int, is_admin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t(lang, "download_btn"), callback_data=f"download:{app_id}")
    if is_admin:
        builder.button(text="✏️ Tahrirlash",  callback_data=f"admin_edit_app:{app_id}")
        builder.button(text="🗑 O'chirish",   callback_data=f"admin_del_app:{app_id}")
    builder.button(text=t(lang, "back"), callback_data="back_apps")
    builder.adjust(1)
    return builder.as_markup()


def channel_post_keyboard(bot_username: str, app_id: int) -> InlineKeyboardMarkup:
    """Kanal uchun post tugmasi — botga deep link"""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="⬇️ Yuklab olish",
            url=f"https://t.me/{bot_username}?start=app_{app_id}"
        )
    ]])


# ─── CONFIRM ───────────────────────────────────────────────────────────

def confirm_keyboard(yes_cb: str, no_cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Ha, yuborish", callback_data=yes_cb),
        InlineKeyboardButton(text="❌ Bekor qilish",  callback_data=no_cb),
    ]])


# ─── SETTINGS ──────────────────────────────────────────────────────────

def settings_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t(lang, "change_lang_btn"), callback_data="change_language")
    builder.button(text=t(lang, "close"),            callback_data="close")
    builder.adjust(1)
    return builder.as_markup()


# ─── CHANNELS ADMIN ────────────────────────────────────────────────────

def channels_admin_keyboard(channels: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ch in channels:
        if ch.get("is_active", 1):
            builder.button(
                text=f"✅ {ch['channel_name']}",
                callback_data=f"ch_detail:{ch['id']}"
            )
    builder.button(text="➕ Kanal qo'shish", callback_data="add_channel")
    builder.button(text="◀️ Orqaga",          callback_data="back_admin")
    builder.adjust(1)
    return builder.as_markup()


def channel_detail_keyboard(channel_id_db: int, ch_id_str: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Statistika",  callback_data=f"ch_stats:{ch_id_str}")
    builder.button(text="🗑 O'chirish",   callback_data=f"ch_remove_confirm:{channel_id_db}")
    builder.button(text="◀️ Orqaga",      callback_data="admin_channels_back")
    builder.adjust(1)
    return builder.as_markup()


def channel_delete_confirm_keyboard(channel_id_db: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="✅ Ha, o'chirish",
            callback_data=f"ch_remove_yes:{channel_id_db}"
        ),
        InlineKeyboardButton(
            text="❌ Yo'q, bekor",
            callback_data=f"ch_remove_no:{channel_id_db}"
        ),
    ]])