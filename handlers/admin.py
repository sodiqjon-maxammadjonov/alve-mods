"""
Admin handlers — app management, channel management, stats, broadcast
Admin panel is always in Uzbek language.
"""

import os
import asyncio
import logging
import html as html_module
from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
from keyboards import (
    admin_menu, admin_cancel_keyboard,
    channels_admin_keyboard, channel_detail_keyboard,
    channel_delete_confirm_keyboard, confirm_keyboard,
    apps_list_keyboard, app_detail_keyboard,
    main_menu, channel_post_keyboard,
)
from subscription import (
    validate_channel_detailed, ChannelValidationError,
    get_channel_member_count,
)

logger = logging.getLogger(__name__)
router = Router()

ADMIN_IDS       = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
SECRET_GROUP_ID = os.getenv("SECRET_GROUP_ID", "")
CANCEL_TEXT     = "❌ Bekor qilish"


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def _parse_tg_link(link: str):
    """
    Telegram xabar havolasidan (chat_id, message_id) ni ajratib oladi.
    https://t.me/c/1234567890/99  → private
    https://t.me/username/99      → public
    """
    import re
    link = link.strip().rstrip("/")
    m = re.search(r"t\.me/c/(\d+)/(\d+)", link)
    if m:
        return int(f"-100{m.group(1)}"), int(m.group(2))
    m = re.search(r"t\.me/([A-Za-z][A-Za-z0-9_]{3,})/(\d+)", link)
    if m:
        return f"@{m.group(1)}", int(m.group(2))
    return None


# ─── FSM STATES ────────────────────────────────────────────────────────

class AddAppStates(StatesGroup):
    waiting_name        = State()
    waiting_description = State()
    waiting_platform    = State()
    waiting_variant     = State()
    waiting_photo       = State()
    waiting_file        = State()


class EditAppStates(StatesGroup):
    choosing_field  = State()
    waiting_name    = State()
    waiting_desc    = State()
    waiting_photo   = State()


class AddChannelStates(StatesGroup):
    waiting_channel_id      = State()
    waiting_channel_name    = State()
    waiting_join_numeric_id = State()   # join request link uchun kanal ID so'rash


class BroadcastStates(StatesGroup):
    waiting_message = State()
    confirming      = State()


# ─── CAPTION BUILDER ───────────────────────────────────────────────────

PLATFORM_EMOJI = {"android": "🤖", "desktop": "🖥"}
VARIANT_EMOJI  = {"original": "✅", "mod": "🔓"}
PLATFORM_LABEL = {"android": "Android", "desktop": "Desktop / PC"}
VARIANT_LABEL  = {"original": "Original", "mod": "Modded"}


def build_app_caption(name: str, description: str,
                      platform: str = "android", app_variant: str = "original") -> str:
    desc_clean   = (description or "").strip()
    plat_emoji   = PLATFORM_EMOJI.get(platform, "📱")
    plat_label   = PLATFORM_LABEL.get(platform, platform.title())
    var_emoji    = VARIANT_EMOJI.get(app_variant, "")
    var_label    = VARIANT_LABEL.get(app_variant, app_variant.title())
    return (
        f"<b>{name}</b>\n\n"
        f"{desc_clean}\n\n"
        f"{plat_emoji} <b>Platform:</b> {plat_label}\n"
        f"{var_emoji} <b>Type:</b> {var_label}"
    )


# ─── ADMIN PANEL ───────────────────────────────────────────────────────

