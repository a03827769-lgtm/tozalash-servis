"""
Tozalash Servis — Admin Boshqaruv Paneli Bot Handlerlari
Admin uchun maxsus komandalar va buyruqlar
"""

import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode
from loguru import logger

from config import TELEGRAM_BOT_TOKEN, ADMIN_TELEGRAM_ID, BUSINESS_NAME
from database import db
from ai_brain import ai_brain


def is_admin(user_id: int) -> bool:
    """Admin tekshiruvi"""
    return user_id == ADMIN_TELEGRAM_ID


# ================================================
# ADMIN KOMANDALAR
# ================================================


async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/admin komandasi — Admin paneli"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Ruxsat yo'q!")
        return

    text = """🔐 *ADMIN BOSHQARUV PANELI*

Quyidagi komandalardan foydalaning:"""

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📊 Statistika", callback_data="admin_stats"),
                InlineKeyboardButton("📦 Buyurtmalar", callback_data="admin_orders"),
            ],
            [
                InlineKeyboardButton("👷 Ishchilar", callback_data="admin_workers"),
                InlineKeyboardButton("👥 Mijozlar", callback_data="admin_clients"),
            ],
            [
                InlineKeyboardButton("💰 Moliya", callback_data="admin_finance"),
                InlineKeyboardButton("📈 Raqiblar", callback_data="admin_competitors"),
            ],
            [
                InlineKeyboardButton(
                    "📢 Xabar yuborish", callback_data="admin_broadcast"
                ),
                InlineKeyboardButton("🧠 AI O'rganish", callback_data="admin_learning"),
            ],
            [
                InlineKeyboardButton(
                    "📊 Hisobot now", callback_data="admin_report_now"
                ),
                InlineKeyboardButton("⚙️ Sozlamalar", callback_data="admin_settings"),
            ],
        ]
    )

    await update.message.reply_text(
        text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
    )


async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin callback handleri"""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text("❌ Ruxsat yo'q!")
        return

    data = query.data

    # ---- STATISTIKA ----
    if data == "admin_stats":
        stats = await db.get_orders_stats(days=30)
        finance = await db.get_finance_stats()
        workers = await db.get_all_workers()

        text = f"""📊 *STATISTIKA (30 kun)*

💰 Daromad (bugun): {finance.get('today_revenue', 0) or 0:,.0f} so'm
💰 Daromad (oy): {finance.get('month_revenue', 0) or 0:,.0f} so'm
💰 Jami daromad: {finance.get('total_revenue', 0) or 0:,.0f} so'm

📦 Jami buyurtmalar: {stats.get('total_orders', 0)}
✅ Bajarilgan: {stats.get('completed', 0)}
📋 Yangi: {stats.get('new_orders', 0)}
💵 O'rtacha chek: {stats.get('avg_order_value', 0) or 0:,.0f} so'm

👷 Ishchilar: {len(workers)} ta"""

        back_btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Admin menyu", callback_data="admin_back")]]
        )

        await query.edit_message_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_btn
        )

    # ---- BUYURTMALAR ----
    elif data == "admin_orders":
        today_orders = await db.get_today_orders()

        if not today_orders:
            text = "📦 Bugun hali buyurtma yo'q."
        else:
            text = f"📦 *Bugungi buyurtmalar ({len(today_orders)} ta):*\n\n"

            for o in today_orders[:10]:  # Max 10 ta ko'rsatish
                status_emoji = {
                    "yangi": "🆕",
                    "tayinlandi": "👷",
                    "jarayonda": "⚙️",
                    "bajarildi": "✅",
                    "bekor": "❌",
                }.get(o.get("status", "yangi"), "📋")

                text += f"{status_emoji} *#{o.get('order_number', '?')}*\n"
                text += f"   🧹 {o.get('service_name', '?')}\n"
                text += f"   📍 {o.get('address', '?')}\n"
                text += f"   💰 {o.get('total_price', 0):,.0f} so'm\n\n"

        back_btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Admin menyu", callback_data="admin_back")]]
        )

        await query.edit_message_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_btn
        )

    # ---- ISHCHILAR ----
    elif data == "admin_workers":
        from workers.workers_manager import workers_manager

        report = await workers_manager.get_workers_status_report()

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "➕ Yangi ishchi", callback_data="admin_add_worker"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "💰 Maosh hisoboti", callback_data="admin_salary_report"
                    )
                ],
                [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")],
            ]
        )

        await query.edit_message_text(
            report, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
        )

    # ---- MOLIYA ----
    elif data == "admin_finance":
        finance = await db.get_finance_stats()

        text = f"""💰 *MOLIYA HISOBOTI*

