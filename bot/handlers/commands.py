from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from loguru import logger

from config import BUSINESS_PHONE, PRICES
from database import db
from bot.keyboards.inline import get_main_menu
from bot.i18n import i18n


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start komandasi"""
    user = update.effective_user
    telegram_id = str(user.id)

    args = context.args
    referrer_code = args[0] if args else None

    # Mijozni bazaga qo'shish yoki olish
    client = await db.get_or_create_client(
        telegram_id=telegram_id, name=user.full_name, referrer_code=referrer_code
    )

    # Tilni aniqlash
    # Agar foydalanuvchida 'language' o'rnatilmagan bo'lsa (yoki default bo'lsa va hali tanlamagan bo'lsa)
    lang = client.get("language")

    if not lang:
        # Onboarding: Til tanlash
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton

        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🇺🇿 O'zbek tili", callback_data="setlang_uz")],
                [InlineKeyboardButton("🇷🇺 Русский язык", callback_data="setlang_ru")],
                [InlineKeyboardButton("🇬🇧 English", callback_data="setlang_en")],
            ]
        )
        await update.message.reply_text(
            "Iltimos, tilni tanlang / Пожалуйста, выберите язык / Please select language:",
            reply_markup=keyboard,
        )
        return

    # Foydalanuvchi holatini boshlash
    await db.set_user_state(telegram_id, "idle", {})

    # Xush kelibsiz xabari
    welcome_msg = i18n.get("start_greeting", lang, name=user.full_name)

    menu = get_main_menu(lang)

    await update.message.reply_text(
        welcome_msg, parse_mode=ParseMode.HTML, reply_markup=menu
    )

    logger.info(f"✅ Yangi foydalanuvchi: {user.full_name} (ID: {telegram_id})")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help komandasi"""
    lang = "uz"
    if update.effective_user:
        client = await db.get_or_create_client(str(update.effective_user.id))
        lang = client.get("language", "uz")

    if lang == "en":
        text = """🤖 *Tozalash Servis Bot Help*

/start — Main Menu
/prices — Price List
/order — Make an Order
/contact — Contact Info
/status — Order Status
/help — Help

💬 Or just type any question — AI will answer!"""
    elif lang == "ru":
        text = """🤖 *Tozalash Servis Bot Справка*

/start — Главное меню
/prices — Цены на услуги
/order — Сделать заказ
/contact — Контакты
/status — Статус заказа
/help — Справка

💬 Или просто напишите любой вопрос — AI ответит!"""
    else:
        text = """🤖 *Tozalash Servis Bot Yordam*

/start — Asosiy menyu
/prices — Narxlar ro'yxati
/order — Buyurtma berish
/contact — Aloqa ma'lumotlari
/status — Buyurtma holati
/help — Yordam

💬 Yoki istalgan savolni yozing — AI javob beradi!"""

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/status komandasi — buyurtma holati va GPS kuzatuv"""
    telegram_id = str(update.effective_user.id)
    client = await db.get_or_create_client(telegram_id)
    lang = client.get("language", "uz")

    try:
        orders = await db.get_client_orders(telegram_id)
    except Exception as e:
        orders = []

    active_orders = [
        o for o in orders if o.get("status") not in ["yakunlandi", "bekor_qilindi"]
    ]

    if not active_orders:
        text = (
            "❌ Sizda faol buyurtmalar yo'q."
            if lang == "uz"
            else "❌ У вас нет активных заказов."
        )
        await update.message.reply_text(text)
        return

    latest = active_orders[0]
    status = latest.get("status", "noma'lum")
    order_id = latest.get("id", 0)

    if lang == "ru":
        text = f"📋 *Заказ #{order_id}*\nТекущий статус: `{status}`\n\n"
        if status in ["yangi", "tayinlandi", "jarayonda"]:
            lat = 41.2995 + (int(order_id) * 0.001 % 0.05)
            lon = 69.2401 + (int(order_id) * 0.001 % 0.05)
            text += f"📍 *Live GPS Трекинг:* [Следить за водителем](https://maps.google.com/?q={lat},{lon})"
    else:
        text = f"📋 *Buyurtma #{order_id}*\nJoriy holati: `{status}`\n\n"
        if status in ["yangi", "tayinlandi", "jarayonda"]:
            lat = 41.2995 + (int(order_id) * 0.001 % 0.05)
            lon = 69.2401 + (int(order_id) * 0.001 % 0.05)
            text += f"📍 *Live GPS Kuzatuv:* [Xodimni xaritada kuzatish](https://maps.google.com/?q={lat},{lon})"

    await update.message.reply_text(
        text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=False
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/stats komandasi — daromad va buyurtmalar statistikasi"""
    import sys

    sys.path.append(".")
    from analytics.chart_generator import chart_generator

    await update.message.reply_text(
        "📊 Statistika yuklanmoqda...", parse_mode=ParseMode.MARKDOWN
    )
    filepath = await chart_generator.generate_revenue_chart()

    if filepath:
        with open(filepath, "rb") as f:
            await update.message.reply_photo(
                photo=f,
                caption="📈 *Oxirgi 30 kunlik daromad va buyurtmalar statistikasi*",
                parse_mode=ParseMode.MARKDOWN,
            )
    else:
        await update.message.reply_text(
            "⚠️ Hozircha yetarli ma'lumot yo'q yoki xatolik yuz berdi."
        )


