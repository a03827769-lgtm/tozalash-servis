from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from loguru import logger
from database import db

# Holatlar
WAITING_NAME, WAITING_PHONE = range(2)


async def cmd_worker_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ishchini ro'yxatdan o'tkazishni boshlash"""
    telegram_id = str(update.effective_user.id)
    worker = await db.get_worker_by_tg_id(telegram_id)

    if worker:
        await update.message.reply_text(
            f"Siz allaqachon ishchi sifatida ro'yxatdan o'tgansiz, {worker['name']}! \nSizning ID: {telegram_id}"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Assalomu alaykum! Ishchi sifatida ro'yxatdan o'tish uchun ismingizni kiriting:"
    )
    return WAITING_NAME


async def worker_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ismni qabul qilish"""
    context.user_data["worker_name"] = update.message.text
    await update.message.reply_text(
        "Yaxshi, endi telefon raqamingizni kiriting (masalan: +998901234567):"
    )
    return WAITING_PHONE


async def worker_phone_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Raqamni qabul qilish va bazaga saqlash"""
    phone = update.message.text
    name = context.user_data.get("worker_name", "Noma'lum")
    telegram_id = str(update.effective_user.id)
    username = update.effective_user.username

    try:
        await db.register_worker(
            telegram_id=telegram_id, name=name, phone=phone, username=username
        )
        await update.message.reply_text(
            f"✅ Tabriklaymiz, {name}! Siz ishchi sifatida ro'yxatdan o'tdingiz. "
            f"Sizning Telegram ID'ngiz tizimga bog'landi: {telegram_id}"
        )
    except Exception as e:
        logger.error(f"Ishchini ro'yxatdan o'tkazishda xato: {e}")
        await update.message.reply_text(
            "Kechirasiz, ro'yxatdan o'tishda xatolik yuz berdi. Keyinroq urinib ko'ring."
        )

    return ConversationHandler.END


async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Jarayonni bekor qilish"""
    await update.message.reply_text("Ro'yxatdan o'tish bekor qilindi.")
    return ConversationHandler.END


def get_worker_registration_handler():
    """Conversation handler qaytaradi"""
    return ConversationHandler(
        entry_points=[CommandHandler("worker", cmd_worker_start)],
        states={
            WAITING_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, worker_name_received)
            ],
            WAITING_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, worker_phone_received)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_registration)],
    )
