"""
Tozalash Servis — Raqiblar Tahlili Tizimi
Toshkentdagi raqib tozalash kompaniyalarini monitoring qilish
"""

import asyncio
import json
import httpx
from datetime import datetime
from typing import List, Dict
from loguru import logger

from config import ADMIN_TELEGRAM_ID, TELEGRAM_BOT_TOKEN, BUSINESS_NAME, BUSINESS_PHONE
from ai_brain import ai_brain
from database import db

# Toshkentdagi asosiy raqiblar (manual qo'shilgan)
KNOWN_COMPETITORS = [
    {
        "name": "Clean House Tashkent",
        "platform": "Instagram",
        "url": "https://www.instagram.com/cleanhouse_tashkent/",
        "search_query": "tozalash xizmati toshkent instagram",
    },
    {
        "name": "Pro Clean Tashkent",
        "platform": "Instagram",
        "url": "https://www.instagram.com/proclean_tashkent/",
        "search_query": "pro clean toshkent",
    },
    {
        "name": "Cleaning Service Toshkent",
        "platform": "Telegram",
        "url": "https://t.me/cleaning_tashkent",
        "search_query": "cleaning service toshkent telegram",
    },
]


class CompetitorAnalyzer:
    """Raqiblarni tahlil qilish tizimi"""

    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.admin_id = ADMIN_TELEGRAM_ID

    async def analyze_all_competitors(self) -> List[Dict]:
        """Barcha raqiblarni tahlil qilish"""
        results = []

        for competitor in KNOWN_COMPETITORS:
            try:
                analysis = await self._analyze_single_competitor(competitor)
                results.append(analysis)

                # Ma'lumotlar bazasiga saqlash (kelgusida implement qilinadi)
                async with db.get_conn() as conn:
                    pass  # TODO: raqib tahlili natijalarini DB ga saqlash

            except Exception as e:
                logger.error(f"Raqib tahlili xatosi ({competitor['name']}): {e}")

        return results

    async def _analyze_single_competitor(self, competitor: Dict) -> Dict:
        """Bitta raqibni tahlil qilish"""

        # AI orqali raqib tahlili
        ai_analysis = await ai_brain.analyze_competitor(
            {
                "name": competitor["name"],
                "platform": competitor["platform"],
                "url": competitor["url"],
                "note": "Toshkentdagi tozalash kompaniyasi",
            }
        )

        result = {
            "name": competitor["name"],
            "platform": competitor["platform"],
            "url": competitor["url"],
            "strengths": ai_analysis.get("strengths", []),
            "weaknesses": ai_analysis.get("weaknesses", []),
            "our_advantages": ai_analysis.get("our_advantages", []),
            "recommendations": ai_analysis.get("recommendations", []),
            "price_strategy": ai_analysis.get("price_strategy", ""),
            "analyzed_at": datetime.now().isoformat(),
        }

        logger.info(f"✅ Raqib tahlili: {competitor['name']}")
        return result

    async def generate_competitive_report(self) -> str:
        """Raqobat tahlili hisoboti"""

        competitors_data = await self.analyze_all_competitors()

        prompt = f"""Quyidagi raqiblar tahlili asosida Tozalash Servis uchun strategik hisobot yoz:

Raqiblar:
{json.dumps(competitors_data, ensure_ascii=False, indent=2)}

Bizning kompaniya: {BUSINESS_NAME}, Toshkent
Bizning narxlarimiz bozorga mos.

Hisobotda quyidagilar bo'lsin:
1. 🎯 Raqobat holati tahlili
2. 💪 Bizning asosiy afzalliklarimiz  
3. ⚠️ Diqqat talab qiladigan sohalar
4. 🚀 Hafta uchun marketing strategiyasi
5. 💡 Bizni raqiblardan ustun qiluvchi 3 ta konkret tavsiya
6. 📈 Narx pozitsioningi tavsiyasi

Professional, konkret va amaliy bo'lsin. O'zbek tilida."""

        try:
            import google.generativeai as genai
            from config import GEMINI_API_KEY

            if not GEMINI_API_KEY:
                return "AI konfiguratsiyasi yo'q (GEMINI_API_KEY topilmadi)."
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = await model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Raqobat hisobot xatosi: {e}")
            return "Raqobat tahlili hisobotini generatsiya qilib bo'lmadi."

    async def search_new_competitors(self) -> List[Dict]:
        """Yangi raqiblarni izlash (Google search orqali)"""
        search_queries = [
            "tozalash xizmati toshkent",
            "cleaning service tashkent",
            "уборка квартир ташкент",
            "professional tozalash toshkent",
        ]

        new_competitors = []

        # Note: Real implementation'da Google Custom Search API ishlatiladi
        # Bu yerda mock data
        for query in search_queries:
            logger.info(f"Yangi raqiblar qidirilmoqda: '{query}'")

        return new_competitors

    async def send_weekly_report(self):
        """Haftalik raqobat hisobotini adminga yuborish"""
        try:
            report = await self.generate_competitive_report()

            # Telegram orqali yuborish
            async with httpx.AsyncClient() as client:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                payload = {
                    "chat_id": self.admin_id,
                    "text": f"📊 *HAFTALIK RAQOBAT TAHLILI*\n\n{report[:4000]}",
                    "parse_mode": "Markdown",
                }

                await client.post(url, json=payload)
                logger.info("✅ Haftalik raqobat hisoboti yuborildi")

        except Exception as e:
            logger.error(f"Haftalik hisobot xatosi: {e}")

    async def run_scheduler(self):
        """Raqib tahlil schedulerini ishga tushirish"""
        logger.info("🔍 Raqib Tahlil Scheduler ishga tushdi")

        check_count = 0

        while True:
            try:
                check_count += 1
                now = datetime.now()

                # Har kuni ertalab 08:00 da tahlil
                if now.hour == 8 and now.minute == 0:
                    logger.info("🔍 Kunlik raqib tahlili boshlanmoqda...")
                    await self.analyze_all_competitors()
                    await asyncio.sleep(61)

                # Har dushanba kuni haftalik hisobot
                if now.weekday() == 0 and now.hour == 9 and now.minute == 0:
                    logger.info("📊 Haftalik raqobat hisoboti tayyorlanmoqda...")
                    await self.send_weekly_report()
                    await asyncio.sleep(61)

            except Exception as e:
                logger.error(f"Raqib scheduler xatosi: {e}")

            await asyncio.sleep(30)


# Global instance
competitor_analyzer = CompetitorAnalyzer()