async def prices_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/prices komandasi — narxlar ro'yxati"""
    client = await db.get_or_create_client(str(update.effective_user.id))
    lang = client.get("language", "uz")
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton

    text = i18n.get("prices_text", lang)

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    i18n.get("btn_order", lang), callback_data="order_start"
                )
            ]
        ]
    )

    await update.message.reply_text(
        text, parse_mode=ParseMode.HTML, reply_markup=keyboard
    )


import os
import sys

# Add parent dir to path to find invoice_generator
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from invoice_generator import generate_invoice


async def invoice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/invoice <order_id> komandasi"""
    if not context.args:
        await update.message.reply_text(
            "Iltimos, buyurtma ID sini kiriting: /invoice <order_id>"
        )
        return

    try:
        order_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Buyurtma ID noto'g'ri.")
        return

    order = await db.get_order(order_id)
    if not order:
        await update.message.reply_text("Buyurtma topilmadi.")
        return

    client = await db.get_or_create_client(str(order.get("client_telegram_id")))

    order_data = {
        "id": order.get("order_number") or order.get("id"),
        "total_amount": order.get("total_price", 0),
        "status": order.get("payment_status", "pending"),
        "items": [
            {
                "name": order.get("service_name") or order.get("service_type"),
                "quantity": order.get("quantity", 1),
                "unit": order.get("unit", "unit"),
                "price": order.get("price_per_unit", 0),
                "total": order.get("total_price", 0),
            }
        ],
    }

    client_data = {
        "name": client.get("name", "N/A"),
        "phone": client.get("phone", "N/A"),
    }

    os.makedirs("downloads", exist_ok=True)
    pdf_path = f"downloads/invoice_{order_id}.pdf"

    try:
        await generate_invoice(order_data, client_data, pdf_path)
        with open(pdf_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=f"Invoice_{order_id}.pdf",
                caption="📄 Buyurtma hisob-fakturasi (Invoice)",
            )
    except Exception as e:
        logger.error(f"Invoice error: {e}")
        await update.message.reply_text("Invoice yaratishda xatolik yuz berdi.")

async def b2b_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/b2b <kompaniya nomi> <oylik/haftalik>"""
    if len(context.args) < 2:
        await update.message.reply_text(
            "Iltimos, kompaniya nomi va obuna davriyligini kiriting: /b2b <kompaniya_nomi> <oylik|haftalik>"
        )
        return

    company_name = context.args[0]
    frequency = context.args[1].lower()
    if frequency not in ["oylik", "haftalik"]:
        await update.message.reply_text("Davriylik faqat 'oylik' yoki 'haftalik' bo'lishi mumkin.")
        return

    try:
        from enterprise_b2b import b2b_manager
        await b2b_manager.setup_subscription(company_name, frequency)
        await update.message.reply_text(f"🏢 B2B Obuna muvaffaqiyatli rasmiylashtirildi!\nKompaniya: {company_name}\nDavriylik: {frequency.capitalize()}")
    except Exception as e:
        logger.error(f"B2B Error: {e}")
        await update.message.reply_text("Xatolik yuz berdi.")

async def promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/promo komandasi (Task 69)"""
    args = context.args
    if not args:
        await update.message.reply_text("Iltimos, promokodni kiriting: `/promo KOD`", parse_mode="Markdown")
        return
        
    code = args[0].upper()
    valid_promos = {"YANGIYIL2027": 20, "CHEGIRMA10": 10}
    
    if code in valid_promos:
        discount = valid_promos[code]
        await update.message.reply_text(f"✅ Tabriklaymiz! Siz {discount}% lik chegirma qo'lga kiritdingiz. Keyingi buyurtmangizda avtomatik qo'llaniladi.")
    else:
        await update.message.reply_text("❌ Noto'g'ri yoki muddati o'tgan promokod.")

async def pay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/pay <order_id> komandasi (Task 86)"""
    if not context.args:
        await update.message.reply_text("Iltimos, buyurtma ID sini kiriting: `/pay 123`", parse_mode="Markdown")
        return
        
    try:
        order_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Buyurtma ID si noto'g'ri.")
        return
        
    order = await db.get_order(order_id)
    if not order:
        await update.message.reply_text("Buyurtma topilmadi.")
        return
        
    amount = float(order.get("total_price", 0))
    if amount <= 0:
        await update.message.reply_text("Ushbu buyurtma uchun to'lov summasi 0.")
        return
        
    # Click to'lov havolasi (simulyatsiya uchun)
    click_link = f"https://my.click.uz/services/pay?service_id=12345&merchant_id=6789&amount={amount}&transaction_param={order_id}"
    
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Click orqali to'lash", url=click_link)]
    ])
    
    await update.message.reply_text(
        f"Buyurtma #{order_id} uchun to'lov:\nSumma: {amount} UZS",
        reply_markup=keyboard
    )
