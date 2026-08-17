from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from datetime import datetime
from loguru import logger

from config import ADMIN_TELEGRAM_ID, ORDERS_CHANNEL_ID
from database import db


async def notify_admin_new_order(bot, order: dict, client: dict):
    """Adminga va kanalga yangi buyurtma haqida xabar yuborish"""
    text = f"""🔔 *YANGI BUYURTMA!*

📋 Raqam: #{order.get('order_number')}
👤 Mijoz: {client.get('name', 'Nomalum')}
🧹 Xizmat: {order.get('service_name')}
📍 Manzil: {order.get('address')}
📅 Sana: {order.get('scheduled_date')}
🔢 Miqdor: {order.get('quantity')} {order.get('unit', '')}
💰 Narx: {order.get('total_price', 0):,.0f} so'm
⏰ Vaqt: {datetime.now().strftime('%H:%M %d.%m.%Y')}"""

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Qabul qilish", callback_data=f"admin_accept_{order['id']}"
                ),
                InlineKeyboardButton(
                    "❌ Rad etish", callback_data=f"admin_reject_{order['id']}"
                ),
            ],
            (
                [
                    InlineKeyboardButton(
                        "📞 Mijozga qo'ng'iroq", url=f"tel:{client.get('phone', '')}"
                    )
                ]
                if client.get("phone")
                else []
            ),
        ]
    )

    try:
        if ADMIN_TELEGRAM_ID:
            await bot.send_message(
                chat_id=ADMIN_TELEGRAM_ID,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard,
            )
    except Exception as e:
        logger.error(f"Admin bildirishnoma xatosi: {e}")

    try:
        if ORDERS_CHANNEL_ID:
            # Kanalda faqat ma'lumot beriladi, qabul qilish/rad etish buttonlarsiz bo'lishi mumkin,
            # yoki xuddi shu keyboard ni qo'yish mumkin
            await bot.send_message(
                chat_id=ORDERS_CHANNEL_ID,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard,
            )
    except Exception as e:
        logger.error(f"Kanal bildirishnoma xatosi: {e}")


async def assign_worker_to_order(bot, order: dict):
    """Buyurtmaga ishchi tayinlash va xabar yuborish"""
    try:
        workers = await db.get_available_workers()

        if not workers:
            logger.warning("Bo'sh ishchi topilmadi!")
            return

        # Birinchi bo'sh ishchini tayinlash
        worker = workers[0]

        if not worker.get("telegram_id"):
            return

        worker_text = f"""🔔 *YANGI VAZIFA!*

📋 Buyurtma: #{order.get('order_number')}
🧹 Xizmat: {order.get('service_name')}
📍 Manzil: {order.get('address')}
📅 Sana: {order.get('scheduled_date')}

✅ Ushbu vazifani qabul qilyapsizmi?"""

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Qabul qilaman", callback_data=f"worker_accept_{order['id']}"
                    ),
                    InlineKeyboardButton(
                        "❌ Qabul qilolmayman",
                        callback_data=f"worker_reject_{order['id']}",
                    ),
                ]
            ]
        )

        await bot.send_message(
            chat_id=worker["telegram_id"],
            text=worker_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
        )

        # Buyurtmaga ishchini tayinlash
        await db.update_order_status(order["id"], "tayinlandi", str(worker["id"]))
        logger.info(
            f"✅ Ishchi tayinlandi: {worker['name']} → Buyurtma #{order.get('order_number')}"
        )

    except Exception as e:
        logger.error(f"Ishchi tayinlash xatosi: {e}")
