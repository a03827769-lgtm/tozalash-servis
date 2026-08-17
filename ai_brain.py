"""
Tozalash Servis — AI Miya (Gemini Cookie Rotation + G4F Fallback)
Professional AI: Tier-1 = Gemini Cookie, Tier-2 = GPT-4o G4F, Tier-3 = Fallback
"""

import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from pydantic import BaseModel, Field
from loguru import logger
import os
import re
import base64
import emoji
from pydub import AudioSegment
import speech_recognition as sr
import edge_tts
import google.generativeai as genai
import httpx

# Premium O'zbek TTS tizimi (3-tier)
from uzbek_tts import generate_uzbek_voice

# Maxsus kutubxonalar (Phase 1 AI Upgrade)
from vector_memory import vector_memory

try:
    from tenacity import (
        retry,
        wait_exponential,
        stop_after_attempt,
        retry_if_exception_type,
    )
except ImportError:
    pass

from config import GEMINI_API_KEY, OFFLINE_VOICE_CLONING, VOICE_REFERENCE_PATH

from config import BUSINESS_NAME, BUSINESS_PHONE, BUSINESS_CITY, PRICES
from database import db
from gemini_rotator import rotator as gemini_rotator

# ================================================
# PYDANTIC SCHEMALAR (Structured Output)
# ================================================


# Eski XTTSv2 kodini saqlab qolamiz agar offline_voice_cloning=True bo'lsa
# Lekin asosiy TTS endi uzbek_tts.py moduli orqali ishlaydi
tts_model = None  # Legacy XTTSv2 model cache

# ================================================
# TTS ASYNC NAVBAT (Task 53 - Non-blocking TTS Queue)
# ================================================
_tts_queue: asyncio.Queue = asyncio.Queue(maxsize=20)


async def _tts_worker():
    """Global TTS navbat ishchisi. main.py ichida ishga tushirilishi kerak."""
    logger.info("TTS Worker navbati ishga tushdi.")
    while True:
        try:
            # Endi 4 ta element qabul qilamiz: text, output_path, speed, future
            text, output_path, speed, future = await _tts_queue.get()
            try:
                success = await generate_uzbek_voice(text, output_path, speed=speed)
                if not future.done():
                    future.set_result(success)
            except Exception as e:
                logger.error(f"TTS Worker xatosi: {e}")
                if not future.done():
                    future.set_result(False)
            finally:
                _tts_queue.task_done()
        except asyncio.CancelledError:
            logger.info("TTS Worker to'xtatildi.")
            break
        except Exception as e:
            logger.error(f"TTS Worker kutilmagan xato: {e}")


def get_tts_model():
    """Legacy XTTSv2 - faqat OFFLINE_VOICE_CLONING=True bo'lganda"""
    global tts_model

    if tts_model is None:
        try:
            import torch
            from TTS.api import TTS

            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(
                f"Yangi offline TTS (XTTSv2) modeli yuklanmoqda... Qurilma: {device}"
            )
            tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
            logger.info("XTTSv2 modeli muvaffaqiyatli yuklandi.")
        except Exception as e:
            logger.error(f"TTS modelini yuklashda xatolik: {e}")
            tts_model = "ERROR"
    return tts_model


def generate_voice_sync(text: str, ref_audio_path: str, output_path: str):
    """Legacy - Blocking function for offline XTTSv2"""
    model = get_tts_model()
    if model and model != "ERROR":
        model.tts_to_file(
            text=text, speaker_wav=ref_audio_path, language="ru", file_path=output_path
        )
        return True
    return False


class OrderDataSchema(BaseModel):
    service_type: Optional[str] = Field(
        None, description="Xizmatning kalit nomi (masalan: 'standart_tozalash')"
    )
    service_name: Optional[str] = Field(
        None, description="Xizmatning inson o'qiydigan nomi"
    )
    quantity: Optional[float] = Field(None, description="Miqdor (kv.m yoki xona soni)")
    unit: Optional[str] = Field(None, description="O'lchov birligi (kv.m, xona)")
    address: Optional[str] = Field(None, description="Mijoz manzili")
    scheduled_date: Optional[str] = Field(None, description="Sana (YYYY-MM-DD)")
    scheduled_time: Optional[str] = Field(None, description="Vaqt (HH:MM)")
    notes: Optional[str] = Field(None, description="Mijozning qo'shimcha izohlari")


class AIResponseSchema(BaseModel):
    action: str = Field(
        ...,
        description="Action: greet, answer_question, collecting_service, collecting_address, collecting_date, collecting_quantity, show_price, create_order, connect_admin, complain, faq, urgent, casual",
    )
    language: str = Field(..., description="Mijoz tili: uz, ru, en")
    message: str = Field(
        ..., description="Mijozga yuboriladigan xabar (emoji bilan, do'stona)"
    )
    new_state: str = Field(
        ..., description="Botning keyingi state holati (masalan: collecting_date)"
    )
    context: Dict = Field(
        default_factory=dict,
        description="Suhbat konteksti (masalan: to'plangan manzil, sana)",
    )
    order_data: Optional[OrderDataSchema] = Field(
        None, description="Faqat action 'create_order' bo'lganda to'ldiriladi"
    )
    sentiment: Optional[str] = Field(
        "neutral",
        description="Mijoz hissiyoti: positive, neutral, negative, angry, satisfied",
    )
    implicit_needs: Optional[List[str]] = Field(
        default_factory=list,
        description="Yashirin ehtiyojlar (masalan: farzandi bor, tezkor kerak, uyda hayvon bor)",
    )


class VisionEstimationSchema(BaseModel):
    service_type: str = Field(
        ...,
        description="Kutilayotgan xizmat turi (masalan, standart_tozalash, gilam_yuvish, oyna_tozalash)",
    )
    estimated_quantity: float = Field(
        ..., description="Tahminiy hajm yoki kvadrat metr"
    )
    stain_severity: str = Field(
        "low", description="Dog'lar darajasi: low, medium, high (narxga ta'sir qiladi)"
    )
    material_type: str = Field(
        "unknown", description="Mebel yoki gilam materiali (teri, mato, jun)"
    )
    details: str = Field(
        ...,
        description="Rasmda ko'rinib turgan holat bo'yicha qisqacha izoh (O'zbek tilida)",
    )
    recommended_price_min: float = Field(
        ..., description="Tavsiya etilgan eng kam narx"
    )
    recommended_price_max: float = Field(
        ..., description="Tavsiya etilgan eng ko'p narx"
    )


