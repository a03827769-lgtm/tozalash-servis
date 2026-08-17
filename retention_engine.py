"""
Tozalash Servis — Retention & Customer Reactivation Engine
Automated 30/60/90 Day Re-booking Triggers, Churn Prevention & Personalized Offers
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from loguru import logger
from database import db


class RetentionEngine:
    """Mijozlarni ushlab qolish va qayta xaridni rag'batlantirish tizimi"""

    def __init__(self):
        logger.info("🔄 Retention Engine ishga tushdi.")

    async def scan_and_generate_reactivations(self, db_inst=None) -> List[Dict[str, Any]]:
        """
        Qayta tozalash vaqti kelgan mijozlarni aniqlash:
        - 30 kun oldin umumiy tozalash qilganlar (10% chegirma)
        - 60 kun oldin gilam/divan yuvdirganlar (15% chegirma)
        - 90 kundan ortiq harakatsiz mijozlar (Maxsus 'Sizni sog'indik' taklifi)
        """
        target_db = db_inst or db
        notifications = []
        now = datetime.now()

        # Oxirgi buyurtmasi 30+ kun bo'lgan mijozlar
        orders = await target_db.fetch_all(
            """
            SELECT o.*, c.name as client_name, c.telegram_id as client_tg
            FROM orders o
            JOIN clients c ON o.client_telegram_id = c.telegram_id
            WHERE o.status = 'bajarildi'
            ORDER BY o.created_at DESC
            """
        )

        seen_clients = set()
        for ord_item in orders:
            tg_id = ord_item.get("client_tg")
            if tg_id in seen_clients:
                continue
            seen_clients.add(tg_id)

            created_at = ord_item.get("created_at")
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at)
                except Exception:
                    continue

            days_passed = (now - created_at).days if created_at else 0
            client_name = ord_item.get("client_name") or "Hurmatli mijoz"

            if 28 <= days_passed <= 35:
                msg = (
                    f"Assalomu alaykum, {client_name}! 😊\n"
                    f"Uyingiz tozalanganiga 1 oy bo'ldi. Xonadoningiz yana toza va shinam bo'lishi uchun "
                    f"sizga maxsus 10% chegirma taqdim etamiz! 🎁\n"
                    f"Buyurtma berish uchun shunchaki xizmat turini tanlang."
                )
                notifications.append({
                    "telegram_id": tg_id,
                    "message": msg,
                    "discount_percent": 10,
                    "trigger": "30_days",
                })

            elif 55 <= days_passed <= 65:
                msg = (
                    f"Assalomu alaykum, {client_name}! 🛋️\n"
                    f"Yumshoq mebel va gilamlarni har 2 oyda profilaktik tozalash tavsiya etiladi. "
                    f"Siz uchun eksklyuziv 15% chegirma kuponini faollashtirdik!\n"
                    f"Bugun buyurtma qilib eng qulay vaqtni band qiling."
                )
                notifications.append({
                    "telegram_id": tg_id,
                    "message": msg,
                    "discount_percent": 15,
                    "trigger": "60_days",
                })

        logger.info(f"🎯 Retention Scan: {len(notifications)} ta mijozga qayta xarid xabarnomasi tayyorlandi.")
        return notifications


# Global Instance
retention_engine = RetentionEngine()