@router.message(Command("admin"))
@router.message(F.text == "👨‍💼 Admin panel")
async def admin_panel(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer(
        f"👨‍💼 <b>Admin Panel</b>\n\n"
        f"👤 <b>{message.from_user.full_name}</b>\n\n"
        f"/commandList — Barcha buyruqlar\n"
        f"/howToUse — Qo'llanma\n"
        f"/user — User rejimida sinov",
        reply_markup=admin_menu(),
        parse_mode="HTML",
    )


@router.message(Command("user"))
async def cmd_user_mode(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    user = await db.get_user(message.from_user.id)
    lang = user["language"] if user else "uz"
    await message.answer(
        "👤 <b>[User rejimi — sinov]</b>\n\nUser menyusi:",
        reply_markup=main_menu(lang),
        parse_mode="HTML",
    )


@router.message(Command("commandList"))
async def cmd_command_list(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "📋 <b>Barcha buyruqlar</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👤 <b>Foydalanuvchilar:</b>\n"
        "/start — Botni ishga tushirish\n\n"
        "👨‍💼 <b>Adminlar:</b>\n"
        "/admin — Admin panel\n"
        "/user — User rejimida sinov\n"
        "/commandList — Buyruqlar ro'yxati\n"
        "/howToUse — Qo'llanma\n\n"
        "📱 <b>Admin panel:</b>\n"
        "📦 Ilovalar — qo'shish/tahrirlash/o'chirish\n"
        "📢 Kanallar — qo'shish/o'chirish\n"
        "👥 Foydalanuvchilar — statistika\n"
        "📊 Statistika — umumiy\n"
        "📣 Broadcast — xabar yuborish",
        parse_mode="HTML",
    )


@router.message(Command("howToUse"))
async def cmd_how_to_use(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "📖 <b>Bot qo'llanmasi</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "1️⃣ <b>Kanal qo'shish:</b>\n"
        "   • Botni kanalingizga admin qiling\n"
        "   • 📢 Kanallar → ➕ Kanal qo'shish\n"
        "   • @username yoki -100ID kiriting\n\n"
        "2️⃣ <b>Ilova qo'shish:</b>\n"
        "   • 📦 Ilovalar → ➕ Ilova qo'shish\n"
        "   • Nom va tavsif kiriting\n"
        "   • Faylni to'g'ridan-to'g'ri yuboring\n"
        "   • Yoki guruhdan forward qiling\n"
        "   • Yoki: <code>https://t.me/c/ID/MSGID</code>\n\n"
        "3️⃣ <b>Ilova tahrirlash:</b>\n"
        "   • 📦 Ilovalar → ilovani tanlang → ✏️ Tahrirlash\n\n"
        "4️⃣ <b>Broadcast:</b>\n"
        "   • 📣 Xabar yuborish → xabar yozing",
        parse_mode="HTML",
    )


# ─── STATS ─────────────────────────────────────────────────────────────

@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    users     = await db.get_users_count()
    apps      = await db.get_apps_count()
    downloads = await db.get_total_downloads()
    channels  = await db.get_channels_count()
    today     = await db.get_today_users_count()

    from locales import t
    await message.answer(
        t("uz", "stats_text",
          users=users, apps=apps, downloads=downloads,
          channels=channels, today_users=today),
        reply_markup=admin_menu(),
        parse_mode="HTML",
    )


@router.message(F.text == "🏠 Asosiy menyu")
async def back_to_user_menu(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    user = await db.get_user(message.from_user.id)
    lang = user["language"] if user else "uz"
    name = message.from_user.first_name or "Admin"
    from locales import t
    await message.answer(
        t(lang, "welcome", name=name),
        reply_markup=main_menu(lang),
        parse_mode="HTML",
    )


# ─── APPS MANAGEMENT ───────────────────────────────────────────────────

@router.message(F.text == "📦 Ilovalar boshqaruvi")
async def apps_management(message: Message):
    if not is_admin(message.from_user.id):
        return
    apps = await db.get_all_apps(active_only=False)

    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Yangi ilova qo'shish", callback_data="start_add_app")
    for app in apps[:20]:
        builder.button(
            text=f"✅ {app['name']} ⬇{app['downloads']}",
            callback_data=f"admin_app:{app['id']}",
        )
    builder.adjust(1)

    await message.answer(
        f"📦 <b>Ilovalar boshqaruvi</b>\n\nJami: <b>{len(apps)}</b> ta ilova",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


# ─── ADD APP ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "start_add_app")
async def start_add_app(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.answer(
        "📝 <b>Ilova nomini kiriting:</b>",
        reply_markup=admin_cancel_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(AddAppStates.waiting_name)
    await callback.answer()


@router.message(AddAppStates.waiting_name)
async def app_name_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == CANCEL_TEXT:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())
        return
    if not message.text:
        await message.answer("❗ Iltimos matn kiriting:")
        return
    await state.update_data(name=message.text.strip())
    await message.answer(
        "📄 <b>Ilova haqida ma'lumot kiriting:</b>\n\n"
        "Har bir xususiyatni alohida qatorda yozing.",
        reply_markup=admin_cancel_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(AddAppStates.waiting_description)


@router.message(AddAppStates.waiting_description)
async def app_desc_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == CANCEL_TEXT:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())
        return
    if not message.text:
        await message.answer("❗ Iltimos matn kiriting:")
        return
    await state.update_data(description=message.text.strip())
    await _ask_platform(message)
    await state.set_state(AddAppStates.waiting_platform)


async def _ask_platform(target):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🤖 Android",     callback_data="set_platform:android"),
            InlineKeyboardButton(text="🖥 Desktop / PC", callback_data="set_platform:desktop"),
        ]
    ])
    txt = "📱 <b>Platformani tanlang:</b>"
    # CallbackQuery.answer() faqat toast ko'rsatadi, reply_markup ni qabul qilmaydi!
    # Shuning uchun har doim message.answer() ishlatamiz
    if isinstance(target, CallbackQuery):
        await target.message.answer(txt, reply_markup=kb, parse_mode="HTML")
    else:
        await target.answer(txt, reply_markup=kb, parse_mode="HTML")


async def _ask_variant(target):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Original", callback_data="set_variant:original"),
            InlineKeyboardButton(text="🔓 Mod",      callback_data="set_variant:mod"),
        ]
    ])
    txt = "🔧 <b>Ilova turini tanlang:</b>"
    # BUG FIX: CallbackQuery.answer() = faqat popup toast, reply_markup ni ko'rsatmaydi!
    # Har doim message.answer() ishlatish kerak
    if isinstance(target, CallbackQuery):
        await target.message.answer(txt, reply_markup=kb, parse_mode="HTML")
    else:
        await target.answer(txt, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("set_platform:"), AddAppStates.waiting_platform)
async def platform_chosen(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    platform = callback.data.split(":")[1]
    await state.update_data(platform=platform)
    await callback.answer()
    await _ask_variant(callback)
    await state.set_state(AddAppStates.waiting_variant)


@router.callback_query(F.data.startswith("set_variant:"), AddAppStates.waiting_variant)
async def variant_chosen(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    variant = callback.data.split(":")[1]
    await state.update_data(app_variant=variant)
    await callback.answer()

    # Rasm/video so'rash — skip tugmasi reply keyboard sifatida
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    skip_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⏭ Rasmsiz davom etish")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await callback.message.answer(
        "🖼 <b>Ilova uchun rasm yoki video yuboring:</b>\n\n"
        "📸 Bir yoki bir nechta rasm yuboring (max 10 ta)\n"
        "🎥 Yoki bitta video yuboring\n"
        "⏭ Ixtiyoriy — qo'shmaslik mumkin",
        reply_markup=skip_kb,
        parse_mode="HTML",
    )
    await state.update_data(media_group=[])
    await state.set_state(AddAppStates.waiting_photo)


async def _proceed_to_file_step(message: Message, state: FSMContext):
    """Ask for the app file after photo step."""
    group_link = (
        f"https://t.me/c/{SECRET_GROUP_ID.replace('-100', '')}"
        if SECRET_GROUP_ID else "maxfiy guruh"
    )
    await message.answer(
        f"📎 <b>Endi ilovani yuboring:</b>\n\n"
        f"• Faylni to'g'ridan-to'g'ri yuboring ✅ (tavsiya)\n"
        f"• Yoki guruhdan forward qiling\n"
        f"• Yoki havola: <code>https://t.me/c/ID/MSGID</code>\n\n"
        f"💡 Guruh: {group_link}",
        reply_markup=admin_cancel_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(AddAppStates.waiting_file)


@router.callback_query(F.data == "skip_app_photo")
async def skip_app_photo(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    await _proceed_to_file_step(callback.message, state)


@router.message(AddAppStates.waiting_photo)
async def app_photo_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == CANCEL_TEXT:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())
        return

    # Skip tugmasi bosilgan
    if message.text == "⏭ Rasmsiz davom etish":
        await state.update_data(media_group=[])
        await _proceed_to_file_step(message, state)
        return

    data = await state.get_data()
    media_group = data.get("media_group", [])

    if len(media_group) >= 10:
        await message.answer("⚠️ Maksimal 10 ta media qo'shish mumkin. ➡️ tugmasini bosing.")
        return

    next_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="➡️ Faylga o'tish", callback_data="photos_done")
    ]])

    if message.photo:
        file_id = message.photo[-1].file_id
        media_group.append({"type": "photo", "file_id": file_id})
        await state.update_data(media_group=media_group)
        if not message.media_group_id:
            await message.answer(
                f"✅ {len(media_group)} ta rasm qabul qilindi.\n"
                f"Yana rasm yuborishingiz yoki faylga o'tishingiz mumkin (max 10 ta).",
                reply_markup=next_kb,
            )
    elif message.video:
        media_group.append({"type": "video", "file_id": message.video.file_id})
        await state.update_data(media_group=media_group)
        await message.answer(
            "✅ Video qabul qilindi.",
            reply_markup=next_kb,
        )
    else:
        await message.answer("❗ Rasm yoki video yuboring, yoki '⏭ Rasmsiz davom etish' tugmasini bosing.")


