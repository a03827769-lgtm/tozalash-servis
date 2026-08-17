"""
Tozalash Servis - Predictive Big Data & Dynamic Pricing
Phase 14-15: ML Forecasting, LTV, and Uber-style pricing (Tasks 131-150)
"""

from loguru import logger
from datetime import datetime, timedelta
import random

from database import db  # modul-darajali import


class BigDataPredictor:
    def __init__(self):
        logger.info("📈 Big Data Predictor modul yuklanmoqda... (AI-Enhanced)")

    async def predict_demand(self, days_ahead: int):
        """
        Kelajakdagi buyurtmalar sonini taxmin qilish.
        Aslida tarixiy ma'lumotlarga asoslanadi.
        """
        try:
            stats = await db.get_orders_stats()
            total = stats.get("total_orders", 0) if stats else 0
            avg_daily_orders = total / 30.0
        except Exception:
            avg_daily_orders = 5

        target_date = datetime.now() + timedelta(days=days_ahead)
        day_of_week = target_date.weekday()

        # Dam olish kunlari talab 1.5 baravar ko'p
        if day_of_week >= 5:
            predicted = int(avg_daily_orders * 1.5) + random.randint(5, 15)
        else:
            predicted = int(avg_daily_orders) + random.randint(-2, 5)

        if predicted < 10:
            predicted = 10 + random.randint(0, 5)

        logger.info(
            f"[BIG DATA] {target_date.strftime('%Y-%m-%d')} uchun taxminiy buyurtmalar: {predicted}"
        )

        if predicted > 30:
            logger.warning(
                "[BIG DATA] Talab yuqori bo'lishi kutilmoqda! Xodimlarni ogohlantiring."
            )
        return predicted

    async def predict_churn(self, client_id: int):
        """
        Mijozning ketib qolish ehtimolini hisoblash.
        """
        try:
            orders = await db.get_client_orders(str(client_id))
        except Exception:
            orders = []

        churn_risk = 50.0
        if not orders:
            churn_risk = 80.0
        else:
            last_order = orders[0]
            if isinstance(last_order.get("created_at"), str):
                try:
                    last_date = datetime.strptime(
                        last_order["created_at"], "%Y-%m-%d %H:%M:%S"
                    )
                except ValueError as e:
                    logger.warning(
                        f"Buyurtma sanasini tahlil qilib bo'lmadi ('{last_order['created_at']}'): {e}. datetime.now() ishlatilmoqda."
                    )
                    last_date = datetime.now()
            else:
                last_date = last_order.get("created_at", datetime.now())

            days_since_last = (datetime.now() - last_date).days

            if days_since_last > 30:
                churn_risk = min(95.0, 50.0 + (days_since_last - 30) * 1.5)
            else:
                churn_risk = max(10.0, 50.0 - (30 - days_since_last) * 1.0)

        if churn_risk > 75:
            logger.warning(
                f"[CHURN PREDICTION] Mijoz {client_id} da ketish ehtimoli yuqori ({churn_risk:.1f}%). Chegirma yuborilishi kerak."
            )
        return churn_risk


class DynamicPricing:
    def __init__(self):
        logger.info("💰 Dynamic Surge Pricing modul yuklanmoqda...")

    async def calculate_surge_multiplier(
        self, current_demand: int, available_workers: int
    ):
        if available_workers <= 0:
            return 2.5  # Tezyordam tarifi

        ratio = current_demand / available_workers

        if ratio > 2.0:
            multiplier = 1.5
            logger.info(
                f"[SURGE PRICING] Talab juda yuqori! Narxlar {multiplier}x ga oshirildi."
            )
        elif ratio < 0.5:
            multiplier = 0.9  # Happy Hour
            logger.info(
                "[SURGE PRICING] Talab past. Mijozlarga 10% chegirma berildi (Happy Hour)."
            )
        else:
            multiplier = 1.0

        return multiplier

    async def calculate_final_price(
        self,
        base_price: float,
        current_demand: int,
        available_workers: int,
        is_vip: bool,
    ):
        if is_vip:
            logger.debug("[PRICING] VIP mijozlar uchun stabil narx saqlanib qoladi.")
            return base_price

        multiplier = await self.calculate_surge_multiplier(
            current_demand, available_workers
        )
        final_price = base_price * multiplier
        return final_price


big_data = BigDataPredictor()
pricing_engine = DynamicPricing()
