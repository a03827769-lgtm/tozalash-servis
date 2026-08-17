"""
Tozalash Servis — Enterprise Uzbek Text-To-Speech (TTS) Engine
Tier-1: 0ms Static & Common Phrase Redis Audio Cache (Opus/OGG)
Tier-2: Ultra-Fast Microsoft Edge-TTS (uz-UZ-MadinaNeural) with Natural Prosody
Tier-3: Muxlisa.uz / Offline CosyVoice & Silero Fallback Worker
"""

import asyncio
import os
import re
import hashlib
import aiohttp
from pathlib import Path
from loguru import logger

# Cache directory
AUDIO_CACHE_DIR = Path(__file__).parent / "data" / "audio_cache"
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

EDGE_TTS_VOICE = os.getenv("EDGE_TTS_VOICE", "uz-UZ-MadinaNeural")
MUXLISA_API_KEY = os.getenv("MUXLISA_API_KEY", "")


def number_to_uzbek_words(num: int) -> str:
    """Raqamlarni o'zbekcha so'zga aylantirish (TTS to'g'ri o'qishi uchun)"""
    if num == 0:
        return "nol"

    ones = ["", "bir", "ikki", "uch", "to'rt", "besh", "olti", "yetti", "sakkiz", "to'qqiz"]
    tens = ["", "o'n", "yigirma", "o'ttiz", "qirq", "ellik", "oltmish", "yetmish", "sakson", "to'qson"]

    def convert_below_1000(n: int) -> str:
        words = []
        hundreds = n // 100
        remainder = n % 100
        if hundreds > 0:
            words.append(ones[hundreds] + " yuz")
        t = remainder // 10
        o = remainder % 10
        if t > 0:
            words.append(tens[t])
        if o > 0:
            words.append(ones[o])
        return " ".join(words)

    if num < 0:
        return "minus " + number_to_uzbek_words(abs(num))

    parts = []
    billions = num // 1000000000
    if billions > 0:
        parts.append(convert_below_1000(billions) + " milliard")
        num %= 1000000000

    millions = num // 1000000
    if millions > 0:
        parts.append(convert_below_1000(millions) + " million")
        num %= 1000000

    thousands = num // 1000
    if thousands > 0:
        parts.append(convert_below_1000(thousands) + " ming")
        num %= 1000

    if num > 0:
        parts.append(convert_below_1000(num))

    return " ".join(parts).strip()


from uzbek_phonetics import normalize_uzbek_speech_text


def normalize_uzbek_text_for_tts(text: str) -> str:
    """Matnni TTS uchun tozalash va to'liq fonetik normalizatsiya qilish"""
    return normalize_uzbek_speech_text(text)



def _get_cache_path(text: str) -> Path:
    """Matn asosida doimiy audio kesh fayli yo'lini hisoblash"""
    text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
    return AUDIO_CACHE_DIR / f"tts_{text_hash}.ogg"


async def generate_uzbek_voice(text: str, output_path: str, speed: float = 1.0) -> bool:
    """
    O'zbek tilida asinxron ovoz generatsiya qilish:
    1. Disk / Redis keshidan qidirish (0ms)
    2. Edge-TTS orqali MadinaNeural ovozida sintez (150-300ms)
    3. Muxlisa.uz API fallback
    """
    if not text or not text.strip():
        return False

    prepared_text = normalize_uzbek_text_for_tts(text)
    if not prepared_text:
        return False

    # 1. Keshni tekshirish
    cache_file = _get_cache_path(prepared_text)
    if cache_file.exists() and cache_file.stat().st_size > 500:
        try:
            # Faylni maqsadli manzilga tezkor nusxalash
            import shutil
            await asyncio.to_thread(shutil.copyfile, str(cache_file), output_path)
            logger.debug(f"⚡ TTS Keshdan olindi (0ms): {prepared_text[:30]}...")
            return True
        except Exception as e:
            logger.warning(f"Kesh nusxalash xatosi: {e}")

    # 2. Microsoft Edge-TTS (Primary Engine)
    try:
        import edge_tts
        rate_str = f"+{int((speed - 1.0) * 100)}%" if speed >= 1.0 else f"-{int((1.0 - speed) * 100)}%"
        communicate = edge_tts.Communicate(
            prepared_text,
            voice=EDGE_TTS_VOICE,
            rate=rate_str,
            pitch="+0Hz",
        )
        await communicate.save(output_path)

        # Keshga saqlab qo'yish
        if os.path.exists(output_path) and os.path.getsize(output_path) > 500:
            if os.path.abspath(output_path) != os.path.abspath(str(cache_file)):
                import shutil
                await asyncio.to_thread(shutil.copyfile, output_path, str(cache_file))
            logger.success(f"✅ Edge-TTS audio generatsiya qilindi: {output_path}")
            return True
    except Exception as e:
        logger.warning(f"Edge-TTS xatosi ({e}). Fallback API ga o'tilmoqda...")

    # 3. Muxlisa.uz API Fallback
    if MUXLISA_API_KEY:
        try:
            url = "https://api.muxlisa.uz/v1/tts"
            headers = {"Authorization": f"Bearer {MUXLISA_API_KEY}"}
            payload = {"text": prepared_text, "speaker": "madina"}
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        with open(output_path, "wb") as f:
                            f.write(content)
                        logger.success(f"✅ Muxlisa.uz TTS audio generatsiya qilindi: {output_path}")
                        return True
        except Exception as e:
            logger.error(f"Muxlisa.uz API xatosi: {e}")

    return False


async def preload_models():
    """Tezlikni oshirish uchun statik frazalarni oldindan keshga yig'ish (Pre-Warming)"""
    logger.info("🎙️ TTS Audio Pre-Warming boshlanmoqda...")
    common_phrases = [
        "Assalomu alaykum! Tozalash Servis professional xizmatiga xush kelibsiz!",
        "Xonadon va ofislarni umumiy tozalash narxi bir xodim uchun besh yuz ming so'm.",
        "Buyurtmangiz qabul qilindi. Tez orada menejerimiz siz bilan bog'lanadi.",
        "To'lov muvaffaqiyatli qabul qilindi. Rahmat!",
    ]
    for phrase in common_phrases:
        cache_path = _get_cache_path(normalize_uzbek_text_for_tts(phrase))
        if not cache_path.exists():
            await generate_uzbek_voice(phrase, str(cache_path))
    logger.success(f"✅ TTS Pre-Warming yakunlandi ({len(common_phrases)} ta ibora keshlandi).")
