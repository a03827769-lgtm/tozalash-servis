"""
Tozalash Servis — Kunlik Hisobot va O'z-O'zini O'rganish Tizimi
Har kuni kechqurun 21:00 da to'liq hisobot generatsiya qiladi va
o'zini tahlil qilib, keyingi kun uchun yaxshilanishlar taklif qiladi
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List
import httpx
from loguru import logger

from config import (
    ADMIN_TELEGRAM_ID,
    TELEGRAM_BOT_TOKEN,
    DAILY_REPORT_TIME,
    BUSINESS_NAME,
    DAILY_IMPROVEMENT_TARGET,
    LEARNING_ENABLED,
)
from database import db
from ai_brain import ai_brain


class DailyReportSystem:
    """Kunlik hisobot va o'z-o'zini o'rganish tizimi"""

    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.admin_id = ADMIN_TELEGRAM_ID
        self.report_time = DAILY_REPORT_TIME  # "21:00"

    async def collect_daily_stats(self) -> Dict:
        """Bugungi statistikani to'plash"""
        try:
            # Buyurtmalar statistikasi
            today_orders = await db.get_today_orders()
            orders_stats = await db.get_orders_stats(days=1)
            month_stats = await db.get_orders_stats(days=30)
            finance_stats = await db.get_finance_stats()

            # Xabarlar soni
            messages_count = await db.get_messages_count_today()

            # Ishchilar holati
            workers = await db.get_all_workers()
            available_workers = await db.get_available_workers()

            # Hisobot ma'lumotlari
            stats = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M"),
                # Buyurtmalar
                "orders_count": orders_stats.get("total_orders", 0),
                "completed_orders": orders_stats.get("completed", 0),
                "new_orders": orders_stats.get("new_orders", 0),
                "avg_order_value": round(orders_stats.get("avg_order_value", 0) or 0),
                # Moliya
                "today_revenue": finance_stats.get("today_revenue", 0) or 0,
                "month_revenue": finance_stats.get("month_revenue", 0) or 0,
                "total_revenue": finance_stats.get("total_revenue", 0) or 0,
                # Mijozlar
                "messages_today": messages_count,
                # Ishchilar
                "total_workers": len(workers),
                "available_workers": len(available_workers),
                # O'sish maqsadi
                "improvement_target": f"{DAILY_IMPROVEMENT_TARGET * 100:.0f}%",
                # Oylik statistika
                "month_orders": month_stats.get("total_orders", 0),
                "month_completed": month_stats.get("completed", 0),
            }

            return stats

        except Exception as e:
            logger.error(f"Statistika to'plash xatosi: {e}")
            return {"date": datetime.now().strftime("%Y-%m-%d"), "error": str(e)}

    async def generate_and_send_report(self):
        """Hisobotni generatsiya qilib yuborish"""
        try:
            logger.info("📊 Kunlik hisobot tayyorlanmoqda...")

            # Statistikani to'plash
            stats = await self.collect_daily_stats()

            # AI o'rganish natijalarini olish
            improvements = []
            if LEARNING_ENABLED:
                improvements = await ai_brain.self_improve()

            # AI dan hisobot generatsiya
            report_text = await ai_brain.generate_daily_report(
                {**stats, "ai_improvements": improvements}
            )

            # Hisobotni ma'lumotlar bazasiga saqlash
            await db.save_daily_report(
                {
                    **stats,
                    "ai_improvements": improvements,
                    "messages_received": stats.get("messages_today", 0),
                    "messages_answered": stats.get(
                        "messages_today", 0
                    ),  # Bot hamma javob beradi
                }
            )

            # Adminga yuborish
            await self._send_to_admin(report_text, stats)

            logger.info("✅ Kunlik hisobot muvaffaqiyatli yuborildi!")

        except Exception as e:
            logger.error(f"Kunlik hisobot xatosi: {e}")

    async def _send_to_admin(self, report_text: str, stats: Dict):
        """Adminga hisobotni yuborish"""
        try:
            # Qisqa statistika bloki
            quick_stats = f"""
📊 *{datetime.now().strftime('%d.%m.%Y')} — KUNLIK HISOBOT*
{BUSINESS_NAME}

━━━━━━━━━━━━━━━━━━━
💰 Bugungi daromad: *{stats.get('today_revenue', 0):,.0f} so'm*
📦 Buyurtmalar: *{stats.get('orders_count', 0)} ta*
✅ Bajarilgan: *{stats.get('completed_orders', 0)} ta*
💬 Xabarlar: *{stats.get('messages_today', 0)} ta*
👷 Ishchilar (bo'sh): *{stats.get('available_workers', 0)} ta*
━━━━━━━━━━━━━━━━━━━

"""

            full_message = quick_stats + report_text

            # Telegram API orqali yuborish (max 4096 belgi)
            async with httpx.AsyncClient() as client:
                # Agar xabar uzun bo'lsa bo'lib yuborish
                messages = self._split_message(full_message, max_length=4000)

                for i, msg in enumerate(messages):
                    payload = {
                        "chat_id": self.admin_id,
                        "text": msg,
                        "parse_mode": "Markdown",
                    }

                    url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                    await client.post(url, json=payload)

                    if i < len(messages) - 1:
                        await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"Admin ga yuborish xatosi: {e}")

    def _split_message(self, text: str, max_length: int = 4000) -> List[str]:
        """Uzun xabarni bo'lish"""
        if len(text) <= max_length:
            return [text]

        parts = []
        while text:
            if len(text) <= max_length:
                parts.append(text)
                break

            # So'z chegarasida kesish
            split_point = text.rfind("\n", 0, max_length)
            if split_point == -1:
                split_point = max_length

            parts.append(text[:split_point])
            text = text[split_point:].lstrip()

        return parts

    async def send_morning_summary(self):
        """Ertalabki qisqa xulosa"""
        try:
            now = datetime.now()
            yesterday_stats = await db.get_orders_stats(days=1)

            text = f"""🌅 *Xayrli tong!*

📅 Bugun: {now.strftime('%d.%m.%Y, %A')}

Kecha:
📦 Buyurtmalar: {yesterday_stats.get('total_orders', 0)} ta
💰 Daromad: {yesterday_stats.get('total_revenue', 0) or 0:,.0f} so'm

🤖 Bot ishlayapti va mijozlarni kutmoqda!
💪 Bugun ham yaxshi ish!"""

            async with httpx.AsyncClient() as client:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                await client.post(
                    url,
                    json={
                        "chat_id": self.admin_id,
                        "text": text,
                        "parse_mode": "Markdown",
                    },
                )

        except Exception as e:
            logger.error(f"Ertalabki xulosa xatosi: {e}")

    async def run_scheduler(self):
        """Hisobot schedulerini ishga tushirish"""
        logger.info("📊 Kunlik Hisobot Scheduler ishga tushdi")

        report_sent_today = False
        morning_sent_today = False

        while True:
            try:
                now = datetime.now()
                current_time = now.strftime("%H:%M")
                today = now.strftime("%Y-%m-%d")

                # Ertalabki xulosa (08:30)
                if current_time == "08:30" and not morning_sent_today:
                    await self.send_morning_summary()
                    morning_sent_today = True

                # Kunlik hisobot (21:00)
                if current_time == self.report_time and not report_sent_today:
                    await self.generate_and_send_report()
                    report_sent_today = True

                # Yangi kun boshlanishida flaglarni reset qilish
                if current_time == "00:01":
                    report_sent_today = False
                    morning_sent_today = False

            except Exception as e:
                logger.error(f"Hisobot scheduler xatosi: {e}")

            await asyncio.sleep(30)


