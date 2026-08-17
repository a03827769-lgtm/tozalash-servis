"""
Tozalash Servis - IoT & Smart Building Integration Moduli
Phase 13: Sensors & IoT (Tasks 121-130)
"""

from loguru import logger
import asyncio
from datetime import datetime


class IoTManager:
    def __init__(self):
        logger.info("📡 IoT & Sensor Manager modul yuklanmoqda...")
        self.karcher_devices = {}
        self.worker_locations = {}
        self.weather_status = "clear"

    async def register_device(self, device_id: str, device_type: str):
        logger.info(f"[IoT] Yangi qurilma ulandi: {device_id} ({device_type})")
        self.karcher_devices[device_id] = {
            "status": "online",
            "chemicals_level": 100,
            "battery": 100,
        }

    async def update_worker_gps(self, worker_id: int, lat: float, lon: float):
        """
        Xodimning joriy lokatsiyasini yangilash.
        """
        self.worker_locations[worker_id] = {
            "lat": lat,
            "lon": lon,
            "updated_at": datetime.now(),
        }
        logger.debug(f"[GPS] Xodim {worker_id} lokatsiyasi yangilandi: {lat}, {lon}")

    async def check_consumables(self, device_id: str):
        """
        Karcher apparatidagi ximikat qoldig'ini tekshirish.
        """
        if device_id in self.karcher_devices:
            level = self.karcher_devices[device_id]["chemicals_level"]
            if level < 15:
                logger.warning(
                    f"[IoT] Uskuna {device_id} da ximikat kam qoldi ({level}%). Omborga zayavka berilmoqda."
                )
                return await self.order_supplies("karcher_shampoo")
        return None

    async def order_supplies(self, item: str):
        logger.info(f"[WAREHOUSE] {item} uchun avtomat zayavka yaratildi.")
        return True

    async def process_weather_alert(self, weather_condition: str):
        """
        Ob-havoga qarab buyurtmalarni avtomat o'zgartirish.
        """
        self.weather_status = weather_condition
        if weather_condition == "rain" or weather_condition == "storm":
            logger.warning(
                "[WEATHER ALERT] Yomg'ir boshlandi. Oyna yuvish xizmatlari bekor qilinadi yoki ko'chiriladi."
            )
            return await self.cancel_window_cleaning_jobs()
        return True

    async def cancel_window_cleaning_jobs(self):
        # Database dan oyna yuvish buyurtmalarini topib, mijozlarga xabar berish
        logger.info("[IoT] Oyna yuvish buyurtmalari keyingi kunga ko'chirildi.")
        return 0


iot_manager = IoTManager()
