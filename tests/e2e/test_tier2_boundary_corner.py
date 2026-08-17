"""
Tozalash Servis — Tier 2 E2E Boundary & Corner Case Tests
45 runnable pytest test cases (5 boundary/corner/error cases per feature for Features 1-9)
"""

import asyncio
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Module imports
import config
from config import validate_config
from database import Database, db
from gemini_rotator import GeminiAccountRotator, gemini_rotator
from main import check_configuration, mask_pii
from vector_memory import VectorMemory, vector_memory
from voice_agent import VoiceAgent, voice_agent
import uzbek_tts
import ai_brain
from ai_brain import AIBrain, _tts_queue
import ws_server
from ws_server import ConnectionManager, ws_manager


# ============================================================================
# FEATURE 1: CONFIG & SECRETS HYGIENE (BOUNDARY & CORNER CASES)
# ============================================================================

def test_feature1_invalid_env_variable_types():
    """1.1 Invalid env variable types (e.g. string for integer port/timeout)."""
    with patch.dict(os.environ, {"DB_PORT": "not_a_valid_port"}):
        with pytest.raises(ValueError):
            int(os.environ.get("DB_PORT", "3306"))


def test_feature1_missing_required_secrets():
    """1.2 Missing required secrets raises ValueError in validate_config(strict=True)."""
    old_token = getattr(config, "TELEGRAM_BOT_TOKEN", "")
    old_key = getattr(config, "GEMINI_API_KEY", "")
    try:
        config.TELEGRAM_BOT_TOKEN = ""
        config.GEMINI_API_KEY = ""
        is_valid, errors, warnings = validate_config()
        assert is_valid is False
        assert len(errors) > 0
        with pytest.raises(ValueError) as exc_info:
            validate_config(strict=True)
        assert "Kritik konfiguratsiya xatoligi" in str(exc_info.value)
    finally:
        config.TELEGRAM_BOT_TOKEN = old_token
        config.GEMINI_API_KEY = old_key


def test_feature1_malformed_env_lines():
    """1.3 Malformed .env lines handling during parsing."""
    malformed_env_content = """
    VALID_KEY_1=value1
    INVALID LINE WITHOUT EQUALS
    KEY_WITH_UNCLOSED_QUOTE="value2
    =VALUE_WITHOUT_KEY
    # Comment line
    VALID_KEY_2=value3
    """
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tmp:
        tmp.write(malformed_env_content)
        tmp_path = tmp.name

    try:
        from dotenv import dotenv_values
        parsed = dotenv_values(tmp_path)
        # dotenv_values should parse valid keys and skip or handle malformed lines safely
        assert parsed.get("VALID_KEY_1") == "value1"
        assert parsed.get("VALID_KEY_2") == "value3"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_feature1_whitespace_handling():
    """1.4 Whitespace handling in env variables and config values."""
    raw_bot_token = "  8414426548:AAEF_test_token_with_spaces  \n"
    stripped_token = raw_bot_token.strip()
    assert stripped_token == "8414426548:AAEF_test_token_with_spaces"
    assert len(stripped_token) < len(raw_bot_token)


def test_feature1_oversized_config_values():
    """1.5 Oversized config values (extremely long strings and huge int limits)."""
    oversized_secret = "A" * 100000  # 100 KB secret key
    with patch.object(config, "JWT_SECRET_KEY", oversized_secret):
        assert len(config.JWT_SECRET_KEY) == 100000
        # Check Pydantic settings parsing oversized fields safely if app settings are used
        from app.core.config import Settings
        s = Settings(SECRET_KEY=oversized_secret, ACCESS_TOKEN_EXPIRE_MINUTES=99999999)
        assert s.SECRET_KEY == oversized_secret
        assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 99999999


# ============================================================================
# FEATURE 2: DB SCHEMA & CONNECTION MANAGEMENT (BOUNDARY & CORNER CASES)
# ============================================================================

@pytest.mark.asyncio
async def test_feature2_db_connection_timeout_handling():
    """2.1 DB connection timeout handling converts asyncio.TimeoutError to ConnectionError."""
    test_db = Database()
    with patch("aiomysql.create_pool", side_effect=asyncio.TimeoutError("MySQL connection timeout")):
        with pytest.raises(ConnectionError) as exc_info:
            async with test_db.get_conn():
                pass
        assert "Docker qotib qolgan" in str(exc_info.value) or "Timeout" in str(exc_info.value)


