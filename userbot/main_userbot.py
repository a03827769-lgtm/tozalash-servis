"""
Tozalash Servis — UserBot (Shaxsiy Akkaunt DM Handler)
=======================================================
Pyrogram asosida mijozlarning shaxsiy xabarlarini ushlab,
AI Brain orqali javob qaytaradi.

MUHIM TEKSHIRUVLAR:
  - 'db' faqat modul darajasida import qilinadi (UnboundLocalError'dan himoya)
  - Pyrogram Client faqat run_userbot_async() ichida yaratiladi (session lock'dan himoya)
  - Barcha try/except bloklari ichida lokal import YO'Q
"""

import os
import sys
import time
from pathlib import Path

from loguru import logger
from pyrogram import Client, filters
from pyrogram.types import Message

# ── Modul-darajali importlar (FAQAT BU YERDA, hech qachon funksiya ichida emas) ──
from config import (
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    ADMIN_TELEGRAM_ID,
    ADMIN_USERNAME,
    ORDERS_CHANNEL_ID,
)
from database import db          # global 'db' — funksiya ichida qayta import qilma!
from ai_brain import ai_brain
from workers.workers_manager import workers_manager

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

# Pyrogram Client — lazily created inside run_userbot_async() to avoid session lock
app: Client | None = None

# ── Rate limiting (Spam himoyasi) ────────────────────────────────────────────────
user_message_timestamps: dict[str, list[float]] = {}
RATE_LIMIT_WINDOW   = 10   # soniya
SPAM_LIMIT          = 5    # oynada max xabar soni


