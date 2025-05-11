import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo,
    CallbackQuery
)
from aiogram.utils.i18n import I18n, FSMI18nMiddleware
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from datetime import datetime, timedelta
from config import Config
from database import Database
from utils import (
    parse_timedelta, format_timedelta,
    is_admin, is_group_admin, get_user_mention
)

# --- إعدادات البوت ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

i18n = I18n(path="locales", default_locale="ar", domain="messages")
bot = Bot(token=Config.BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()
dp.message.middleware(FSMI18nMiddleware(i18n))
db = Database()

# --- أنظمة البوت ---
class ProtectionSystem:
    @staticmethod
    async def check_message(message: Message):
        _ = i18n.gettext
        user = message.from_user
        chat = message.chat
        
        # تخطي المشرفين
        if await is_admin(user.id) or await is_group_admin(bot, chat.id, user.id):
            return False
        
        # التحقق من الاشتراك
        if not await SubscriptionSystem.check_subscription(user.id):
            await message.delete()
            await message.answer(
                _("يجب الاشتراك في القنوات المطلوبة أولاً!"),
                reply_markup=await SubscriptionSystem.get_keyboard()
            )
            return True
        
        # فحص المحتوى
        violation = await ProtectionSystem._check_content(message)
        if violation:
            await message.delete()
            await ProtectionSystem.handle_violation(message, violation)
            return True
        
        return False

    @staticmethod
    async def _check_content(message: Message):
        _ = i18n.gettext
        text = (message.text or message.caption or "").lower()
        
        # الكلمات الممنوعة
        banned_words = await db.get_banned_words(message.chat.id)
        for word in banned_words:
            if word in text:
                return {
                    "type": "banned_word",
                    "reason": _("كلمة ممنوعة: {word}").format(word=word)
                }
        
        # الروابط الخارجية
        if any(link in text for link in ["http://", "https://", "www."]):
            return {
                "type": "external_link",
                "reason": _("إرسال روابط خارجية")
            }
        
        return None

    @staticmethod
    async def handle_violation(message: Message, violation: dict):
        _ = i18n.gettext
        user = message.from_user
        chat = message.chat
        
        # تسجيل الانتهاك
        await db.log_violation(
            user_id=user.id,
            chat_id=chat.id,
            violation_type=violation["type"],
            content=message.text or message.caption or ""
        )
        
        # إعطاء تحذير
        warn_count = await db.add_warning(
            user_id=user.id,
            chat_id=chat.id,
            admin_id=bot.id,  # النظام التلقائي
            reason=violation["reason"]
        )
        
        max_warns = await db.get_chat_setting(chat.id, "max_warnings", Config.MAX_WARNINGS)
        
        if warn_count >= max_warns:
            # حظر المستخدم
            ban_duration = await db.get_chat_setting(chat.id, "ban_duration", 86400)  # يوم واحد
            await AdminSystem.ban_user(
                chat_id=chat.id,
                user_id=user.id,
                admin_id=bot.id,
                duration=timedelta(seconds=ban_duration),
                reason=_("تجاوز عدد التحذيرات المسموحة")
            )
            
            await message.answer(
                _("🚨 تم حظر {user} بسبب تجاوز عدد التحذيرات").format(
                    user=get_user_mention(user)
                )
            )
        else:
            await message.answer(
                _("⚠️ تحذير لـ {user}\nالسبب: {reason}\nعدد التحذيرات: {warns}/{max_warns}").format(
                    user=get_user_mention(user),
                    reason=violation["reason"],
                    warns=warn_count,
                    max_warns=max_warns
                )
            )

class AdminSystem:
    @staticmethod
    async def ban_user(
        chat_id: int,
        user_id: int,
        admin_id: int,
        duration: timedelta = None,
        reason: str = None,
        permanent: bool = False
    ):
        _ = i18n.gettext
        try:
            until_date = None if permanent else (datetime.now() + duration if duration else None)
            
            await bot.ban_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                until_date=until_date
            )
            
            await db.add_ban(
                user_id=user_id,
                chat_id=chat_id,
                admin_id=admin_id,
                duration=duration.total_seconds() if duration else None,
                reason=reason,
                permanent=permanent
            )
            
            return _("✅ تم حظر المستخدم بنجاح")
        except Exception as e:
            logger.error(f"Error banning user: {e}")
            return _("❌ حدث خطأ أثناء محاولة حظر المستخدم")

class SubscriptionSystem:
    @staticmethod
    async def check_subscription(user_id: int):
        # في الواقع يجب التحقق من اشتراك المستخدم في القنوات المطلوبة
        return True

    @staticmethod
    async def get_keyboard():
        builder = InlineKeyboardBuilder()
        for channel in Config.REQUIRED_CHANNELS:
            builder.button(
                text=f"اشترك في @{channel}",
                url=f"https://t.me/{channel}"
            )
        builder.button(text="✅ تأكيد الاشتراك", callback_data="check_subscription")
        builder.adjust(1)
        return builder.as_markup()

# --- الأوامر الأساسية ---
@dp.message(CommandStart())
async def cmd_start(message: Message):
    _ = i18n.gettext
    user = message.from_user
    
    await db.add_user(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name
    )
    
    if not await SubscriptionSystem.check_subscription(user.id):
        await message.answer(
            _("يجب الاشتراك في القنوات التالية:"),
            reply_markup=await SubscriptionSystem.get_keyboard()
        )
        return
    
    await message.answer(_(Config.WELCOME_MESSAGE))

# ... (بقية الأوامر والمعالجات)

# --- تشغيل البوت ---
async def main():
    await db.initialize()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
