"""
Tozalash Servis — Ishchilar Boshqaruv Tizimi
10 ta ishchini avtomatik boshqarish, vazifa berish va monitoring
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Optional
import httpx
from loguru import logger
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
import aiomysql

from config import TELEGRAM_BOT_TOKEN, ADMIN_TELEGRAM_ID
from database import db


class WorkersManager:
    """Ishchilar boshqaruv tizimi"""

    def __init__(self):
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)

    async def setup_initial_workers(self):
        """Boshlang'ich ishchilarni bazaga qo'shish (bir marta)"""
        workers_data = [
            {
                "name": "1-Ishchi",
                "phone": "+998901000001",
                "telegram_id": "WORKER_TG_ID_1",
            },
            {
                "name": "2-Ishchi",
                "phone": "+998901000002",
                "telegram_id": "WORKER_TG_ID_2",
            },
            {
                "name": "3-Ishchi",
                "phone": "+998901000003",
                "telegram_id": "WORKER_TG_ID_3",
            },
            {
                "name": "4-Ishchi",
                "phone": "+998901000004",
                "telegram_id": "WORKER_TG_ID_4",
            },
            {
                "name": "5-Ishchi",
                "phone": "+998901000005",
                "telegram_id": "WORKER_TG_ID_5",
            },
            {
                "name": "6-Ishchi",
                "phone": "+998901000006",
                "telegram_id": "WORKER_TG_ID_6",
            },
            {
                "name": "7-Ishchi",
                "phone": "+998901000007",
                "telegram_id": "WORKER_TG_ID_7",
            },
            {
                "name": "8-Ishchi",
                "phone": "+998901000008",
                "telegram_id": "WORKER_TG_ID_8",
            },
            {
                "name": "9-Ishchi",
                "phone": "+998901000009",
                "telegram_id": "WORKER_TG_ID_9",
            },
            {
                "name": "10-Ishchi",
                "phone": "+998901000010",
                "telegram_id": "WORKER_TG_ID_10",
            },
        ]

        for worker in workers_data:
            await db.add_worker(
                name=worker["name"],
                phone=worker["phone"],
                telegram_id=worker["telegram_id"],
            )

        logger.info("✅ Boshlang'ich ishchilar bazaga qo'shildi")

    async def assign_order_to_best_worker(
        self, order: Dict, order_lat: float = None, order_lon: float = None
    ) -> Optional[Dict]:
        """Buyurtmaga eng mos ishchini topib tayinlash (GPS va Rating asosida)"""
        available_workers = await db.get_available_workers()

        if not available_workers:
            logger.warning("⚠️ Bo'sh ishchi yo'q!")
            await self._notify_admin_no_worker(order)
            return None

        # AI Auto-Dispatch: Eng yuqori reyting, oz ish va eng yaqin ishchini tanlash
        def calculate_score(w):
            rating_score = w.get("rating", 5.0) * 20
            workload_penalty = w.get("total_jobs", 0) * 5

            # GPS asosiada masofa jarimasi (agar lat/lon bo'lsa)
            distance_penalty = 0
            if order_lat and order_lon and w.get("gps_lat") and w.get("gps_lon"):
                dist = (
                    (w["gps_lat"] - order_lat) ** 2 + (w["gps_lon"] - order_lon) ** 2
                ) ** 0.5
                distance_penalty = dist * 1000  # Taxminiy koeficient

            return rating_score - workload_penalty - distance_penalty

        best_worker = max(available_workers, key=calculate_score)

        # Ishchiga vazifa yuborish
        success = await self._send_task_to_worker(best_worker, order)

        if success:
            # Sifat nazorati (QA) rasmlarini talab qilish xabarini ham jo'natib qo'yamiz
            asyncio.create_task(
                self.request_qa_photos(best_worker.get("telegram_id"), order.get("id"))
            )

            # Ishchini band deb belgilash
            async with db.get_conn() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE workers SET is_available = 0 WHERE id = %s",
                        (best_worker["id"],),
                    )

            logger.info(
                f"✅ Ishchi tayinlandi: {best_worker['name']} → #{order.get('order_number')}"
            )
            return best_worker

        return None

    async def _send_task_to_worker(self, worker: Dict, order: Dict) -> bool:
        """Ishchiga vazifa xabari yuborish"""
        try:
            telegram_id = worker.get("telegram_id")
            if not telegram_id or telegram_id.startswith("WORKER_TG_ID"):
                logger.warning(f"Ishchi Telegram ID yo'q: {worker['name']}")
                return False

            service_name = order.get("service_name", "Tozalash")
            address = order.get("address", "Manzil ko'rsatilmagan")
            date = order.get("scheduled_date", "Sana ko'rsatilmagan")
            order_num = order.get("order_number", "???")
            total = order.get("total_price", 0)

            text = f"""🔔 *YANGI VAZIFA #{order_num}*