# ════════════════════════════════════════════════════════════════════════════════
# ASOSIY HANDLER
# ════════════════════════════════════════════════════════════════════════════════
async def handle_private_message(client: Client, message: Message) -> None:
    """
    Barcha DM xabarlarni qabul qilib, AI orqali javob beradi.
    Rasm, ovoz va matn turlari qo'llab-quvvatlanadi.
    """
    try:
        user = message.from_user
        if not user:
            return

        telegram_id = str(user.id)

        # ── Spam himoyasi ────────────────────────────────────────────────────
        now = time.time()
        history = [t for t in user_message_timestamps.get(telegram_id, []) if now - t < RATE_LIMIT_WINDOW]
        if len(history) >= SPAM_LIMIT:
            logger.warning(f"🚫 Spam aniqlandi: {telegram_id}. Xabar e'tiborga olinmadi.")
            return
        history.append(now)
        user_message_timestamps[telegram_id] = history

        user_name    = user.first_name or "Mijoz"
        message_text = message.text or message.caption or ""

        # ── Gamification: Gold Status tekshiruvi ────────────────────────────
        client_info  = await db.get_or_create_client(telegram_id)
        orders_count = client_info.get("orders_count", 0)
        if orders_count == 10 and not client_info.get("gold_status_notified"):
            await client.send_message(
                chat_id=message.chat.id,
                text=(
                    "🎉 Tabriklaymiz! Siz 10 ta buyurtmani amalga oshirib, "
                    "**Gold Status** ga yetishdingiz!\n"
                    "Endi sizga doimiy 10% chegirma taqdim etiladi! 👑"
                ),
            )
            await db.update_client(telegram_id, gold_status_notified=True)

        # ── Rasm tahlili ─────────────────────────────────────────────────────
        if message.photo:
            logger.info(f"📸 Rasm qabul qilindi: {user_name} ({telegram_id})")
            photo_path = await message.download(file_name=f"{DATA_DIR}/downloads/")
            vision_result = await ai_brain.analyze_image(photo_path, message_text)
            if "error" not in vision_result:
                message_text = (
                    f"[Rasm AI tahlili]\n"
                    f"Xizmat turi: {vision_result.get('service_type')}\n"
                    f"Taxminiy hajm: {vision_result.get('estimated_quantity')}\n"
                    f"Holat: {vision_result.get('condition_notes')}\n"
                    f"Taxminiy narx: {vision_result.get('recommended_price_min')} - "
                    f"{vision_result.get('recommended_price_max')} so'm\n"
                    f"Mijoz so'rovi: {message_text}"
                )
            else:
                logger.error(f"Vision xatosi: {vision_result.get('error')}")
            try:
                if os.path.exists(photo_path):
                    os.remove(photo_path)
            except Exception as del_err:
                logger.warning(f"Rasmni o'chirishda xato: {del_err}")

        # ── Ovozli xabar tahlili ─────────────────────────────────────────────
        if message.voice:
            logger.info(f"🎤 Ovozli xabar: {user_name} ({telegram_id})")
            from pyrogram.enums import ChatAction
            await client.send_chat_action(message.chat.id, ChatAction.RECORD_AUDIO)
            voice_path = await message.download(file_name=f"{DATA_DIR}/downloads/")
            transcribed_text = await ai_brain.analyze_audio(voice_path)
            logger.info(f"🎤 Transkripsiya: {transcribed_text}")
            message_text = transcribed_text
            try:
                if os.path.exists(voice_path):
                    os.remove(voice_path)
            except Exception as del_err:
                logger.warning(f"Ovozli faylni o'chirishda xato: {del_err}")

        if not message_text:
            return

        logger.info(f"📨 DM keldi: {user_name} ({telegram_id}) → {message_text[:80]}")

        # ── Mijoz ma'lumotlarini yangilash ───────────────────────────────────
        client_data = await db.get_or_create_client(telegram_id)
        if not client_data.get("name"):
            await db.update_client_name(telegram_id, user_name)

        # ── Typing indikatori ────────────────────────────────────────────────
        if not message.voice:
            from pyrogram.enums import ChatAction
            await client.send_chat_action(message.chat.id, ChatAction.TYPING)

        # ── AI javob ─────────────────────────────────────────────────────────
        ai_response   = await ai_brain.respond(
            telegram_id=telegram_id,
            user_message=message_text,
            user_name=user_name,
        )
        response_text = ai_response.get("message", "Kechirasiz, biroz tushunmadim.")
        action        = ai_response.get("action", "answer_question")

        # ── Admin xabarlari ──────────────────────────────────────────────────
        if action == "complain":
            logger.warning(f"⚠️ SHIKOYAT: {user_name} ({telegram_id}) — {message_text}")
            if ADMIN_TELEGRAM_ID:
                await client.send_message(
                    int(ADMIN_TELEGRAM_ID),
                    f"⚠️ SHIKOYAT!\nMijoz: {user_name} ({telegram_id})\nXabar: {message_text}",
                )
        elif action == "urgent":
            logger.info(f"🚨 SHOSHILINCH: {user_name} ({telegram_id})")
            if ADMIN_TELEGRAM_ID:
                await client.send_message(
                    int(ADMIN_TELEGRAM_ID),
                    f"🚨 SHOSHILINCH BUYURTMA!\nMijoz: {user_name} ({telegram_id})\nXabar: {message_text}",
                )
        elif action == "connect_admin":
            logger.info(f"👨‍💻 ADMIN KERAK: {user_name} ({telegram_id})")
            if ADMIN_TELEGRAM_ID:
                await client.send_message(
                    int(ADMIN_TELEGRAM_ID),
                    f"👨‍💻 ADMIN BILAN BOG'LANISH!\nMijoz: {user_name} ({telegram_id})\nXabar: {message_text}",
                )
        elif action == "ask_admin_for_knowledge":
            admin_question = ai_response.get("admin_question", "Mijozga nima deb javob beray?")
            logger.info(f"🧠 AI ADMINDAN YORDAM: {admin_question}")
            if ADMIN_USERNAME:
                admin_target = ADMIN_USERNAME if ADMIN_USERNAME.startswith("@") else f"@{ADMIN_USERNAME}"
                try:
                    await client.send_message(
                        admin_target,
                        f"❓ AI Savoli:\nMijoz: {user_name} ({telegram_id})\n"
                        f"Mijoz xabari: {message_text}\nAI Savoli: {admin_question}",
                    )
                except Exception as e:
                    logger.error(f"Admin ({admin_target}) ga xabar yuborishda xato: {e}")

        # ── Buyurtma yaratish ────────────────────────────────────────────────
        if action == "create_order":
            order_data = ai_response.get("order_data") or {}
            if order_data:
                order_data["client_id"]           = client_data.get("id")
                order_data["client_telegram_id"]  = telegram_id
                try:
                    order = await db.create_order({
                        "client_id":          order_data.get("client_id"),
                        "client_telegram_id": str(telegram_id),
                        "service_type":       order_data.get("service_type"),
                        "address":            order_data.get("address"),
                        "scheduled_date":     order_data.get("scheduled_date"),
                        "quantity":           order_data.get("quantity"),
                        "total_price":        order_data.get("total_price"),
                        "status":             "yangi",
                    })

                    await workers_manager.assign_order_to_best_worker(order)
                    response_text += f"\n\n📋 Buyurtmangiz tizimga kiritildi! Raqami: #{order.get('id')}"

                    if ORDERS_CHANNEL_ID:
                        order_msg = (
                            f"🆕 **YANGI BUYURTMA #{order.get('id')}**\n"
                            f"👤 Mijoz: {user_name} ({telegram_id})\n"
                            f"🧹 Xizmat: {order_data.get('service_type')}\n"
                            f"📍 Manzil: {order_data.get('address')}\n"
                            f"📅 Sana: {order_data.get('scheduled_date')}\n"
                            f"📦 Hajmi: {order_data.get('quantity')}\n"
                            f"💰 Narxi: {order_data.get('total_price')} so'm\n"
                            f"📲 Username: @{user.username or 'Yoq'}"
                        )
                        try:
                            await client.send_message(int(ORDERS_CHANNEL_ID), order_msg)
                        except Exception as ch_err:
                            logger.error(f"Kanalga yuborishda xato: {ch_err}")
                except Exception as order_err:
                    logger.error(f"Buyurtma yaratishda xato: {order_err}")
                    response_text += "\n\n(Buyurtmani saqlashda xatolik. Admin bilan bog'laning.)"

        # ── Javob yuborish ───────────────────────────────────────────────────
        if message.voice:
            audio_out = f"{DATA_DIR}/downloads/response_{telegram_id}_{int(time.time())}.mp3"
            success = await ai_brain.generate_voice_response(response_text, audio_out)
            if success and os.path.exists(audio_out):
                await message.reply_voice(voice=audio_out, caption=response_text, quote=True)
                try:
                    os.remove(audio_out)
                except Exception:
                    pass
            else:
                await message.reply_text(response_text, quote=True)
        else:
            await message.reply_text(response_text, quote=True)

    except Exception:
        logger.exception("❌ UserBot xabarni qayta ishlashda kutilmagan xatolik")