📅 Bugun: {finance.get('today_revenue', 0) or 0:,.0f} so'm
📆 Bu oy: {finance.get('month_revenue', 0) or 0:,.0f} so'm
📊 Jami: {finance.get('total_revenue', 0) or 0:,.0f} so'm"""

        back_btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]]
        )

        await query.edit_message_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_btn
        )

    # ---- RAQIBLAR ----
    elif data == "admin_competitors":
        await query.edit_message_text(
            "🔍 Raqib tahlili boshlanmoqda... (bir necha daqiqa kutib turing)"
        )

        from analytics.competitor_analyzer import competitor_analyzer

        report = await competitor_analyzer.generate_competitive_report()

        await query.edit_message_text(
            f"📈 *RAQOBAT TAHLILI*\n\n{report[:3500]}", parse_mode=ParseMode.MARKDOWN
        )

    # ---- HISOBOT NOW ----
    elif data == "admin_report_now":
        await query.edit_message_text("📊 Hisobot tayyorlanmoqda...")

        from reports.daily_reports import daily_report_system

        await daily_report_system.generate_and_send_report()

        await query.edit_message_text(
            "✅ Hisobot yuborildi! Telegram da tekshiring.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]]
            ),
        )

    # ---- AI O'RGANISH ----
    elif data == "admin_learning":
        improvements = await ai_brain.self_improve()

        if improvements:
            text = "🧠 *AI bugun o'rgangan narsalar:*\n\n"
            for imp in improvements:
                text += f"• {imp}\n"
        else:
            text = "🧠 AI bu kun yangi narsalar o'rganyapti..."

        back_btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]]
        )

        await query.edit_message_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_btn
        )

    # ---- BROADCAST ----
    elif data == "admin_broadcast":
        context.user_data["state"] = "admin_broadcast"
        await query.edit_message_text(
            "📢 *Xabar yuboring*\n\nKanalga yuboriladigan xabarni yozing:",
            parse_mode=ParseMode.MARKDOWN,
        )

    # ---- ORQAGA ----
    elif data == "admin_back":
        text = "🔐 *ADMIN BOSHQARUV PANELI*"
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("📊 Statistika", callback_data="admin_stats"),
                    InlineKeyboardButton(
                        "📦 Buyurtmalar", callback_data="admin_orders"
                    ),
                ],
                [
                    InlineKeyboardButton("👷 Ishchilar", callback_data="admin_workers"),
                    InlineKeyboardButton("💰 Moliya", callback_data="admin_finance"),
                ],
                [
                    InlineKeyboardButton(
                        "📈 Raqiblar", callback_data="admin_competitors"
                    ),
                    InlineKeyboardButton(
                        "🧠 AI O'rganish", callback_data="admin_learning"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "📊 Hisobot now", callback_data="admin_report_now"
                    ),
                    InlineKeyboardButton(
                        "📢 Broadcast", callback_data="admin_broadcast"
                    ),
                ],
            ]
        )

        await query.edit_message_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
        )

    # ---- ISHCHI QABUL / RAD ----
    elif data.startswith("admin_accept_"):
        order_id = int(data.replace("admin_accept_", ""))
        await db.update_order_status(order_id, "qabul_qilindi")
        await query.edit_message_text(f"✅ Buyurtma #{order_id} qabul qilindi!")

    elif data.startswith("admin_reject_"):
        order_id = int(data.replace("admin_reject_", ""))
        await db.update_order_status(order_id, "rad_etildi")
        await query.edit_message_text(f"❌ Buyurtma #{order_id} rad etildi.")

    # ---- MAOSH HISOBOTI ----
    elif data == "admin_salary_report":
        from workers.workers_manager import workers_manager

        await workers_manager.send_salary_report()
        await query.edit_message_text(
            "✅ Maosh hisoboti yuborildi!",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]]
            ),
        )


