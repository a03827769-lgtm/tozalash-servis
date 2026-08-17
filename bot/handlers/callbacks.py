from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from loguru import logger
from datetime import datetime
import os

from config import BUSINESS_PHONE, PRICES, TELEGRAM_BOT_TOKEN, ADMIN_TELEGRAM_ID
from bot.i18n import i18n
from database import db
from bot.keyboards.inline import (
    get_main_menu,
    get_services_keyboard,
    get_confirm_keyboard,
)
from bot.i18n import i18n
from ai_brain import ai_brain
from bot.handlers.commands import prices_command
from bot.services.notifications import notify_admin_new_order


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Barcha inline tugmalarni boshqarish"""
    query = update.callback_query
    await query.answer()

    telegram_id = str(query.from_user.id)
    client = await db.get_or_create_client(telegram_id)
    lang = client.get("language", "uz")
    data = query.data

    # ---- TIL TANLASH (ONBOARDING & SETTINGS) ----
    if data.startswith("setlang_"):
        new_lang = data.split("_")[1]
        await db.update_client(telegram_id, {"language": new_lang})
        client["language"] = new_lang
        lang = new_lang

        # Start menu
        await db.set_user_state(telegram_id, "idle", {})
        welcome_msg = i18n.get("start_greeting", lang, name=query.from_user.full_name)
        menu = get_main_menu(lang)
        await query.edit_message_text(
            welcome_msg, parse_mode=ParseMode.HTML, reply_markup=menu
        )
        return

    # ---- ASOSIY MENYU ----
    if data == "main_menu":
        welcome_msg = i18n.get("start_greeting", lang, name=query.from_user.full_name)
        menu = get_main_menu(lang)
        await query.edit_message_text(
            welcome_msg, parse_mode=ParseMode.HTML, reply_markup=menu
        )

    # ---- BUYURTMA BOSHLASH ----
    elif data == "order_start":
        await db.set_user_state(telegram_id, "selecting_service", {})
        text = (
            "🧹 Qaysi xizmatni xohlaysiz?"
            if lang == "uz"
            else "🧹 Какую услугу вы хотите?"
        )
        await query.edit_message_text(text, reply_markup=get_services_keyboard(lang))

    # ---- XIZMAT TANLASH ----
    elif data.startswith("svc_"):
        service_type = data.replace("svc_", "")
        service = PRICES.get(service_type)

        if not service:
            await query.edit_message_text("❌ Xizmat topilmadi!")
            return

        # Kontekstga saqlash
        await db.set_user_state(
            telegram_id,
            "collecting_address",
            {
                "service_type": service_type,
                "service_name": service["name_uz"],
                "price_per_unit": service["price"],
                "unit": service["unit"],
                "minimum": service.get("minimum", 1),
            },
        )

        if lang == "ru":
            text = f"""✅ Выбрано: *{service['name_ru']}*
Цена: {service['price']:,} сум/{service['unit_ru']}

📍 Отправьте ваш адрес (район, улица, номер дома):"""
        else:
            text = f"""✅ Tanlandi: *{service['name_uz']}*
Narx: {service['price']:,} so'm/{service['unit']}

