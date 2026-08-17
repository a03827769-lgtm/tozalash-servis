from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from loguru import logger
from datetime import datetime
import os

from config import BUSINESS_PHONE, PRICES
from database import db
from ai_brain import ai_brain
from bot.keyboards.inline import get_main_menu
from bot.i18n import i18n
from bot.services.notifications import notify_admin_new_order


import time

USER_MESSAGE_RATES = {}  # { telegram_id: [timestamp1, timestamp2, ...] }
SPAM_BLOCKS = {} # { telegram_id: unblock_timestamp }

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Barcha matnli va rasmli xabarlarni AI orqali qayta ishlash"""
    user = update.effective_user
    telegram_id = str(user.id)
    message_text = update.message.text or update.message.caption or ""

    # --- ANOMALY DETECTION (Anti-Spam) Task 47 ---
    now = time.time()
    
    # Check if blocked
    if telegram_id in SPAM_BLOCKS:
        if now < SPAM_BLOCKS[telegram_id]:
            return # Blocked, ignore message silently
        else:
            del SPAM_BLOCKS[telegram_id] # Unblock
            
    # Track message rate
    if telegram_id not in USER_MESSAGE_RATES:
        USER_MESSAGE_RATES[telegram_id] = []
        
    # Remove older than 10 seconds
    USER_MESSAGE_RATES[telegram_id] = [t for t in USER_MESSAGE_RATES[telegram_id] if now - t < 10]
    USER_MESSAGE_RATES[telegram_id].append(now)
    
    if len(USER_MESSAGE_RATES[telegram_id]) > 5:
        # Spam detected! Block for 60 seconds
        SPAM_BLOCKS[telegram_id] = now + 60
        await update.message.reply_text("🚨 Tizim xavfsizligi (Spam Filter): Iltimos, xabarlarni sekinroq yuboring. 1 daqiqa kuting.")
        return
    # -----------------------------------------------

    # Agar foydalanuvchi sticker, document yoki boshqa qo'llab quvvatlanmaydigan fayl yuborsa
    if (
        not update.message.text
        and not update.message.caption
        and not update.message.photo
        and not update.message.voice
    ):
        client = await db.get_or_create_client(telegram_id)
        lang = client.get("language", "uz")
        msg = (
            "Iltimos, menga matn, rasm yoki ovozli xabar yuboring 😊"
            if lang == "uz"
            else "Пожалуйста, отправьте мне текст, фото или голосовое сообщение 😊"
        )
        await update.message.reply_text(msg)
        return

    # Yozmoqda... ko'rsatish
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    # Agar mijoz rasm yuborgan bo'lsa
    if update.message.photo:
        photo = update.message.photo[-1]

        # Max file size limit (5MB)
        if getattr(photo, "file_size", 0) > 5 * 1024 * 1024:
            await update.message.reply_text("❌ Rasm hajmi juda katta (Maksimum 5MB).")
            return

        photo_file = await photo.get_file()
        os.makedirs("data/downloads", exist_ok=True)
        # Xavfsiz fayl nomi (path traversal oldini olish)
        safe_tg_id = "".join(c for c in str(telegram_id) if c.isdigit())
        img_path = (
            f"data/downloads/photo_{safe_tg_id}_{int(datetime.now().timestamp())}.jpg"
        )
        await photo_file.download_to_drive(img_path)

        try:
            vision_result = await ai_brain.analyze_image(img_path, message_text)

            client = await db.get_or_create_client(telegram_id)
            lang = client.get("language", "uz")

            if "error" in vision_result:
                error_msg = (
                    "Kechirasiz, rasmni tahlil qila olmadim."
                    if lang == "uz"
                    else "Извините, не удалось проанализировать изображение."
                )
                await update.message.reply_text(error_msg)
                return

            min_p = vision_result.get("recommended_price_min", 0)
            max_p = vision_result.get("recommended_price_max", 0)
            svc = vision_result.get("service_type", "Noma'lum")
            notes = vision_result.get("condition_notes", "")
            qty = vision_result.get("estimated_quantity", 1)

            if lang == "ru":
                reply = f"🔍 *Анализ изображения завершен!*\n\n🧹 Услуга: {svc}\n📏 Примерный объем: {qty}\n📝 Заметки: {notes}\n💰 Примерная цена: {min_p:,.0f} - {max_p:,.0f} сум\n\nЖелаете заказать эту услугу?"
            else:
                reply = f"🔍 *Rasm tahlili yakunlandi!*\n\n🧹 Xizmat turi: {svc}\n📏 Taxminiy hajm: {qty}\n📝 Holat: {notes}\n💰 Taxminiy narx: {min_p:,.0f} - {max_p:,.0f} so'm\n\nUshbu xizmatni buyurtma qilishni xohlaysizmi?"

            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🧹 Buyurtma berish" if lang == "uz" else "🧹 Заказать",
                            callback_data="order_start",
                        )
                    ]
                ]
            )

            await update.message.reply_text(
                reply, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
            )
        finally:
            # Xavfsizlik va joy tejash uchun yuklangan faylni o'chirib tashlash
            if os.path.exists(img_path):
                os.remove(img_path)

        return

    # Agar mijoz ovozli xabar yuborgan bo'lsa
    if update.message.voice:
        voice = update.message.voice

        # Max file size limit (5MB)
        if getattr(voice, "file_size", 0) > 5 * 1024 * 1024:
            await update.message.reply_text(
                "❌ Ovozli xabar hajmi juda katta (Maksimum 5MB)."
            )
            return

        voice_file = await voice.get_file()
        os.makedirs("data/downloads", exist_ok=True)
        safe_tg_id = "".join(c for c in str(telegram_id) if c.isdigit())
        audio_path = (
            f"data/downloads/voice_{safe_tg_id}_{int(datetime.now().timestamp())}.ogg"
        )
        await voice_file.download_to_drive(audio_path)

        out_voice_path = f"data/downloads/response_{safe_tg_id}_{int(datetime.now().timestamp())}.mp3"
        try:
            # 1. Transcribe audio
            transcript = await ai_brain.analyze_audio(audio_path)
            if not transcript or transcript.startswith("Kechirasiz, ovozli"):
                await update.message.reply_text(transcript or "Ovozni taniy olmadim.")
                return

            # 2. Get AI response based on the transcript
            ai_response = await ai_brain.respond(
                telegram_id=telegram_id,
                user_message=transcript,
                user_name=user.full_name,
            )
            # Sentimentga qarab gapirish tezligini (tempo) sozlash (Task 34)
            sentiment = ai_response.get("sentiment", "neutral")
            action = ai_response.get("action", "none")
            
            speed = 1.0 # default
            if sentiment == "angry" or action == "urgent":
                speed = 1.15 # tezroq, shoshilinch holatda
            elif sentiment == "negative" or action == "complain":
                speed = 0.90 # sekinroq, muloyim va xotirjam tushuntirish uchun
            elif action == "sales":
                speed = 1.05 # ishonchli va biroz tetik
                
            # 3. Generate voice response
            success = await ai_brain.generate_voice_response(
                response_text, out_voice_path, speed=speed
            )

            if success:
                with open(out_voice_path, "rb") as vf:
                    await update.message.reply_voice(
                        voice=vf, caption=response_text[:1000]
                    )
            else:
                await update.message.reply_text(
                    response_text, parse_mode=ParseMode.MARKDOWN
                )
        finally:
            # Maxfiylik va joyni tejash uchun tozalash
            if os.path.exists(audio_path):
                os.remove(audio_path)
            if os.path.exists(out_voice_path):
                os.remove(out_voice_path)
        return

    # Foydalanuvchi holatini olish
    user_state = await db.get_user_state(telegram_id)
    state = user_state.get("state", "idle")
    ctx = user_state.get("context", {})

    # ---- MANZIL TO'PLASH ----
    if state == "collecting_address":
        ctx["address"] = message_text
        await db.set_user_state(telegram_id, "collecting_date", ctx)

        client = await db.get_or_create_client(telegram_id)
        lang = client.get("language", "uz")
        if lang == "ru":
            text = "📅 Какого числа вы хотите нашу услугу?\n(например: завтра, 20 августа, 15.08)"
        else:
            text = "📅 Qaysi kunda xizmat ko'rsatishimizni xohlaysiz?\n(masalan: ertaga, 20 avgust, 15.08)"

        await update.message.reply_text(text)
        return

    # ---- SANA TO'PLASH ----
    elif state == "collecting_date":
        ctx["scheduled_date"] = message_text

        service_type = ctx.get("service_type")
        service = PRICES.get(service_type, {})
        minimum = service.get("minimum", 1)
        unit = service.get("unit", "dona")

        # Agar miqdor kerak bo'lmasa (paketli xizmatlar)
        if service_type in [
            "regular_cleaning",
            "renovation_cleaning",
            "move_out_cleaning",
        ]:
            await db.set_user_state(telegram_id, "collecting_workers_count", ctx)
            client = await db.get_or_create_client(telegram_id)
            lang = client.get("language", "uz")
            if lang == "ru":
                text = f"🔢 Сколько работников нужно?\n(Цена: 1 работник = {service.get('price', 0):,} сум)"
            else:
                text = f"🔢 Nechta ishchi kerak?\n(Narx: 1 ishchi = {service.get('price', 0):,} so'm)"
        else:
            await db.set_user_state(telegram_id, "collecting_quantity", ctx)
            client = await db.get_or_create_client(telegram_id)
            lang = client.get("language", "uz")
            if lang == "ru":
                text = f"🔢 Введите количество ({unit}):\n(Минимум: {minimum} {unit})"
            else:
                text = f"🔢 Miqdorni kiriting ({unit}):\n(Minimum: {minimum} {unit})"

        await update.message.reply_text(text)
        return

    # ---- MIQDOR / ISHCHILAR SONI TO'PLASH ----
    elif state in ["collecting_quantity", "collecting_workers_count"]:
        try:
            quantity = float(message_text.replace(",", ".").replace(" ", ""))
        except ValueError:
            client = await db.get_or_create_client(telegram_id)
            lang = client.get("language", "uz")
            if lang == "ru":
                text = "❌ Пожалуйста, введите число (например: 3, 10, 25.5)"
            else:
                text = "❌ Iltimos, raqam kiriting (masalan: 3, 10, 25.5)"
            await update.message.reply_text(text)
            return

        service_type = ctx.get("service_type")
        service = PRICES.get(service_type, {})
        minimum = service.get("minimum", 1)

        if quantity < minimum:
            client = await db.get_or_create_client(telegram_id)
            lang = client.get("language", "uz")
            if lang == "ru":
                text = f"❌ Минимальное количество: {minimum} {service.get('unit_ru', 'штук')}"
            else:
                text = f"❌ Minimal miqdor: {minimum} {service.get('unit', 'dona')}"
            await update.message.reply_text(text)
            return

        # Narx hisoblash
        price_per_unit = ctx.get("price_per_unit", 0)
        total_price = price_per_unit * quantity

        ctx["quantity"] = quantity
        ctx["total_price"] = total_price
        await db.set_user_state(telegram_id, "collecting_eco", ctx)

        client = await db.get_or_create_client(telegram_id)
        lang = client.get("language", "uz")

        if lang == "ru":
            text = "🌱 *Экологически чистая уборка?*\n\nХотите ли вы, чтобы мы использовали специальные эко-средства (безопасные для детей и животных)? (+20% к стоимости)"
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "✅ Да, эко-уборка (+20%)", callback_data="eco_yes"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "❌ Нет, обычные средства", callback_data="eco_no"
                        )
                    ],
                ]
            )
        else:
            text = "🌱 *Eko-tozalash xizmati?*\n\nBolalar va uy hayvonlari uchun xavfsiz bo'lgan maxsus eko-vositachalardan foydalanishimizni xohlaysizmi? (narxga +20% qo'shiladi)"
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "✅ Ha, eko-tozalash (+20%)", callback_data="eco_yes"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "❌ Yo'q, oddiy vositalar", callback_data="eco_no"
                        )
                    ],
                ]
            )

        await update.message.reply_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
        )
        return

    # ---- CUSTOM CHECKLIST TO'PLASH ----
    elif state == "collecting_checklist":
        ctx["custom_checklist"] = message_text if message_text.lower() != "skip" else ""
        await db.set_user_state(telegram_id, "collecting_subscription", ctx)

        client = await db.get_or_create_client(telegram_id)
        lang = client.get("language", "uz")

        if lang == "ru":
            text = "🔄 *Хотите оформить подписку на эту услугу?*\n\nПодписка позволяет автоматически создавать заказ с заданной регулярностью."
            keyboard = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("❌ Один раз", callback_data="sub_none")],
                    [
                        InlineKeyboardButton(
                            "📅 Каждую неделю", callback_data="sub_weekly"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🗓 Каждый месяц", callback_data="sub_monthly"
                        )
                    ],
                ]
            )
        else:
            text = "🔄 *Ushbu xizmatga doimiy obuna bo'lishni xohlaysizmi?*\n\nObuna orqali siz belgilangan vaqtda avtomatik buyurtma yaratilishiga erishasiz."
            keyboard = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("❌ Bir marta", callback_data="sub_none")],
                    [InlineKeyboardButton("📅 Har hafta", callback_data="sub_weekly")],
                    [InlineKeyboardButton("🗓 Har oy", callback_data="sub_monthly")],
                ]
            )

        await update.message.reply_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
        )
        return

    # ---- AI BILAN ERKIN SUHBAT ----
    else:
        try:
            # AI dan javob olish
            ai_response = await ai_brain.respond(
                telegram_id=telegram_id,
                user_message=message_text,
                user_name=user.full_name,
            )

            response_text = ai_response.get(
                "message", "Kechirasiz, qayta urinib ko'ring."
            )
            action = ai_response.get("action", "answer_question")

            if action == "ask_admin_for_knowledge":
                admin_question = ai_response.get(
                    "admin_question", "Savolim bor edi, mijozga nima deb javob beray?"
                )
                logger.info(f"🧠 AI ADMINDAN YORDAM SO'RAMOQDA: {admin_question}")
                from config import ADMIN_TELEGRAM_ID

                if ADMIN_TELEGRAM_ID:
                    try:
                        await context.bot.send_message(
                            chat_id=ADMIN_TELEGRAM_ID,
                            text=f"❓ *AI Yordam so'ramoqda:*\n\n👤 Mijoz: {user.full_name} ({telegram_id})\n💬 Mijoz xabari: {message_text}\n\n🤖 AI Savoli: {admin_question}",
                            parse_mode=ParseMode.MARKDOWN,
                        )
                    except Exception as e:
                        logger.error(f"Adminga AI savolini yuborishda xato: {e}")
                else:
                    logger.warning(
                        "ADMIN_TELEGRAM_ID topilmadi, AI savoli adminga yetib bormadi."
                    )

            # Agar AI buyurtma boshlashni taklif qilsa
            if action == "create_order":
                order_data = ai_response.get("order_data", {})
                if order_data:
                    # AI orqali to'g'ridan-to'g'ri buyurtma
                    client = await db.get_or_create_client(telegram_id)

                    try:
                        order = await db.create_order(
                            {
                                "telegram_id": telegram_id,
                                "service_type": order_data.get("service_type"),
                                "address": order_data.get("address"),
                                "scheduled_date": order_data.get("scheduled_date"),
                                "quantity": order_data.get("quantity"),
                                "total_price": order_data.get("total_price"),
                                "status": "yangi",
                            }
                        )

                        # Adminga bildirishnoma
                        await notify_admin_new_order(context.bot, order, client)

                        # Bo'sh ishchilarni topib, tayinlash
                        from workers.workers_manager import workers_manager

                        await workers_manager.assign_order_to_best_worker(order)

                        response_text += (
                            f"\n\n📋 Sizning buyurtma raqamingiz: #{order.get('id')}"
                        )

                        # Generate and send PDF Invoice
                        import sys

                        sys.path.append(
                            os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                        )
                        from invoice_generator import generate_invoice

                        order_data_inv = {
                            "id": order.get("order_number") or order.get("id"),
                            "total_amount": order.get("total_price", 0),
                            "status": order.get("payment_status", "pending"),
                            "items": [
                                {
                                    "name": order.get("service_name")
                                    or order.get("service_type"),
                                    "quantity": order.get("quantity", 1),
                                    "unit": order.get("unit", "unit"),
                                    "price": order.get("price_per_unit", 0),
                                    "total": order.get("total_price", 0),
                                }
                            ],
                        }
                        client_data_inv = {
                            "name": client.get("name", "N/A"),
                            "phone": client.get("phone", "N/A"),
                        }
                        os.makedirs("downloads", exist_ok=True)
                        pdf_path = f"downloads/invoice_{order.get('id')}.pdf"
                        try:
                            await generate_invoice(
                                order_data_inv, client_data_inv, pdf_path
                            )
                            with open(pdf_path, "rb") as f:
                                await update.message.reply_document(
                                    document=f,
                                    filename=f"Invoice_{order.get('id')}.pdf",
                                    caption="📄 Sizning hisob-fakturangiz (Invoice)",
                                )
                        except Exception as e:
                            logger.error(f"Invoice error on create: {e}")

                    except Exception as e:
                        logger.error(f"API Error in bot: {e}")
                        response_text += "\n\n(Tizimda xatolik yuz berdi. Iltimos keyinroq urinib ko'ring.)"

            lang = ai_response.get("language", "uz")

            # Javob yuborish
            if action in ["greet", "answer_question"] or action.startswith(
                "collecting"
            ):
                menu = get_main_menu(lang)
                await update.message.reply_text(
                    response_text, parse_mode=ParseMode.HTML, reply_markup=menu
                )
            else:
                await update.message.reply_text(
                    response_text, parse_mode=ParseMode.HTML
                )

        except Exception as e:
            logger.error(f"Xabar qayta ishlash xatosi: {e}")
            lang = "uz"  # Default fallback
            error_text = (
                f"😔 Xato yuz berdi. Iltimos, qo'ng'iroq qiling: {BUSINESS_PHONE}"
            )
            await update.message.reply_text(error_text)
