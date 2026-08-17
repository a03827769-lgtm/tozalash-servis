"""
Tozalash Servis — 24/7 Keepalive & Self-Healing Worker
Bepul bulutli serverlar (Render/Koyeb) inaktivlik tufayli uyqu holatiga ketmasligi uchun
har 8-10 daqiqada /health endpointini avtomatik chaqirib turuvchi xizmat.
"""

import asyncio
import os
import httpx
from loguru import logger


async def start_keepalive_worker():
    """Serverni 24/7 doimiy uyg'oq (active) holatda ushlab turish"""
    app_url = os.getenv("APP_PUBLIC_URL", os.getenv("RENDER_EXTERNAL_URL", ""))
    
    if not app_url:
        logger.info("ℹ️ APP_PUBLIC_URL o'rnatilmagan (lokal rejim). Keepalive pinger kutilmoqda.")
        return

    health_url = f"{app_url.rstrip('/')}/health"
    logger.success(f"🚀 24/7 Keepalive Pinger faollashdi: {health_url} (interval: 8 daqiqa)")

    while True:
        try:
            await asyncio.sleep(480)  # 8 daqiqa (480 sekund)
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(health_url)
                if resp.status_code == 200:
                    logger.debug("💓 Keepalive Ping muvaffaqiyatli: 200 OK")
                else:
                    logger.warning(f"⚠️ Keepalive Ping noaniq holat: {resp.status_code}")
        except asyncio.CancelledError:
            logger.info("Keepalive pinger to'xtatildi.")
            break
        except Exception as e:
            logger.warning(f"Keepalive ping xatosi: {e}")


if __name__ == "__main__":
    asyncio.run(start_keepalive_worker())
