"""
Tozalash Servis — Smart Worker Dispatch Engine
Multi-Factor Scoring: Proximity (40%) + Rating (30%) + Experience (20%) + Skills/Equipment (10%)
Haversine Geolocation Calculation for Automated Cleaner Assignment
"""

import math
from typing import List, Dict, Any, Optional
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
    """Buyurtmaga eng mos tozalash xodimini avtomatik tanlash va biriktirish"""

    def __init__(self):
        logger.info("📍 Smart Dispatcher moduli ishga tushdi.")

    async def calculate_worker_score(
        self, worker: Dict[str, Any], order: Dict[str, Any]
    ) -> float:
        """
        Xodimning ushbu buyurtmaga moslik ballini hisoblash (0 - 100 ball)
        Score = (40 * DistanceScore) + (30 * RatingScore) + (20 * ExpScore) + (10 * SkillScore)
        """
        # 1. Masofa balli (0-40)
        order_lat = order.get("lat") or 41.311081  # Default Toshkent markazi
        order_lon = order.get("lon") or 69.240562
        worker_lat = worker.get("current_lat") or 41.311081
        worker_lon = worker.get("current_lon") or 69.240562

        dist_km = haversine_distance(order_lat, order_lon, worker_lat, worker_lon)
        # 5 km gacha = 40 ball, 15 km = 20 ball, 25 km dan ortiq = 5 ball
        if dist_km <= 3.0:
            dist_score = 40.0
        elif dist_km <= 8.0:
            dist_score = 30.0
        elif dist_km <= 15.0:
            dist_score = 20.0
        else:
            dist_score = max(5.0, 40.0 - (dist_km * 1.5))

        # 2. Reyting balli (0-30)
        rating = float(worker.get("rating") or 5.0)
        rating_score = (rating / 5.0) * 30.0

        # 3. Tajriba va bajarilgan buyurtmalar balli (0-20)
        completed = int(worker.get("completed_orders") or 0)
        exp_score = min(20.0, (completed / 50.0) * 20.0)

        # 4. Ko'nikma va uskunalar balli (0-10)
        service_type = order.get("service_type", "").lower()
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

        scored_workers = []
        for w in workers:
            score = await self.calculate_worker_score(w, order)
            scored_workers.append((score, w))

        # Eng yuqori ball bo'yicha saralash
        scored_workers.sort(key=lambda x: x[0], reverse=True)
        best_score, best_worker = scored_workers[0]

        # DB da buyurtmaga biriktirish
        await db.update_order_status(order_id, "ishchiga_biriktirildi", worker_id=best_worker["id"])
        logger.success(
            f"🎯 Buyurtma #{order_id} xodimga biriktirildi: {best_worker['name']} (Ball: {best_score})"
        )

        return {
            "order_id": order_id,
            "worker": best_worker,
            "match_score": best_score,
        }


# Global Instance
smart_dispatcher = SmartDispatcher()
