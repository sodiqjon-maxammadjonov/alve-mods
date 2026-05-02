"""
User handlers — start, apps, download, settings, contact admin, my downloads
"""

import os
import logging
from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ChatJoinRequest,
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

import database as db
from locales import t, LANG_FLAGS
from keyboards import (
    lang_keyboard, main_menu, subscribe_keyboard,
    apps_list_keyboard, app_detail_keyboard,
    settings_keyboard, cancel_keyboard,
)
from subscription import check_user_subscriptions

logger = logging.getLogger(__name__)
router = Router()

ADMIN_IDS      = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")


# ─── JOIN REQUEST — FAQAT QAYD ETISH (approve qilinmaydi) ─────────────

@router.chat_join_request()
async def handle_join_request(update: ChatJoinRequest, bot: Bot):
    """
    Foydalanuvchi join request link orqali kanalga so'rov yuborganda
    faqat bazaga yozamiz. Approve QILINMAYDI — admin o'zi tasdiqlaydi.
    """
    try:
        ch_id_str = str(update.chat.id)
        await db.record_join_request(ch_id_str, update.from_user.id)
        logger.info(
            f"Join request recorded (NOT approved): "
            f"user {update.from_user.id} → chat {update.chat.id}"
        )
    except Exception as e:
        logger.warning(f"Failed to record join request: {e}")


# ─── TASHQI KANAL CLICK HANDLER (YouTube, Instagram va h.k.) ──────────

@router.callback_query(F.data.startswith("ext_clicked:"))
async def external_channel_clicked(callback: CallbackQuery):
    """
    Foydalanuvchi tashqi platforma (YouTube va h.k.) tugmasini bossa,
    DB ga yozamiz — keyingi tekshiruvda a'zo hisob bo'ladi.
    """
    try:
        channel_url = callback.data.replace("ext_clicked:", "", 1)
        await db.record_join_request(channel_url, callback.from_user.id)
    except Exception as e:
        logger.warning(f"external_channel_clicked error: {e}")
    await callback.answer("✅ Ochilmoqda...")


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ─── HELPERS ───────────────────────────────────────────────────────────

_PLATFORM_EMOJI = {"android": "🤖", "desktop": "🖥"}
_VARIANT_EMOJI  = {"original": "✅", "mod": "🔓"}
_PLATFORM_LABEL = {"android": "Android", "desktop": "Desktop / PC"}
_VARIANT_LABEL  = {"original": "Original", "mod": "Modded"}


def build_app_caption(lang: str, name: str, description: str,
                      downloads: int, platform: str = "android",
                      app_variant: str = "original") -> str:
    desc_clean  = (description or "").strip()
    plat_emoji  = _PLATFORM_EMOJI.get(platform, "📱")
    plat_label  = _PLATFORM_LABEL.get(platform, platform.title())
    var_emoji   = _VARIANT_EMOJI.get(app_variant, "")
    var_label   = _VARIANT_LABEL.get(app_variant, app_variant.title())
    return (
        f"<b>{name}</b>\n\n"
        f"{desc_clean}\n\n"
        f"{plat_emoji} <b>Platform:</b> {plat_label}\n"
        f"{var_emoji} <b>Type:</b> {var_label}"
    )


async def _deliver_app(
    bot: Bot,
    user_id: int,
    app: dict,
    lang: str,
    reply_to: Message,
) -> bool:
    """
    Copy/send the app file directly to the user.
    Returns True on success, False on failure.
    """
    caption = build_app_caption(
        lang, app["name"], app.get("description", ""), app["downloads"],
        app.get("platform", "android"), app.get("app_variant", "original")
    )

    try:
        if app.get("src_chat_id") and app.get("src_message_id"):
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=app["src_chat_id"],
                message_id=app["src_message_id"],
                caption=caption,
                parse_mode="HTML",
            )
        elif app.get("file_id"):
            # Try as document first, fallback to video
            try:
                await bot.send_document(
                    chat_id=user_id,
                    document=app["file_id"],
                    caption=caption,
                    parse_mode="HTML",
                )
            except Exception:
                await bot.send_video(
                    chat_id=user_id,
                    video=app["file_id"],
                    caption=caption,
                    parse_mode="HTML",
                )
        elif app.get("file_link"):
            kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text=t(lang, "file_link_btn"),
                    url=app["file_link"]
                )
            ]])
            await bot.send_message(
                chat_id=user_id,
                text=caption,
                reply_markup=kb,
                parse_mode="HTML",
            )
        else:
            await reply_to.answer(t(lang, "download_failed"))
            return False

        await db.log_download(user_id, app["id"])
        return True

    except Exception as e:
        logger.error(f"_deliver_app error for user {user_id}, app {app['id']}: {e}")
        await reply_to.answer(t(lang, "download_failed"))
        return False


