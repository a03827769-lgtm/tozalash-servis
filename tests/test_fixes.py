import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

# Mock out heavy dependencies before any local imports
sys.modules["edge_tts"] = MagicMock()
sys.modules["speech_recognition"] = MagicMock()
sys.modules["pydub"] = MagicMock()
sys.modules["telegram"] = MagicMock()
sys.modules["telegram.ext"] = MagicMock()
sys.modules["telegram.constants"] = MagicMock()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# 1. Test admin_handlers.py for sqlite syntax
@pytest.mark.asyncio
async def test_admin_handlers_sqlite_syntax():
    """
    admin_handlers.py da aiomysql sintaksisi (%s) ishlatilishini tekshirish
    """
    from bot.admin_handlers import admin_worker_response

    class DummyUpdate:
        def __init__(self):
            self.callback_query = DummyQuery()

    class DummyQuery:
        def __init__(self):
            self.data = "worker_accept_123"
            self.from_user = DummyUser()

        async def answer(self):
            pass

        async def edit_message_text(self, *args, **kwargs):
            pass

    class DummyUser:
        def __init__(self):
            self.id = 999999

    # Mock database to check execute call
    with patch("bot.admin_handlers.db") as mock_db, patch("telegram.Bot") as mock_bot:
        mock_conn = MagicMock()
        mock_cursor = AsyncMock()

        mock_db.get_conn.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {"id": 1, "name": "Test Worker"}
        mock_db.update_order_status = AsyncMock()
        mock_db.assign_order_worker = AsyncMock()

        # mock bot instance
        mock_bot_instance = AsyncMock()
        mock_bot.return_value = mock_bot_instance

        update = DummyUpdate()
        context = MagicMock()

        await admin_worker_response(update, context)

        # Check what was executed
        execute_calls = mock_cursor.execute.call_args_list
        assert len(execute_calls) > 0, "execute method was not called"

        query = execute_calls[0][0][0]
        args = execute_calls[0][0][1]

        # Verify it uses %s and not ?
        assert "%s" in query, "SQL query must use aiomysql %s placeholder"
        assert "?" not in query, "SQL query must NOT use sqlite ? placeholder"
        assert args == ("999999",), "Argument passing is incorrect"


# 2. Test ai_brain.py parameter
@pytest.mark.asyncio
async def test_ai_brain_successful_patterns():
    """
    ai_brain.py da get_successful_patterns() input_data bilan chaqirilishini tekshirish
    """
    from ai_brain import ai_brain

    # Model bo'lmasa, uni yaratib qo'yamiz
    ai_brain.model = AsyncMock()

    with patch("ai_brain.db") as mock_db, patch("database.db") as mock_db_local:
        mock_db_local.get_orders_stats = AsyncMock(return_value={"total_orders": 100})
        mock_db_local.get_messages_count_today = AsyncMock(return_value=50)

        # database.py returns input_data, output_data
        mock_db_local.get_successful_patterns = AsyncMock(
            return_value=[
                {
                    "input_data": "Mijoz 1 xabari",
                    "output_data": "AI javobi 1",
                    "feedback_score": 5,
                },
                {
                    "input_data": "Mijoz 2 xabari",
                    "output_data": "AI javobi 2",
                    "feedback_score": 5,
                },
            ]
        )

        # mock GPT response
        class DummyResp:
            text = '["Yaxshilanish 1", "Yaxshilanish 2", "Yaxshilanish 3"]'

        ai_brain.model.generate_content_async.return_value = DummyResp()

        improvements = await ai_brain.self_improve()

        # Check if model was called with correctly extracted input_data
        call_args = ai_brain.model.generate_content_async.call_args[0]
        user_msg = call_args[0]

        assert (
            "Mijoz 1 xabari Mijoz 2 xabari" in user_msg
        ), "AI is not correctly extracting input_data from patterns"


# 3. Test config.py models
def test_config_models():
    """
    Config.py da model nomlari to'g'riligini tekshirish
    """
    import config

    assert config.GEMINI_MODEL in [
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.0-pro",
    ], "Invalid GEMINI_MODEL name"
    assert config.GEMINI_FLASH_MODEL in [
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.0-pro",
    ], "Invalid GEMINI_FLASH_MODEL name"
    assert "2.5" not in config.GEMINI_MODEL
    assert "2.5" not in config.GEMINI_FLASH_MODEL

    # Check ai_brain.py code directly to ensure 1.5 is used
    with open(
        os.path.join(os.path.dirname(__file__), "..", "ai_brain.py"),
        "r",
        encoding="utf-8",
    ) as f:
        content = f.read()
        assert (
            "gemini-1.5-flash" in content
        ), "ai_brain.py must use gemini-1.5-flash model"


# 4. Test ws_server.py CORS
def test_ws_server_cors():
    """
    ws_server.py da allow_origins yulduzcha (*) emasligini tekshirish
    """
    import config

    assert config.ALLOWED_ORIGINS != "*", "ALLOWED_ORIGINS must not be '*'"
    assert "tozalash.uz" in config.ALLOWED_ORIGINS, "Trusted domain missing in config"

    with open(
        os.path.join(os.path.dirname(__file__), "..", "ws_server.py"),
        "r",
        encoding="utf-8",
    ) as f:
        content = f.read()

        # We ensure that if ALLOWED_ORIGINS fails, it doesn't default to ["*"]
        assert '["*"]' not in content or (
            'origins = ["*"]' not in content
            and 'origins = [o.strip() for o in ALLOWED_ORIGINS.split(",") if o.strip()] if ALLOWED_ORIGINS else ["*"]'
            not in content
        )
        assert (
            'origins = ["https://tozalash.uz", "https://staging.tozalash.uz", "http://localhost:3000"]'
            in content
        )
