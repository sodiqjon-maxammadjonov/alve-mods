"""
Subscription checker utility
"""

import types
import logging
import html
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

import database as db

logger = logging.getLogger(__name__)


class ChannelValidationError(Exception):
    """validate_channel_detailed tomonidan tashlanadi — xabar HTML formatda"""
    pass


def _safe_html(text: str) -> str:
    return html.escape(str(text))


def _is_join_request_link(invite_link: str | None) -> bool:
    """https://t.me/+xxx ko'rinishidagi join request link ekanligini tekshiradi"""
    if not invite_link:
        return False
    return "t.me/+" in invite_link


async def _get_chat_safe(bot: Bot, channel_id):
    """
    bot.get_chat() ni xavfsiz chaqiradi.
    Agar aiogram parse qila olmasa, raw JSON dan o'qiydi.
    """
    try:
        return await bot.get_chat(channel_id)
    except Exception as e:
        raw = getattr(e, 'data', None)
        if not isinstance(raw, dict):
            raise
        result = raw.get('result', {})
        if not raw.get('ok') or not result:
            raise
        logger.info(f"get_chat parsed manually for {channel_id}")
        return types.SimpleNamespace(
            id=result.get('id'),
            title=result.get('title', ''),
            username=result.get('username'),
            type=result.get('type', ''),
            invite_link=result.get('invite_link'),
        )


async def check_user_subscriptions(bot: Bot, user_id: int, channels: list) -> tuple[bool, list]:
    """
    Foydalanuvchi barcha kanallarga a'zo yoki so'rov yuborganini tekshiradi.

    Oddiy kanal  → get_chat_member orqali tekshirish
    Join-request kanal (invite_link da t.me/+ bor) →
        avval get_chat_member (tasdiqlangan bo'lishi mumkin),
        keyin join_requests jadvalidan (so'rov yuborgan, hali tasdiqlanmagan)
    """
    unsubscribed = []
    for channel in channels:
        ch_id      = channel.get("channel_id", "")
        inv_link   = channel.get("invite_link", "")
        is_jr_chan = _is_join_request_link(inv_link)

        # Eski noto'g'ri saqlangan linklar
        if ch_id.startswith("https://") or ch_id.startswith("http://"):
            logger.warning(f"Invalid channel_id stored as URL: {ch_id}. Re-add this channel.")
            unsubscribed.append(channel)
            continue

        subscribed = False

        # 1. get_chat_member — tasdiqlangan a'zolar
        try:
            member = await bot.get_chat_member(chat_id=ch_id, user_id=user_id)
            if member.status not in ("left", "kicked"):
                subscribed = True
        except (TelegramForbiddenError, TelegramBadRequest):
            pass
        except Exception as e:
            logger.warning(f"check_user_subscriptions get_chat_member error for {ch_id}: {e}")

        # 2. Join-request kanal: so'rov yuborganmi? (hali tasdiqlanmagan bo'lishi mumkin)
        if not subscribed and is_jr_chan:
            try:
                subscribed = await db.has_join_request(ch_id, user_id)
            except Exception as e:
                logger.warning(f"has_join_request error for {ch_id}: {e}")

        if not subscribed:
            unsubscribed.append(channel)

    return len(unsubscribed) == 0, unsubscribed


async def get_channel_member_count(bot: Bot, channel_id: str) -> int:
    try:
        return await bot.get_chat_member_count(channel_id)
    except Exception as e:
        logger.warning(f"get_channel_member_count error: {e}")
        return 0


async def validate_channel(bot: Bot, raw_input: str) -> dict | None:
    try:
        return await validate_channel_detailed(bot, raw_input)
    except ChannelValidationError:
        return None


