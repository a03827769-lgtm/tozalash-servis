"""
Tozalash Servis — Proactive Upselling & Cross-selling AI Engine
Mijoz buyurtma berayotgan xizmatga mos keluvchi qo'shimcha xizmatlarni
aqlli ravishda taklif qilib, o'rtacha chekni 30-40% ga oshiruvchi modul.
"""

from typing import Dict, List, Any, Optional


UPSELL_RULES = {
    "regular_cleaning": {
        "title_uz": "Oddiy / General Tozalash",
        "suggestions": [
            {
                "service": "sofa_cleaning",
                "name_uz": "Yumshoq mebel (divan/kreslo) ximchistkasi",
                "discount_percent": 20,
                "pitch_uz": "💡 Bugun general tozalash bilan birga divan yuvishga buyurtma bersangiz, mebel ximchistkasiga **20% maxsus chegirma** taqdim etamiz!"
            },
            {
                "service": "window_cleaning",
                "name_uz": "Deraza va vitrinalarni maxsus yuvish",
                "discount_percent": 15,
                "pitch_uz": "🪟 Tozalash bilan birga barcha derazalarni ikki taraflama yaltiratib berishimizni xohlaysizmi? (15% chegirma bilan)"
            }
        ]
    },
    "renovation_cleaning": {
        "title_uz": "Ta'mirdan keyingi tozalash",
        "suggestions": [
            {
                "service": "deep_ozonation",
                "name_uz": "Havoni chang va bo'yoq hididan tozalash (Ozonatsiya)",
                "discount_percent": 25,
                "pitch_uz": "✨ Ta'mirdan keyin xonadonda bo'yoq va qurilish hidi qolmasligi uchun **antibakterial ozonatsiya** xizmatimizni 25% chegirma bilan qo'shib beramiz!"
            }
        ]
    },
    "sofa_cleaning": {
        "title_uz": "Divan yuvish",
        "suggestions": [
            {
                "service": "carpet_cleaning",
                "name_uz": "Gilam va kovrolinlarni chuqur tozalash",
                "discount_percent": 15,
                "pitch_uz": "🛋 Divan bilan birga xonadagi gilamni ham maxsus Kärcher ekstraktorida yuvib berishimizni xohlaysizmi?"
            }
        ]
    }
}


class UpsellingEngine:
    @staticmethod
    def get_upsell_pitch(service_type: str, language: str = "uz") -> Optional[str]:
        """Buyurtma turiga qarab mijozga taklif qilinadigan qo'shimcha xizmat matnini olish"""
        rule = UPSELL_RULES.get(service_type)
        if not rule or not rule.get("suggestions"):
            return None

        # Birinchi eng mos taklifni qaytarish
        top_suggestion = rule["suggestions"][0]
        return top_suggestion.get(f"pitch_{language}") or top_suggestion.get("pitch_uz")


upselling_engine = UpsellingEngine()
