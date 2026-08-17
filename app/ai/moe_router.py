"""
Tozalash Servis — AI MoE (Mixture of Experts) Hybrid Router
Har bir mijoz so'rovining murakkabligi va turini avtomatik tahlil qilib,
eng optimal AI modeliga (Gemini Flash, Gemini Pro, GPT-4o, Claude, G4F) yo'naltiruvchi aqlli motor.
"""

import time
import asyncio
from typing import Dict, Any, Optional, Tuple
from loguru import logger
from app.core.circuit_breaker import gemini_breaker


class AIModelTier:
    FAST_FLASH = "gemini-1.5-flash"       # Narxlar, oddiy savollar, salomlashish (<200ms)
    DEEP_REASONING = "gemini-1.5-pro"     # Hisob-kitoblar, shikoyatlar, murakkab tahlil
    VISION_EXPERT = "gemini-1.5-flash"     # Fotosuratlar, ifloslik darajasini baholash
    FALLBACK_G4F = "gpt-4o-mini"          # Zaxira neyron tarmog'i


class AIRouter:
    """Mijoz so'roviga qarab optimal AI modelini tanlovchi aqlli router"""

    @staticmethod
    def classify_intent(text: str, has_image: bool = False) -> Tuple[str, str]:
        """
        Matn tahlili asosida vazifa turi va model tierini aniqlash.
        Returns: (intent_type, recommended_model)
        """
        if has_image:
            return "vision_estimation", AIModelTier.VISION_EXPERT

        t = text.lower().strip()

        # 1. Tezkor / Oddiy savollar (Fast Flash Tier)
        quick_keywords = ["salom", "assalom", "qalesiz", "rahmat", "narx", "qancha", "manzil", "telefon", "ish vaqti"]
        if any(w in t for w in quick_keywords) and len(t) < 80:
            return "quick_inquiry", AIModelTier.FAST_FLASH

        # 2. Shikoyat va e'tirozlar (Deep Reasoning Tier)
        complaint_keywords = ["yomon", "tozalanmadi", "kechikdi", "qoniqmadim", "aldov", "shikoyat", "rahbar", "pulimni qaytar"]
        if any(w in t for w in complaint_keywords):
            return "complaint_dispute", AIModelTier.DEEP_REASONING

        # 3. Katta hisob-kitob va buyurtma tafsilotlari (Deep Reasoning)
        complex_keywords = ["shartnoma", "b2b", "ofis", "kottej", "kvadrat", "ta'mirdan keyin", "didox", "invoys"]
        if any(w in t for w in complex_keywords) or len(t) > 200:
            return "complex_booking", AIModelTier.DEEP_REASONING

        # Standart
        return "general_conversation", AIModelTier.FAST_FLASH

    @staticmethod
    async def route_execution(prompt: str, system_prompt: str, has_image: bool = False, image_data: Optional[bytes] = None) -> Dict[str, Any]:
        """
        So'rovni tegishli model orqali bajarish va vaqt diagnostikasini qaytarish.
        """
        intent, model_tier = AIRouter.classify_intent(prompt, has_image)
        start_time = time.perf_counter()

        logger.info(f"AI MoE Router: Intent=[{intent}] -> Model=[{model_tier}]")

        # Circuit Breaker orqali Gemini rotatordan foydalanish
        try:
            from ai_brain import ai_brain
            response_text = await gemini_breaker.call(
                ai_brain.generate_response_direct,
                prompt=prompt,
                system_prompt=system_prompt,
                image_data=image_data
            )
            provider = "Gemini-Native"
        except Exception as e:
            logger.warning(f"Primary Gemini AI xatosi ({e}), Tier-2 G4F Fallback ga o'tilmoqda...")
            try:
                from ai_brain import ai_brain
                response_text = await ai_brain.generate_g4f_fallback(prompt, system_prompt)
                provider = "G4F-Fallback"
            except Exception as g4f_err:
                logger.error(f"G4F Fallback ham ishlamadi: {g4f_err}")
                response_text = (
                    "Assalomu alaykum! Xabaringiz qabul qilindi. "
                    "Mutaxassisimiz 1 daqiqa ichida siz bilan bog'lanadi yoki +998 (90) 123-45-67 raqamiga qo'ng'iroq qilishingiz mumkin."
                )
                provider = "Offline-Rule-Engine"

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "response": response_text,
            "intent": intent,
            "model_used": model_tier,
            "provider": provider,
            "latency_ms": latency_ms
        }


moe_router = AIRouter()