@router.callback_query(F.data == "photos_done")
async def photos_done(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    await _proceed_to_file_step(callback.message, state)


@router.message(AddAppStates.waiting_file)
async def app_file_received(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    if message.text == CANCEL_TEXT:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())
        return

    data = await state.get_data()
    file_id      = None
    thumbnail_id = None
    src_chat_id  = None
    src_msg_id   = None

    # 1. To'g'ridan-to'g'ri fayl
    if message.document:
        file_id     = message.document.file_id
        src_chat_id = message.chat.id
        src_msg_id  = message.message_id
        if message.document.thumbnail:
            thumbnail_id = message.document.thumbnail.file_id
    elif message.photo:
        file_id     = message.photo[-1].file_id
        src_chat_id = message.chat.id
        src_msg_id  = message.message_id

    # 2. Forward
    elif message.forward_from_chat:
        src_chat_id = message.forward_from_chat.id
        src_msg_id  = getattr(message, "forward_from_message_id", None)
        if not src_msg_id:
            await message.answer(
                "❌ Forward qilingan xabardan ID olib bo'lmadi.\n"
                "Iltimos to'g'ridan-to'g'ri fayl yuboring."
            )
            return

    # 3. Telegram havola
    elif message.text:
        link   = message.text.strip()
        parsed = _parse_tg_link(link)
        if not parsed:
            await message.answer(
                "❌ <b>Noto'g'ri format!</b>\n\n"
                "Quyidagilardan birini yuboring:\n"
                "• Fayl to'g'ridan-to'g'ri\n"
                "• Guruhdan forward\n"
                "• Havola: <code>https://t.me/c/1234567890/99</code>",
                parse_mode="HTML",
            )
            return

        raw_chat_id, raw_msg_id = parsed
        try:
            fwd = await bot.forward_message(
                chat_id=message.chat.id,
                from_chat_id=raw_chat_id,
                message_id=raw_msg_id,
            )
            src_chat_id = raw_chat_id
            src_msg_id  = raw_msg_id
            if fwd.document:
                file_id = fwd.document.file_id
                if fwd.document.thumbnail:
                    thumbnail_id = fwd.document.thumbnail.file_id
            elif fwd.photo:
                file_id = fwd.photo[-1].file_id
            try:
                await fwd.delete()
            except Exception:
                pass
        except Exception as e:
            err = str(e).lower()
            if "chat not found" in err:
                reason = "Guruh/kanal topilmadi — botni o'sha guruhga admin qiling"
            elif "message not found" in err or "invalid" in err:
                reason = "Xabar topilmadi — link ID si noto'g'ri"
            elif "forbidden" in err or "rights" in err:
                reason = "Bot o'sha guruhda admin emas"
            else:
                reason = "Telegram server xatosi — qayta urinib ko'ring"
            await message.answer(
                f"❌ <b>Xabarni olib bo'lmadi!</b>\n\n"
                f"Sabab: {reason}\n\n"
                f"Yoki faylni to'g'ridan-to'g'ri yuboring.",
                parse_mode="HTML",
            )
            return
    else:
        await message.answer(
            "❗ Fayl, forward yoki havola yuboring.\n"
            "Misol: <code>https://t.me/c/1234567890/99</code>",
            parse_mode="HTML",
        )
        return

    app_id = await db.add_app(
        name=data["name"],
        description=data["description"],
        app_type="app",
        platform=data.get("platform", "android"),
        app_variant=data.get("app_variant", "original"),
        file_id=file_id,
        file_link=None,
        thumbnail_file_id=thumbnail_id,
        created_by=message.from_user.id,
        src_chat_id=src_chat_id,
        src_message_id=src_msg_id,
    )

    # Save media_group file_ids to DB (store as JSON string in thumbnail_file_id if multiple)
    media_group = data.get("media_group", [])
    if media_group and not thumbnail_id:
        # Store first photo as thumbnail, rest as json in a new field (we use thumbnail_file_id for first)
        first = media_group[0]["file_id"]
        await db.update_app(app_id, thumbnail_file_id=first)
        # Store all media as JSON in description suffix — we'll store in a dedicated way
        import json
        media_json = json.dumps(media_group)
        await db.update_app(app_id, media_group_json=media_json)
    elif media_group and thumbnail_id:
        import json
        media_json = json.dumps(media_group)
        await db.update_app(app_id, media_group_json=media_json)

    await state.clear()

    me         = await bot.get_me()
    caption    = build_app_caption(
        data["name"], data["description"],
        data.get("platform", "android"), data.get("app_variant", "original")
    )
    download_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="⬇️ Download",
            url=f"https://t.me/{me.username}?start=app_{app_id}"
        )
    ]])

    await message.answer(
        f"✅ <b>Ilova qo'shildi!</b>\n\n📱 <b>{data['name']}</b>\n\n"
        f"👇 Kanal uchun tayyor post:",
        reply_markup=admin_menu(),
        parse_mode="HTML",
    )

    # Send channel post: photo(s) if any, then caption + Download button
    if media_group:
        if len(media_group) == 1:
            m = media_group[0]
            if m["type"] == "photo":
                await message.answer_photo(
                    photo=m["file_id"],
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=download_kb,
                )
            else:
                await message.answer_video(
                    video=m["file_id"],
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=download_kb,
                )
        else:
            from aiogram.types import InputMediaPhoto, InputMediaVideo
            media_list = []
            for i, m in enumerate(media_group):
                cap = caption if i == 0 else None
                if m["type"] == "photo":
                    media_list.append(InputMediaPhoto(media=m["file_id"], caption=cap, parse_mode="HTML"))
                else:
                    media_list.append(InputMediaVideo(media=m["file_id"], caption=cap, parse_mode="HTML"))
            await message.answer_media_group(media=media_list)
            # Send Download button separately after media group
            await message.answer("👆 Kanal uchun post yuqorida.", reply_markup=download_kb)
    else:
        # No photo — just text post with Download button
        try:
            await bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=src_chat_id,
                message_id=src_msg_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=download_kb,
            )
        except Exception:
            await message.answer(caption, parse_mode="HTML", reply_markup=download_kb)


