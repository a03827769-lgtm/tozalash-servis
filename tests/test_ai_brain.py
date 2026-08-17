import pytest
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from unittest.mock import patch, AsyncMock, MagicMock
from ai_brain import AIBrain


@pytest.mark.asyncio
async def test_ai_brain_methods():
    with patch("ai_brain.db") as mock_db:

        mock_db.get_successful_patterns = AsyncMock(return_value=[])
        mock_db.get_conversation_history = AsyncMock(return_value=[])
        mock_db.save_message = AsyncMock()
        mock_db.save_learning = AsyncMock()
        mock_db.get_or_create_client = AsyncMock(
            return_value={"id": 1, "language": "uz"}
        )
        mock_db.get_user_state = AsyncMock(
            return_value={"state": "idle", "context": {}}
        )
        mock_db.get_client_orders = AsyncMock(return_value=[])
        mock_db.set_user_state = AsyncMock()
        mock_db.update_client = AsyncMock()

        brain = AIBrain()

        mock_genai_model = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = '{"message": "Hello", "action": "answer_question", "new_state": "idle", "language": "uz"}'
        mock_genai_model.generate_content_async = AsyncMock(return_value=mock_resp)

        with patch("ai_brain.genai.GenerativeModel", return_value=mock_genai_model):
            # respond
            res = await brain.respond("123", "Hello", "Test User")
            assert res.get("message") == "Hello"

            # analyze_image
            mock_vision = AsyncMock()
            mock_vision.return_value.text = '{"service_type": "Qurilishdan keyin tozalash", "recommended_price_min": 100000, "recommended_price_max": 200000, "details": "test"}'
            mock_genai_model.generate_content_async = mock_vision
            res = await brain.analyze_image("data/test.jpg", "Test")
            assert res is not None

        # analyze_audio
        with patch("ai_brain.os.remove", return_value=None), patch(
            "ai_brain.os.path.exists", return_value=True
        ), patch("ai_brain.sr.Recognizer") as mock_rec, patch(
            "ai_brain.sr.AudioFile"
        ), patch(
            "ai_brain.AudioSegment.from_ogg"
        ) as mock_audio:

            mock_audio.return_value.__len__.return_value = 25000
            mock_audio.return_value.__getitem__.return_value = MagicMock()
            mock_rec.return_value.record.return_value = MagicMock()
            mock_rec.return_value.recognize_google.return_value = "audio text"

            res = await brain.analyze_audio("test.ogg")
            assert res == "audio text"