📍 Manzilingizni yuboring (tuman, ko'cha, uy raqami):"""

        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)

    # ---- NARXLAR ----
    elif data == "show_prices":
        await prices_command(update, context)

    # ---- HAMKORLIK (REFERRAL) ----
    elif data == "referral":
        # Provide the user with their referral link
        bot_username = context.bot.username
        ref_code = client.get("referral_code", "error")
        ref_link = f"https://t.me/{bot_username}?start={ref_code}"

        if lang == "ru":
            text = f"""🤝 *Партнерская программа*

Приглашайте друзей и получайте бонусы!
За каждого друга, который сделает первый заказ по вашей ссылке, вы получите баллы лояльности.

🔗 *Ваша уникальная ссылка:*
`{ref_link}`

🏆 *Ваши баллы лояльности:* {client.get('loyalty_points', 0)}
"""
        else:
            text = f"""🤝 *Hamkorlik Dasturi*

Do'stlaringizni taklif qiling va bonuslarga ega bo'ling!
Sizning havolangiz orqali birinchi marta buyurtma bergan har bir do'stingiz uchun sizga sodiqlik ballari beriladi.

🔗 *Sizning maxsus havolangiz:*
`{ref_link}`

🏆 *Sodiqlik ballaringiz:* {client.get('loyalty_points', 0)}
"""
        back_btn = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔙 Orqaga" if lang == "uz" else "🔙 Назад",
                        callback_data="main_menu",
                    )
                ]
            ]
        )
        await query.edit_message_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_btn
        )

    # ---- KABINET (PROFILE) ----
    elif data == "profile":
        points = client.get("loyalty_points", 0)

        # Calculate Loyalty Tier
        if points < 500:
            tier_uz, tier_ru = "🥉 Bronza", "🥉 Бронза"
            next_tier_uz, next_tier_ru = "🥈 Kumush", "🥈 Серебро"
            points_needed = 500 - points
        elif points < 2000:
            tier_uz, tier_ru = "🥈 Kumush", "🥈 Серебро"
            next_tier_uz, next_tier_ru = "🥇 Oltin", "🥇 Золото"
            points_needed = 2000 - points
        else:
            tier_uz, tier_ru = "🥇 Oltin", "🥇 Золото"
            next_tier_uz, next_tier_ru = "💎 Vip", "💎 Vip"
            points_needed = 0

        if lang == "ru":
            text = f"""👤 *Личный кабинет*

🏆 *Ваш текущий статус:* {tier_ru}
⭐ *Накоплено баллов:* {points}

"""
            if points_needed > 0:
                text += f"До статуса {next_tier_ru} осталось: {points_needed} баллов!\n"
            text += "\n_Баллы начисляются за каждый заказ и приглашенного друга._"
        else:
            text = f"""👤 *Shaxsiy kabinet*

🏆 *Joriy statusingiz:* {tier_uz}
⭐ *Yig'ilgan ballar:* {points}

"""
            if points_needed > 0:
                text += f"{next_tier_uz} statusiga erishish uchun: {points_needed} ball yetishmayapti!\n"
            text += (
                "\n_Ballar har bir buyurtma va taklif qilingan do'st uchun beriladi._"
            )

        back_btn = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔙 Orqaga" if lang == "uz" else "🔙 Назад",
                        callback_data="main_menu",
                    )
                ]
            ]
        )
        await query.edit_message_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_btn
        )

    # ---- GALEREYA (GALLERY) ----
    elif data == "gallery":
        if lang == "ru":
            text = """📸 *Галерея наших работ*
            
Посмотрите примеры "До и После" наших услуг! Мы гордимся чистотой, которую создаем.
Для просмотра полного портфолио перейдите в наш Instagram:

👉 [Посмотреть Галерею (Instagram)](https://instagram.com/tozalash_servis)"""
        else:
            text = """📸 *Bizning ishlar galereyasi*
            
Xizmatlarimizdan "Oldin va Keyin" misollarini ko'ring! Biz yaratgan tozaligimiz bilan faxrlanamiz.
To'liq portfolioni ko'rish uchun Instagram sahifamizga o'ting:

👉 [Galereyani ko'rish (Instagram)](https://instagram.com/tozalash_servis)"""

        back_btn = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📸 Instagram", url="https://instagram.com/tozalash_servis"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 Orqaga" if lang == "uz" else "🔙 Назад",
                        callback_data="main_menu",
                    )
                ],
            ]
        )
        await query.edit_message_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_btn
        )

    # ---- HAQIMIZDA ----
    elif data == "about":
        if lang == "ru":
            text = i18n.get("about", lang="ru", phone=BUSINESS_PHONE)
        else:
            text = i18n.get("about", lang="uz", phone=BUSINESS_PHONE)

        back_btn = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔙 Orqaga" if lang == "uz" else "🔙 Назад",
                        callback_data="main_menu",
                    )
                ]
            ]
        )
        await query.edit_message_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_btn
        )

    # ---- RATING (FEEDBACK) ----
    elif data.startswith("rate_"):
        parts = data.split("_")
        rating = int(parts[1])
        order_id = parts[2]

        if lang == "ru":
            if rating >= 4:
                text = f"⭐⭐⭐⭐⭐\nСпасибо за вашу высокую оценку ({rating}/5)! Мы рады, что вам понравилось."
            else:
                text = f"⭐⭐\nСпасибо за ваш отзыв ({rating}/5). Мы свяжемся с вами, чтобы улучшить качество наших услуг."
        else:
            if rating >= 4:
                text = f"⭐⭐⭐⭐⭐\nYuqori bahoingiz uchun rahmat ({rating}/5)! Xizmatimiz yoqqanidan xursandmiz."
            else:
                text = f"⭐⭐\nFikringiz uchun rahmat ({rating}/5). Xizmat sifatini yaxshilash uchun siz bilan bog'lanamiz."

        # Send admin notification if rating is low
        if rating <= 3:
            try:
                from telegram import Bot

                bot = Bot(token=TELEGRAM_BOT_TOKEN)
                await bot.send_message(
                    chat_id=ADMIN_TELEGRAM_ID,
                    text=f"⚠️ *DIQQAT: Past baho!*\nBuyurtma #{order_id} uchun {rating}/5 baho qo'yildi.\nMijoz bilan bog'laning!",
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception as e:
                logger.error(f"Failed to notify admin of low rating: {e}")

        await query.edit_message_text(text)

    # ---- BOG'LANISH ----
    elif data == "contact":
        if lang == "ru":
            text = f"""📞 *Контакты Tozalash Servis*

📱 Телефон: {BUSINESS_PHONE}
📍 Город: Ташкент
🕐 Работаем: 24/7
💬 Telegram: @tozalash_servis_bot"""
        else:
            text = f"""📞 *Tozalash Servis Aloqa*

📱 Telefon: {BUSINESS_PHONE}
📍 Shahar: Toshkent
🕐 Ish vaqti: 24/7
💬 Telegram: @tozalash_servis_bot"""

        back_btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Orqaga", callback_data="main_menu")]]
        )
        await query.edit_message_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_btn
        )

    # ---- ECO-FRIENDLY TANLOVI ----
    elif data.startswith("eco_"):
        user_state = await db.get_user_state(telegram_id)
        ctx = user_state.get("context", {})

        is_eco = data == "eco_yes"
        ctx["is_eco_friendly"] = is_eco
        if is_eco:
            ctx["total_price"] = ctx.get("total_price", 0) * 1.2

        await db.set_user_state(telegram_id, "collecting_checklist", ctx)

        if lang == "ru":
            text = "📝 *Особые инструкции или пожелания (Чеклист)?*\n\nНапишите, если есть особые места, на которые нужно обратить внимание. Или отправьте 'skip', чтобы пропустить."
        else:
            text = "📝 *Maxsus ko'rsatmalar yoki istaklar (Cheklist)?*\n\nE'tibor qaratish kerak bo'lgan maxsus joylar bo'lsa yozib qoldiring. Yoki o'tkazib yuborish uchun 'skip' deb yozing."

        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)

    # ---- OBUNA TANLOVI ----
    elif data.startswith("sub_"):
        user_state = await db.get_user_state(telegram_id)
        ctx = user_state.get("context", {})

        if data == "sub_weekly":
            ctx["is_recurring"] = True
            ctx["recurring_interval"] = "weekly"
        elif data == "sub_monthly":
            ctx["is_recurring"] = True
            ctx["recurring_interval"] = "monthly"
        else:
            ctx["is_recurring"] = False
            ctx["recurring_interval"] = None

        await db.set_user_state(telegram_id, "confirming_order", ctx)

        lang = client.get("language", "uz")

        sub_text_uz = {"weekly": "Har hafta", "monthly": "Har oy", None: "Bir marta"}
        sub_text_ru = {
            "weekly": "Каждую неделю",
            "monthly": "Каждый месяц",
            None: "Один раз",
        }
        sub_val = ctx.get("recurring_interval")

        eco_ru = "Да (+20%)" if ctx.get("is_eco_friendly") else "Нет"
        eco_uz = "Ha (+20%)" if ctx.get("is_eco_friendly") else "Yo'q"

        if lang == "ru":
            confirm_text = f"""📋 *Подтвердите заказ:*
    
🧹 Услуга: {ctx.get('service_name')}
🌱 Эко-средства: {eco_ru}
📝 Заметки: {ctx.get('custom_checklist', '-')}
📍 Адрес: {ctx.get('address')}
📅 Дата: {ctx.get('scheduled_date')}
🔄 Подписка: {sub_text_ru[sub_val]}
🔢 Количество: {ctx.get('quantity')}
💰 Сумма: {ctx.get('total_price', 0):,.0f} сум
    
Всё верно?"""
        else:
            confirm_text = f"""📋 *Buyurtmangizni tasdiqlang:*
    
🧹 Xizmat: {ctx.get('service_name')}
🌱 Eko-vositachalar: {eco_uz}
📝 Ko'rsatmalar: {ctx.get('custom_checklist', '-')}
📍 Manzil: {ctx.get('address')}
📅 Sana: {ctx.get('scheduled_date')}
🔄 Obuna: {sub_text_uz[sub_val]}
🔢 Miqdor: {ctx.get('quantity')}
💰 Jami: {ctx.get('total_price', 0):,.0f} so'm
    
Hammasi to'g'rimi?"""

        await query.edit_message_text(
            confirm_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_confirm_keyboard(lang),
        )

    # ---- BUYURTMANI TASDIQLASH ----
    elif data == "confirm_order":
        user_state = await db.get_user_state(telegram_id)
        context_data = user_state.get("context", {})

        if not context_data:
            await query.edit_message_text(
                "❌ Buyurtma ma'lumotlari topilmadi. Qayta urinib ko'ring."
            )
            return

        # Buyurtmani yaratish
        client = await db.get_or_create_client(telegram_id)

        order = await db.create_order(
            {
                "telegram_id": telegram_id,
                "service_type": context_data.get("service_type"),
                "address": context_data.get("address"),
                "scheduled_date": context_data.get("scheduled_date"),
                "quantity": context_data.get("quantity"),
                "total_price": context_data.get("total_price"),
                "is_recurring": context_data.get("is_recurring", False),
                "recurring_interval": context_data.get("recurring_interval"),
                "is_eco_friendly": context_data.get("is_eco_friendly", False),
                "custom_checklist": context_data.get("custom_checklist", ""),
                "status": "yangi",
            }
        )
        # Add properties for local display
        order["order_number"] = order.get("id", "N/A")
        order["service_name"] = context_data.get("service_name")

        # Holatni tozalash
        await db.set_user_state(telegram_id, "idle", {})

        # Mijozga tasdiqlash
        if lang == "ru":
            confirm_text = f"""✅ *Ваш заказ принят!*

📋 *Заказ #{order['order_number']}*
🧹 Услуга: {order['service_name']}
📍 Адрес: {order['address']}
📅 Дата: {order['scheduled_date']}
💰 Сумма: {order['total_price']:,.0f} сум

⏳ Наши сотрудники свяжутся с вами в ближайшее время.
📞 Вопросы: {BUSINESS_PHONE}

Спасибо за доверие! 🙏"""
        else:
            confirm_text = f"""✅ *Buyurtmangiz qabul qilindi!*

📋 *Buyurtma #{order['order_number']}*
🧹 Xizmat: {order['service_name']}
📍 Manzil: {order['address']}
📅 Sana: {order['scheduled_date']}
💰 Narx: {order['total_price']:,.0f} so'm

⏳ Xodimlarimiz tez orada siz bilan bog'lanadi.
📞 Savol uchun: {BUSINESS_PHONE}

Ishonch uchun rahmat! 🙏"""

        await query.edit_message_text(confirm_text, parse_mode=ParseMode.MARKDOWN)

        # Adminga bildirishnoma
        await notify_admin_new_order(context.bot, order, client)

        # Bo'sh ishchilarni topib, xabar yuborish
        from workers.workers_manager import workers_manager

        await workers_manager.assign_order_to_best_worker(order)

    # ---- BUYURTMANI BEKOR QILISH ----
    elif data == "cancel_order":
        await db.set_user_state(telegram_id, "idle", {})
        if lang == "ru":
            text = "❌ Заказ отменён. Если передумаете — пишите!"
        else:
            text = "❌ Buyurtma bekor qilindi. Fikr o'zgarsangiz — yozing!"

        await query.edit_message_text(text)

    # ---- AKSIYALAR ----
    elif data == "promos":
        if lang == "ru":
            text = """🎁 *Наши акции:*

🌟 *Первый заказ — 10% скидка!*
👥 *Приведи друга — 15% скидка обоим!*
🔄 *Постоянным клиентам — накопительная скидка*
📦 *Комплекс услуг — специальная цена*

Подробности: {phone}""".format(phone=BUSINESS_PHONE)
        else:
            text = """🎁 *Bizning aksiyalar:*

🌟 *Birinchi buyurtma — 10% chegirma!*
👥 *Do'stingizni taklif qiling — har ikkovingizga 15% chegirma!*
🔄 *Doimiy mijozlarga — jamg'arib boradigan chegirma*
📦 *Kompleks xizmatlar — maxsus narx*

Batafsil: {phone}""".format(phone=BUSINESS_PHONE)

        back_btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Orqaga", callback_data="main_menu")]]
        )
        await query.edit_message_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_btn
        )

    # ---- SHARHLAR ----
    elif data == "reviews":
        base_text = """⭐ *Mijozlarimiz sharhlari:*

⭐⭐⭐⭐⭐ _"Ajoyib ish! Xonadon yarqirab ketdi!"_ — Malika R.
⭐⭐⭐⭐⭐ _"Professional yondashuv, tavsiya qilaman!"_ — Alisher K.
⭐⭐⭐⭐⭐ _"2 yildan beri ketmagan dog'larni olib ketishdi"_ — Gulnora T.

📢 Sizning sharhingiz ham biz uchun muhim!"""

        # Real-time AI Translation
        if lang != "uz":
            target = "Rus" if lang == "ru" else "Ingliz"
            text = await ai_brain.translate_text(base_text, target)
        else:
            text = base_text

        back_btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Orqaga", callback_data="main_menu")]]
        )
        await query.edit_message_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_btn
        )