# ─── ADMIN APP DETAIL ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin_app:"))
async def admin_app_detail(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        return
    app_id   = int(callback.data.split(":")[1])
    all_apps = await db.get_all_apps(active_only=False)
    app      = next((a for a in all_apps if a["id"] == app_id), None)

    if not app:
        await callback.answer("Topilmadi", show_alert=True)
        return

    created = str(app.get("created_at", ""))[:10]
    text = (
        f"📱 <b>{app['name']}</b>\n\n"
        f"📄 {app.get('description') or '—'}\n\n"
        f"⬇️ Yuklamalar: <b>{app['downloads']}</b>\n"
        f"📅 Qo'shilgan: <b>{created}</b>"
    )
    me = await bot.get_me()
    builder = InlineKeyboardBuilder()
    builder.button(text="⬇️ Download",       url=f"https://t.me/{me.username}?start=app_{app_id}")
    builder.button(text="💬 Xabarni ko'rish", callback_data=f"admin_show_post:{app_id}")
    builder.button(text="✏️ Tahrirlash",      callback_data=f"admin_edit_app:{app_id}")
    builder.button(text="🗑 O'chirish",       callback_data=f"admin_del_confirm:{app_id}")
    builder.button(text="◀️ Orqaga",          callback_data="back_apps_admin")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "back_apps_admin")
async def back_apps_admin(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    apps = await db.get_all_apps(active_only=False)
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Yangi ilova qo'shish", callback_data="start_add_app")
    for app in apps[:20]:
        builder.button(
            text=f"✅ {app['name']} ⬇{app['downloads']}",
            callback_data=f"admin_app:{app['id']}",
        )
    builder.adjust(1)
    await callback.message.edit_text(
        f"📦 <b>Ilovalar boshqaruvi</b>\n\nJami: <b>{len(apps)}</b> ta ilova",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_show_post:"))
async def admin_show_post(callback: CallbackQuery, bot: Bot):
    """Show the channel post preview (photo + name + description + Download button)"""
    if not is_admin(callback.from_user.id):
        return
    app_id   = int(callback.data.split(":")[1])
    all_apps = await db.get_all_apps(active_only=False)
    app      = next((a for a in all_apps if a["id"] == app_id), None)
    if not app:
        await callback.answer("Topilmadi", show_alert=True)
        return

    me       = await bot.get_me()
    caption  = build_app_caption(
        app["name"], app.get("description", ""),
        app.get("platform", "android"), app.get("app_variant", "original")
    )
    download_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⬇️ Download", url=f"https://t.me/{me.username}?start=app_{app_id}")
    ]])

    await callback.answer()

    # Check for media
    import json
    media_json = app.get("media_group_json")
    media_group = []
    if media_json:
        try:
            media_group = json.loads(media_json)
        except Exception:
            pass

    if media_group:
        if len(media_group) == 1:
            m = media_group[0]
            if m["type"] == "photo":
                await callback.message.answer_photo(
                    photo=m["file_id"], caption=caption,
                    parse_mode="HTML", reply_markup=download_kb
                )
            else:
                await callback.message.answer_video(
                    video=m["file_id"], caption=caption,
                    parse_mode="HTML", reply_markup=download_kb
                )
        else:
            from aiogram.types import InputMediaPhoto, InputMediaVideo
            media_list = []
            for i, m in enumerate(media_group):
                cap = caption if i == 0 else None
                if m["type"] == "photo":
                    media_list.append(InputMediaPhoto(media=m["file_id"], caption=cap, parse_mode="HTML"))
                else:
                    media_list.append(InputMediaVideo(media=m["file_id"], caption=cap, parse_mode="HTML"))
            await callback.message.answer_media_group(media=media_list)
            await callback.message.answer("⬆️ Post yuqorida.", reply_markup=download_kb)
    elif app.get("thumbnail_file_id"):
        await callback.message.answer_photo(
            photo=app["thumbnail_file_id"], caption=caption,
            parse_mode="HTML", reply_markup=download_kb
        )
    else:
        await callback.message.answer(caption, parse_mode="HTML", reply_markup=download_kb)


# ─── DELETE APP (tasdiqlash bilan) ─────────────────────────────────────

@router.callback_query(F.data.startswith("admin_del_confirm:"))
async def admin_del_confirm(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    app_id   = int(callback.data.split(":")[1])
    all_apps = await db.get_all_apps(active_only=False)
    app      = next((a for a in all_apps if a["id"] == app_id), None)
    if not app:
        await callback.answer("Topilmadi", show_alert=True)
        return

    await callback.message.edit_text(
        f"⚠️ <b>Ilovani o'chirishni tasdiqlang</b>\n\n"
        f"📱 <b>{app['name']}</b>\n\n"
        f"Bu ilova butunlay o'chiriladi va qaytib chiqmaydi!\n"
        f"Ishonchingiz komilmi?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Ha, o'chirish",  callback_data=f"admin_del_yes:{app_id}"),
            InlineKeyboardButton(text="❌ Yo'q, bekor",    callback_data=f"admin_app:{app_id}"),
        ]]),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_del_yes:"))
