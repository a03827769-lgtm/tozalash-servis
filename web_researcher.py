"""
Autonomous Competitor Web Researcher Agent
Scrapes competitor Telegram channels/sites, parses prices using Gemini, and updates the database.
"""

import httpx
import asyncio
import json
import re
from loguru import logger
from bs4 import BeautifulSoup
from database import db
from gemini_rotator import rotator

COMPETITOR_CHANNELS = [
    {"name": "Ideal Tozalash", "url": "https://t.me/s/ideal_tozalash"},
    {"name": "Pokiza Xizmat", "url": "https://t.me/s/pokiza_xizmat_uz"}
]

PROMPT_TEMPLATE = """
Sen O'zbekiston bozoridagi tozalash xizmatlari raqobatchilarini analiz qiluvchi AI Agentsan.
Quyidagi matn raqobatchi telegram kanalidan olingan.
Iltimos, ushbu matndan gilam yuvish (carpet_washing), uy tozalash (house_cleaning) va mebel tozalash (furniture_cleaning) xizmatlari narxlarini (faqat so'mda, raqamda) aniqlab, qat'iy JSON formatida qaytar.
Agar biror xizmat narxi yo'q bo'lsa, uni null deb yoz. 
JSON strukturasi:
{
    "carpet_washing": 15000,
    "house_cleaning": 20000,
    "furniture_cleaning": null
}
Matn:
{text}
Faqat JSON qaytar, boshqa gap qo'shma.
"""

async def scrape_channel(url: str) -> str:
    """Telegram public web preview dan xabarlarni qirqib olish"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                messages = soup.find_all('div', class_='tgme_widget_message_text')
                recent_texts = [m.get_text(separator=" ") for m in messages[-5:]]
                return "\n---\n".join(recent_texts)
    except Exception as e:
        logger.error(f"WebResearcher: Error scraping {url}: {e}")
    return ""

def parse_json_from_ai(response_text: str) -> dict:
    """AI javobidan JSON ni ajratib olish"""
    try:
        # JSON code blocklarni tozalash
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        start = response_text.find("{")
        end = response_text.rfind("}")
        if start != -1 and end != -1:
            json_str = response_text[start:end+1]
            return json.loads(json_str)
    except Exception as e:
        logger.error(f"WebResearcher: JSON parse xatosi: {e}")
    return {}

async def run_researcher():
    """Barcha raqobatchilarni tekshirish va bazani yangilash"""
    logger.info("WebResearcher: Raqobatchilar narxlarini analiz qilish boshlandi...")
    for comp in COMPETITOR_CHANNELS:
        logger.info(f"WebResearcher: Tekshirilmoqda -> {comp['name']}")
        raw_text = await scrape_channel(comp['url'])
        if not raw_text:
            logger.warning(f"WebResearcher: {comp['name']} dan ma'lumot topilmadi.")
            continue
            
        prompt = PROMPT_TEMPLATE.format(text=raw_text)
        
        try:
            ai_response = await rotator.ask(prompt)
            data = parse_json_from_ai(ai_response)
            
            if not data:
                logger.warning(f"WebResearcher: {comp['name']} uchun AI narxlarni aniqlay olmadi.")
                continue
                
            # Bazaga yozish
            for service_code, price in data.items():
                if price and isinstance(price, (int, float)):
                    # db.execute xatoni ushlash
                    async with db.get_pool().cursor() as cursor:
                        await cursor.execute(
                            "INSERT INTO competitor_prices (competitor_name, service_name, price, source_url) VALUES (?, ?, ?, ?)",
                            (comp['name'], service_code, float(price), comp['url'])
                        )
                    await db.get_pool().commit()
                    logger.info(f"WebResearcher: Yangilandi -> {comp['name']} - {service_code}: {price} UZS")
                    
        except Exception as e:
            logger.error(f"WebResearcher: AI ishlov berishda xatolik: {e}")

    logger.info("WebResearcher: Analiz yakunlandi.")

if __name__ == "__main__":
    asyncio.run(run_researcher())
