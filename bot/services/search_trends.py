from duckduckgo_search import DDGS
from loguru import logger
import random
import httpx
import re


async def analyze_channel_history(channel_username: str) -> str:
    """
    Kanalning ochiq web sahifasidan (t.me/s/...) oxirgi postlarni o'qib,
    kanalning umumiy uslubi va mavzularini tahlil qilish uchun matn qaytaradi.
    """
    try:
        username = channel_username.replace("@", "")
        url = f"https://t.me/s/{username}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return "Kanal tarixini o'qish imkonsiz (Status xato)."

            # HTML dan post matnlarini ajratib olish (juda oddiy regex orqali)
            # tgme_widget_message_text div ichidagi matnlar
            html = response.text
            matches = re.findall(
                r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>',
                html,
                re.DOTALL,
            )

            if not matches:
                return "Kanalda hozircha postlar topilmadi yoki o'qishning iloji yo'q."

            # Oxirgi 5 ta postni olish va HTML teglarni tozalash
            recent_posts = matches[-5:]
            clean_posts = []
            for post in recent_posts:
                clean_text = re.sub(r"<br/?>", "\n", post)
                clean_text = re.sub(r"<[^>]+>", "", clean_text)
                clean_posts.append(clean_text.strip())

            result = "Kanalning oxirgi postlari (Tahlil va o'xshashlikni saqlash, lekin takrorlamaslik uchun):\n\n"
            for i, p in enumerate(clean_posts, 1):
                result += f"--- {i}-POST ---\n{p[:300]}...\n"

            return result
    except Exception as e:
        logger.error(f"Kanalni tahlil qilishda xato: {e}")
        return "Kanal tarixini o'qishda xatolik yuz berdi."


def fetch_cleaning_trends() -> str:
    """
    Internetdan tozalash xizmatlari, gigiyena, uy parvarishi yoki samaradorlik
    bo'yicha eng so'nggi va qiziqarli xabarlarni topib qaytaradi.
    """
    queries = [
        "home cleaning hacks and modern trends 2024",
        "innovations in professional cleaning services",
        "health benefits of a clean house psychology",
        "modern eco-friendly cleaning methods",
        "how to keep office clean and productive tips",
        "uy tozalash foydali maslahatlar",
        "professional tozalash xizmatlari trendlar",
        "marketing strategies for cleaning business",
        "engaging content ideas for cleaning services",
    ]
    query = random.choice(queries)

    logger.info(f"🔍 Internetdan trendlar qidirilmoqda: {query}")
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return (
                "Professional tozalash xizmatlarining foydasi haqida umumiy ma'lumot."
            )

        trend_text = "Mana ba'zi yangi ma'lumotlar va trendlar:\n"
        for r in results:
            trend_text += f"- {r.get('title')}: {r.get('body')}\n"

        return trend_text
    except Exception as e:
        logger.error(f"Trend qidirishda xato: {e}")
        return "Professional tozalash xizmatlarining afzalliklari."