class AIBrain:
    """Tozalash Servis uchun Asinxron AI Miya (API Limitsiz)"""

    def __init__(self):
        # Cookie-based Gemini orqali ishlaydi — API key kerak emas
        # g4f.Provider.Gemini: gemini-3.5-flash, gemini-3.1-pro modellari
        # gemini-webapi PRO modellar (gemini_rotator ichida boshqariladi)
        # ADVANCED_FLASH → ADVANCED_PRO → ADVANCED_THINKING → PLUS_FLASH
        self._g4f_models = ["ADVANCED_FLASH", "ADVANCED_PRO", "ADVANCED_THINKING"]
        # google-generativeai fallback (API key bo'lsa ishlatiladi)
        self.model = None
        if GEMINI_API_KEY and GEMINI_API_KEY.startswith("AIza"):
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                self.model = genai.GenerativeModel("gemini-2.5-flash")
                logger.info("✅ Gemini API key (backup) tayyor: gemini-2.5-flash")
            except Exception:
                pass

        if gemini_rotator.has_accounts:
            logger.success(
                f"✅ Google AI PRO Cookie Gemini: {gemini_rotator.total} akkaunt "
                f"| ADVANCED_FLASH → ADVANCED_PRO → ADVANCED_THINKING"
            )
        else:
            logger.warning("⚠️ Cookie akkauntlar topilmadi. API key rejimiga o'tildi.")

        logger.info("✅ AI Miya muvaffaqiyatli ishga tushirildi")

    async def _build_system_prompt(self) -> str:
        prices_text = "\n".join(
            [
                f"  - {v['name_uz']}: {v['price']:,} so'm/{v['unit']}"
                + (
                    f" (min: {v.get('minimum', 1)} {v['unit']})"
                    if v.get("minimum")
                    else ""
                )
                for v in PRICES.values()
            ]
        )

        # O'z-o'zini rivojlantirish uchun dinamik qoidalarni DB dan yuklash
        dynamic_guidelines = ""
        try:
            guidelines_list = await db.get_dynamic_guidelines()
            if guidelines_list:
                dynamic_guidelines = "\nYANGI O'RGANILGAN QOIDALAR (Bularga qat'iy amal qil!):\n" + "\n".join(guidelines_list)
        except Exception as e:
            logger.warning(f"Dynamic guidelines DB dan yuklashda xato: {e}")

        try:
            with open("prompts.json", "r", encoding="utf-8") as f:
                prompts_data = json.load(f)
            prompt_template = prompts_data.get("system_prompt_base", "")
            return prompt_template.format(
                prices_text=prices_text,
                dynamic_guidelines=dynamic_guidelines
            )
        except Exception as e:
            logger.error(f"Prompts yuklashda xato: {e}")
            return f"Asal ismli tozalash menejerisan. Narxlar:\n{prices_text}\n{dynamic_guidelines}"

    # ================================================
    # ASOSIY JAVOB BERISH
    async def _detect_language(self, text: str) -> str:
        text_lower = text.lower()
        if any(c in text_lower for c in "ўқғҳ"):
            return "uz"
        if any(c in text_lower for c in "ъыьёэ"):
            return "ru"
        return "uz"

    async def _classify_intent(self, user_message: str, language: str) -> str:
        msg = (user_message or "").lower()
        if any(w in msg for w in ["shikoyat", "yomon", "toza emas", "pretenziya", "yoqmadi", "жалоба", "плохо", "грязно", "ужасно"]):
            return "complain"
        if any(w in msg for w in ["tez", "shoshilinch", "hozir", "bugun", "tezroq", "срочно", "быстро", "сегодня"]):
            return "urgent"
        if any(w in msg for w in ["narx", "qancha", "buyurtma", "zakaz", "tozalash", "gilam", "divan", "uborka", "цена", "сколько", "заказ", "уборка", "купить", "акция", "скидка"]):
            return "sales"
        if any(w in msg for w in ["admin", "operator", "inson", "aloqa", "телефон", "оператор", "админ"]):
            return "support"
        return "sales"

    # ================================================

    async def respond(
        self, telegram_id: str, user_message: str, user_name: str = None
    ) -> Dict:
        """Mijoz xabariga asinxron javob berish"""
        try:
            language = await self._detect_language(user_message)

            # Parallel data fetching to reduce latency
            history_task = db.get_conversation_history(str(telegram_id), limit=10)
            state_task = db.get_user_state(str(telegram_id))
            client_task = db.get_or_create_client(str(telegram_id), user_name)
            orders_task = db.get_client_orders(str(telegram_id), limit=3)
            agent_type_task = self._classify_intent(user_message, language)

            history, user_state_data, client_data, past_orders, agent_type = await asyncio.gather(
                history_task, state_task, client_task, orders_task, agent_type_task
            )

            state = user_state_data.get("state", "idle")
            context = user_state_data.get("context", {})

            # Saving message asynchronously without blocking the main response flow
            asyncio.create_task(db.save_message(str(telegram_id), "user", user_message, state))

            prompt = await self._build_contextual_prompt(
                user_message,
                history,
                state,
                context,
                user_name,
                language,
                past_orders,
                client_data,
                agent_type,
            )
            
            # Phase 1: Swarm Architecture Integration
            result = None
            try:
                from swarm_agents import SwarmOrchestrator
                try:
                    with open("prompts.json", "r", encoding="utf-8") as f:
                        prompts_data = json.load(f)
                except Exception:
                    prompts_data = {}
                    
                orchestrator = SwarmOrchestrator(prompts_data)
                response_text = await orchestrator.process_message(prompt, context, language)
                if response_text and "Kechirasiz" not in response_text[:30]:
                    parsed = self._parse_and_validate(response_text, language)
                    if parsed and parsed.get("message") and "qisqa uzilish" not in parsed["message"]:
                        result = parsed
            except Exception as swarm_err:
                logger.warning(f"Swarm orchestrator bypass: {swarm_err}")

            # If LLM response unavailable or empty, use intelligent expert domain engine
            if not result or not result.get("message"):
                result = self._generate_intelligent_expert_response(
                    user_message=user_message,
                    client_data=client_data,
                    state=state,
                    context=context,
                    language=language,
                    user_name=user_name,
                )

            # Mijoz hissiyotini tahlil qilish (Churn prevention)
            sentiment = result.get("sentiment", "neutral")
            if sentiment == "negative" or agent_type == "complain":
                await db.update_client(str(telegram_id), churn_risk=0.8)
                if "chegirma" not in result["message"].lower():
                    result["message"] += "\n\n🎁 Noqulayliklar uchun uzr so'raymiz! Keyingi buyurtmangiz uchun sizga 10% chegirma taqdim etamiz."

                asyncio.create_task(
                    self.evaluate_and_learn(
                        user_message,
                        result["message"],
                        sentiment,
                    )
                )

            new_state = result.get("next_state", "idle")
            await db.set_user_state(str(telegram_id), new_state, result)
            await db.save_message(str(telegram_id), "ai", result["message"], new_state)
            
            # Phase 2: RAG Memory Store
            try:
                import vector_memory
                asyncio.create_task(
                    vector_memory.store_interaction(
                        str(telegram_id), user_message, result["message"], sentiment
                    )
                )
            except Exception:
                pass

            # Agar muvaffaqiyatli buyurtma bo'lsa, uni o'rganish
            if result.get("action") == "create_order":
                await db.save_learning(
                    "order_conversion",
                    user_message,
                    result.get("message", ""),
                    True,
                    5.0,
                )

            return result
        except Exception as e:
            import traceback
            logger.error(f"Xato AI javobida: {e}\n{traceback.format_exc()}")
            return self._generate_intelligent_expert_response(
                user_message=user_message,
                client_data={},
                state="idle",
                context={},
                language=language or "uz",
                user_name=user_name,
            )

    def _generate_intelligent_expert_response(
        self,
        user_message: str,
        client_data: dict,
        state: str,
        context: dict,
        language: str,
        user_name: str = None,
    ) -> Dict:
        msg = (user_message or "").lower().strip()
        name = user_name or (client_data.get("name") if client_data else "Hurmatli mijoz")
        is_ru = (language == "ru")

        # 1. SALOM / GREETINGS
        if any(w in msg for w in ["salom", "assalom", "assalomu alaykum", "qale", "qalaysiz", "привет", "здравствуйте", "добрый", "хай"]):
            if is_ru:
                message = (
                    f"Здравствуйте, {name}! 😊 Добро пожаловать в компанию 'Tozalash Servis'!\n\n"
                    f"Чем мы можем вам помочь сегодня?\n"
                    f"✨ Генеральная уборка квартир и домов\n"
                    f"🛋 Химчистка диванов, кресел и матрасов\n"
                    f"🧶 Стирка и сушка ковров с вывозом\n"
                    f"🏗 Уборка после ремонта\n\n"
                    f"Напишите интересующую услугу для расчета точной цены!"
                )
            else:
                message = (
                    f"Assalomu alaykum, {name}! 😊 'Tozalash Servis' professional tozalash xizmatiga xush kelibsiz!\n\n"
                    f"Sizga qanday xizmatimiz kerak?\n"
                    f"✨ Xonadon va uylarni umumiy tozalash\n"
                    f"🛋 Divan va yumshoq mebellarni kimyoviy tozalash (ximchistka)\n"
                    f"🧶 Gilam yuvish (olib ketish va yetkazish bepul)\n"
                    f"🏗 Remont / ta'mirdan keyingi tozalash\n\n"
                    f"Narxlarni bilish uchun xizmat turini yozing yoki to'g'ridan-to'g'ri buyurtma qiling!"
                )
            return {
                "action": "greet",
                "message": message,
                "language": language,
                "new_state": "idle",
                "context": context or {},
                "sentiment": "positive",
                "implicit_needs": []
            }

        # 2. SHIKOYAT / COMPLAIN
        if any(w in msg for w in ["shikoyat", "yomon", "toza emas", "pretenziya", "yoqmadi", "qoniqmadim", "жалоба", "плохо", "грязно", "ужасно"]):
            if is_ru:
                message = (
                    f"Приносим искренние извинения за доставленные неудобства! 😔\n"
                    f"Мы очень ценим качество и передали ваше обращение главному менеджеру по контролю качества.\n"
                    f"Мы свяжемся с вами в течение 15 минут для решения проблемы. Также дарим вам скидку 10% на следующий заказ!"
                )
            else:
                message = (
                    f"Keltirilgan noqulayliklar uchun chin dildan uzr so'raymiz! 😔\n"
                    f"Biz uchun xizmat sifati eng muhimi. Xabaringiz zudlik bilan Sifat nazorati bosh menejeriga yuborildi.\n"
                    f"Muammoni bartaraf etish uchun 15 daqiqa ichida siz bilan bog'lanamiz. Shuningdek, sizga 10% maxsus chegirma taqdim etamiz!"
                )
            return {
                "action": "complain",
                "message": message,
                "language": language,
                "new_state": "complain_pending",
                "context": context or {},
                "sentiment": "negative",
                "implicit_needs": ["urgent_resolution"]
            }

        # 3. GILAM / CARPET
        if any(w in msg for w in ["gilam", "kover", "kovyor", "ковер", "ковры"]):
            price = PRICES.get("carpet_cleaning", {}).get("price", 15000)
            if is_ru:
                message = (
                    f"🧶 **Стирка ковров:**\n"
                    f"• Стоимость: **{price:,} сум** за 1 кв.м\n"
                    f"• Профессиональное турецкое оборудование и гипоаллергенные средства\n"
                    f"• Бесплатный забор и доставка до двери!\n\n"
                    f"Оформить заявку? Напишите адрес или примерный размер ковров (например: 3х4 м)."
                )
            else:
                message = (
                    f"🧶 **Gilam yuvish xizmati:**\n"
                    f"• Narxi: **{price:,} so'm** / kv.m\n"
                    f"• Maxsus antibakterial yuvish va xushbo'y quritish\n"
                    f"• Shahar bo'ylab olib ketish va yetkazib berish bepul!\n\n"
                    f"Buyurtma berish uchun gilam o'lchamini (masalan: 3x4 metr) yoki manzilingizni yozing 😊"
                )
            return {
                "action": "collecting_service",
                "message": message,
                "language": language,
                "new_state": "collecting_details",
                "context": {"selected_service": "carpet_cleaning"},
                "sentiment": "neutral",
                "implicit_needs": ["carpet_cleaning"]
            }

        # 4. DIVAN / MEBEL / SOFA
        if any(w in msg for w in ["divan", "mebel", "stul", "kreslo", "matras", "диван", "мебель", "стул", "кресло", "матрас"]):
            sofa_p = PRICES.get("sofa_cleaning", {}).get("price", 120000)
            chair_p = PRICES.get("chair_cleaning", {}).get("price", 25000)
            if is_ru:
                message = (
                    f"🛋 **Химчистка мягкой мебели:**\n"
                    f"• Диван: от **{sofa_p:,} сум** за посадочное место (мин. 3 места)\n"
                    f"• Стулья: **{chair_p:,} сум** / шт\n"
                    f"• Удаляем 99% застарелых пятен, запахов и пылевых клещей прямо у вас дома!\n\n"
                    f"Укажите ваш адрес и удобное время для выезда мастера."
                )
            else:
                message = (
                    f"🛋 **Mebel va divan ximchistkasi:**\n"
                    f"• Divan: **{sofa_p:,} so'm** / o'rindiq (kamida 3 o'rin)\n"
                    f"• Stul: **{chair_p:,} so'm** / dona\n"
                    f"• Nemis Kärcher uskunalari bilan uyingizga borib chuqur tozalab beramiz!\n\n"
                    f"Buyurtma qilish uchun qulay vaqtingiz va manzilingizni yuboring."
                )
            return {
                "action": "collecting_service",
                "message": message,
                "language": language,
                "new_state": "collecting_details",
                "context": {"selected_service": "sofa_cleaning"},
                "sentiment": "neutral",
                "implicit_needs": ["sofa_cleaning"]
            }

        # 5. UBORKA / TOZALASH / REMONT / KVARTIRA
        if any(w in msg for w in ["uborka", "tozalash", "remont", "ta'mir", "kvartira", "uy", "hovli", "ofis", "уборка", "квартира", "дом", "ремонт", "офис"]):
            reg_p = PRICES.get("regular_cleaning", {}).get("price", 300000)
            renov_p = PRICES.get("renovation_cleaning", {}).get("price", 400000)
            if is_ru:
                message = (
                    f"🧹 **Уборка квартир, домов и офисов:**\n"
                    f"• Генеральная уборка: **{reg_p:,} сум** / сотрудник\n"
                    f"• Уборка после ремонта: **{renov_p:,} сум** / сотрудник\n"
                    f"• Включает: мытье окон, сантехники, полов, удаление строительной пыли и грязи.\n\n"
                    f"Сколько комнат или какая площадь вашего помещения?"
                )
            else:
                message = (
                    f"🧹 **Xonadon va binolarni tozalash:**\n"
                    f"• Oddiy / General tozalash: **{reg_p:,} so'm** / ishchi\n"
                    f"• Ta'mirdan (remontdan) keyingi tozalash: **{renov_p:,} so'm** / ishchi\n"
                    f"• Barcha vositalar va uskunalar bizdan!\n\n"
                    f"Uyingiz necha xona yoki maydoni taxminan qancha kv.m?"
                )
            return {
                "action": "collecting_service",
                "message": message,
                "language": language,
                "new_state": "collecting_details",
                "context": {"selected_service": "general_cleaning"},
                "sentiment": "neutral",
                "implicit_needs": ["cleaning"]
            }

        # 6. NARXLAR / PRICING GENERAL
        if any(w in msg for w in ["narx", "qancha", "necha pul", "narxi", "qimmat", "прайс", "сколько", "цена", "стоимость", "расценки"]):
            if is_ru:
                message = (
                    f"📋 **Прайс-лист 'Tozalash Servis':**\n\n"
                    f"1. 🧹 Генеральная уборка — **300,000 сум** / работник\n"
                    f"2. 🏗 Уборка после ремонта — **400,000 сум** / работник\n"
                    f"3. 🛋 Химчистка дивана — **120,000 сум** / место\n"
                    f"4. 🪑 Химчистка стульев — **25,000 сум** / шт\n"
                    f"5. 🧶 Стирка ковров — **15,000 сум** / кв.м\n\n"
                    f"Какую услугу вы хотите заказать?"
                )
            else:
                message = (
                    f"📋 **'Tozalash Servis' rasmiy narxlari:**\n\n"
                    f"1. 🧹 Umumiy / General tozalash — **300,000 so'm** / ishchi\n"
                    f"2. 🏗 Ta'mirdan keyingi tozalash — **400,000 so'm** / ishchi\n"
                    f"3. 🛋 Divan yuvish (ximchistka) — **120,000 so'm** / o'rin\n"
                    f"4. 🪑 Stul yuvish — **25,000 so'm** / dona\n"
                    f"5. 🧶 Gilam yuvish — **15,000 so'm** / kv.m\n\n"
                    f"Qaysi xizmat bo'yicha buyurtma bermoqchisiz?"
                )
            return {
                "action": "show_price",
                "message": message,
                "language": language,
                "new_state": "idle",
                "context": context or {},
                "sentiment": "neutral",
                "implicit_needs": ["price_inquiry"]
            }

        # 7. ADMIN / OPERATOR / CONTACT
        if any(w in msg for w in ["admin", "operator", "inson", "menejer", "telefon", "bog'lanish", "aloqa", "админ", "оператор", "менеджер", "телефон", "связь"]):
            phone = BUSINESS_PHONE or "+998 90 123 45 67"
            if is_ru:
                message = (
                    f"👨‍💻 Вы можете связаться с нашим администратором напрямую:\n"
                    f"📞 Телефон: **{phone}**\n"
                    f"💬 Telegram: @tozalash_admin\n"
                    f"Менеджер ответит на все ваши вопросы!"
                )
            else:
                message = (
                    f"👨‍💻 Siz to'g'ridan-to'g'ri administratorimiz bilan bog'lanishingiz mumkin:\n"
                    f"📞 Telefon: **{phone}**\n"
                    f"💬 Telegram: @tozalash_admin\n"
                    f"Menejerimiz sizga bajonidil yordam beradi!"
                )
            return {
                "action": "connect_admin",
                "message": message,
                "language": language,
                "new_state": "idle",
                "context": context or {},
                "sentiment": "neutral",
                "implicit_needs": ["human_support"]
            }

        # 8. BUYURTMA / ZAKAZ / BOOKING FLOW
        if any(w in msg for w in ["buyurtma", "zakaz", "chaqirmoqchiman", "kerak", "yozdirmoqchiman", "заказ", "заказать", "вызвать", "оформить"]):
            if is_ru:
                message = (
                    f"Отлично! Давайте оформим заявку на уборку 📝\n\n"
                    f"Пожалуйста, напишите:\n"
                    f"1. Какая услуга нужна (генеральная уборка, ковры, диван)?\n"
                    f"2. Ваш адрес (город/район/улица)?\n"
                    f"3. Удобная дата и время?"
                )
            else:
                message = (
                    f"Ajoyib! Buyurtmangizni birgalikda rasmiylashtiramiz 📝\n\n"
                    f"Iltimos, quyidagilarni yozib yuboring:\n"
                    f"1. Qaysi xizmat kerak (general tozalash, gilam, divan)?\n"
                    f"2. Manzilingiz (tuman, ko'cha, uy)?\n"
                    f"3. Qaysi kun va soatda qulay?"
                )
            return {
                "action": "collecting_address",
                "message": message,
                "language": language,
                "new_state": "collecting_address",
                "context": context or {},
                "sentiment": "positive",
                "implicit_needs": ["order_intent"]
            }

        # 9. GENERAL SMART DEFAULT
        if is_ru:
            message = (
                f"Спасибо за ваше сообщение! 😊\n"
                f"Компания 'Tozalash Servis' готова выполнить любую работу по уборке дома, стирке ковров и химчистке мебели.\n\n"
                f"Напишите, что именно нужно почистить, или оставьте номер телефона для консультации!"
            )
        else:
            message = (
                f"Xabaringiz uchun rahmat! 😊\n"
                f"'Tozalash Servis' jamoasi uyingizni tozalash, gilam yuvish va mebellarni ximchistka qilishga doim tayyor.\n\n"
                f"Qaysi xizmatimiz haqida batafsil ma'lumot beraylik yoki buyurtma rasmiylashtiraylik?"
            )
        return {
            "action": "answer_question",
            "message": message,
            "language": language,
            "new_state": "idle",
            "context": context or {},
            "sentiment": "neutral",
            "implicit_needs": []
        }

    async def _build_contextual_prompt(
        self,
        user_message: str,
        history: List[Dict],
        state: str,
        context: Dict,
        user_name: str,
        language: str,
        past_orders: List[Dict],
        client_data: Dict,
        agent_type: str = "support",
    ) -> str:
        # History formatlash (Token limitni boshqarish - Task 52)
        MAX_HISTORY_CHARS = 2000
        history_lines = []
        current_chars = 0
        for msg in reversed(history):  # Oxirgi xabarlar muhimroq
            line = f"{msg['role'].upper()}: {msg['message']}"
            if current_chars + len(line) > MAX_HISTORY_CHARS:
                break
            history_lines.insert(0, line)
            current_chars += len(line)
        
        history_text = "\n".join(history_lines)

        # State formatlash
        state_text = f"\nHOZIRGI HOLAT (STATE): {state}"
        if context:
            state_text += f"\nSAQLANGAN MA'LUMOTLAR: {json.dumps(context, ensure_ascii=False)}"

        orders_text = ""
        if past_orders:
            orders_list = "\n".join(
                [
                    f" - {o['created_at']}: {o['service_name']} ({o['status']})"
                    for o in past_orders
                ]
            )
            orders_text = f"\nMIJOZNING OLDINGI BUYURTMALARI: {orders_list}\nShu ma'lumotlarni hisobga olib, mijozni eslab iliq kutib ol."

        # Vector Memory RAG dan kontekst qidirish
        rag_context = ""
        try:
            rag_context = await vector_memory.retrieve_context(client_data.get("telegram_id", "0"), user_message)
        except Exception as e:
            logger.error(f"RAG xatosi: {e}")

        vip_text = ""
        if client_data:
            total_orders = client_data.get("total_orders", 0)
            churn_risk = client_data.get("churn_risk", 0.0)
            gender = client_data.get("gender", "unknown")

            # Dinamik System Prompt (VIP va xususiyatlar)
            if total_orders >= 5:
                vip_text += "\nMIJOZ VIP STATUSDA (5+ buyurtma). Unga alohida e'tibor va eng yuqori hurmat bilan munosabatda bo'l."
            if churn_risk > 0.5:
                vip_text += "\nDIQQAT: Mijoz oldingi safar norozi bo'lgan (Churn risk yuqori). O'ta muloyim bo'l, xizmat sifatini 100% kafolatla va ehtiyotkor bo'l."
            if gender == "female":
                vip_text += "\nDIQQAT: Mijoz ayol kishi bo'lishi mumkin. Chiroyli dizayn, shinamlik, bolalar xavfsizligi va ekologik tozalikka urg'u ber."
            elif gender == "male":
                vip_text += "\nDIQQAT: Mijoz erkak kishi bo'lishi mumkin. Aniq faktlar, vaqtni tejash va qat'iy narxlarga urg'u ber."

        # Phase 8: Multi-Agent Personas
        agent_persona = ""
        if agent_type == "sales":
            agent_persona = "\nSENING ROLING: Sotuvchi-Vositachi Agent. Maqsading mijozni ko'ndirish va buyurtma olish. Agar qimmat desa, 5% chegirma yoki maxsus to'plam (Bundle) taklif qil."
        elif agent_type == "complain":
            agent_persona = "\nSENING ROLING: Sifat Nazorati Agenti. Mijozni yupat, uzr so'ra va xatoni zudlik bilan to'g'rilashga va'da ber."
        elif agent_type == "urgent":
            agent_persona = "\nSENING ROLING: Tezkor Yordam Agenti. Eng yaqin ishchi ajratilishini va tez orada yetib borishini aytib ishontir."

        # Har doim fayldan yangi qoidalarni o'qib olish (o'z-o'zini rivojlantirish real-time ishlashi uchun)
        current_system_prompt = await self._build_system_prompt()

        clean_user_name = (user_name or "Mijoz").replace('"""', '"').replace("===", "")
        clean_user_message = (user_message or "").replace('"""', '"').replace("===", "")

        try:
            with open("prompts.json", "r", encoding="utf-8") as f:
                prompts_data = json.load(f)
            prompt_template = prompts_data.get("main_interaction", "")
            return prompt_template.format(
                current_system_prompt=current_system_prompt,
                agent_persona=agent_persona,
                history_text=history_text,
                state_text=state_text,
                orders_text=orders_text,
                vip_text=vip_text,
                rag_context=rag_context,
                clean_user_name=clean_user_name,
                clean_user_message=clean_user_message,
                language=language
            )
        except Exception:
            return f"""{current_system_prompt}
{agent_persona}
{history_text}
{state_text}
{orders_text}
{vip_text}
{rag_context}
MIJOZ: ==={clean_user_name}===


YANGI XABAR: ==={clean_user_message}===

Javobingni qat'iy JSON formatida qaytar. Mijoz xabari === belgilari orasida berilgan. Pydantic schema:
{{
  "action": "greet|answer_question|collecting_service|collecting_address|collecting_date|show_price|create_order|complain|faq|urgent|casual|connect_admin|ask_admin_for_knowledge",
  "language": "{language}",
  "message": "xabar matni",
  "new_state": "keyingi holat",
  "context": {{"key": "value"}},
  "sentiment": "positive|neutral|negative|angry|satisfied",
  "implicit_needs": ["qisqacha yashirin ehtiyojlar ro'yxati (masalan, shoshilinch, farzandi bor)"],
  "order_data": null,
  "admin_question": "agar action ask_admin_for_knowledge bo'lsa, adminga yozmoqchi bo'lgan savolingizni shu yerga yozasiz, aks holda null"
}}
Hech qanday markdown belgilari (```json) ishlatma, faqat JSON object qaytar."""

    async def _get_openai_response(self, prompt: str) -> str:
        """OpenAI (GPT-4o) orqali zaxira javob olish"""
        if not os.getenv("OPENAI_API_KEY"):
            return self._fallback_json()
        try:
            import openai

            client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI xatosi: {e}")
        return self._fallback_json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception)
    )
    async def _get_ai_response(self, prompt: str) -> str:
        """
        Google AI PRO Cookie-based Gemini (Tier-1) → API key (Tier-2) → Fallback (Tier-3)

        Model tartibi (PRO akkaunt):
          ADVANCED_FLASH → ADVANCED_PRO → ADVANCED_THINKING → PLUS_FLASH
        4 akkaunt Round-Robin bilan.
        """
        from gemini_rotator import rotator

        # ── TIER-1: Google AI PRO Cookie (4 akkaunt, PRO models) ─────────────
        if rotator.has_accounts:
            result = await rotator.ask(
                prompt,
                retries=rotator.total,
            )
            if result:
                return result

        # ── TIER-2: google-generativeai API key (zaxira) ─────────────────────
        if self.model:
            try:
                response = await asyncio.wait_for(
                    self.model.generate_content_async(
                        prompt,
                        generation_config={"response_mime_type": "application/json"},
                    ),
                    timeout=30.0,
                )
                if response.text:
                    logger.info("Gemini API key (Tier-2) ishlatildi")
                    return response.text
            except Exception as e:
                logger.warning(f"Gemini API key ham ishlamadi: {e}")

        # ── TIER-3: Fallback JSON ─────────────────────────────────────────────
        logger.error("Barcha Gemini manbalari ishlamadi. Fallback javob qaytarilmoqda.")
        return self._fallback_json()


    def _fallback_json(self):
        return json.dumps(
            {
                "action": "answer_question",
                "message": "Kechirasiz, AI xizmati hozircha band. Iltimos adminga yozing yoki birozdan so'ng urinib ko'ring.",
                "language": "uz",
                "new_state": "idle",
                "context": {},
                "sentiment": "neutral",
                "implicit_needs": [],
            }
        )

    def _parse_and_validate(self, response_text: str, language: str) -> Dict:
        """AI javobini JSON ga o'tkazish va tasdiqlash"""
        try:
            match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if match:
                data = json.loads(match.group())
            else:
                data = json.loads(response_text)

            # Default qiymatlar va tahlil
            if "action" not in data:
                data["action"] = "answer_question"
            if "message" not in data:
                data["message"] = "Kechirasiz, tushunmadim."

            return data
        except Exception as e:
            logger.error(f"JSON parse error: {e}\nResponse: {response_text}")
            return {
                "action": "answer_question",
                "message": "Kechirasiz, texnik xatolik yuz berdi.",
                "language": language,
                "new_state": "idle",
            }

    async def calculate_price(self, service_type: str, quantity: float) -> Dict:
        """Xizmat narxini hisoblash"""
        if service_type not in PRICES:
            return {"status": "error", "message": "Noma'lum xizmat turi"}

        service_info = PRICES[service_type]
        price_per_unit = service_info["price"]
        minimum = service_info.get("minimum", 1)

        final_quantity = max(quantity, minimum)
        total = final_quantity * price_per_unit

        return {
            "status": "success",
            "service_name": service_info["name_uz"],
            "quantity": final_quantity,
            "unit": service_info["unit"],
            "total": total,
            "price_per_unit": price_per_unit,
        }

    async def analyze_image(self, image_path: str, user_prompt: str = "") -> Dict:
        """Rasmni tahlil qilib narx va xizmat turini chiqarish"""
        if not self.model:
            return {
                "service_type": "standart_tozalash",
                "estimated_quantity": 1.0,
                "condition_notes": "Gemini API o'rnatilmagan",
                "recommended_price_min": 150000,
                "recommended_price_max": 250000,
            }
        try:
            import PIL.Image

            img = PIL.Image.open(image_path)
            # Vision optimizatsiyasi: Rasmni kichraytirish upload/process tezligini keskin oshiradi
            img.thumbnail((1024, 1024), PIL.Image.Resampling.LANCZOS)
            if img.mode != "RGB":
                img = img.convert("RGB")

            prompt = f"""Mijoz rasm jo'natdi va qo'shimcha matn yozdi: '{user_prompt}'. 
Rasmni tahlil qil va tozalash xizmati uchun baho ber. 

Quyidagi misollarga (Few-Shot) e'tibor qaratib, xuddi shunday sifatli javob qaytar:
Misol 1 (Kichik xona):
{{
  "service_type": "standart_tozalash",
  "estimated_quantity": 20.0,
  "condition_notes": "Xona unchalik iflos emas, changlar bor. 20 kv.m atrofida.",
  "recommended_price_min": 100000,
  "recommended_price_max": 150000
}}

Misol 2 (Qurilishdan keyingi holat):
{{
  "service_type": "remontdan_keyingi_tozalash",
  "estimated_quantity": 50.0,
  "condition_notes": "Pol va derazalarda qurilish changi va qoldiqlari bor.",
  "recommended_price_min": 500000,
  "recommended_price_max": 700000
}}

Qat'iy JSON formatida qaytar:
{{
  "service_type": "...",
  "estimated_quantity": ...,
  "condition_notes": "...",
  "recommended_price_min": ...,
  "recommended_price_max": ...
}}"""

            response = await self.model.generate_content_async([prompt, img])

            content = response.text
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                data = json.loads(match.group())
                return data
            else:
                raise ValueError("JSON topilmadi")
        except Exception as e:
            logger.error(f"AI Vision tahlilida xato: {e}")
            return {
                "service_type": "standart_tozalash",
                "estimated_quantity": 1.0,
                "condition_notes": f"Xatolik yuz berdi. ({e})",
                "recommended_price_min": 150000,
                "recommended_price_max": 250000,
            }

    # ================================================
    # AI AUDIO (OVOZLI XABARLAR) UCHUN
    # ================================================

    async def translate_text(self, text: str, target_language: str) -> str:
        """Matnni real vaqt rejimida tarjima qilish"""
        if not self.model:
            return text
        try:
            prompt = f"""Quyidagi matnni {target_language} tiliga tarjima qil. Faqat tarjima qilingan matnni qaytar, boshqa izoh qo'shma:

{text}"""
            response = await self.model.generate_content_async(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Tarjimada xato: {e}")
            return text

    async def analyze_audio(self, audio_path: str) -> str:
        """Ovozli xabarni matnga o'girish (transkripsiya) - Eng tezkor va barqaror usul (Google Web Speech API)"""
        converted_path = None
        try:
            # 1. Telegram .ogg faylini .wav formatiga asinxron o'tkazish
            def _convert():
                wav_path = audio_path.rsplit(".", 1)[0] + ".wav"
                from pydub import AudioSegment
                audio = AudioSegment.from_file(audio_path)
                audio.export(wav_path, format="wav")
                return wav_path

            import asyncio
            converted_path = await asyncio.to_thread(_convert)
            
            # 2. Nutqni aniqlash
            def _recognize():
                import speech_recognition as sr
                recognizer = sr.Recognizer()
                with sr.AudioFile(converted_path) as source:
                    audio_data = recognizer.record(source)
                    # O'zbek tili uchun uz-UZ ishlatamiz
                    return recognizer.recognize_google(audio_data, language="uz-UZ")
                    
            text = await asyncio.to_thread(_recognize)
            
            if text:
                return text.strip()
            return "Kechirasiz, ovozli xabarni tushunib bo'lmadi."
            
        except Exception as e:
            logger.error(f"AI Audio tahlilida xato: {e}")
            return "Kechirasiz, ovozli xabarni eshitishda xatolik yuz berdi. Iltimos, matn ko'rinishida yozib yuboring."
        finally:
            try:
                if converted_path and os.path.exists(converted_path):
                    import os
                    os.remove(converted_path)
            except Exception:
                pass

    async def generate_voice_response(self, text: str, output_path: str, speed: float = 1.0) -> bool:
        """Matnni TTS navbati (Queue) orqali asinxron ovozga aylantirish (Task 53)"""
        loop = asyncio.get_event_loop()
        future: asyncio.Future = loop.create_future()

        await _tts_queue.put((text, output_path, speed, future))

        try:
            success = await asyncio.wait_for(future, timeout=30.0)
            return success
        except asyncio.TimeoutError:
            logger.error("TTS queue timeout (30s). Ovoz yaratilmadi.")
            return False

    # ================================================
    # INSTAGRAM KONTENT
    # ================================================

    async def generate_instagram_post(self, context: str = None) -> Dict:
        if not self.model:
            return {
                "caption": f"Professional tozalash! 📞 {BUSINESS_PHONE}",
                "hashtags": "#tozalash",
            }
        prompt = f"Tozalash Servis uchun Instagram post yoz. Kontekst: {context or 'Uyni professional tozalash'}. Format JSON."
        try:
            response = await self.model.generate_content_async(prompt)
            data = json.loads(re.search(r"\{.*\}", response.text, re.DOTALL).group())
            return data
        except Exception as e:
            logger.error(
                f"Instagram post generatsiyasida xato: {type(e).__name__}",
                exc_info=True,
            )
            return {
                "caption": f"Professional tozalash! 📞 {BUSINESS_PHONE}",
                "hashtags": "#tozalash",
            }

    async def generate_channel_post(
        self, post_type: str, trend_context: str = ""
    ) -> Dict:
        """Kanal uchun uzun, qiziqarli, emojilarga boy post va ingliz tilidagi rasm promptini yaratish"""
        if not self.model:
            return {
                "text": f"O'z uyingizni professionallarga ishonib topshiring!\n\n📞 {BUSINESS_PHONE}",
                "image_prompt": "clean beautiful home interior, professional cleaning, 4k",
            }

        prompt = f"""Sening vazifang "Tozalash Servis" kompaniyasining Telegram kanali uchun SMM mutaxassisi darajasida, juda kuchli marketing strategiyalari asosida, mijozlarni jalb qiluvchi va professional post yozish.

Post turi: {post_type}
Qo'shimcha internet trend va kanal tarixi: {trend_context}

QOIDALAR VA MARKETING STRATEGIYASI:
1. Post strukturasi: Hook (jozibali sarlavha) -> Muammo/Ehtiyoj -> Yechim (bizning xizmat) -> Call to Action (harakatga chorlash).
2. Psixologik ta'sir: Odamlar tozalikni emas, xotirjamlikni, vaqtni tejashni va salomatlikni sotib oladi. Shu nuqtalarga urg'u bering.
3. Uzunlik: Kamida 3-4 ta xat boshidan iborat bo'lsin. Juda qisqa bo'lmasin.
4. Emojilar: O'z o'rnida, estetik va professional ko'rinishda ishlating.
5. Matn oxirida doim kompaniya kontaktlarini qoldiring:
   👉 Telegram: @tozalash_admin
   📞 Telefon: {BUSINESS_PHONE}
6. Rasm generatsiyasi: Postga aloqador, juda yuqori sifatli (high-end, luxury, highly detailed, photorealistic, 8k, cinematic lighting) rasm chizish uchun Ingliz tilida mukammal 'image_prompt' yozing. (Masalan: "A luxurious and spotless modern living room bathed in golden hour sunlight, professional cleaning service concept, hyper-realistic, 8k, architectural digest style").

Barchasini qat'iy JSON formatida qaytar:
{{
    "text": "Postning to'liq matni (o'zbek tilida, emojilar bilan)",
    "image_prompt": "Rasm generatsiyasi uchun ingliz tilidagi prompt"
}}
Hech qanday markdown belgilari (```json) ishlatma, faqat JSON object qaytar."""

        try:
            response = await self.model.generate_content_async(prompt)
            match = re.search(r"\{.*\}", response.text, re.DOTALL)
            if match:
                data = json.loads(match.group())
            else:
                data = json.loads(response.text)

            if "text" not in data or "image_prompt" not in data:
                raise ValueError("JSON tuzilishi noto'g'ri")
            return data
        except Exception as e:
            logger.error(
                f"Kanal posti generatsiyasida xato: {type(e).__name__}", exc_info=True
            )
            return {
                "text": f"✨ Uyingiz ozodaligi – bizning vazifamiz!\n\nProfessional tozalash xizmatlarimizdan foydalaning va vaqtingizni o'zingizga ajrating.\n\n📞 Biz bilan bog'laning: {BUSINESS_PHONE}",
                "image_prompt": "professional cleaning service, sparkling clean room, sunlight, high quality",
            }

    async def self_improve(self) -> List[str]:
        """AI ning o'zini o'zi tahlil qilib, DB ma'lumotlariga asosan yaxshilanish takliflarini berishi"""
        if not self.model:
            return ["Mijozlarga tezroq javob berish", "Xizmat sifatini oshirish"]
        try:
            # db global darajada import qilingan (modul boshida)
            # Get some stats from DB for context
            stats = await db.get_orders_stats()
            messages_today = await db.get_messages_count_today()
            successful_patterns = await db.get_successful_patterns(
                context_type="order_conversion", limit=5
            )

            patterns_text = " ".join(
                [p.get("input_data", "") for p in successful_patterns]
            )

            prompt = (
                f"Sen aqlli Tozalash Servis yordamchisisan. Bugungi natijalar:\n"
                f"Umumiy buyurtmalar: {stats.get('total_orders', 0)}\n"
                f"Bugungi xabarlar: {messages_today}\n"
                f"Muvaffaqiyatli na'munalar: {patterns_text}\n\n"
                f"Shu ma'lumotlarni tahlil qilib, xizmat sifatini oshirish uchun 3 ta aniq va qisqa amaliy taklif ber. "
                f'Faqat JSON array qaytar: ["Taklif 1", "Taklif 2", "Taklif 3"]'
            )
            response = await self.model.generate_content_async(prompt)
            json_str = response.text
            match = re.search(r"\[.*\]", json_str, re.DOTALL)
            if match:
                json_str = match.group()
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Self-improve xatosi: {e}")
            return ["Mijozlarga tezroq javob berish", "Xizmat sifatini oshirish"]

    async def evaluate_and_learn(
        self, user_message: str, ai_response: str, sentiment: str
    ):
        """LLM-as-a-Judge mexanizmi: Xatolarni tahlil qilib o'zini o'zi yangilaydi"""
        if not self.model:
            return
        prompt = f"""Mijoz yozdi: "{user_message}"
Sening oldingi javobing: "{ai_response}"
Mijozning hissiyoti: {sentiment}

Ushbu suhbatda mijoz norozi bo'lgan. Qisqa tahlil qilib, kelajakda AI qanday javob berishi kerakligi haqida Bitta aniq OLTIN QOIDA (Golden Rule) yoz. 
Qoida qisqa va amaliy bo'lsin. (Masalan: 'Agar mijoz xizmat kechikkanidan nolisa, darhol 5% chegirma taklif qil va uzr so'ra')."""
        try:
            response = await self.model.generate_content_async(prompt)
            rule = response.text.strip().replace('"', "")

            # K4 FIX: Prompt injection sanitization — faqat xavfsiz belgilar qoldiriladi
            # Qoida 250 belgidan oshmasin, har qanday fayl/qobiq buyrug'i tashlab yuborilsin
            rule = re.sub(
                r"[\r\n\x00-\x1f]", " ", rule
            )  # Yangi satr va boshqarish belgilarini olib tashlash
            rule = re.sub(
                r"(import |exec\(|eval\(|open\(|os\.)", "", rule, flags=re.IGNORECASE
            )
            rule = rule[:200].strip()  # Maksimal 200 belgi

            if rule and len(rule) >= 10:  # Juda qisqa "qoidalar" ni ham filtrlash

                def _write_rule():
                    with open("dynamic_guidelines.txt", "a", encoding="utf-8") as f:
                        f.write(f"\n- YANGI O'RGANILGAN QOIDA: {rule}")

                # K4+K6 FIX: Fayl I/O bloking — asyncio.to_thread() ga o'tkazildi
                await asyncio.to_thread(_write_rule)
                logger.info(f"🧠 AI yangi qoida o'rgandi va saqladi: {rule}")
        except Exception as e:
            logger.error(f"Self-learning baholashda xato: {e}")


# Global AI instance
ai_brain = AIBrain()
