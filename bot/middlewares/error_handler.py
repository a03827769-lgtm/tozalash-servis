from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger
import traceback


async def global_error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log the error and send a message to notify the user."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(f"Exception while handling an update: {context.error}")
    logger.error(traceback.format_exc())

    # Ensure update is present (sometimes it's None)
    if update and update.effective_user:
        try:
            # Fallback message
            if update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Tizimda xatolik yuz berdi. Iltimos keyinroq urinib ko'ring yoki administratorga murojaat qiling.",
                )
        except Exception as send_e:
            logger.error(f"Error while sending error message: {send_e}")