🧹 Xizmat: {service_name}
📍 Manzil: {address}
📅 Sana: {date}
💰 Summa: {total:,.0f} so'm

⚠️ Iltimos, qabul qilganingizni tasdiqlang!"""

            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "✅ Qabul qildim",
                            callback_data=f"worker_accept_{order.get('id', 0)}",
                        ),
                        InlineKeyboardButton(
                            "❌ Qabul qilolmayman",
                            callback_data=f"worker_reject_{order.get('id', 0)}",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "🗺 Manzilni ko'rish",
                            url=f"https://maps.google.com/?q={address.replace(' ', '+')}",
                        )
                    ],
                ]
            )

            await self.bot.send_message(
                chat_id=telegram_id,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard,
            )

            return True

        except Exception as e:
            logger.error(f"Ishchiga xabar yuborish xatosi: {e}")
            return False

    async def _notify_admin_no_worker(self, order: Dict):
        """Adminga ishchi yo'qligi haqida xabar"""
        try:
            text = f"""⚠️ *DIQQAT: Ishchi topilmadi!*

Buyurtma #{order.get('order_number')} uchun bo'sh ishchi yo'q.
Iltimos, qo'lda tayinlang!

🧹 Xizmat: {order.get('service_name')}
📍 Manzil: {order.get('address')}
📅 Sana: {order.get('scheduled_date')}"""

            await self.bot.send_message(
                chat_id=ADMIN_TELEGRAM_ID, text=text, parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Admin xabari xatosi: {e}")

    async def mark_worker_available(self, worker_id: int):
        """Ishchini bo'sh deb belgilash (ish tugaganidan keyin)"""
        async with db.get_conn() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "UPDATE workers SET is_available = 1, total_jobs = total_jobs + 1 WHERE id = %s",
                    (worker_id,),
                )
        logger.info(f"✅ Ishchi #{worker_id} bo'sh deb belgilandi")

    async def request_qa_photos(self, worker_telegram_id: str, order_id: int):
        """Ishchidan sifat nazorati uchun Before/After rasm so'rash"""
        if not worker_telegram_id or worker_telegram_id.startswith("WORKER_TG"):
            return
        try:
            text = (
                f"📸 *SIFAT NAZORATI (QA)*\n\n"
                f"Buyurtma #{order_id} bo'yicha ishni tugatganingizdan so'ng, "
                f"orqaga 'Oldin' (Before) va 'Keyin' (After) rasmlarini yuboring.\n"
                f"AI sifatni baholaydi va 5-yulduzli baho uchun bonus yoziladi!"
            )
            await self.bot.send_message(
                chat_id=worker_telegram_id, text=text, parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"QA rasm so'rashda xato: {e}")

    async def run_predictive_maintenance(self):
        """
        AI Predictive Maintenance:
        Checks completed orders from a certain time ago and sends a smart reminder to the customer.
        For example, suggesting a new cleaning 30 days after a regular cleaning, or 6 months after a carpet cleaning.
        """
        try:
            logger.info("Predictive Maintenance analizi boshlanmoqda...")
            # Real loyihada bu sql query bilan o'tgan buyurtmalarni (30 kun/6 oy oldingi) topadi.
            # Hozircha stub logic:

            async with db.get_conn() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # Misol: 30 kundan eski "regular_cleaning" buyurtmalari
                    sql = "SELECT client_telegram_id AS telegram_id, service_type, created_at FROM orders WHERE status='completed' AND created_at < DATE_SUB(NOW(), INTERVAL 30 DAY)"
                    await cursor.execute(sql)
                    old_orders = await cursor.fetchall()

            for order in old_orders:
                tg_id = order["telegram_id"]
                svc = order["service_type"]

                # AI orqali personalizatsiya qilingan xabar yozish
                from ai_brain import ai_brain

                msg = f"Assalomu alaykum! Siz oxirgi marta bizdan '{svc}' xizmatidan foydalangandingiz. Uy/ofisingizni yana tozalash vaqti kelmadimikan? Hozir buyurtma bersangiz, sizga maxsus 10% chegirma taqdim etamiz! 😊"
                try:
                    prompt = f"Mijoz oldin '{svc}' xizmatidan foydalangan. Unga shu xizmatni yana taklif qiladigan, do'stona va sotuvga undovchi 2-3 ta gapdan iborat o'zbekcha xabar yoz (oxirida 10% chegirma taklif qil)."
                    if ai_brain.model:
                        resp = await ai_brain.model.generate_content_async(prompt)
                        if resp.text:
                            msg = resp.text.strip()
                except Exception as e:
                    logger.warning(f"AI marketing xabarini yaratishda xato: {e}")

                try:
                    await self.bot.send_message(chat_id=tg_id, text=msg)
                    logger.info(f"Predictive maintenance xabari yuborildi: {tg_id}")
                except Exception as e:
                    logger.warning(f"Xabar yuborishda xato ({tg_id}): {e}")

        except Exception as e:
            logger.error(f"Predictive Maintenance xatosi: {e}")

    async def get_workers_status_report(self) -> str:
        """Barcha ishchilar holati hisoboti"""
        workers = await db.get_all_workers()

        if not workers:
            return "Ishchilar topilmadi"

        report = "👷 *ISHCHILAR HOLATI:*\n\n"

        for i, w in enumerate(workers, 1):
            status = "🟢 Bo'sh" if w.get("is_available") else "🔴 Band"
            report += f"{i}. {w.get('name', '?')} — {status}\n"
            report += f"   📊 Jami ish: {w.get('total_jobs', 0)} ta\n"
            report += f"   ⭐ Reyting: {w.get('rating', 5.0)}\n\n"

        return report

    async def calculate_monthly_salaries(self) -> Dict:
        """Oylik maoshlarni hisoblash"""
        workers = await db.get_all_workers()
        salaries = {}

        for worker in workers:
            worker_id = worker["id"]

            # Bu oy qilgan ishlar soni
            async with db.get_conn() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                        SELECT COUNT(*) as jobs, SUM(total_price) as total_revenue
                        FROM orders 
                        WHERE worker_ids LIKE %s 
                        AND DATE_FORMAT(created_at, '%Y-%m') = DATE_FORMAT(CURDATE(), '%Y-%m')
                        AND status = 'bajarildi'
                    """,
                        (f"%{worker_id}%",),
                    )
                    result = await cursor.fetchone()

            jobs = result["jobs"] or 0
            total_revenue = result["total_revenue"] or 0

            # Maosh = Jami daromadning 30% (sozlanishi mumkin)
            base_salary = total_revenue * 0.30

            # Bonus tizimi (5-yulduzli baho uchun bonus)
            # Faraz qilaylik, o'rtacha reyting 4.8 dan baland bo'lsa, +5% bonus
            worker_rating = worker.get("rating", 5.0)
            bonus = 0
            if worker_rating >= 4.8 and jobs > 5:
                bonus = base_salary * 0.05  # 5% bonus

            total_salary = base_salary + bonus

            salaries[worker["name"]] = {
                "jobs_count": jobs,
                "total_revenue": total_revenue,
                "base_salary": base_salary,
                "bonus": bonus,
                "salary": total_salary,
            }

        return salaries

    async def send_salary_report(self):
        """Oylik maosh hisobotini adminga yuborish"""
        try:
            salaries = await self.calculate_monthly_salaries()

            now = datetime.now()
            month_name = now.strftime("%B %Y")

            text = f"💰 *{month_name} — MAOSH HISOBOTI*\n\n"

            total_salary = 0
            for name, data in salaries.items():
                text += f"👷 *{name}*\n"
                text += f"   📦 Ishlar: {data['jobs_count']} ta\n"
                text += f"   💰 Hissa: {data['total_revenue']:,.0f} so'm\n"
                text += f"   🎯 Asosiy Maosh (30%): {data['base_salary']:,.0f} so'm\n"
                if data["bonus"] > 0:
                    text += f"   ⭐ Sifat Bonusi: +{data['bonus']:,.0f} so'm\n"
                text += f"   💵 Jami to'lov: {data['salary']:,.0f} so'm\n\n"
                total_salary += data["salary"]

            text += f"━━━━━━━━━━━\n💳 *Jami maoshlar: {total_salary:,.0f} so'm*"

            await self.bot.send_message(
                chat_id=ADMIN_TELEGRAM_ID, text=text, parse_mode=ParseMode.MARKDOWN
            )

            logger.info("✅ Maosh hisoboti yuborildi")

        except Exception as e:
            logger.error(f"Maosh hisobot xatosi: {e}")

    async def run_scheduler(self):
        """Ishchilar scheduler"""
        logger.info("👷 Ishchilar Scheduler ishga tushdi")

        salary_sent = False

        while True:
            now = datetime.now()

            # Har oy oxirida (30/31-kuni 20:00) maosh hisoboti
            if now.day >= 28 and now.hour == 20 and now.minute == 0 and not salary_sent:
                await self.send_salary_report()
                salary_sent = True

            # Yangi oy boshida reset
            if now.day == 1:
                salary_sent = False

            await asyncio.sleep(30)


# Global instance
workers_manager = WorkersManager()
