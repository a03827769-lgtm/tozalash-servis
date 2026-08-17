import aiohttp
from loguru import logger
from config import GOOGLE_SEARCH_API_KEY, GOOGLE_CX
from database import db
import json
from datetime import datetime


async def search_competitors():
    """Google Custom Search API orqali raqobatchilar narxlarini va xizmatlarini qidirish"""
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_CX:
        logger.warning(
            "⚠️ Google Search API kalitlari (GOOGLE_SEARCH_API_KEY yoki GOOGLE_CX) .env da sozlanmagan. Qidiruv ishlamaydi."
        )
        return

    logger.info("🔍 Raqobatchilarni qidirish boshlanmoqda...")
    queries = [
        "toshkent tozalash xizmati narxlari",
        "cleaning service tashkent price",
        "gilam yuvish narxlari toshkent",
    ]

    results = []

    async with aiohttp.ClientSession() as session:
        for query in queries:
            url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_SEARCH_API_KEY}&cx={GOOGLE_CX}&q={query}&num=3"
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get("items", [])
                        for item in items:
                            results.append(
                                {
                                    "title": item.get("title"),
                                    "link": item.get("link"),
                                    "snippet": item.get("snippet"),
                                    "query": query,
                                }
                            )
                    else:
                        logger.error(
                            f"Google Search xatosi: {response.status} - {await response.text()}"
                        )
            except Exception as e:
                logger.error(f"Qidiruv jarayonida xatolik: {e}")

    if results:
        logger.info(f"✅ {len(results)} ta natija topildi. Ma'lumotlarni saqlash...")
        try:
            # We can save this into a daily report or a new table.
            # For now, let's just log it and perhaps save into ai_learning for the AI to know about it.
            # But the requirement says "Competitor Search". So we can just save it to daily_reports competitor_insights
            # or simply log it. Let's create a report object and update it.
            report_data = {
                "competitor_insights": results,
                "messages_received": 0,
                "messages_answered": 0,
            }
            await db.save_daily_report(report_data)
            logger.info("✅ Raqobatchilar tahlili ma'lumotlari saqlandi.")
        except Exception as e:
            logger.error(f"Natijalarni saqlashda xatolik: {e}")
