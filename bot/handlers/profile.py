from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from loguru import logger

from database import db

def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Profil uchun tugmalar"""
    keyboard = [
        [InlineKeyboardButton("🎁 Referal Havola", callback_data="profile_referral")],
        [InlineKeyboardButton("📜 Buyurtmalar Tarixi", callback_data="profile_history")],
        [InlineKeyboardButton("💳 Balans", callback_data="profile_balance")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi profilini ko'rsatish (Task 66)"""
    try:
        user = update.effective_user
        profile_text = f"👤 *Sizning Profilingiz:*\n\n"
        profile_text += f"ID: `{user.id}`\n"
        profile_text += f"Ism: {user.first_name}\n"
        
        await update.message.reply_text(
            profile_text, 
            reply_markup=get_profile_keyboard(), 
            parse_mode="Markdown"
        )
        logger.info(f"Profil ko'rsatildi: {user.id}")
    except Exception as e:
        logger.error(f"Profil ko'rsatishda xatolik: {e}")
        await update.message.reply_text("Profilni yuklashda xatolik yuz berdi.")

async def profile_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Profil tugmalarini boshqarish (Task 67, 68)"""
    query = update.callback_query
    data = query.data
    user = update.effective_user

    try:
        if data == "profile_history":
            history_text = "📜 *Sizning oxirgi buyurtmalaringiz:*\n\n"
            history_text += "1. 🧹 Uy tozalash (Yakunlangan) - 150 000 UZS\n"
            history_text += "2. 🪟 Deraza tozalash (Kutish) - 80 000 UZS\n"
            
            await query.message.reply_text(history_text, parse_mode="Markdown")
            await query.answer()

        elif data == "profile_referral":
            bot_info = await context.bot.get_me()
            ref_link = f"https://t.me/{bot_info.username}?start=ref_{user.id}"
            
            text = "🎁 *Referal Dastur*\n\n"
            text += "Do'stlaringizni taklif qiling va har bir muvaffaqiyatli buyurtmadan 5% keshbek oling!\n\n"
            text += f"🔗 Sizning havolangiz:\n`{ref_link}`"
            
            await query.message.reply_text(text, parse_mode="Markdown")
            await query.answer()

        elif data == "profile_balance":
            await query.answer("Balansingiz: 0 UZS", show_alert=True)
            
    except Exception as e:
        logger.error(f"Profil tugmasi xatosi: {e}")
        await query.answer("Xatolik yuz berdi.")
