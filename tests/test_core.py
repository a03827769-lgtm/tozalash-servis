import pytest
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from unittest.mock import patch, MagicMock, AsyncMock
from config import BASE_DIR, DATA_DIR, LOGS_DIR, TELEGRAM_BOT_TOKEN
from main import check_configuration
import database
from database import Database
from bot.services.search import search_competitors
from bot.handlers.worker_handlers import (
    cmd_worker_start,
    worker_name_received,
    worker_phone_received,
    cancel_registration,
)


def test_config_dirs():
    assert BASE_DIR.exists()
    assert DATA_DIR.exists()
    assert LOGS_DIR.exists()


@patch("config.os.path.exists", return_value=True)
def test_check_configuration(mock_exists):
    assert check_configuration() is not None


@pytest.mark.asyncio
async def test_search_competitors():
    with patch("bot.services.search.GOOGLE_SEARCH_API_KEY", "test_key"), patch(
        "bot.services.search.GOOGLE_CX", "test_cx"
    ), patch("bot.services.search.aiohttp.ClientSession.get") as mock_get:

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "items": [
                    {"title": "Test", "link": "http://test", "snippet": "test snippet"}
                ]
            }
        )
        mock_response.__aenter__.return_value = mock_response
        mock_get.return_value = mock_response

        with patch(
            "bot.services.search.db.save_daily_report", new_callable=AsyncMock
        ) as mock_db_save:
            await search_competitors()
            assert mock_db_save.called


@pytest.mark.asyncio
async def test_worker_handlers():
    update = MagicMock()
    update.effective_user.id = 12345
    update.effective_user.username = "test_user"
    update.message.text = "John Doe"
    update.message.reply_text = AsyncMock()

    context = MagicMock()
    context.user_data = {}

    with patch(
        "bot.handlers.worker_handlers.db.get_worker_by_tg_id",
        new_callable=AsyncMock,
        return_value=None,
    ):
        res = await cmd_worker_start(update, context)
        assert res == 0  # WAITING_NAME

    res2 = await worker_name_received(update, context)
    assert context.user_data["worker_name"] == "John Doe"
    assert res2 == 1  # WAITING_PHONE

    update.message.text = "+998901234567"
    with patch(
        "bot.handlers.worker_handlers.db.register_worker", new_callable=AsyncMock
    ) as mock_reg:
        res3 = await worker_phone_received(update, context)
        mock_reg.assert_called_once()
        assert res3 == -1  # ConversationHandler.END

    res4 = await cancel_registration(update, context)
    assert res4 == -1