class SelfLearningSystem:
    """O'z-o'zini o'rganish va takomillashtirish tizimi"""

    def __init__(self):
        self.improvement_target = DAILY_IMPROVEMENT_TARGET
        self.daily_improvements = []

    async def analyze_performance(self) -> Dict:
        """Ish samaradorligini tahlil qilish"""
        # Muvaffaqiyatli patternlarni olish
        successful_orders = await db.get_successful_patterns(
            "order_conversion", limit=20
        )

        # Statistikani olish
        stats = await db.get_orders_stats(days=7)

        return {
            "conversion_rate": await self._calculate_conversion_rate(),
            "successful_patterns": len(successful_orders),
            "avg_response_effectiveness": 5.0,  # Default
            "weekly_orders": stats.get("total_orders", 0),
            "weekly_revenue": stats.get("total_revenue", 0) or 0,
        }

    async def _calculate_conversion_rate(self) -> float:
        """Suhbatlardan buyurtmaga o'tish nisbati"""
        try:
            async with db.get_conn() as conn:
                # Jami noyob foydalanuvchilar (so'nggi 7 kun)
                async with conn.execute(
                    "SELECT COUNT(DISTINCT telegram_id) as cnt FROM conversations "
                    "WHERE created_at >= datetime('now', '-7 days')"
                ) as cursor:
                    row = await cursor.fetchone()
                    total_users = row["cnt"] if row else 0

                # Buyurtma berganlar (so'nggi 7 kun)
                async with conn.execute(
                    "SELECT COUNT(DISTINCT client_id) as cnt FROM orders "
                    "WHERE created_at >= datetime('now', '-7 days')"
                ) as cursor:
                    row = await cursor.fetchone()
                    converted = row["cnt"] if row else 0

                if total_users > 0:
                    return (converted / total_users) * 100
                return 0
        except Exception as e:
            logger.error(f"Konversiya nisbatini hisoblashda xato: {e}", exc_info=True)
            return 0

    async def implement_improvements(self, improvements: List[str]):
        """Yaxshilanishlarni qo'llash va saqlash"""
        for imp in improvements:
            self.daily_improvements.append(
                {"improvement": imp, "implemented_at": datetime.now().isoformat()}
            )
            logger.info(f"🧠 Yaxshilanish qo'llandi: {imp}")

    async def run_daily_learning(self):
        """Kunlik o'rganish sikli"""
        logger.info("🧠 Kunlik o'rganish siklі ishga tushdi")

        while True:
            now = datetime.now()

            # Har kuni 23:00 da o'rganish
            if now.hour == 23 and now.minute == 0:
                try:
                    logger.info("🧠 Kunlik o'rganish boshlanmoqda...")

                    # Performance tahlil
                    performance = await self.analyze_performance()

                    # AI o'rganish
                    improvements = await ai_brain.self_improve()

                    # Yaxshilanishlarni qo'llash
                    await self.implement_improvements(improvements)

                    logger.info(
                        f"✅ Kunlik o'rganish tugadi. {len(improvements)} ta yaxshilanish"
                    )

                    await asyncio.sleep(61)
                except Exception as e:
                    logger.error(f"O'rganish xatosi: {e}")

            await asyncio.sleep(30)


# Global instances
daily_report_system = DailyReportSystem()
self_learning_system = SelfLearningSystem()