async def admin_delete_app_confirmed(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    app_id = int(callback.data.split(":")[1])
    await db.delete_app(app_id)
    await callback.message.edit_text(
        "✅ <b>Ilova butunlay o'chirildi!</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="◀️ Ilovalar ro'yxati", callback_data="back_apps_admin")
        ]]),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── EDIT APP ──────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin_edit_app:"))
async def admin_edit_app(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    app_id = int(callback.data.split(":")[1])
    await state.update_data(edit_app_id=app_id)

    await callback.message.edit_text(
        "✏️ <b>Nimani tahrirlash?</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Nomni o'zgartirish",       callback_data=f"edit_field:name:{app_id}")],
            [InlineKeyboardButton(text="📄 Tavsifni o'zgartirish",    callback_data=f"edit_field:desc:{app_id}")],
            [InlineKeyboardButton(text="📱 Platformani o'zgartirish", callback_data=f"edit_field:platform:{app_id}")],
            [InlineKeyboardButton(text="🔧 Turini o'zgartirish",      callback_data=f"edit_field:variant:{app_id}")],
            [InlineKeyboardButton(text="🖼 Rasmni tahrirlash",        callback_data=f"edit_field:photo:{app_id}")],
            [InlineKeyboardButton(text="◀️ Orqaga",                   callback_data=f"admin_app:{app_id}")],
        ]),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_field:"))
async def edit_field_chosen(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    parts  = callback.data.split(":")
    field  = parts[1]
    app_id = int(parts[2])
    await state.update_data(edit_app_id=app_id, edit_field=field)

    if field == "name":
        await callback.message.answer(
            "📝 <b>Yangi nom kiriting:</b>",
            reply_markup=admin_cancel_keyboard(),
            parse_mode="HTML",
        )
        await state.set_state(EditAppStates.waiting_name)
    elif field == "desc":
        await callback.message.answer(
            "📄 <b>Yangi tavsif kiriting:</b>\n\nHar bir xususiyat alohida qatorda.",
            reply_markup=admin_cancel_keyboard(),
            parse_mode="HTML",
        )
        await state.set_state(EditAppStates.waiting_desc)
    elif field == "platform":
        await callback.message.answer(
            "📱 <b>Yangi platformani tanlang:</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🤖 Android",      callback_data=f"edit_platform_set:{app_id}:android"),
                InlineKeyboardButton(text="🖥 Desktop / PC", callback_data=f"edit_platform_set:{app_id}:desktop"),
            ]]),
            parse_mode="HTML",
        )
    elif field == "variant":
        await callback.message.answer(
            "🔧 <b>Yangi turni tanlang:</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="✅ Original", callback_data=f"edit_variant_set:{app_id}:original"),
                InlineKeyboardButton(text="🔓 Mod",      callback_data=f"edit_variant_set:{app_id}:mod"),
            ]]),
            parse_mode="HTML",
        )
    elif field == "photo":
        # Mavjud medialarni ko'rsatish
        import json
        all_apps = await db.get_all_apps(active_only=False)
        app      = next((a for a in all_apps if a["id"] == app_id), None)
        media_group = []
        if app and app.get("media_group_json"):
            try:
                media_group = json.loads(app["media_group_json"])
            except Exception:
                pass

        if media_group:
            # Har bir media uchun tugmalar
            rows = []
            for i, m in enumerate(media_group):
                emoji = "🖼" if m["type"] == "photo" else "🎥"
                rows.append([
                    InlineKeyboardButton(
                        text=f"{emoji} {m['type'].title()} {i+1} — 🗑 O'chirish",
                        callback_data=f"edit_media_del:{app_id}:{i}"
                    )
                ])
            rows.append([InlineKeyboardButton(text="➕ Yangi rasm/video qo'shish", callback_data=f"edit_photo_add:{app_id}")])
            rows.append([InlineKeyboardButton(text="🗑 Hammasini o'chirish", callback_data=f"edit_photo_delete:{app_id}")])
            rows.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data=f"admin_edit_app:{app_id}")])
            await callback.message.answer(
                f"🖼 <b>Mavjud medialar ({len(media_group)} ta):</b>\n\n"
                "Har birini alohida o'chirish yoki yangi qo'shish mumkin:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
                parse_mode="HTML",
            )
        else:
            builder = InlineKeyboardBuilder()
            builder.button(text="➕ Rasm/video qo'shish",  callback_data=f"edit_photo_add:{app_id}")
            builder.button(text="◀️ Orqaga",               callback_data=f"admin_edit_app:{app_id}")
            builder.adjust(1)
            await callback.message.answer(
                "🖼 <b>Rasm tahrirlash:</b>\n\nHozircha rasm yo'q.",
                reply_markup=builder.as_markup(),
                parse_mode="HTML",
            )

    await callback.answer()


@router.message(EditAppStates.waiting_name)
async def edit_name_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == CANCEL_TEXT:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())
        return
    data   = await state.get_data()
    app_id = data["edit_app_id"]
    await db.update_app(app_id, name=message.text.strip())
    await state.clear()
    await message.answer(
        f"✅ <b>Ilova nomi yangilandi!</b>",
        reply_markup=admin_menu(),
        parse_mode="HTML",
    )


@router.message(EditAppStates.waiting_desc)
async def edit_desc_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == CANCEL_TEXT:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())
        return
    data   = await state.get_data()
    app_id = data["edit_app_id"]
    await db.update_app(app_id, description=message.text.strip())
    await state.clear()
    await message.answer(
        "✅ <b>Ilova tavsifi yangilandi!</b>",
        reply_markup=admin_menu(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("edit_platform_set:"))
async def edit_platform_set(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    _, app_id_str, platform = callback.data.split(":")
    app_id = int(app_id_str)
    await db.update_app(app_id, platform=platform)
    label = "Android" if platform == "android" else "Desktop / PC"
    await callback.message.edit_text(
        f"✅ <b>Platform yangilandi:</b> {label}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="◀️ Ilovaga qaytish", callback_data=f"admin_app:{app_id}")
        ]]),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_variant_set:"))
async def edit_variant_set(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    _, app_id_str, variant = callback.data.split(":")
    app_id = int(app_id_str)
    await db.update_app(app_id, app_variant=variant)
    label = "Original" if variant == "original" else "Mod"
    await callback.message.edit_text(
        f"✅ <b>Tur yangilandi:</b> {label}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="◀️ Ilovaga qaytish", callback_data=f"admin_app:{app_id}")
        ]]),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_media_del:"))
