import asyncio
import json
from datetime import datetime, timedelta
import google.generativeai as genai
from config import GEMINI_API_KEY
from loguru import logger
from database import db

logger.add("logs/optimizer.log", rotation="10 MB", level="INFO")


async def get_recent_conversations(limit=10):
    """Bazada saqlangan oxirgi 24 soat ichidagi eng qiyin yoki oxiriga yetmagan suhbatlarni tortib olish"""
    try:
        async with db.get_conn() as conn:
            # O'tgan 24 soat ichidagi suhbatlarni olish
            yesterday = (datetime.now() - timedelta(days=1)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # Barcha oxirgi xabarlar
            async with conn.execute(
                """
                SELECT telegram_id, role, message, created_at 
                FROM conversations 
                WHERE created_at >= ?
                ORDER BY telegram_id, id ASC
            """,
                (yesterday,),
            ) as cursor:
                rows = await cursor.fetchall()

        # Suhbatlarni guruhlash
        conversations = {}
        for r in rows:
            tid = r["telegram_id"]
            if tid not in conversations:
                conversations[tid] = []
            conversations[tid].append(
                f"{'User' if r['role'] == 'user' else 'AI'}: {r['message']}"
            )

        # Qisqa suhbatlarni olib tashlash (faqat 4 tadan ko'p xabar almashilganlarini qoldiramiz)
        filtered = {k: v for k, v in conversations.items() if len(v) >= 4}

        # Eng uzun limit ta suhbatni qaytaramiz
        return list(filtered.values())[:limit]
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return []


async def optimize_guidelines():
    """AI ning kechagi xatolarini tahlil qilib, qoidalarni yangilaydi (10% Daily Improvement)"""
    logger.info("Daily Optimizer: Kechagi suhbatlarni tahlil qilish boshlandi...")

    if not GEMINI_API_KEY:
        logger.error("GEMINI API KEY topilmadi!")
        return

    conversations = await get_recent_conversations()
    if not conversations:
        logger.info("Yetarli suhbat topilmadi, o'zgarishsiz qoldirildi.")
        return

    genai.configure(api_key=GEMINI_API_KEY)

    # Faqat model initsializatsiyasi
    try:
        model = genai.GenerativeModel("gemini-3.6-flash")
    except Exception:
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
        except Exception as e:
            logger.error(f"Model ishga tushmadi: {e}")
            return

    # Eski qoidalarni o'qib olish
    try:
        with open("dynamic_guidelines.txt", "r", encoding="utf-8") as f:
            old_guidelines = f.read()
    except:
        old_guidelines = ""

    # Prompt: Reflexion & Evaluator
    logs_text = "\n\n---\n\n".join(["\n".join(conv) for conv in conversations])

    evaluator_prompt = f"""Sen AI psixologi va Prompt Optimizersan. Sening vazifang Tozalash Servis boti va mijozlar o'rtasidagi kechagi suhbatlarni tahlil qilish va botni insoniylashtirish, robotona ohangini yo'qotish va sotuvni oshirish.

OLDINGI QOIDALAR (Bular allaqachon mavjud):
{old_guidelines}

KECHAGI SUHBATLAR (LOGLAR):
{logs_text}

QILISHING KERAK:
1. Suhbatlarni o'qib chiqib, AI qayerda robotdek gapirganini, qayerda ortiqcha ma'lumot berganini yoki qayerda mijozni sovuqroq kutib olganini aniqla.
2. Shunga asoslanib, AI ertaga 10% yaxshiroq ishlashi uchun MAVJUD QOIDALARNI YANGILA va YAXSHILA. Xatolarni to'g'rilovchi yangi bandlar qo'sh.
3. YANGI QOIDALARNI (Dynamic Guidelines) qisqa, aniq bullet point (-) lar tarzida O'zbek tilida yoz. (Maksimal 7-8 ta band qoldir, eng muhimlarini saqla).

DIQQAT: Faqat yangilangan qoidalar ro'yxatini qaytar. Hech qanday kirish so'zlari kerak emas!"""

    try:
        response = await model.generate_content_async(evaluator_prompt)
        new_guidelines = response.text.strip()

        # Check if it actually returned some bullet points
        if "-" in new_guidelines and len(new_guidelines) > 50:
            with open("dynamic_guidelines.txt", "w", encoding="utf-8") as f:
                f.write(new_guidelines)
            logger.info("✅ Qoidalar muvaffaqiyatli yangilandi va saqlandi!")
            logger.info(f"Yangi qoidalar:\n{new_guidelines}")
        else:
            logger.error("Model xato formatda javob qaytardi.")

    except Exception as e:
        logger.error(f"Optimizer xatosi: {e}")


if __name__ == "__main__":
    asyncio.run(optimize_guidelines())