async def _check_and_deliver(
    bot: Bot,
    user_id: int,
    app_id: int,
    lang: str,
    reply_to: Message,
    answer_callback=None,
) -> bool:
    """
    Check channel subscriptions and deliver the app.
    answer_callback — optional coroutine to call on success before delivery.
    Returns True if delivered, False if subscription required.
    """
    app = await db.get_app(app_id)
    if not app:
        await reply_to.answer(t(lang, "app_not_found"))
        return False

    channels = await db.get_active_channels()
    if channels:
        all_sub, unsub = await check_user_subscriptions(bot, user_id, channels)

        if not all_sub:
            channel_labels = {
                "uz": "Kanal", "ru": "Канал", "en": "Channel",
                "tr": "Kanal", "hi": "चैनल",
            }
            label = channel_labels.get(lang, "Kanal")
            channels_text = "\n".join(
                f"• <b>{label} {i+1}</b>"
                for i, _ in enumerate(unsub)
            )
            await reply_to.answer(
                t(lang, "subscribe_required", channels=channels_text),
                reply_markup=subscribe_keyboard(lang, unsub, app_id),
            )
            return False

        # A'zolikni qayd etamiz
        for ch in channels:
            ch_id = ch.get("channel_id", "")
            if ch_id and not ch_id.startswith("https://"):
                await db.record_channel_join(ch_id, user_id)

    if answer_callback:
        await answer_callback()

    await _deliver_app(bot, user_id, app, lang, reply_to)
    return True


# ─── START ─────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()

    user = await db.get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
    )
    lang = user.get("language", "uz")

    # Handle deep link: /start app_123
    args = message.text.split(maxsplit=1)
    if len(args) > 1 and args[1].startswith("app_"):
        try:
            app_id = int(args[1].replace("app_", ""))
            await _check_and_deliver(
                bot=bot,
                user_id=message.from_user.id,
                app_id=app_id,
                lang=lang,
                reply_to=message,
            )
            return
        except ValueError:
            pass

    # Normal start
    name = message.from_user.first_name or "Foydalanuvchi"
    await message.answer(
        t(lang, "welcome", name=name),
        reply_markup=main_menu(lang),
    )

    if is_admin(message.from_user.id):
        from keyboards import admin_menu
        await message.answer(
            "👨‍💼 <b>Admin buyruqlari:</b>\n"
            "/admin — Admin panel\n"
            "/commandList — Barcha buyruqlar\n"
            "/howToUse — Qo'llanma",
            reply_markup=admin_menu(),
        )


# ─── LANGUAGE ──────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("lang:"))
async def set_language(callback: CallbackQuery, bot: Bot):
    lang = callback.data.split(":")[1]
    user_id = callback.from_user.id
    await db.set_user_language(user_id, lang)

    name = callback.from_user.first_name or "Foydalanuvchi"
    await callback.message.edit_text(t(lang, "language_set"))
    await callback.message.answer(
        t(lang, "welcome", name=name),
        reply_markup=main_menu(lang),
    )

    if is_admin(user_id):
        from keyboards import admin_menu
        await callback.message.answer(
            "👨‍💼 <b>Admin:</b> /admin — panel",
            reply_markup=admin_menu(),
        )

    await callback.answer()


@router.callback_query(F.data == "change_language")
async def change_language(callback: CallbackQuery):
    await callback.message.edit_text(
        t("uz", "choose_language"),
        reply_markup=lang_keyboard(),
    )
    await callback.answer()


# ─── ALL APPS ──────────────────────────────────────────────────────────

ALL_APPS_TEXTS = {t(lang, "all_apps") for lang in ("uz", "ru", "en", "tr", "hi")}

@router.message(F.text.func(lambda txt: txt in {
    "📦 Barcha ilovalar", "📦 Все приложения", "📦 All Apps",
    "📦 Tüm Uygulamalar", "📦 सभी ऐप्स",
}))
async def show_all_apps(message: Message):
    user = await db.get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.full_name
    )
    lang = user.get("language", "uz")
    apps = await db.get_all_apps()

    if not apps:
        await message.answer(t(lang, "no_apps"))
        return

    await message.answer(
        t(lang, "all_apps_header", count=len(apps)),
        reply_markup=apps_list_keyboard(lang, apps),
    )


