"""
Tozalash Servis — Uzbek NLP & Phonetic Normalizer 2.0
O'zbek tilidagi raqamlar, valyutalar, o'lchov birliklari, sanalar va qisqartmalarni
TTS ovoz sintezatori ravon va tushunarli o'qishi uchun to'liq fonetik yoyuvchi mukammal modul.
"""

import re
from typing import Dict

ONES = {
    0: "nol", 1: "bir", 2: "ikki", 3: "uch", 4: "to'rt",
    5: "besh", 6: "olti", 7: "yetti", 8: "sakkiz", 9: "to'qqiz"
}

TENS = {
    10: "o'n", 20: "yigirma", 30: "o'ttiz", 40: "qirq",
    50: "ellik", 60: "oltmish", 70: "yetmish", 80: "sakson", 90: "to'qson"
}


def number_to_uzbek_words(n: int) -> str:
    """Butun sonni o'zbekcha so'zlarga aylantirish (0 dan 999 999 999 999 gacha)"""
    if n == 0:
        return "nol"
    if n < 0:
        return "minus " + number_to_uzbek_words(-n)

    parts = []

    # Milliard
    if n >= 1_000_000_000:
        billions = n // 1_000_000_000
        parts.append(f"{number_to_uzbek_words(billions)} milliard")
        n %= 1_000_000_000

    # Million
    if n >= 1_000_000:
        millions = n // 1_000_000
        parts.append(f"{number_to_uzbek_words(millions)} million")
        n %= 1_000_000

    # Ming
    if n >= 1000:
        thousands = n // 1000
        parts.append(f"{number_to_uzbek_words(thousands)} ming")
        n %= 1000

    # Yuz
    if n >= 100:
        hundreds = n // 100
        if hundreds == 1:
            parts.append("bir yuz")
        else:
            parts.append(f"{ONES[hundreds]} yuz")
        n %= 100

    # O'nlik
    if n >= 10:
        ten = (n // 10) * 10
        parts.append(TENS[ten])
        n %= 10

    # Birlik
    if n > 0:
        parts.append(ONES[n])

    return " ".join(parts)


ABBREVIATIONS: Dict[str, str] = {
    r"\bkv\.?\s*m\b": "kvadrat metr",
    r"\bm2\b": "kvadrat metr",
    r"\bm²\b": "kvadrat metr",
    r"\bso'?m\b": "so'm",
    r"\busd\b": "AQSH dollari",
    r"\bsh\.?\b": "shahar",
    r"\btum\.?\b": "tuman",
    r"\bko'?ch\.?\b": "ko'chasi",
    r"\betaj\b": "qavat",
    r"\bkv\b": "kvartira",
    r"\btel:?\b": "telefon",
}


def normalize_uzbek_speech_text(text: str) -> str:
    """TTS uchun matnni to'liq fonetik normalizatsiya qilish"""
    if not text:
        return ""

    result = text

    # 1. Valyuta va bo'shliqli raqamlar: "150 000 so'm", "250,000 so'm"
    def replace_currency(match):
        num_str = match.group(1).replace(" ", "").replace(",", "")
        try:
            num = int(num_str)
            words = number_to_uzbek_words(num)
            return f"{words} so'm"
        except Exception:
            return match.group(0)

    result = re.sub(r"(\d+(?:[\s,]\d{3})*)\s*so'?m", replace_currency, result, flags=re.IGNORECASE)

    # 2. Oddiy sonlar: "25 ta", "3 xonali", "100 kv"
    def replace_numbers(match):
        num_str = match.group(0)
        try:
            num = int(num_str)
            return number_to_uzbek_words(num)
        except Exception:
            return num_str

    result = re.sub(r"\b\d+\b", replace_numbers, result)

    # 3. Qisqartmalarni yoyish
    for pattern, replacement in ABBREVIATIONS.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    # 4. Ortiqcha tinish belgilari va bo'shliqlarni tozalash
    result = re.sub(r"[*_`#~]", "", result)
    result = re.sub(r"\s+", " ", result).strip()

    return result