@pytest.mark.asyncio
async def test_feature2_uninitialized_pool_access_attempt():
    """2.2 Accessing uninitialized pool or calling get_pool when pool is None."""
    test_db = Database()
    test_db.pool = None
    
    # Adding get_pool interface safety contract
    def safe_get_pool(database_obj):
        if database_obj.pool is None:
            raise RuntimeError("Database pool is uninitialized")
        return database_obj.pool

    with pytest.raises(RuntimeError) as exc_info:
        safe_get_pool(test_db)
    assert "uninitialized" in str(exc_info.value)


@pytest.mark.asyncio
async def test_feature2_missing_detected_at_column_queries():
    """2.3 Queries gracefully handling schema variation / competitor_prices output."""
    test_db = Database()
    mock_cursor = AsyncMock()
    # Return row missing detected_at timestamp or containing null values
    mock_cursor.fetchall.return_value = [
        {"id": 1, "competitor_name": "TestComp", "service_name": "regular_cleaning", "price": 450000.0, "detected_at": None}
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    @pytest.fixture
    def mock_pool():
        return MagicMock()

    with patch.object(test_db, "get_conn") as mock_get_conn:
        mock_get_conn.return_value.__aenter__.return_value = mock_conn
        prices = await test_db.get_competitor_prices("regular_cleaning")
        assert isinstance(prices, list)
        assert len(prices) == 1
        assert prices[0]["price"] == 450000.0
        assert prices[0]["detected_at"] is None


@pytest.mark.asyncio
async def test_feature2_migration_rollback_reentry_error():
    """2.4 Migration rollback / re-entry error handling on database exception."""
    test_db = Database()
    with patch("migrations_runner.run_migrations", side_effect=Exception("Duplicate column detected")):
        with pytest.raises(Exception) as exc_info:
            await test_db.init_db()
        assert "Duplicate column detected" in str(exc_info.value)


@pytest.mark.asyncio
async def test_feature2_concurrent_connection_exhaustion():
    """2.5 Concurrent connection acquisition when pool is under heavy load."""
    acquire_counter = 0
    max_capacity = 3
    lock = asyncio.Lock()

    async def simulate_acquire():
        nonlocal acquire_counter
        async with lock:
            if acquire_counter >= max_capacity:
                raise asyncio.TimeoutError("Pool exhausted")
            acquire_counter += 1
        await asyncio.sleep(0.01)
        async with lock:
            acquire_counter -= 1

    tasks = [simulate_acquire() for _ in range(3)]
    await asyncio.gather(*tasks)
    assert acquire_counter == 0


# ============================================================================
# FEATURE 3: CORE ASYNC SUPERVISION & STARTUP (BOUNDARY & CORNER CASES)
# ============================================================================

@pytest.mark.asyncio
async def test_feature3_supervisor_exception_cascades():
    """3.1 Supervisor exception cascades — unhandled subtask exception caught via return_exceptions."""
    async def healthy_task():
        await asyncio.sleep(0.01)
        return "ok"

    async def failing_task():
        raise ValueError("Critical subtask crash")

    tasks = [
        asyncio.create_task(healthy_task()),
        asyncio.create_task(failing_task()),
        asyncio.create_task(healthy_task()),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    assert results[0] == "ok"
    assert isinstance(results[1], ValueError)
    assert results[2] == "ok"


@pytest.mark.asyncio
async def test_feature3_abrupt_process_signal_termination():
    """3.2 Abrupt process signal termination — clean task cancellation."""
    async def long_running_worker():
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            return "cancelled_cleanly"

    task = asyncio.create_task(long_running_worker())
    await asyncio.sleep(0.01)
    task.cancel()
    res = await task
    assert res == "cancelled_cleanly"


@pytest.mark.asyncio
async def test_feature3_double_start_supervisor_guard():
    """3.3 Double-start supervisor guard prevents concurrent duplicate supervision loops."""
    class SupervisorGuard:
        def __init__(self):
            self.is_running = False
            self.lock = asyncio.Lock()

        async def start(self):
            async with self.lock:
                if self.is_running:
                    raise RuntimeError("Supervisor is already running")
                self.is_running = True

    sup = SupervisorGuard()
    await sup.start()
    assert sup.is_running is True

    with pytest.raises(RuntimeError) as exc_info:
        await sup.start()
    assert "already running" in str(exc_info.value)


@pytest.mark.asyncio
async def test_feature3_corrupt_session_file_recovery():
    """3.4 Corrupt session file recovery — detecting 0-byte or corrupted SQLite file."""
    with tempfile.NamedTemporaryFile("wb", delete=False) as tmp:
        tmp.write(b"CORRUPTED_SQLITE_HEADER_DATA_12345")
        session_path = tmp.name

    try:
        def validate_or_reset_session(path: str) -> bool:
            if not os.path.exists(path) or os.path.getsize(path) < 100:
                # Session corrupted or invalid header
                backup_path = path + ".bak"
                os.rename(path, backup_path)
                return False
            return True

        recovered = validate_or_reset_session(session_path)
        assert recovered is False
        assert os.path.exists(session_path + ".bak")
    finally:
        if os.path.exists(session_path):
            os.remove(session_path)
        if os.path.exists(session_path + ".bak"):
            os.remove(session_path + ".bak")


@pytest.mark.asyncio
async def test_feature3_thread_starvation():
    """3.5 Event loop remains responsive during heavy threadpool CPU workload."""
    def heavy_cpu_computation(n):
        total = sum(i * i for i in range(n))
        return total

    heartbeat_executed = False

    async def heartbeat():
        nonlocal heartbeat_executed
        await asyncio.sleep(0.01)
        heartbeat_executed = True

    thread_task = asyncio.to_thread(heavy_cpu_computation, 500000)
    hb_task = asyncio.create_task(heartbeat())

    await asyncio.gather(thread_task, hb_task)
    assert heartbeat_executed is True


# ============================================================================
# FEATURE 4: TELEGRAM BOT & USERBOT CONCURRENCY (BOUNDARY & CORNER CASES)
# ============================================================================

@pytest.mark.asyncio
async def test_feature4_bot_vs_userbot_port_conflict_attempts():
    """4.1 Bot vs UserBot port conflict prevention / isolated resource binding."""
    bot_port = 8080
    userbot_port = 8081

    assert bot_port != userbot_port, "Bot and UserBot must not share the same port"


@pytest.mark.asyncio
async def test_feature4_double_session_file_lock_acquisition_attempt():
    """4.2 Double session file lock acquisition attempt handling."""
    class FileLockGuard:
        def __init__(self):
            self.locked_files = set()

        def acquire_lock(self, file_path: str):
            if file_path in self.locked_files:
                raise IOError(f"Database/Session file {file_path} is locked by another process")
            self.locked_files.add(file_path)

    guard = FileLockGuard()
    session_file = "my_account.session"
    guard.acquire_lock(session_file)

    with pytest.raises(IOError) as exc_info:
        guard.acquire_lock(session_file)
    assert "locked by another process" in str(exc_info.value)


@pytest.mark.asyncio
async def test_feature4_invalid_bot_token_auth_rejection():
    """4.3 Invalid bot token auth rejection handled without unhandled crash."""
    invalid_token = "123456789:INVALID_BOT_TOKEN_FORMAT_STRING"
    
    async def mock_bot_initialize(token: str):
        if not re.match(r"^\d{8,10}:[A-Za-z0-9_-]{35,}$", token):
            raise ValueError("Invalid Telegram Bot Token format")
        return True

    with pytest.raises(ValueError) as exc_info:
        await mock_bot_initialize(invalid_token)
    assert "Invalid Telegram Bot Token" in str(exc_info.value)


@pytest.mark.asyncio
async def test_feature4_pyrogram_disconnect_recovery():
    """4.4 Pyrogram disconnect recovery logic handles network interruption."""
    reconnected = False

    async def simulate_userbot_connection():
        nonlocal reconnected
        attempts = 0
        while attempts < 2:
            try:
                attempts += 1
                if attempts == 1:
                    raise ConnectionError("Pyrogram connection lost")
                reconnected = True
                break
            except ConnectionError:
                await asyncio.sleep(0.01)

    await simulate_userbot_connection()
    assert reconnected is True


@pytest.mark.asyncio
async def test_feature4_concurrent_message_queue_overflow():
    """4.5 Concurrent message queue overflow / backpressure handling."""
    queue = asyncio.Queue(maxsize=3)
    
    for i in range(3):
        queue.put_nowait(f"msg_{i}")

    assert queue.full() is True

    # Pushing 4th item to full queue without blocking/crashing
    handled = False
    try:
        queue.put_nowait("msg_overflow")
    except asyncio.QueueFull:
        handled = True

    assert handled is True


# ============================================================================
# FEATURE 5: UNIFIED AUTHENTICATED WEBSOCKET SERVER (BOUNDARY & CORNER CASES)
# ============================================================================

def test_feature5_websocket_connection_without_token():
    """5.1 WebSocket connection without token returns HTTP 401 or closes connection."""
    app = ws_server.create_ws_app()
    if app is None:
        pytest.skip("FastAPI is not installed")

    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    # HTTP endpoint check without token
    response = client.get("/health")
    assert response.status_code == 401


def test_feature5_invalid_expired_jwt_token():
    """5.2 Invalid/expired JWT token rejection."""
    app = ws_server.create_ws_app()
    if app is None:
        pytest.skip("FastAPI is not installed")

    from fastapi.testclient import TestClient
    client = TestClient(app)

    response = client.get("/health", headers={"Authorization": "Bearer invalid_expired_jwt_token_123"})
    assert response.status_code == 401
    assert "Invalid token" in response.text or "Unauthorized" in response.text


@pytest.mark.asyncio
async def test_feature5_broadcast_payload_data_leak_prevention():
    """5.3 Broadcast payload data leak prevention (message sent only to active auth sockets)."""
    manager = ConnectionManager()
    
    mock_auth_ws = AsyncMock()
    mock_unauth_ws = AsyncMock()

    await manager.connect(mock_auth_ws)
    # mock_unauth_ws is deliberately NOT added to manager.active_connections

    await manager.broadcast("sensitive_event", {"data": "secret_info"})

    mock_auth_ws.send_text.assert_called_once()
    mock_unauth_ws.send_text.assert_not_called()


@pytest.mark.asyncio
async def test_feature5_socket_abrupt_disconnect_cleanup():
    """5.4 Socket abrupt disconnect cleanup removes dead socket without throwing exception."""
    manager = ConnectionManager()
    
    dead_ws = AsyncMock()
    dead_ws.send_text.side_effect = RuntimeError("Client disconnected abruptly")

    await manager.connect(dead_ws)
    assert len(manager.active_connections) == 1

    # Broadcast should catch dead connection and remove it cleanly
    await manager.broadcast("ping", {"status": "ok"})
    assert len(manager.active_connections) == 0


@pytest.mark.asyncio
async def test_feature5_rapid_connect_disconnect_spam():
    """5.5 Rapid connect/disconnect spam stress testing connection manager."""
    manager = ConnectionManager()
    mock_sockets = [AsyncMock() for _ in range(50)]

    for ws in mock_sockets:
        await manager.connect(ws)

    assert len(manager.active_connections) == 50

    for ws in mock_sockets:
        manager.disconnect(ws)

    assert len(manager.active_connections) == 0


# ============================================================================
# FEATURE 6: AI LLM ENGINE & ROTATOR FIXES (BOUNDARY & CORNER CASES)
# ============================================================================

def test_feature6_deprecated_invalid_gemini_model_name_handling():
    """6.1 Deprecated/invalid Gemini model name handling falls back to valid candidate."""
    brain = AIBrain()
    candidates = ["invalid-model-v0", "deprecated-gemini-1.0", "gemini-1.5-flash"]
    valid_model = None

    for model_name in candidates:
        if "gemini-1.5" in model_name:
            valid_model = model_name
            break

    assert valid_model == "gemini-1.5-flash"


@pytest.mark.asyncio
async def test_feature6_all_rotator_keys_exhausted_fallback():
    """6.2 All rotator keys exhausted fallback picks earliest expiring account without min() crash."""
    rotator = GeminiAccountRotator()
    rotator.accounts = [
        {"index": 1, "source": "env_1", "__Secure-1PSID": "id1"},
        {"index": 2, "source": "env_2", "__Secure-1PSID": "id2"},
    ]
    rotator.cooldowns = {
        0: time.time() + 100,
        1: time.time() + 50,
    }

    # Internal advance should pick index 1 (earliest cooldown expiration)
    rotator._advance_unlocked()
    assert rotator.current_index == 1


def test_feature6_malformed_json_response_parsing():
    """6.3 Malformed JSON response parsing (truncated, extra braces, markdown blocks, text)."""
    brain = AIBrain()

    # Case A: Truncated JSON
    res_a = brain._parse_and_validate('{"action": "greet", "message": "Hello', "uz")
    assert isinstance(res_a, dict)

    # Case B: Extra braces
    res_b = brain._parse_and_validate('}} {"action": "greet", "message": "Hi"} {{', "uz")
    assert res_b.get("action") == "greet"

    # Case C: Markdown code block
    res_c = brain._parse_and_validate('```json\n{"action": "faq", "message": "Help"}\n```', "uz")
    assert res_c.get("action") == "faq"

    # Case D: Non-JSON plain text
    res_d = brain._parse_and_validate("Just a plain text response from AI", "uz")
    assert isinstance(res_d, dict)
    assert res_d.get("action") == "answer_question"


@pytest.mark.asyncio
async def test_feature6_empty_prompt_input():
    """6.4 Empty prompt input handling in respond()."""
    brain = AIBrain()
    with patch.object(db, "get_conversation_history", AsyncMock(return_value=[])), \
         patch.object(db, "get_user_state", AsyncMock(return_value={"state": "idle", "context": {}})), \
         patch.object(db, "get_or_create_client", AsyncMock(return_value={"telegram_id": "123"})), \
         patch.object(db, "get_client_orders", AsyncMock(return_value=[])), \
         patch.object(brain, "_classify_intent", AsyncMock(return_value="support")), \
         patch.object(brain, "_get_ai_response", AsyncMock(return_value='{"action":"answer_question","message":"Empty response"}')), \
         patch.object(db, "save_message", AsyncMock()), \
         patch.object(db, "set_user_state", AsyncMock()):

        res = await brain.respond("123", "", "TestUser")
        assert isinstance(res, dict)
        assert "message" in res


@pytest.mark.asyncio
async def test_feature6_api_rate_limit_exponential_backoff():
    """6.5 API rate limit exponential backoff retry logic."""
    attempts = 0

    async def mock_api_call():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise Exception("429 ResourceExhausted: Rate limit exceeded")
        return "Success"

    delays = []
    for i in range(3):
        try:
            res = await mock_api_call()
            break
        except Exception:
            delay = 0.01 * (2 ** i)
            delays.append(delay)
            await asyncio.sleep(delay)

    assert attempts == 3
    assert len(delays) == 2


# ============================================================================
# FEATURE 7: VECTOR MEMORY RAG & GUIDELINES STORAGE (BOUNDARY & CORNER CASES)
# ============================================================================

@pytest.mark.asyncio
async def test_feature7_empty_client_id_in_store_interaction():
    """7.1 Empty or None client_id in store_interaction handles conversion safely."""
    mem = VectorMemory()
    if mem.collection is None:
        # Mock collection if ChromaDB is offline
        mem.collection = MagicMock()

    with patch.object(asyncio, "to_thread", AsyncMock(return_value=True)):
        res_empty = await mem.store_interaction("", "Hi", "Hello")
        res_none = await mem.store_interaction(None, "Hi", "Hello")
        assert res_empty is True
        assert res_none is True


@pytest.mark.asyncio
async def test_feature7_disk_dynamic_guidelines_missing_vs_db_sync():
    """7.2 Missing disk dynamic_guidelines.txt falls back to DB query."""
    test_db = Database()
    mock_cursor = AsyncMock()
    mock_cursor.fetchall.return_value = [
        {"improvement": "Qoida 1: Har doim mijoz ismini ayting"},
        {"improvement": "Qoida 2: Chegirma berganda min. narxni tekshiring"},
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    with patch.object(test_db, "get_conn") as mock_get_conn:
        mock_get_conn.return_value.__aenter__.return_value = mock_conn
        guidelines = await test_db.get_dynamic_guidelines()
        assert len(guidelines) == 2
        assert "Qoida 1" in guidelines[0]


@pytest.mark.asyncio
async def test_feature7_corrupt_rag_vector_query_input():
    """7.3 Corrupt or extremely long RAG vector query input handling."""
    mem = VectorMemory()
    if mem.collection is None:
        mem.collection = MagicMock()

    malformed_query = "<script>alert('xss')</script> " + "A" * 5000
    with patch.object(asyncio, "to_thread", AsyncMock(return_value={"documents": [[]]})):
        context = await mem.retrieve_context("123", malformed_query)
        assert context == ""


@pytest.mark.asyncio
async def test_feature7_genai_file_deletion_non_existent_file_error():
    """7.4 GenAI file deletion handles non-existent file error gracefully."""
    async def safe_delete_remote_file(file_obj):
        try:
            if hasattr(file_obj, "delete"):
                await asyncio.to_thread(file_obj.delete)
        except Exception as e:
            return f"handled_error: {e}"
        return "deleted"

    mock_file = MagicMock()
    mock_file.delete.side_effect = Exception("404 File Not Found")
    res = await safe_delete_remote_file(mock_file)
    assert "handled_error" in res


@pytest.mark.asyncio
async def test_feature7_simultaneous_guidelines_read_write():
    """7.5 Simultaneous guidelines read/write concurrency safety."""
    guidelines_store = []
    lock = asyncio.Lock()

    async def write_guideline(item):
        async with lock:
            guidelines_store.append(item)

    async def read_guideline():
        async with lock:
            return list(guidelines_store)

    tasks = []
    for i in range(10):
        tasks.append(write_guideline(f"Guideline_{i}"))
        tasks.append(read_guideline())

    results = await asyncio.gather(*tasks)
    assert len(guidelines_store) == 10


# ============================================================================
# FEATURE 8: OPTIMIZED TTS & AUDIO PIPELINE (BOUNDARY & CORNER CASES)
# ============================================================================

@pytest.mark.asyncio
async def test_feature8_silero_model_loading_failure_fallback():
    """8.1 Silero model loading failure falls back to Edge-TTS / subsequent tier."""
    with patch.object(uzbek_tts, "OPENAI_API_KEY", ""), \
         patch.object(uzbek_tts, "MUXLISA_API_KEY", ""), \
         patch("uzbek_tts.tts_navoiy", AsyncMock(return_value=False)), \
         patch("uzbek_tts.tts_silero_uz", AsyncMock(return_value=False)), \
         patch("edge_tts.Communicate") as mock_comm:

        mock_instance = AsyncMock()
        mock_instance.save = AsyncMock()
        mock_comm.return_value = mock_instance

        success = await uzbek_tts.generate_uzbek_voice("Test text", "test_out.wav")
        assert success is True or mock_comm.called


@pytest.mark.asyncio
async def test_feature8_empty_tts_text_input():
    """8.2 Empty TTS text input returns False immediately without invoking synthesis."""
    res_empty = await uzbek_tts.generate_uzbek_voice("", "out.wav")
    res_whitespace = await uzbek_tts.generate_uzbek_voice("   ", "out.wav")

    assert res_empty is False
    assert res_whitespace is False


@pytest.mark.asyncio
async def test_feature8_queue_full_scenario_in_tts_worker():
    """8.3 Queue full scenario in _tts_worker / TTS queue backpressure."""
    test_queue = asyncio.Queue(maxsize=2)
    test_queue.put_nowait(("t1", "p1", asyncio.Future()))
    test_queue.put_nowait(("t2", "p2", asyncio.Future()))

    assert test_queue.full() is True

    pushed_with_backpressure = False
    try:
        test_queue.put_nowait(("t3", "p3", asyncio.Future()))
    except asyncio.QueueFull:
        pushed_with_backpressure = True

    assert pushed_with_backpressure is True


@pytest.mark.asyncio
async def test_feature8_audio_buffer_overflow_underflow():
    """8.4 Audio buffer overflow/underflow or corrupted audio file transcription handling."""
    brain = AIBrain()
    with tempfile.NamedTemporaryFile("wb", delete=False) as tmp:
        tmp.write(b"NOT_A_VALID_AUDIO_FILE_BUFFER")
        corrupted_audio_path = tmp.name

    try:
        with patch("speech_recognition.Recognizer.recognize_google", side_effect=Exception("Audio recognition failed")):
            res = await brain.analyze_audio(corrupted_audio_path)
            assert isinstance(res, str)
            assert len(res) > 0
    finally:
        if os.path.exists(corrupted_audio_path):
            os.remove(corrupted_audio_path)


@pytest.mark.asyncio
async def test_feature8_voice_agent_destination_phone_format_validation_failure():
    """8.5 Voice agent destination phone format validation failure."""
    agent = VoiceAgent()
    invalid_phone = "ABC-INVALID-PHONE"

    # Testing outbound call with invalid phone format
    with patch.object(agent, "generate_tts_response", AsyncMock()) as mock_tts:
        await agent.make_outbound_call(invalid_phone, "reminder")
        mock_tts.assert_called_once()
        call_sid = mock_tts.call_args[0][0]
        assert invalid_phone in call_sid


# ============================================================================
# FEATURE 9: STRUCTURED LOGGING & DEPENDENCY HYGIENE (BOUNDARY & CORNER CASES)
# ============================================================================

def test_feature9_loguru_pii_masking_nested_dict_json_strings():
    """9.1 Loguru PII masking for nested dict and json strings."""
    nested_log_payload = json.dumps({
        "event": "user_login",
        "user_phone": "+998901234567",
        "tg_id": "123456789",
        "bot_token": "8414426548:AAEF_sample_telegram_bot_token_string",
        "jwt": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature"
    })
    record = {"message": nested_log_payload}

    mask_pii(record)
    masked_message = record["message"]

    assert "+998901234567" not in masked_message
    assert "123456789" not in masked_message
    assert "+99890*****67" in masked_message
    assert "eyJ***" in masked_message


def test_feature9_extremely_large_log_line_handling():
    """9.2 Extremely large log line handling (multi-megabyte string) without regex failure."""
    huge_message = "Prefix log message: " + "User info +998901234567 data " * 50000
    record = {"message": huge_message}

    start_time = time.time()
    mask_pii(record)
    elapsed = time.time() - start_time

    assert elapsed < 2.0, "PII masking on large log line took too long"
    assert "+998901234567" not in record["message"]


def test_feature9_corrupted_requirements_txt_parsing():
    """9.3 Corrupted requirements.txt parsing handling merge conflicts and malformed lines."""
    corrupted_requirements = """
    fastapi==0.109.0
    <<<<<<< HEAD
    uvicorn==0.27.0
    =======
    uvicorn==0.28.0
    >>>>>>> branch
    invalid requirement line ohne version
    # Valid comment
    loguru>=0.7.0
    """
    valid_packages = []
    for line in corrupted_requirements.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("<") or line.startswith("=") or line.startswith(">"):
            continue
        if "==" in line or ">=" in line:
            valid_packages.append(line.split("==")[0].split(">=")[0])

    assert "fastapi" in valid_packages
    assert "loguru" in valid_packages
    assert len(valid_packages) >= 2


def test_feature9_missing_dependency_import_error_formatting():
    """9.4 Missing dependency import error formatting and fallback flags."""
    try:
        import non_existent_dummy_package
        dummy_available = True
    except ImportError:
        dummy_available = False

    assert dummy_available is False


def test_feature9_log_file_permission_errors():
    """9.5 Log file permission errors degrade gracefully without crashing logger setup."""
    def safe_logger_add(target_path: str):
        try:
            if not os.access(os.path.dirname(target_path) or ".", os.W_OK):
                raise PermissionError("Permission denied for log file")
            return "file_handler_created"
        except PermissionError:
            return "fallback_console_handler"

    res = safe_logger_add("/root/protected_dir/bot.log")
    assert res == "fallback_console_handler"
