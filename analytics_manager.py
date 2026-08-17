"""
Tozalash Servis — Analytics Manager Moduli
Buyurtmalar va mijozlar bo'yicha kunlik tahlillar (SQLite versiyasi).
"""

import aiosqlite
from datetime import datetime
from typing import Optional
from database import db
from loguru import logger


class AnalyticsManager:
    """Kunlik tahlil va Customer Lifetime Value hisoblovchi klass."""

    async def get_daily_summary(self) -> str:
        """
        Bugungi buyurtmalar va daromad haqida qisqacha xulosa.

        Returns:
            Formatlangan Markdown matni (Telegram uchun).
        """
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
        today_str = now.strftime("%Y-%m-%d")

        try:
            async with db.get_conn() as conn:
                # Bajarilgan buyurtmalar
                async with conn.execute(
                    """
                    SELECT
                        COUNT(*) AS cnt,
                        COALESCE(SUM(total_price), 0) AS total
                    FROM orders
                    WHERE created_at >= ?
                      AND created_at <= ?
                      AND status = 'bajarildi'
                    """,
                    (today_start, today_end),
                ) as cur:
                    completed_data = await cur.fetchone()
                    completed_count = completed_data["cnt"] if completed_data else 0
                    earned = completed_data["total"] if completed_data else 0

                # Eng mashhur xizmatlar (Top 3)
                async with conn.execute(
                    """
                    SELECT service_type, COUNT(*) AS c
                    FROM orders
                    WHERE created_at >= ?
                      AND created_at <= ?
                    GROUP BY service_type
                    ORDER BY c DESC
                    LIMIT 3
                    """,
                    (today_start, today_end),
                ) as cur2:
                    popular = await cur2.fetchall()
                    popular_str = (
                        ", ".join([f"{p['service_type']} ({p['c']})" for p in popular])
                        if popular
                        else "N/A"
                    )

            return (
                f"📊 *Kunlik Hisobot ({today_str})*\n\n"
                f"✅ Bajarilgan buyurtmalar: {completed_count}\n"
                f"💰 Jami daromad: {earned:,.0f} UZS\n"
                f"🔥 Mashhur xizmatlar: {popular_str}"
            )

        except Exception as e:
            logger.error(f"AnalyticsManager.get_daily_summary xatosi: {e}")
            return "📊 Kunlik hisobot tayyorlanmadi (texnik xatolik)."

    async def calculate_clv(self, user_id: int) -> float:
        """
        Mijozning Lifetime Value (CLV) qiymatini hisoblash.

        Args:
            user_id: Mijoz ID si (clients.id).

        Returns:
            Jami sarflangan summa (UZS), yoki 0.0 xato holda.
        """
        try:
            async with db.get_conn() as conn:
                async with conn.execute(
                    """
                    SELECT COALESCE(SUM(total_price), 0) AS total
                    FROM orders
                    WHERE client_id = ?
                      AND status = 'bajarildi'
                    """,
                    (user_id,),
                ) as cur:
                    res = await cur.fetchone()
                    return float(res["total"]) if res else 0.0
        except Exception as e:
            logger.error(
                f"AnalyticsManager.calculate_clv xatosi (user_id={user_id}): {e}"
            )
            return 0.0


analytics_manager = AnalyticsManager()