@router.callback_query(F.data.startswith("apps_page:"))
async def apps_page(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uz"
    page = int(callback.data.split(":")[1])
    apps = await db.get_all_apps()
    await callback.message.edit_reply_markup(
        reply_markup=apps_list_keyboard(lang, apps, page)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("app:"))
async def show_app_detail(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uz"
    app_id = int(callback.data.split(":")[1])
    app = await db.get_app(app_id)

    if not app:
        await callback.answer(t(lang, "app_not_found"), show_alert=True)
        return

    text = build_app_caption(
        lang, app["name"], app.get("description", ""), app["downloads"],
        app.get("platform", "android"), app.get("app_variant", "original")
    )
    kb   = app_detail_keyboard(lang, app_id, is_admin=is_admin(callback.from_user.id))

    if app.get("thumbnail_file_id"):
        await callback.message.answer_photo(
            app["thumbnail_file_id"], caption=text, reply_markup=kb, parse_mode="HTML"
        )
        try:
            await callback.message.delete()
        except Exception:
            pass
    else:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

    await callback.answer()


# ─── DOWNLOAD ──────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("download:"))
async def download_app(callback: CallbackQuery, bot: Bot):
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uz"
    app_id = int(callback.data.split(":")[1])

    await _check_and_deliver(
        bot=bot,
        user_id=callback.from_user.id,
        app_id=app_id,
        lang=lang,
        reply_to=callback.message,
        answer_callback=lambda: callback.answer(t(lang, "downloading")),
    )


# ─── SUBSCRIPTION CHECK ────────────────────────────────────────────────

@router.callback_query(F.data.startswith("check_sub:"))
async def check_subscription(callback: CallbackQuery, bot: Bot):
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uz"
    app_id = int(callback.data.split(":")[1])

    channels = await db.get_active_channels()

    # Tashqi kanallar uchun: foydalanuvchi "Tekshirish" bosganida
    # URL tugmani bosgandek qabul qilamiz — DB ga yozamiz
    for ch in channels:
        ch_id = ch.get("channel_id", "")
        is_external = ch_id.startswith("http://") or ch_id.startswith("https://")
        if is_external:
            try:
                await db.record_join_request(ch_id, callback.from_user.id)
            except Exception:
                pass

    all_sub, unsub = await check_user_subscriptions(bot, callback.from_user.id, channels)

    if not all_sub:
        await callback.answer(t(lang, "not_subscribed"), show_alert=True)
        return

    # A'zolikni qayd etamiz (Telegram kanallar uchun)
    for ch in channels:
        ch_id = ch.get("channel_id", "")
        if ch_id and not ch_id.startswith("http"):
            await db.record_channel_join(ch_id, callback.from_user.id)

    await callback.message.edit_text(t(lang, "subscribed_ok"))
    await callback.answer()

    if app_id > 0:
        app = await db.get_app(app_id)
        if app:
            await _deliver_app(bot, callback.from_user.id, app, lang, callback.message)


# ─── MY DOWNLOADS ──────────────────────────────────────────────────────

@router.message(F.text.func(lambda txt: txt in {
    "📋 Mening yuklamalarim", "📋 Мои загрузки", "📋 My Downloads",
    "📋 İndirmelerim", "📋 मेरे डाउनलोड",
}))
async def my_downloads(message: Message):
    user = await db.get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.full_name
    )
    lang = user.get("language", "uz")
    downloads = await db.get_user_downloads(message.from_user.id)

    if not downloads:
        await message.answer(t(lang, "no_requests"))
        return

    text = t(lang, "downloads_text", count=len(downloads))
    for d in downloads[:20]:
        date_str = str(d.get("downloaded_at", ""))[:10]
        text += t(lang, "downloads_item", name=d["name"], date=date_str)

    await message.answer(text, parse_mode="HTML")


# ─── SETTINGS ──────────────────────────────────────────────────────────

@router.message(F.text.func(lambda txt: txt in {
    "⚙️ Sozlamalar", "⚙️ Настройки", "⚙️ Settings",
    "⚙️ Ayarlar", "⚙️ सेटिंग्स",
}))
async def settings(message: Message):
    user = await db.get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.full_name
    )
    lang = user.get("language", "uz")
    lang_name = LANG_FLAGS.get(lang, "🌐")

    await message.answer(
        t(lang, "settings_text", lang_name=lang_name, user_id=message.from_user.id),
        reply_markup=settings_keyboard(lang),
        parse_mode="HTML",
    )


# ─── CONTACT ADMIN ─────────────────────────────────────────────────────

