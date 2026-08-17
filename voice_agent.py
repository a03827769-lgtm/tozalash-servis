"""
Tozalash Servis - Ovozli AI (Voice Agent) Moduli
Phase 11-12: Inbound & Outbound Telephony
"""

import asyncio
from loguru import logger
import json


class VoiceAgent:
    def __init__(self):
        logger.info("🎙️ Voice Agent (Ovozli AI) modul yuklanmoqda...")
        self.active_calls = {}

    async def handle_inbound_call(
        self, call_sid: str, from_number: str, text_input: str
    ):
        """
        Twilio / Asterisk orqali qabul qilingan ovozni STT (Speech-to-text) dan o'tkazib
        ushbu funksiyaga yuboriladi.
        """
        logger.info(f"[VOICE INBOUND] Qo'ng'iroq: {from_number} - Matn: {text_input}")

        # Anti-"Bilmayman" Protocol Check
        if "?" in text_input and any(
            word in text_input.lower() for word in ["qanday", "qanaqa", "nima"]
        ):
            # Complex question -> Route to Admin immediately to avoid AI hallucination
            return await self.route_to_human_admin(
                call_sid, from_number, "Mijoz qiyin savol berdi. Adminga ulanmoqda."
            )

        # Intent routing (Mock logic for voice)
        if "shikoyat" in text_input.lower() or "yomon" in text_input.lower():
            return await self.generate_tts_response(
                call_sid,
                "Kechirasiz, xizmatimizdan norozi bo'lganingizdan afsusdamiz. Hozir sizni Sifat Nazorati bo'limiga ulayman.",
            )
        elif "buyurtma" in text_input.lower() or "kerak" in text_input.lower():
            return await self.generate_tts_response(
                call_sid,
                "Buyurtmangiz qabul qilindi. Ovozli tasdiqlash uchun tizimimiz sizga SMS orqali to'lov havolasini yuboradi. Rahmat!",
            )
        else:
            return await self.generate_tts_response(
                call_sid,
                "Tozalash Servis kompaniyasiga xush kelibsiz. Bizda Karcher uskunalari bilan professional tozalash mavjud. Xizmat turini tanlang.",
            )

    async def make_outbound_call(
        self, to_number: str, purpose: str, context: dict = None
    ):
        """
        Mijozga avtomat qo'ng'iroq qilish (Outbound).
        """
        call_sid = f"OUT_{to_number}_{purpose}"
        logger.info(
            f"[VOICE OUTBOUND] Qo'ng'iroq qilinmoqda: {to_number}, Maqsad: {purpose}"
        )

        if purpose == "abandoned_cart":
            message = "Assalomu alaykum! Siz Telegram botimizda tozalash xizmati narxlarini ko'rdingiz, lekin buyurtma bermadingiz. Agar hozir buyurtma qilsangiz, sizga maxsus 10 foiz chegirma beramiz."
            await self.generate_tts_response(call_sid, message)
        elif purpose == "satisfaction_survey":
            message = "Assalomu alaykum! Kecha uyingizni tozalab ketishgandi. Sifatidan qoniqdingizmi? Bahongizni ayting."
            await self.generate_tts_response(call_sid, message)
        elif purpose == "reminder":
            date = context.get("date", "ertaga") if context else "ertaga"
            message = f"Assalomu alaykum. Eslatib o'tamiz, {date} kunga tozalash xizmati band qilingan. Xodimlarimiz o'z vaqtida borishadi."
            await self.generate_tts_response(call_sid, message)

    async def generate_tts_response(self, call_sid: str, message: str):
        """
        Generates Text-to-Speech audio and streams it to the call.
        """
        logger.info(f"[TTS] Call {call_sid} ga gapirilmoqda: '{message}'")
        return {"action": "play", "text": message}

    async def route_to_human_admin(self, call_sid: str, from_number: str, reason: str):
        """
        Qat'iy qoida: Bilmayman demaslik uchun adminga uzatish.
        """
        logger.warning(
            f"[VOICE TRANSFER] Call {call_sid} adminga uzatildi. Sabab: {reason}"
        )
        return {"action": "dial", "number": "+998887887011"}


# Global Instance
voice_agent = VoiceAgent()
