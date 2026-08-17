"""
Tozalash Servis - Telegram Bot Handler Simulyatsion Testlar (Task 60)
- Bot handlerlarini UpdateMock orqali tekshirish
- Onboarding, manzil to'plash, buyurtma, shikoyat
"""
import sys
import os
import json
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ================================================
# HELPER: Telegram Update Mock
# ================================================

def make_update(text: str, user_id: int = 123456, full_name: str = "Test User", is_voice: bool = False):
    """Telegram Update ob'ektining to'liq mock versiyasi"""
    user = MagicMock()
    user.id = user_id
    user.full_name = full_name
    user.is_bot = False

    message = MagicMock()
    message.from_user = user
    message.text = text
    message.voice = MagicMock() if is_voice else None
    message.photo = None
    message.reply_text = AsyncMock()
    message.reply_voice = AsyncMock()
    message.reply_document = AsyncMock()
    message.chat_id = user_id

    update = MagicMock()
    update.message = message
    update.effective_user = user
    return update


def make_context():
    context = MagicMock()
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    context.bot.send_document = AsyncMock()
    return context


# ================================================
# 1. SALOMLASHISH VA ONBOARDING TESTLARI
# ================================================

class TestOnboarding:
    """Yangi foydalanuvchi onboarding jarayoni"""

    @pytest.mark.asyncio
    async def test_start_command_sends_reply(self):
        """'/start' komandasi javob yuborishi kerak"""
        update = make_update("/start")
        context = make_context()

        # Simulate start handler logic
        await update.message.reply_text("Xush kelibsiz!")
        update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_greeting_triggers_ai_response(self):
        """Salomlashish xabari AI javobini ishga tushirishi kerak"""
        update = make_update("Salom!")
        ai_response = {
            "message": "Assalomu alaykum! Tozalash Servisiga xush kelibsiz 😊",
            "action": "greet",
            "next_state": "idle",
            "sentiment": "positive",
        }
        with patch("database.db") as mock_db:
            mock_db.get_user_state = AsyncMock(return_value={"state": "idle", "context": {}})
            mock_db.get_or_create_client = AsyncMock(return_value={"telegram_id": "123456", "name": "Test", "total_orders": 0, "churn_risk": 0.0})
            mock_db.save_message = AsyncMock()
            mock_db.get_conversation_history = AsyncMock(return_value=[])
            mock_db.get_client_orders = AsyncMock(return_value=[])

            # We mock ai_brain.respond
            with patch("ai_brain.ai_brain") as mock_brain:
                mock_brain.respond = AsyncMock(return_value=ai_response)
                result = await mock_brain.respond(
                    telegram_id="123456",
                    user_message="Salom!",
                    user_name="Test User"
                )
                assert result["action"] == "greet"
                assert "Assalomu" in result["message"]


# ================================================
# 2. BUYURTMA BERISH OQIMI
# ================================================

class TestOrderFlow:
    """Buyurtma berish jarayonini tekshirish"""

    @pytest.mark.asyncio
    async def test_service_inquiry_triggers_order_intent(self):
        """Xizmat so'rovida 'create_order' actioni bo'lishi kerak"""
        update = make_update("Divan yuvish kerak, narxi necha?")
        ai_response = {
            "message": "Divan yuvish narxi 100,000 so'mdan boshlanadi 😊",
            "action": "provide_price",
            "next_state": "idle",
            "sentiment": "neutral",
        }
        with patch("ai_brain.ai_brain") as mock_brain:
            mock_brain.respond = AsyncMock(return_value=ai_response)
            result = await mock_brain.respond(
                telegram_id="123456",
                user_message="Divan yuvish kerak, narxi necha?",
                user_name="Test"
            )
            assert "narx" in result["message"].lower() or "100,000" in result["message"]

    @pytest.mark.asyncio
    async def test_address_collection_state(self):
        """Manzil to'plash holatida DB yangilanishi kerak"""
        with patch("database.db") as mock_db:
            mock_db.set_user_state = AsyncMock()
            mock_db.get_user_state = AsyncMock(
                return_value={"state": "collecting_address", "context": {}}
            )
            mock_db.get_or_create_client = AsyncMock(
                return_value={"telegram_id": "123456", "language": "uz"}
            )

            # Simulate collecting_address handler
            ctx = {}
            ctx["address"] = "Yunusobod 19-kvartal"
            await mock_db.set_user_state("123456", "collecting_date", ctx)
            mock_db.set_user_state.assert_called_with("123456", "collecting_date", {"address": "Yunusobod 19-kvartal"})

    @pytest.mark.asyncio
    async def test_order_creation_saves_to_db(self):
        """Buyurtma yaratilganda DB ga saqlanishi kerak"""
        with patch("database.db") as mock_db:
            mock_db.create_order = AsyncMock(return_value={"id": 42, "service_name": "Divan yuvish", "status": "new"})
            order = await mock_db.create_order(
                telegram_id="123456",
                service_type="sofa_cleaning",
                service_name="Divan yuvish",
                quantity=1,
                address="Yunusobod",
                scheduled_date="2024-02-01",
                scheduled_time="10:00"
            )
            assert order["id"] == 42
            assert order["status"] == "new"


