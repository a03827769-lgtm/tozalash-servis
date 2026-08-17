"""
Tozalash Servis — Telegram Bot (Asosiy Modul)
24/7 mijozlarga xizmat ko'rsatuvchi AI bot
"""

import sys
import asyncio
from pathlib import Path
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from loguru import logger

from config import TELEGRAM_BOT_TOKEN
from bot.handlers.commands import (
    start_command,
    help_command,
    prices_command,
    stats_command,
    status_command,
    invoice_command,
    b2b_command,
    promo_command,
    pay_command,
)
from bot.handlers.callbacks import button_handler
from bot.handlers.messages import message_handler
from bot.handlers.profile import profile_command, profile_callback_handler
from bot.middlewares.error_handler import global_error_handler
from bot.handlers.worker_handlers import get_worker_registration_handler


async def run_bot_async():
    """Telegram botni asinxron ishga tushirish"""
    logger.info("🚀 Telegram Bot ishga tushirilmoqda...")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Global Xatolik ushlagichi
    app.add_error_handler(global_error_handler)

    # Conversation handler'lar
    app.add_handler(get_worker_registration_handler())

    # Komandalar
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("prices", prices_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("invoice", invoice_command))
    app.add_handler(CommandHandler("b2b", b2b_command))
    app.add_handler(CommandHandler("promo", promo_command))
    app.add_handler(CommandHandler("pay", pay_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("order", lambda u, c: button_handler(u, c)))

    # Tugmalar
    app.add_handler(CallbackQueryHandler(profile_callback_handler, pattern="^profile_"))
    app.add_handler(CallbackQueryHandler(button_handler))

    # Xabarlar (AI orqali, matn va rasm)
    app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.PHOTO | filters.VOICE) & ~filters.COMMAND,
            message_handler,
        )
    )

    logger.info("✅ Bot muvaffaqiyatli ishga tushdi! 24/7 faol.")

    # Start bot
    try:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        # Block until cancelled gracefully
        stop_event = asyncio.Event()

        # Windowsda graceful shutdown uchun
        import signal

        try:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass  # Windows da add_signal_handler ishlamaydi, shuning uchun pass

        await stop_event.wait()
    except asyncio.CancelledError:
        logger.info("Polling to'xtatildi (Cancelled).")
    except Exception as e:
        logger.error(f"Telegram Bot xatosi: {e}")
    finally:
        logger.info("🔴 Telegram Bot to'xtatilmoqda...")
        try:
            await app.updater.stop()
            await app.stop()
            await app.shutdown()
        except Exception:
            pass


def run_bot():
    """Telegram botni ishga tushirish"""
    import asyncio

    try:
        asyncio.run(run_bot_async())
    except KeyboardInterrupt:
        logger.info("Dastur foydalanuvchi tomonidan to'xtatildi.")


if __name__ == "__main__":
    # Ensure root folder is in python path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    run_bot()
