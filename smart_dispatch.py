"""
Tozalash Servis — Smart Worker Dispatch & Logistics Engine 2.0
1. Multi-Factor Scoring: Proximity (40%) + Rating (30%) + Experience (20%) + Equipment (10%)
2. Dynamic Surge Pricing: Talab va vaqtga qarab narxni 1.0x - 1.5x dinamik sozlash
3. Team Matching Engine: Katta obyektlar (>150 kv.m) uchun avtomatlashtirilgan brigada tuzish
4. Emergency Re-assignment: 30 soniyalik fors-major zaxira xodimiga o'tkazish
"""

import math
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger
from database import db


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Ikki koordinata orasidagi masofani kilometrda hisoblash (Haversine Formula)"""
    if not (lat1 and lon1 and lat2 and lon2):
        return 999.0  # Noma'lum masofa uchun katta qiymat

    R = 6371.0  # Yer radiusi (km)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class SmartDispatcher:
    """Buyurtmaga eng mos tozalash xodimlarini avtomatik tanlash va boshqarish"""

    def __init__(self):
        logger.info("📍 Smart Dispatcher 2.0 moduli ishga tushdi.")

    def calculate_surge_multiplier(self, active_orders_count: int, available_workers_count: int) -> float:
        """
        Dinamik narxlash koeffitsientini hisoblash (Surge Pricing: 1.0x - 1.5x)
        Shanba-Yakshanba va bayram kunlari hamda talab taklifdan 2x ko'p bo'lganda ishlaydi.
        """
        now = datetime.now()
        is_weekend = now.weekday() in (5, 6)  # Shanba yoki Yakshanba
        is_rush_hour = (now.hour in (8, 9, 10, 17, 18, 19))

        base_multiplier = 1.0

        if available_workers_count > 0:
            demand_ratio = active_orders_count / available_workers_count
            if demand_ratio > 3.0:
                base_multiplier = 1.35
            elif demand_ratio > 1.8:
                base_multiplier = 1.20

        if is_weekend:
            base_multiplier += 0.10
        if is_rush_hour:
            base_multiplier += 0.05

        return min(1.50, round(base_multiplier, 2))

    async def calculate_worker_score(
        self, worker: Dict[str, Any], order: Dict[str, Any]
    ) -> float:
        """
        Xodimning ushbu buyurtmaga moslik ballini hisoblash (0 - 100 ball)
        Score = (40 * DistanceScore) + (30 * RatingScore) + (20 * ExpScore) + (10 * SkillScore)
        """
        order_lat = order.get("lat") or 41.311081
        order_lon = order.get("lon") or 69.240562
        worker_lat = worker.get("current_lat") or 41.311081
        worker_lon = worker.get("current_lon") or 69.240562

        dist_km = haversine_distance(order_lat, order_lon, worker_lat, worker_lon)
        if dist_km <= 3.0:
            dist_score = 40.0
        elif dist_km <= 8.0:
            dist_score = 30.0
        elif dist_km <= 15.0:
            dist_score = 20.0
        else:
            dist_score = max(5.0, 40.0 - (dist_km * 1.5))

        rating = float(worker.get("rating") or 5.0)
        rating_score = (rating / 5.0) * 30.0

        completed = int(worker.get("completed_orders") or 0)
        exp_score = min(20.0, (completed / 50.0) * 20.0)

        service_type = (order.get("service_type") or "").lower()
        skills = (worker.get("skills") or "").lower()
        skill_score = 10.0 if (service_type in skills or "universal" in skills) else 5.0

        total_score = dist_score + rating_score + exp_score + skill_score
        return round(total_score, 2)

    async def assign_optimal_worker(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Buyurtmaga eng yuqori ball to'plagan xodimni biriktirish"""
        order = await db.get_order(order_id)
        if not order:
            logger.warning(f"Buyurtma #{order_id} topilmadi.")
            return None

        workers = await db.get_active_workers()
        if not workers:
            logger.warning(f"Aktiv xodimlar mavjud emas (Buyurtma #{order_id}).")
            return None

        # Kvadratura bo'yicha brigada talab qilinishini tekshirish (>150 kv.m)
        area = float(order.get("area_sqm") or 0.0)
        if area >= 150.0:
            return await self.assign_team_for_large_venue(order_id, workers, area)

        scored_workers = []
        for w in workers:
            score = await self.calculate_worker_score(w, order)
            scored_workers.append((score, w))

        scored_workers.sort(key=lambda x: x[0], reverse=True)
        best_score, best_worker = scored_workers[0]

        await db.update_order_status(order_id, "ishchiga_biriktirildi", worker_id=best_worker["id"])
        logger.success(f"🎯 Buyurtma #{order_id} xodimga biriktirildi: {best_worker['name']} (Ball: {best_score})")

        return {
            "order_id": order_id,
            "worker": best_worker,
            "match_score": best_score,
            "team_size": 1
        }

    async def assign_team_for_large_venue(self, order_id: int, workers: List[Dict[str, Any]], area_sqm: float) -> Dict[str, Any]:
        """Katta maydonlar (>150 kv.m) uchun bir nechta xodimdan iborat brigada tuzish"""
        required_workers_count = max(2, min(5, int(area_sqm // 70)))
        logger.info(f"Katta obyekt #{order_id} ({area_sqm} kv.m) uchun {required_workers_count} ta xodim tanlanmoqda...")

        # Xodimlarni reytingi va tajribasi bo'yicha saralash
        workers_sorted = sorted(workers, key=lambda w: float(w.get("rating") or 5.0), reverse=True)
        assigned_team = workers_sorted[:required_workers_count]

        lead_worker = assigned_team[0]
        await db.update_order_status(order_id, "brigadaga_biriktirildi", worker_id=lead_worker["id"])

        team_names = ", ".join([w["name"] for w in assigned_team])
        logger.success(f"👥 Katta obyekt #{order_id} brigadaga biriktirildi: {team_names} (Brigadir: {lead_worker['name']})")

        return {
            "order_id": order_id,
            "lead_worker": lead_worker,
            "team": assigned_team,
            "team_size": len(assigned_team)
        }

    async def emergency_reassign(self, order_id: int, failed_worker_id: int) -> Optional[Dict[str, Any]]:
        """Fors-major holatlarida 30 soniyada buyurtmani eng yaqin boshqa zaxira xodimga o'tkazish"""
        logger.warning(f"⚠️ FORS-MAJOR: Buyurtma #{order_id} xodim #{failed_worker_id} dan olinmoqda va qayta biriktirilmoqda...")
        workers = await db.get_active_workers()
        available = [w for w in workers if w["id"] != failed_worker_id]

        if not available:
            logger.error(f"Zaxira xodimlar mavjud emas #{order_id} uchun!")
            return None

        order = await db.get_order(order_id)
        scored = []
        for w in available:
            score = await self.calculate_worker_score(w, order)
            scored.append((score, w))

        scored.sort(key=lambda x: x[0], reverse=True)
        best_score, best_backup = scored[0]

        await db.update_order_status(order_id, "zaxira_xodimga_otkazildi", worker_id=best_backup["id"])
        logger.success(f"✅ Buyurtma #{order_id} favqulodda zaxira xodimga o'tkazildi: {best_backup['name']}")

        return {
            "order_id": order_id,
            "backup_worker": best_backup,
            "match_score": best_score
        }


smart_dispatcher = SmartDispatcher()