async def validate_channel_detailed(bot: Bot, raw_input: str) -> dict:
    """
    Kanalning to'g'riligini tekshiradi.
    Private kanal → avtomatik join request link yaratadi (creates_join_request=True).
    Public kanal  → @username dan oddiy link hosil qiladi.
    """
    channel_id = _normalize_channel_id(raw_input)

    # 1. Kanal ma'lumotlarini olish
    try:
        chat = await _get_chat_safe(bot, channel_id)
    except TelegramBadRequest as e:
        err = str(e).lower()
        if "chat not found" in err or "invalid" in err:
            raise ChannelValidationError(
                "❌ <b>Kanal topilmadi!</b>\n\n"
                "Mumkin sabablar:\n"
                "• Username yoki ID noto'g'ri kiritilgan\n"
                "• Kanal mavjud emas yoki o'chirilgan\n\n"
                f"💡 Kiritilgan: <code>{_safe_html(raw_input)}</code>\n"
                "Format: <code>@username</code> yoki <code>-1001234567890</code>"
            )
        raise ChannelValidationError(
            f"❌ <b>Telegram xatosi!</b>\n\nKiritilgan: <code>{_safe_html(raw_input)}</code>"
        )
    except TelegramForbiddenError:
        raise ChannelValidationError(
            "❌ <b>Kanal yopiq yoki bot bloklangan!</b>\n\nBot bu kanalga kirish huquqiga ega emas."
        )
    except Exception:
        raise ChannelValidationError("❌ <b>Ulanish xatosi!</b>\n\nQayta urinib ko'ring.")

    # 2. Chat turi
    if chat.type not in ("channel", "supergroup", "group"):
        raise ChannelValidationError(
            f"❌ <b>Bu kanal emas!</b>\n\n"
            f"<b>{_safe_html(chat.title)}</b> — turi: {_safe_html(chat.type)}\n\n"
            "Faqat kanallar va superguruhlar qo'shilishi mumkin."
        )

    # 3. Bot admin ekanligini tekshirish
    try:
        me         = await bot.get_me()
        bot_member = await bot.get_chat_member(chat.id, me.id)
    except TelegramForbiddenError:
        raise ChannelValidationError(
            f"❌ <b>Bot bu kanalda yo'q!</b>\n\n"
            f"📢 Kanal: <b>{_safe_html(chat.title)}</b>\n\n"
            "Botni kanalga qo'shib, admin huquqi bering."
        )
    except Exception:
        raise ChannelValidationError(
            "❌ <b>Bot holatini tekshirib bo'lmadi.</b>\n\nQayta urinib ko'ring."
        )

    if bot_member.status not in ("administrator", "creator"):
        status_uz = {
            "member":     "oddiy a'zo — admin emas",
            "left":       "kanalda yo'q",
            "kicked":     "kanaldan chiqarib yuborilgan",
            "restricted": "cheklangan",
        }.get(bot_member.status, bot_member.status)
        raise ChannelValidationError(
            f"❌ <b>Bot admin emas!</b>\n\n"
            f"📢 Kanal: <b>{_safe_html(chat.title)}</b>\n"
            f"🤖 Bot holati: <b>{status_uz}</b>\n\n"
            "Botga quyidagi huquqlarni bering:\n"
            "• A'zolarni boshqarish\n"
            "• Xabarlarni o'qish\n"
            "• Taklif havolalari yaratish"
        )

    # 4. Havola yaratish
    # Public → @username link
    # Private → join request link (creates_join_request=True)
    username       = getattr(chat, 'username', None)
    invite_link    = None
    invite_warning = None
    is_private     = not bool(username)

    try:
        if username:
            invite_link = f"https://t.me/{username}"
        else:
            # Private kanal: join request link yaratamiz — bot approve qilmaydi,
            # admin o'zi tasdiqlaydi. Bot faqat so'rovni qayd etadi.
            link_obj    = await bot.create_chat_invite_link(
                chat.id,
                creates_join_request=True,
                name="Bot subscription link",
            )
            invite_link = link_obj.invite_link
    except Exception as e:
        invite_warning = (
            "⚠️ Join request havola yaratib bo'lmadi.\n"
            "Botga 'Taklif havolalari yaratish' huquqi bering."
        )
        logger.warning(f"create_chat_invite_link error: {e}")

    return {
        "title":          chat.title,
        "username":       username,
        "invite_link":    invite_link,
        "numeric_id":     str(chat.id),
        "is_private":     is_private,
        "invite_warning": invite_warning,
    }


def _normalize_channel_id(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("-100") or raw.startswith("@"):
        return raw
    if raw.lstrip("-").isdigit():
        num = int(raw)
        return f"-100{num}" if num > 0 else raw
    return f"@{raw}" if not raw.startswith("@") else raw