@router.message(F.text.func(lambda txt: txt in {
    "👨‍💻 Admin bilan bog'lanish", "👨‍💻 Связаться с админом",
    "👨‍💻 Contact Admin", "👨‍💻 Admin ile İletişim", "👨‍💻 एडमिन से संपर्क",
}))
async def contact_admin(message: Message):
    user = await db.get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.full_name
    )
    lang = user.get("language", "uz")

    admin_link = f"@{ADMIN_USERNAME}" if ADMIN_USERNAME else "—"
    kb = None
    if ADMIN_USERNAME:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text=t(lang, "contact_admin_btn"),
                url=f"https://t.me/{ADMIN_USERNAME}",
            )
        ]])

    await message.answer(
        t(lang, "contact_admin_text", admin_link=admin_link),
        reply_markup=kb,
        parse_mode="HTML",
    )


# ─── SEARCH ────────────────────────────────────────────────────────────

# All known menu button texts — skip these from search
_MENU_TEXTS = {
    # User menu buttons
    "📦 Barcha ilovalar", "📦 Все приложения", "📦 All Apps",
    "📦 Tüm Uygulamalar", "📦 सभी ऐप्स",
    "📋 Mening yuklamalarim", "📋 Мои загрузки", "📋 My Downloads",
    "📋 İndirmelerim", "📋 मेरे डाउनलोड",
    "👨‍💻 Admin bilan bog'lanish", "👨‍💻 Связаться с админом",
    "👨‍💻 Contact Admin", "👨‍💻 Admin ile İletişim", "👨‍💻 एडमिन से संपर्क",
    "⚙️ Sozlamalar", "⚙️ Настройки", "⚙️ Settings", "⚙️ Ayarlar", "⚙️ सेटिंग्स",
    "❌ Bekor qilish", "❌ Отмена", "❌ Cancel", "❌ İptal", "❌ रद्द करें",
    "/start", "/admin", "/user", "/commandList", "/howToUse",
    # Admin menu buttons
    "📦 Ilovalar boshqaruvi",
    "📢 Kanallar boshqaruvi",
    "👥 Foydalanuvchilar",
    "📊 Statistika",
    "📣 Xabar yuborish",
    "🗄 Backup olish",
    "🏠 Asosiy menyu",
    "👨‍💼 Admin panel",
}


from aiogram.fsm.state import default_state


@router.message(
    default_state,
    F.text.func(lambda txt: bool(txt and txt not in _MENU_TEXTS and not txt.startswith("/")))
)
async def text_search(message: Message):
    user = await db.get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.full_name
    )
    lang  = user.get("language", "uz")
    query = message.text.strip()

    if len(query) < 2:
        return

    apps = await db.search_apps(query)

    if not apps:
        await message.answer(
            t(lang, "search_no_results", query=query),
            parse_mode="HTML",
        )
        return

    if len(apps) == 1:
        app = apps[0]
        text = build_app_caption(
            lang, app["name"], app.get("description", ""), app["downloads"],
            app.get("platform", "android"), app.get("app_variant", "original")
        )
        kb = app_detail_keyboard(lang, app["id"], is_admin=is_admin(message.from_user.id))
        if app.get("thumbnail_file_id"):
            await message.answer_photo(
                app["thumbnail_file_id"], caption=text,
                reply_markup=kb, parse_mode="HTML"
            )
        else:
            await message.answer(text, reply_markup=kb, parse_mode="HTML")
        return

    # Multiple results — show list (max 6)
    display = apps[:6]
    total   = len(apps)
    await message.answer(
        t(lang, "search_results", query=query, count=total),
        reply_markup=apps_list_keyboard(lang, display),
        parse_mode="HTML",
    )


# ─── CALLBACKS ─────────────────────────────────────────────────────────

@router.callback_query(F.data == "close")
async def close_message(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "back_apps")
async def back_to_apps(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uz"
    apps = await db.get_all_apps()

    if not apps:
        await callback.message.edit_text(t(lang, "no_apps"))
    else:
        await callback.message.edit_text(
            t(lang, "all_apps_header", count=len(apps)),
            reply_markup=apps_list_keyboard(lang, apps),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data == "admin_channels_back")
async def admin_channels_back(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    from keyboards import channels_admin_keyboard
    channels = await db.get_active_channels()
    count    = len(channels)

    await callback.message.edit_text(
        f"📢 <b>Kanallar boshqaruvi</b>\n\nFaol kanallar: <b>{count}</b> ta",
        reply_markup=channels_admin_keyboard(channels),
        parse_mode="HTML",
    )
    await callback.answer()