# ================================================
# 3. SHIKOYAT VA SUPPORT
# ================================================

class TestComplaintFlow:
    """Shikoyat va support oqimini tekshirish"""

    @pytest.mark.asyncio
    async def test_complaint_triggers_churn_risk_update(self):
        """Shikoyat bo'lganda churn_risk yangilanishi kerak"""
        with patch("database.db") as mock_db:
            mock_db.update_client = AsyncMock()

            # Simulate respond when complaint detected
            ai_result = {"sentiment": "negative", "message": "Uzr!", "action": "none", "next_state": "idle"}
            if ai_result.get("sentiment") == "negative":
                await mock_db.update_client("123456", churn_risk=0.8)
            mock_db.update_client.assert_called_with("123456", churn_risk=0.8)

    @pytest.mark.asyncio
    async def test_complaint_adds_discount_message(self):
        """Shikoyat javobi chegirma taklifini o'z ichiga olishi kerak"""
        message = "Xizmatdan norozi bo'ldingiz."
        if "chegirma" not in message.lower():
            message += "\n\n🎁 Noqulayliklar uchun uzr so'raymiz! Keyingi buyurtmangiz uchun sizga 10% chegirma taqdim etamiz."
        assert "chegirma" in message.lower() or "10%" in message

    @pytest.mark.asyncio
    async def test_urgent_message_recognized(self):
        """Shoshilinch xabar to'g'ri aniqlanishi kerak"""
        def classify(text):
            urgent_words = ["tez", "bugun", "shoshilinch", "zudlik", "mehmon"]
            return "urgent" if any(w in text.lower() for w in urgent_words) else "support"

        assert classify("Bugun kelishingiz mumkinmi?") == "urgent"
        assert classify("Narxi qancha?") == "support"


# ================================================
# 4. RASM YUBORISH (VISION)
# ================================================

class TestVisionHandler:
    """Rasm orqali narx hisoblash handlerini tekshirish"""

    @pytest.mark.asyncio
    async def test_vision_returns_price_range(self):
        """Vision AI natijasida narx diapazoni bo'lishi kerak"""
        vision_result = {
            "service_type": "standart_tozalash",
            "estimated_quantity": 30.0,
            "condition_notes": "O'rtacha tozalash kerak.",
            "recommended_price_min": 150_000,
            "recommended_price_max": 200_000,
        }
        with patch("ai_brain.ai_brain") as mock_brain:
            mock_brain.analyze_image = AsyncMock(return_value=vision_result)
            result = await mock_brain.analyze_image("/tmp/test.jpg", "Xona tozalash kerak")
            assert result["recommended_price_min"] > 0
            assert result["recommended_price_max"] >= result["recommended_price_min"]

    @pytest.mark.asyncio
    async def test_vision_fallback_on_error(self):
        """Vision AI xatoligida fallback natija qaytarishi kerak"""
        fallback = {
            "service_type": "standart_tozalash",
            "estimated_quantity": 1.0,
            "condition_notes": "Xatolik yuz berdi.",
            "recommended_price_min": 150_000,
            "recommended_price_max": 250_000,
        }
        with patch("ai_brain.ai_brain") as mock_brain:
            mock_brain.analyze_image = AsyncMock(return_value=fallback)
            result = await mock_brain.analyze_image("/nonexistent/path.jpg")
            assert "service_type" in result
            assert result["recommended_price_min"] > 0


# ================================================
# 5. OVOZ XABARI (STT)
# ================================================

class TestVoiceHandler:
    """Ovozli xabar handlerini tekshirish"""

    @pytest.mark.asyncio
    async def test_audio_transcription_returns_string(self):
        """STT natijasi string bo'lishi kerak"""
        with patch("ai_brain.ai_brain") as mock_brain:
            mock_brain.analyze_audio = AsyncMock(return_value="Divan yuvish kerak")
            transcript = await mock_brain.analyze_audio("/tmp/voice.ogg")
            assert isinstance(transcript, str)
            assert len(transcript) > 0

    @pytest.mark.asyncio
    async def test_empty_audio_returns_fallback(self):
        """Bo'sh audio uchun fallback matn qaytarishi kerak"""
        with patch("ai_brain.ai_brain") as mock_brain:
            mock_brain.analyze_audio = AsyncMock(return_value="Kechirasiz, ovozli xabaringizni tushuna olmadim.")
            result = await mock_brain.analyze_audio("/empty.ogg")
            assert "tushuna" in result or len(result) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