async def edit_media_del_one(callback: CallbackQuery):
    """Bitta media elementini o'chirish"""
    if not is_admin(callback.from_user.id):
        return
    import json
    parts  = callback.data.split(":")
    app_id = int(parts[1])
    idx    = int(parts[2])

    all_apps = await db.get_all_apps(active_only=False)
    app      = next((a for a in all_apps if a["id"] == app_id), None)
    if not app:
        await callback.answer("Topilmadi", show_alert=True)
        return

    media_group = []
    if app.get("media_group_json"):
        try:
            media_group = json.loads(app["media_group_json"])
        except Exception:
            pass

    if 0 <= idx < len(media_group):
        media_group.pop(idx)

    if media_group:
        first    = media_group[0]["file_id"]
        media_js = json.dumps(media_group)
        await db.update_app(app_id, thumbnail_file_id=first, media_group_json=media_js)
        msg = f"✅ Media o'chirildi! Qolgan: {len(media_group)} ta"
    else:
        await db.update_app(app_id, thumbnail_file_id=None, media_group_json=None)
        msg = "✅ Barcha medialar o'chirildi!"

    await callback.message.edit_text(
        msg,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="◀️ Ilovaga qaytish", callback_data=f"admin_app:{app_id}")
        ]]),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_photo_delete:"))
async def edit_photo_delete(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    app_id = int(callback.data.split(":")[1])
    await db.update_app(app_id, thumbnail_file_id=None, media_group_json=None)
    await callback.message.edit_text(
        "✅ <b>Rasmlar o'chirildi!</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="◀️ Ilovaga qaytish", callback_data=f"admin_app:{app_id}")
        ]]),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_photo_add:"))
async def edit_photo_add(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    app_id = int(callback.data.split(":")[1])
    await state.update_data(edit_app_id=app_id, edit_field="photo", media_group=[])
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tayyor", callback_data="edit_photo_done")
    await callback.message.answer(
        "🖼 <b>Yangi rasm(lar) yuboring:</b>\n\n"
        "• Bir yoki bir nechta rasm yuboring\n"
        "• Yoki video yuboring\n"
        "• Tayyor bo'lgach ✅ Tayyor bosing",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )
    await state.set_state(EditAppStates.waiting_photo)
    await callback.answer()


@router.message(EditAppStates.waiting_photo)
async def edit_photo_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == CANCEL_TEXT:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())
        return

    data        = await state.get_data()
    media_group = data.get("media_group", [])

    if message.photo:
        media_group.append({"type": "photo", "file_id": message.photo[-1].file_id})
        await state.update_data(media_group=media_group)
        await message.answer(
            f"✅ {len(media_group)} ta rasm qabul qilindi. Yana yuborishingiz yoki Tayyor bosishingiz mumkin.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="✅ Tayyor", callback_data="edit_photo_done")
            ]]),
        )
    elif message.video:
        media_group.append({"type": "video", "file_id": message.video.file_id})
        await state.update_data(media_group=media_group)
        await message.answer(
            "✅ Video qabul qilindi.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="✅ Tayyor", callback_data="edit_photo_done")
            ]]),
        )
    else:
        await message.answer("❗ Rasm yoki video yuboring.")


@router.callback_query(F.data == "edit_photo_done")
async def edit_photo_done(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    data        = await state.get_data()
    app_id      = data.get("edit_app_id")
    media_group = data.get("media_group", [])

    if not media_group:
        await callback.answer("❗ Hech qanday rasm yuborilmadi.", show_alert=True)
        return

    import json
    first    = media_group[0]["file_id"]
    media_js = json.dumps(media_group)
    await db.update_app(app_id, thumbnail_file_id=first, media_group_json=media_js)
    await state.clear()
    await callback.message.edit_text(
        f"✅ <b>{len(media_group)} ta rasm saqlandi!</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="◀️ Ilovaga qaytish", callback_data=f"admin_app:{app_id}")
        ]]),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── CHANNELS MANAGEMENT ───────────────────────────────────────────────

@router.message(F.text == "📢 Kanallar boshqaruvi")
async def channels_management(message: Message):
    if not is_admin(message.from_user.id):
        return
    channels = await db.get_active_channels()
    if not channels:
        await message.answer(
            "📭 Hozircha kanallar yo'q.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="add_channel")
            ]])
        )
        return
    await message.answer(
        f"📢 <b>Kanallar boshqaruvi</b>\n\nFaol kanallar: <b>{len(channels)}</b> ta",
        reply_markup=channels_admin_keyboard(channels),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "add_channel")