# ════════════════════════════════════════════════════════════════════════════════
# USERBOT ISHGA TUSHIRISH
# ════════════════════════════════════════════════════════════════════════════════
async def run_userbot_async() -> None:
    """UserBot ni ishga tushiradi va DM xabarlarni kutadi."""
    global app

    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        logger.error("❌ TELEGRAM_API_ID yoki TELEGRAM_API_HASH topilmadi! .env ni tekshiring.")
        return

    session_file = DATA_DIR / "userbot.session"
    if not session_file.exists():
        logger.error("❌ Sessiya fayli topilmadi: data/userbot.session")
        logger.error("Birinchi: terminalda `python login.py` ni ishga tushiring.")
        return

    # Sessiya fayli himoyasi (Unix-da 600 huquqi)
    try:
        import stat
        os.chmod(session_file, stat.S_IRUSR | stat.S_IWUSR)
        logger.info("🔒 Sessiya fayli himoyalandi (chmod 600)")
    except Exception:
        pass  # Windows da chmod ta'sir qilmaydi, e'tiborsiz

    # ── Pyrogram Client — FAQAT BU YERDA yaratiladi (session lock oldini olish) ──
    app = Client(
        name=str(session_file.with_suffix("").absolute()),
        api_id=int(TELEGRAM_API_ID),
        api_hash=TELEGRAM_API_HASH,
    )

    # Handler'ni yangi app obyektga bog'laymiz
    app.on_message(filters.private & ~filters.me)(handle_private_message)

    # ── Autonomous Outreach Handlerlarini ro'yxatdan o'tkazish ──
    try:
        from userbot.autonomous_outreach import register_autonomous_handlers
        register_autonomous_handlers(app)
    except Exception as e:
        logger.error(f"Autonomous Outreach yuklanishida xato: {e}")

    logger.info("🟢 Shaxsiy Akkaunt (UserBot) DM-lar uchun ishga tushmoqda...")
    try:
        await app.start()
        me = await app.get_me()
        logger.info(f"✅ UserBot ulandi: @{me.username} | {me.first_name} (ID: {me.id})")
        from pyrogram import idle
        await idle()
    except Exception as e:
        logger.error(f"❌ UserBot xatolik: {type(e).__name__}: {e}")
    finally:
        logger.info("🔴 UserBot to'xtatilmoqda...")
        try:
            if app and app.is_connected:
                await app.stop()
        except Exception:
            pass
