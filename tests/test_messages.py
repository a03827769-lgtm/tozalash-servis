import pytest
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from unittest.mock import patch, AsyncMock, MagicMock
from bot.handlers import messages


@pytest.mark.asyncio
async def test_message_handler():
    update = MagicMock()
    update.effective_user.id = 123
    update.effective_user.full_name = "test user"
    update.effective_chat.id = 123
    update.message.text = "Hello"
    update.message.caption = None
    update.message.photo = None
    update.message.voice = None
    update.message.reply_text = AsyncMock()
    update.message.reply_photo = AsyncMock()
    update.message.reply_voice = AsyncMock()
    context = MagicMock()
    context.bot.send_chat_action = AsyncMock()

    with patch("bot.handlers.messages.db") as mock_db, patch(
        "bot.handlers.messages.ai_brain"
    ) as mock_brain, patch("bot.handlers.messages.os.makedirs"):

        mock_db.get_or_create_client = AsyncMock(
            return_value={"id": 1, "language": "uz"}
        )
        mock_db.get_user_state = AsyncMock(
            return_value={"state": "idle", "context": {}}
        )
        mock_db.set_user_state = AsyncMock()
        mock_brain.respond = AsyncMock(
            return_value={"message": "AI Reply", "action": "answer_question"}
        )

        # 1. Test normal text message
        await messages.message_handler(update, context)
        mock_brain.respond.assert_called_once()
        update.message.reply_text.assert_called_once()

        # 2. Test image message
        photo_file_mock = AsyncMock()
        photo_file_mock.download_to_drive = AsyncMock()
        photo_mock = MagicMock()
        photo_mock.file_size = 1000
        photo_mock.get_file = AsyncMock(return_value=photo_file_mock)
        update.message.photo = [photo_mock]
        update.message.text = None

        mock_brain.analyze_image = AsyncMock(
            return_value={
                "service_type": "Uy tozalash",
                "recommended_price_min": 100000,
            }
        )
        await messages.message_handler(update, context)
        mock_brain.analyze_image.assert_called_once()

        # 3. Test audio message
        update.message.photo = None
        voice_file_mock = AsyncMock()
        voice_file_mock.download_to_drive = AsyncMock()
        voice_mock = MagicMock()
        voice_mock.file_size = 1000
        voice_mock.get_file = AsyncMock(return_value=voice_file_mock)
        update.message.voice = voice_mock

        mock_brain.analyze_audio = AsyncMock(return_value="audio text")
        mock_brain.respond = AsyncMock(
            return_value={"message": "voice response", "action": "answer_question"}
        )
        mock_brain.generate_voice_response = AsyncMock(return_value=False)
        await messages.message_handler(update, context)
        mock_brain.analyze_audio.assert_called_once()
        mock_brain.respond.assert_called()