async def add_channel_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.answer(
        "📢 <b>Kanal username, ID yoki invite link kiriting:</b>\n\n"
        "Misol: <code>@mening_kanalim</code>\n"
        "Yoki: <code>-1001234567890</code>\n"
        "Yoki join request link: <code>https://t.me/+xxxxxxxx</code>",
        reply_markup=admin_cancel_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(AddChannelStates.waiting_channel_id)
    await callback.answer()


@router.message(AddChannelStates.waiting_channel_id)
async def channel_id_received(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    if message.text == CANCEL_TEXT:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())
        return

    raw_input = message.text.strip()

    # Join request link (https://t.me/+xxxx) — kanal ID ni alohida so'raymiz
    import re
    is_join_link = bool(re.match(r"https?://t\.me/\+[A-Za-z0-9_-]+", raw_input))

    if is_join_link:
        # Join link ni saqlab, kanal ID ni so'raymiz
        await state.update_data(join_invite_link=raw_input)
        await message.answer(
            "🔗 <b>Join request havola qabul qilindi!</b>\n\n"
            "Endi bot a'zolikni tekshira olishi uchun kanalning <b>raqamli ID sini</b> kiriting:\n\n"
            "📌 Raqamli ID ni qanday topish:\n"
            "• Botingizni kanalga admin qilib, @userinfobot ga forward qiling\n"
            "• Yoki: Settings → Channel Info → Share → link dan <code>-100...</code> ID olish\n\n"
            "Misol: <code>-1001234567890</code>",
            reply_markup=admin_cancel_keyboard(),
            parse_mode="HTML",
        )
        await state.set_state(AddChannelStates.waiting_join_numeric_id)
        return

    wait_msg = await message.answer("🔍 Kanal tekshirilmoqda...")

    try:
        info = await validate_channel_detailed(bot, raw_input)
        try:
            await wait_msg.delete()
        except Exception:
            pass
    except ChannelValidationError as e:
        try:
            await wait_msg.delete()
        except Exception:
            pass
        await message.answer(
            str(e),
            reply_markup=admin_cancel_keyboard(),
            parse_mode="HTML",
        )
        return
    except Exception:
        try:
            await wait_msg.delete()
        except Exception:
            pass
        await message.answer(
            "❌ <b>Kutilmagan xato yuz berdi.</b>\n\nQayta urinib ko'ring.",
            reply_markup=admin_cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    channel_id_to_store = info.get("numeric_id") or raw_input

    name  = info["title"]
    added = await db.add_channel(
        channel_id=channel_id_to_store,
        channel_name=name,
        invite_link=info.get("invite_link"),
        added_by=message.from_user.id,
    )
    await state.clear()

    text = f"✅ <b>Kanal qo'shildi!</b>\n\n📢 <b>{name}</b>\n🆔 <code>{channel_id_to_store}</code>"
    if info.get("invite_warning"):
        text += f"\n\n{info['invite_warning']}"

    await message.answer(text, reply_markup=admin_menu(), parse_mode="HTML")


@router.message(AddChannelStates.waiting_join_numeric_id)
async def join_numeric_id_received(message: Message, state: FSMContext, bot: Bot):
    """Join request link uchun kanal raqamli ID qabul qilish va tekshirish"""
    if not is_admin(message.from_user.id):
        return
    if message.text == CANCEL_TEXT:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())
        return

    raw_input = message.text.strip()
    data      = await state.get_data()
    join_link = data.get("join_invite_link", "")

    wait_msg = await message.answer("🔍 Kanal tekshirilmoqda...")

    try:
        info = await validate_channel_detailed(bot, raw_input)
        try:
            await wait_msg.delete()
        except Exception:
            pass
    except ChannelValidationError as e:
        try:
            await wait_msg.delete()
        except Exception:
            pass
        await message.answer(
            str(e) + "\n\n💡 Raqamli ID ni to'g'ri kiriting (masalan: <code>-1001234567890</code>)",
            reply_markup=admin_cancel_keyboard(),
            parse_mode="HTML",
        )
        return
    except Exception:
        try:
            await wait_msg.delete()
        except Exception:
            pass
        await message.answer(
            "❌ <b>Kutilmagan xato.</b> Qayta urinib ko'ring.",
            reply_markup=admin_cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    channel_id_to_store = info.get("numeric_id") or raw_input
    name  = info["title"]
    # invite_link = join request havola (foydalanuvchilarga ko'rsatiladi)
    added = await db.add_channel(
        channel_id=channel_id_to_store,
        channel_name=name,
        invite_link=join_link,        # ← join request link tugmada ko'rsatiladi
        added_by=message.from_user.id,
    )
    await state.clear()

    if added:
        await message.answer(
            f"✅ <b>Join request kanal qo'shildi!</b>\n\n"
            f"📢 <b>{name}</b>\n"
            f"🆔 <code>{channel_id_to_store}</code>\n"
            f"🔗 {join_link}\n\n"
            f"✅ Bot endi a'zolikni tekshira oladi!\n"
            f"👥 Foydalanuvchilar join request link orqali kanalga kiradi,\n"
            f"   siz tasdiqlaysiz — bot ularni a'zo sifatida tekshiradi.",
            reply_markup=admin_menu(),
            parse_mode="HTML",
        )
    else:
        await message.answer("⚠️ Bu kanal allaqachon ro'yxatda.", reply_markup=admin_menu())


@router.callback_query(F.data.startswith("ch_detail:"))
async def channel_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    ch_db_id = int(callback.data.split(":")[1])
    channels = await db.get_all_channels()
    ch       = next((c for c in channels if c["id"] == ch_db_id), None)
    if not ch:
        await callback.answer("Topilmadi", show_alert=True)
        return

    stats  = await db.get_channel_join_stats(ch["channel_id"])
    added  = str(ch.get("added_at", ""))[:10]

    text = (
        f"📢 <b>{ch['channel_name']}</b>\n\n"
        f"🆔 ID: <code>{ch['channel_id']}</code>\n"
        f"📅 Qo'shilgan: <b>{added}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 <b>Bot orqali statistika:</b>\n"
        f"👥 Jami qo'shilganlar: <b>{stats['total_joined']}</b>\n"
        f"✅ Hozirda faol: <b>{stats['currently_active']}</b>\n"
        f"❌ Chiqib ketganlar: <b>{stats['left_count']}</b>"
    )
    await callback.message.edit_text(
        text,
        reply_markup=channel_detail_keyboard(ch_db_id, ch["channel_id"]),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ch_stats:"))
async def channel_stats(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        return
    ch_id    = callback.data.split(":")[1]
    count    = await get_channel_member_count(bot, ch_id)
    await db.update_channel_subscribers(ch_id, count)
    stats    = await db.get_channel_join_stats(ch_id)
    jr_count = await db.get_join_request_count(ch_id)
    await callback.answer(
        f"📊 Kanal statistikasi:\n"
        f"👥 Umumiy obunachi: {count}\n"
        f"🤖 Bot orqali a'zo: {stats['total_joined']}\n"
        f"⏳ Kutilayotgan so'rovlar: {jr_count}\n"
        f"✅ Hozirda faol: {stats['currently_active']}\n"
        f"❌ Chiqib ketgan: {stats['left_count']}",
        show_alert=True,
    )


@router.callback_query(F.data.startswith("ch_remove_confirm:"))
async def channel_remove_confirm(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    ch_db_id = int(callback.data.split(":")[1])
    channels = await db.get_all_channels()
    ch       = next((c for c in channels if c["id"] == ch_db_id), None)
    if not ch:
        await callback.answer("Topilmadi", show_alert=True)
        return

    await callback.message.edit_text(
        f"⚠️ <b>Kanal o'chirilsinmi?</b>\n\n"
        f"📢 <b>{ch['channel_name']}</b>\n"
        f"🆔 {ch['channel_id']}\n\n"
        f"Bu kanal butunlay o'chiriladi va qaytib chiqmaydi!\n"
        f"Ishonchingiz komilmi?",
        reply_markup=channel_delete_confirm_keyboard(ch_db_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ch_remove_yes:"))
async def channel_remove_yes(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    ch_db_id = int(callback.data.split(":")[1])
    channels = await db.get_all_channels()
    ch       = next((c for c in channels if c["id"] == ch_db_id), None)
    if ch:
        await db.hard_delete_channel(ch["channel_id"])
        await callback.message.edit_text(
            f"✅ <b>Kanal butunlay o'chirildi!</b>\n\n📢 {ch['channel_name']}",
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text("❌ Kanal topilmadi yoki allaqachon o'chirilgan.")
    await callback.answer()


@router.callback_query(F.data.startswith("ch_remove_no:"))
async def channel_remove_no(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    ch_db_id = int(callback.data.split(":")[1])
    channels = await db.get_all_channels()
    ch       = next((c for c in channels if c["id"] == ch_db_id), None)
    if not ch:
        await callback.answer("Topilmadi")
        return
    stats = await db.get_channel_join_stats(ch["channel_id"])
    added = str(ch.get("added_at", ""))[:10]
    text  = (
        f"📢 <b>{ch['channel_name']}</b>\n\n"
        f"🆔 ID: <code>{ch['channel_id']}</code>\n"
        f"📅 Qo'shilgan: <b>{added}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 <b>Bot orqali statistika:</b>\n"
        f"👥 Jami: <b>{stats['total_joined']}</b>\n"
        f"✅ Faol: <b>{stats['currently_active']}</b>\n"
        f"❌ Ketgan: <b>{stats['left_count']}</b>"
    )
    await callback.message.edit_text(
        text,
        reply_markup=channel_detail_keyboard(ch_db_id, ch["channel_id"]),
        parse_mode="HTML",
    )
    await callback.answer("❌ Bekor qilindi")


@router.callback_query(F.data == "admin_channels_back")
async def admin_channels_back(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    channels = await db.get_active_channels()
    await callback.message.edit_text(
        f"📢 <b>Kanallar boshqaruvi</b>\n\nFaol kanallar: <b>{len(channels)}</b> ta",
        reply_markup=channels_admin_keyboard(channels),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── BROADCAST ─────────────────────────────────────────────────────────

@router.message(F.text == "📣 Xabar yuborish")
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    users = await db.get_all_users()
    await message.answer(
        f"📣 <b>Broadcast</b>\n\n"
        f"Hozirda <b>{len(users)}</b> ta foydalanuvchi bor.\n\n"
        f"Barcha foydalanuvchilarga yuboriladigan xabarni yozing:",
        reply_markup=admin_cancel_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(BroadcastStates.waiting_message)


@router.message(BroadcastStates.waiting_message)
async def broadcast_message_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == CANCEL_TEXT:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())
        return
    users = await db.get_all_users()
    await state.update_data(msg_id=message.message_id, count=len(users))
    await message.answer(
        f"📣 Xabar <b>{len(users)}</b> ta foydalanuvchiga yuboriladi.\n\nTasdiqlaysizmi?",
        reply_markup=confirm_keyboard("broadcast_confirm_yes", "broadcast_confirm_no"),
        parse_mode="HTML",
    )
    await state.set_state(BroadcastStates.confirming)


@router.callback_query(F.data == "broadcast_confirm_yes", BroadcastStates.confirming)
async def broadcast_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data      = await state.get_data()
    await state.clear()
    users     = await db.get_all_users()
    sent      = 0
    failed    = 0
    total     = len(users)
    # Xabar admin bilan bot o'rtasidagi chatda — chat_id = from_user.id (private chat)
    src_chat  = callback.message.chat.id
    msg_id    = data["msg_id"]

    progress = await callback.message.edit_text("📣 Yuborilmoqda... 0%")

    for i, u in enumerate(users):
        try:
            await bot.copy_message(
                chat_id=u["user_id"],
                from_chat_id=src_chat,
                message_id=msg_id,
            )
            sent += 1
        except Exception:
            failed += 1
            await db.block_user(u["user_id"])

        if (i + 1) % 25 == 0 or (i + 1) == total:
            pct = int((i + 1) / total * 100)
            try:
                await progress.edit_text(f"📣 Yuborilmoqda... {pct}%")
            except Exception:
                pass
        await asyncio.sleep(0.04)

    await progress.edit_text(
        f"✅ <b>Broadcast yakunlandi!</b>\n\n"
        f"📤 Yuborildi: <b>{sent}</b>\n"
        f"❌ Xato: <b>{failed}</b>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "broadcast_confirm_no", BroadcastStates.confirming)
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Broadcast bekor qilindi.")
    await callback.answer()


# ─── USERS ─────────────────────────────────────────────────────────────

@router.message(F.text == "👥 Foydalanuvchilar")
async def users_management(message: Message):
    if not is_admin(message.from_user.id):
        return
    total       = await db.get_users_count()
    today       = await db.get_today_users_count()
    recent      = await db.get_recent_users(limit=10)

    text = (
        f"👥 <b>Foydalanuvchilar</b>\n\n"
        f"Jami: <b>{total}</b>\n"
        f"Bugun yangi: <b>{today}</b>\n\n"
        f"<b>So'nggi 10 ta:</b>\n"
    )
    for u in recent:
        name     = u.get("full_name") or "Nomsiz"
        username = f"@{u['username']}" if u.get("username") else ""
        lang     = u.get("language", "uz")
        text    += f"• {name} {username} <code>{u['user_id']}</code> [{lang}]\n"

    await message.answer(text, reply_markup=admin_menu(), parse_mode="HTML")


# ─── BACK TO ADMIN ─────────────────────────────────────────────────────

@router.callback_query(F.data == "back_admin")
async def back_to_admin(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.edit_text("👨‍💼 <b>Admin Panel</b>", parse_mode="HTML")
    await callback.message.answer(
        "👨‍💼 <b>Admin Panel</b>",
        reply_markup=admin_menu(),
        parse_mode="HTML",
    )
    await callback.answer()