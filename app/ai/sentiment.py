"""
Tozalash Servis — Real-Time Sentiment & Dispute Escalation Engine
Mijozning xabarlaridagi ohang, kayfiyat va qoniqish darajasini (Sentiment) aniqlab,
shikoyat yoki g'azab alomatlari bo'lsa, zudlik bilan boshqaruvchiga ogohlantirish yuboruvchi neyron tizim.
"""

from typing import Dict, Any
from loguru import logger


# Salbiy va nizoli kalit so'zlar
NEGATIVE_KEYWORDS = [
    "yomon", "tozalamadi", "iflos", "chala", "kechikdi", "aldading", "aldash", "pulim", "qaytaring",
    "rasvo", "buzuq", "shikoyat", "sud", "haqorat", "yoqmadi", "qoniqmadim", "rahbar", "direktor",
    "telefonni ko'tarmadi", "janjal", "ustanovka", "zarar"
]

POSITIVE_KEYWORDS = [
    "raxmat", "rahmat", "baraka", "zo'r", "ajoyib", "yaltirab", "toza", "katta rahmat", "minnatdor",
    "gap yo'q", "malades", "tavsiya", "yoqdi", "professional", "chiroyli", "super"
]


class SentimentAnalyzer:
    @staticmethod
    def analyze_message(text: str) -> Dict[str, Any]:
        """
        Matndagi kayfiyatni baholash.
        Returns: {
            "score": float (-1.0 to 1.0),
            "label": "POSITIVE" | "NEUTRAL" | "NEGATIVE" | "CRITICAL_DISPUTE",
            "needs_escalation": bool
        }
        """
        t = text.lower()

        neg_matches = [w for w in NEGATIVE_KEYWORDS if w in t]
        pos_matches = [w for w in POSITIVE_KEYWORDS if w in t]

        neg_count = len(neg_matches)
        pos_count = len(pos_matches)

        if neg_count >= 2 or any(critical in t for critical in ["aldash", "sud", "pulimni qaytar", "shikoyat"]):
            label = "CRITICAL_DISPUTE"
            score = -0.9
            needs_escalation = True
        elif neg_count == 1:
            label = "NEGATIVE"
            score = -0.5
            needs_escalation = True
        elif pos_count > 0:
            label = "POSITIVE"
            score = min(1.0, 0.4 + (pos_count * 0.3))
            needs_escalation = False
        else:
            label = "NEUTRAL"
            score = 0.0
            needs_escalation = False

        if needs_escalation:
            logger.warning(f"🚨 SENTIMENT ESCALATION TRIGGERED! Label=[{label}], Keywords={neg_matches}, Text='{text[:60]}...'")

        return {
            "score": score,
            "label": label,
            "needs_escalation": needs_escalation,
            "detected_keywords": neg_matches if needs_escalation else pos_matches
        }


sentiment_analyzer = SentimentAnalyzer()