async def admin_worker_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ishchi qabul/rad javoblarini qayta ishlash"""
    query = update.callback_query
    await query.answer()

    data = query.data
    worker_telegram_id = str(query.from_user.id)

    # Ishchini topish (aiomysql pattern: cursor() + %s placeholder)
    async with db.get_conn() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM workers WHERE telegram_id = %s", (worker_telegram_id,)
            )
            worker = await cursor.fetchone()

    if not worker:
        await query.edit_message_text("❌ Sizning ma'lumotlaringiz topilmadi.")
        return

    if data.startswith("worker_accept_"):
        order_id = int(data.replace("worker_accept_", ""))
        await db.update_order_status(order_id, "jarayonda", str(dict(worker)["id"]))

        # Ishchiga tasdiqlash
        await query.edit_message_text(
            "✅ *Vazifa qabul qilindi!*\n\nMijozning manzilida bo'ling va ishni bajarganingizdan keyin bizga xabar bering.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "✅ Ish tugadi!", callback_data=f"worker_done_{order_id}"
                        )
                    ]
                ]
            ),
        )

        # Adminga xabar
        from telegram import Bot

        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=ADMIN_TELEGRAM_ID,
            text=f"✅ Buyurtma #{order_id} ni *{dict(worker)['name']}* qabul qildi!",
            parse_mode=ParseMode.MARKDOWN,
        )

    elif data.startswith("worker_reject_"):
        order_id = int(data.replace("worker_reject_", ""))
        await query.edit_message_text(
            "❌ Qabul qilmadingiz. Admin boshqa ishchi tayinlaydi."
        )

        # Boshqa ishchi topish
        order = await db.get_order(order_id)
        if order:
            from workers.workers_manager import workers_manager

            await workers_manager.assign_order_to_best_worker(order)

    elif data.startswith("worker_done_"):
        order_id = int(data.replace("worker_done_", ""))

        worker_id = dict(worker)["id"]
        await db.update_order_status(order_id, "bajarildi")

        # Ishchini bo'sh deb belgilash
        from workers.workers_manager import workers_manager

        await workers_manager.mark_worker_available(worker_id)

        await query.edit_message_text(
            "🎉 *Ajoyib ish!*\n\nBuyurtma bajarildi deb belgilandi. Rahmat!",
            parse_mode=ParseMode.MARKDOWN,
        )

        # Mijozga invoys yuborish va fikr so'rash
        order = await db.get_order(order_id)
        if order:
            from telegram import Bot

            bot = Bot(token=TELEGRAM_BOT_TOKEN)

            client_id = order.get("client_telegram_id")
            if client_id:
                try:
                    # Invoys generatsiya qilish
                    from crm.invoice_generator import invoice_generator

                    invoice_text = await invoice_generator.generate_invoice_text(
                        order_id
                    )

                    sent_via_tg = False
                    if client_id and not str(client_id).startswith("offline"):
                        try:
                            await bot.send_message(
                                chat_id=client_id,
                                text=f"{invoice_text}\n\nIltimos, ish sifatini baholang:",
                                parse_mode=ParseMode.MARKDOWN,
                                reply_markup=InlineKeyboardMarkup(
                                    [
                                        [
                                            InlineKeyboardButton(
                                                "⭐", callback_data=f"rate_1_{order_id}"
                                            ),
                                            InlineKeyboardButton(
                                                "⭐⭐",
                                                callback_data=f"rate_2_{order_id}",
                                            ),
                                            InlineKeyboardButton(
                                                "⭐⭐⭐",
                                                callback_data=f"rate_3_{order_id}",
                                            ),
                                            InlineKeyboardButton(
                                                "⭐⭐⭐⭐",
                                                callback_data=f"rate_4_{order_id}",
                                            ),
                                            InlineKeyboardButton(
                                                "⭐⭐⭐⭐⭐",
                                                callback_data=f"rate_5_{order_id}",
                                            ),
                                        ]
                                    ]
                                ),
                            )
                            sent_via_tg = True
                        except Exception as e:
                            logger.error(f"Telegram orqali xabar yuborish xatosi: {e}")

                    if not sent_via_tg:
                        # Offline mijoz yoki Telegram orqali yuborib bo'lmadi, SMS yuboramiz
                        client = await db.get_or_create_client(client_id)
                        phone = client.get("phone")
                        if phone:
                            from crm.sms_sender import sms_sender

                            sms_text = f"Tozalash Servis: Buyurtmangiz (#{order_id}) yakunlandi. Xizmatimizdan foydalanganingiz uchun rahmat! Summa: {order.get('total_price', 0)} UZS"
                            await sms_sender.send_sms(phone, sms_text)

                except Exception as e:
                    logger.error(f"Baholash/Invoys yuborish xatosi: {e}")
