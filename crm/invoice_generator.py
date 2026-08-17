import os
from datetime import datetime
from loguru import logger
from database import db
from config import BUSINESS_NAME, BUSINESS_PHONE, BUSINESS_CITY


class InvoiceGenerator:
    """Buyurtmalar uchun elektron chek (Invoice) generatsiya qilish moduli"""

    def __init__(self):
        pass

    async def generate_invoice_text(self, order_id: int) -> str:
        """Buyurtma ma'lumotlari asosida Markdown formatidagi invoys yaratadi"""
        try:
            async with db.get_conn() as conn:
                # Buyurtma ma'lumotlarini olish
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT * FROM orders WHERE id = %s", (order_id,)
                    )
                    order = await cursor.fetchone()

                if not order:
                    return "Xatolik: Buyurtma topilmadi."

                # Mijoz ma'lumotlarini olish
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT name, phone FROM clients WHERE id = %s",
                        (order["client_id"],),
                    )
                    client = await cursor.fetchone()

            client_name = client["name"] if client else "Noma'lum Mijoz"
            client_phone = client["phone"] if client else "Kiritilmagan"

            order_num = order["order_number"]
            service_name = order["service_name"]
            quantity = order["quantity"]
            total_price = order["total_price"]
            date_done = datetime.now().strftime("%Y-%m-%d %H:%M")

            invoice_text = f"""🧾 *RASMIY CHEK (INVOYS)*
===============================
🏢 *{BUSINESS_NAME}*
📍 {BUSINESS_CITY}
📞 {BUSINESS_PHONE}
===============================

📄 *Buyurtma:* #{order_num}
📅 *Sana:* {date_done}

👤 *Mijoz:* {client_name}
📞 *Tel:* {client_phone}
🏠 *Manzil:* {order['address']}

*XIZMATLAR:*
-------------------------------
🧹 {service_name}
📊 Miqdor: {quantity}
💰 Jami summa: {total_price:,.0f} UZS
-------------------------------

💳 *TO'LANISHI KEREK:* {total_price:,.0f} UZS

✨ *Xizmatimizdan foydalanganingiz uchun tashakkur!*
_Umid qilamizki, natijadan mamnunsiz. Har qanday savollar bo'yicha bizga murojaat qiling._"""

            return invoice_text

        except Exception as e:
            logger.error(f"Invoys yaratishda xato: {e}")
            return "Kechirasiz, chek yaratishda texnik xatolik yuz berdi."


invoice_generator = InvoiceGenerator()
