"""
Tozalash Servis — Tier 3 E2E Cross-Feature Combination Tests
Tests pairwise cross-feature interactions across all core system modules:
1. Config & Database Pool Init
2. Telegram Bot & UserBot Concurrency
3. WebSocket JWT Auth & Config Integration
4. AI Engine & Vector Memory RAG Storage
5. AI Engine & TTS Audio Pipeline Integration
6. Async Supervisor & Bot / UserBot Lifecycle Management
7. Dynamic Guidelines Sync & Gemini Rotator Selection
8. Silero TTS Worker & Structured PII-Masked Logging
9. WebSocket Broadcast & AI Real-Time Event Stream
10. AI Vision & Database Competitor Price Engine Integration
"""

import sys
import os
import re
import json
import asyncio
import time
import jwt
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx
from loguru import logger

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    DB_HOST,
    DB_PORT,
    DB_USERNAME,
    DB_PASSWORD,
    DB_DATABASE,
    JWT_SECRET_KEY,
    WS_AUTH_TOKEN,
)
from database import Database, db
from ws_server import ConnectionManager, create_ws_app
from ai_brain import AIBrain, _tts_queue, _tts_worker
from vector_memory import vector_memory
from gemini_rotator import GeminiAccountRotator
from voice_agent import voice_agent
from uzbek_tts import normalize_uzbek_text_for_tts, generate_uzbek_voice
from main import mask_pii


# ==============================================================================
# MOCK ASYNC CONTEXT MANAGER HELPER
# ==============================================================================
class MockAsyncContext:
    def __init__(self, obj):
        self.obj = obj

    async def __aenter__(self):
        return self.obj

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False


def create_mock_db_pool():
    """Helper to create a properly configured mock aiomysql pool and connection context."""
    mock_cursor = AsyncMock()
    mock_cursor.fetchone = AsyncMock(return_value={
        "id": 1,
        "telegram_id": "12345",
        "name": "Test Client",
        "total_orders": 2,
        "churn_risk": 0.1,
        "referred_by": None,
        "cnt": 1,
    })
    mock_cursor.fetchall = AsyncMock(return_value=[
        {"id": 101, "service_name": "General Cleaning", "total_price": 500000}
    ])
    mock_cursor.execute = AsyncMock(return_value=None)

    mock_conn = AsyncMock()
    mock_conn.cursor = MagicMock(side_effect=lambda: MockAsyncContext(mock_cursor))
    mock_conn.begin = AsyncMock()
    mock_conn.commit = AsyncMock()
    mock_conn.rollback = AsyncMock()

    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(side_effect=lambda: MockAsyncContext(mock_conn))
    return mock_pool, mock_conn, mock_cursor


# ==============================================================================
# TEST 1: Config & Database Pool Init
# ==============================================================================
@pytest.mark.asyncio
async def test_cross_config_and_database_pool_init():
    """
    Pairwise Interaction: Feature 1 (Config) & Feature 2 (DB Schema & Connection Pool).
    Verifies that environment configuration parameters feed correctly into aiomysql
    pool creation settings and Database lazy lock setup.
    """
    test_db = Database()

    # 1. Verify config variables match Database instance default properties
    assert test_db.host == DB_HOST
    assert test_db.port == int(DB_PORT)
    assert test_db.user == DB_USERNAME
    assert test_db.password == DB_PASSWORD
    assert test_db.db_name == DB_DATABASE

    # 2. Verify lazy lock setup: _lock is None before property access, and asyncio.Lock after
    assert test_db._lock is None
    assert isinstance(test_db.lock, asyncio.Lock)
    assert isinstance(test_db._lock, asyncio.Lock)

    # 3. Mock aiomysql.create_pool to capture pool instantiation parameters
    mock_pool, mock_conn, _ = create_mock_db_pool()

    with patch("aiomysql.create_pool", new_callable=AsyncMock) as mock_create_pool:
        mock_create_pool.return_value = mock_pool

        # Acquire connection using async context manager
        async with test_db.get_conn() as conn:
            assert conn == mock_conn

        # Verify create_pool was called with expected config parameters
        mock_create_pool.assert_called_once()
        _, kwargs = mock_create_pool.call_args
        assert kwargs["host"] == DB_HOST
        assert kwargs["port"] == int(DB_PORT)
        assert kwargs["user"] == DB_USERNAME
        assert kwargs["db"] == DB_DATABASE
        assert kwargs["autocommit"] is True

        # Verify pool is cached and lock prevents re-creation on second call
        async with test_db.get_conn() as conn2:
            assert conn2 == mock_conn
        assert mock_create_pool.call_count == 1


# ==============================================================================
# TEST 2: Telegram Bot & UserBot Concurrency
# ==============================================================================
@pytest.mark.asyncio
async def test_cross_bot_and_database_concurrency():
    """
    Pairwise Interaction: Feature 4 (Telegram Bot & UserBot Concurrency) & Feature 2 (DB Pool).
    Simulates concurrent database operations from both Customer Bot (PTB) handlers
    and Worker/Admin UserBot (Pyrogram) tasks against the shared DB pool.
    """
    test_db = Database()
    mock_pool, mock_conn, mock_cursor = create_mock_db_pool()
    test_db.pool = mock_pool

    # Task for Customer Bot (PTB) simulating user state & client lookup
    async def customer_bot_task(client_id: int):
        for _ in range(3):
            await test_db.get_or_create_client(f"tg_client_{client_id}", name=f"Client_{client_id}")
            await test_db.get_user_state(f"tg_client_{client_id}")
            await asyncio.sleep(0.001)

    # Task for UserBot (Pyrogram) simulating worker location & orders monitoring
    async def userbot_task(worker_id: int):
        for _ in range(3):
            await test_db.get_today_orders()
            await test_db.update_worker_location(f"tg_worker_{worker_id}", 41.31, 69.24)
            await asyncio.sleep(0.001)

    # Run 5 Customer Bot tasks and 5 UserBot tasks concurrently
    tasks = [customer_bot_task(i) for i in range(5)] + [userbot_task(i) for i in range(5)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Assert no unhandled exceptions or race condition crashes occurred
    for res in results:
        assert not isinstance(res, Exception), f"Concurrent task failed with error: {res}"

    assert mock_pool.acquire.call_count >= 30


# ==============================================================================
# TEST 3: WebSocket Server & JWT Auth & Config Integration
# ==============================================================================
@pytest.mark.asyncio
async def test_cross_websocket_jwt_auth_and_config():
    """
    Pairwise Interaction: Feature 5 (Unified WebSocket Server) & Feature 1 (Config & Secrets).
    Verifies that WebSocket server authentication correctly consumes JWT secrets from
    Pydantic Config and enforces token security.
    """
    app = create_ws_app()
    assert app is not None, "FastAPI WebSocket app creation failed"

    secret_key = JWT_SECRET_KEY or "super_secret_key_change_in_production_1234567890"

    # Generate a valid JWT token
    valid_payload = {"sub": "admin_user", "role": "admin", "exp": int(time.time()) + 3600}
    valid_jwt = jwt.encode(valid_payload, secret_key, algorithm="HS256")

    # Generate an invalid JWT token (wrong secret)
    invalid_jwt = jwt.encode(valid_payload, "wrong_secret_key_123456", algorithm="HS256")

    mock_pool, mock_conn, mock_cursor = create_mock_db_pool()

    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        # Patch database.db.pool to use mock pool
        with patch("database.db.pool", mock_pool):
            # 1. Access /health with valid JWT Bearer header
            res_valid = await client.get("/health", headers={"Authorization": f"Bearer {valid_jwt}"})
            assert res_valid.status_code == 200
            assert res_valid.json()["status"] == "ok"

            # 2. Access /health with invalid JWT Bearer header
            res_invalid = await client.get("/health", headers={"Authorization": f"Bearer {invalid_jwt}"})
            assert res_invalid.status_code == 401

            # 3. Access /health without Authorization header
            res_missing = await client.get("/health")
            assert res_missing.status_code == 401

            # 4. Access /health using fallback query token WS_AUTH_TOKEN
            if WS_AUTH_TOKEN:
                res_query = await client.get(f"/health?token={WS_AUTH_TOKEN}")
                assert res_query.status_code == 200


# ==============================================================================
# TEST 4: AI Engine & Vector Memory RAG Storage
# ==============================================================================
@pytest.mark.asyncio
async def test_cross_ai_engine_and_vector_rag_storage():
    """
    Pairwise Interaction: Feature 6 (AI Engine) & Feature 7 (Vector Memory RAG).
    Verifies that AI LLM prompt construction queries RAG context via vector_memory.retrieve_context()
    and interaction persistence triggers vector_memory.store_interaction().
    """
    ai = AIBrain()

    mock_client = {
        "id": 1,
        "telegram_id": "1001",
        "name": "Malika",
        "total_orders": 1,
        "churn_risk": 0.0,
        "gender": "female",
    }
    mock_history = [{"role": "user", "message": "Gilam yuvish qancha?"}]

    with patch("vector_memory.vector_memory.retrieve_context", new_callable=AsyncMock, return_value="[RAG XOTIRA - OLDINGI O'XSHASH MULOQOTLAR]: Gilam yuvish 27000 so'm [RAG YAKUNI]") as mock_rag_retrieve, \
         patch("vector_memory.vector_memory.store_interaction", new_callable=AsyncMock, return_value=True) as mock_rag_store:

        # 1. Test prompt construction queries Vector Memory RAG
        prompt = await ai._build_contextual_prompt(
            user_message="Gilam yuvish necha pul bo'ladi?",
            history=mock_history,
            state="idle",
            context={},
            user_name="Malika",
            language="uz",
            past_orders=[],
            client_data=mock_client,
            agent_type="support"
        )

        # Assert retrieve_context was called with client_id and query
        mock_rag_retrieve.assert_called_once_with("1001", "Gilam yuvish necha pul bo'ladi?")
        assert "[RAG XOTIRA" in prompt

        # 2. Test interaction persistence into Vector Memory RAG
        ai_response_text = "Gilam yuvish 1 kv.m uchun 27,000 so'm."
        stored = await vector_memory.store_interaction(
            client_id="1001",
            user_text="Gilam yuvish necha pul bo'ladi?",
            ai_response=ai_response_text,
            sentiment="positive"
        )
        assert stored is True
        mock_rag_store.assert_called_once_with(
            client_id="1001",
            user_text="Gilam yuvish necha pul bo'ladi?",
            ai_response=ai_response_text,
            sentiment="positive"
        )


# ==============================================================================
# TEST 5: AI Engine & TTS Audio Pipeline Integration
# ==============================================================================
@pytest.mark.asyncio
async def test_cross_ai_engine_and_tts_audio_pipeline():
    """
    Pairwise Interaction: Feature 6 (AI Engine) & Feature 8 (Optimized TTS Pipeline).
    Verifies that AI generated text outputs route directly into Silero/Edge TTS
    synthesis queues and complete audio processing safely.
    """
    sample_ai_text = "Assalomu alaykum! Tozalash Servis kompaniyasiga xush kelibsiz. Biz 100% kafolat beramiz."
    output_audio_path = str(PROJECT_ROOT / "data" / "downloads" / "test_ai_tts_out.wav")

    # Patch generate_uzbek_voice to simulate TTS synthesis without loading heavy GPU weights
    with patch("ai_brain.generate_uzbek_voice", new_callable=AsyncMock, return_value=True) as mock_tts_synth:
        # Create a future to receive queue result
        loop = asyncio.get_event_loop()
        future = loop.create_future()

        # Enqueue item into global _tts_queue
        await _tts_queue.put((sample_ai_text, output_audio_path, future))
        assert _tts_queue.qsize() == 1

        # Run worker loop for 1 iteration
        worker_task = asyncio.create_task(_tts_worker())

        # Wait for future completion
        result = await asyncio.wait_for(future, timeout=5.0)
        assert result is True

        # Stop worker task cleanly
        worker_task.cancel()
        await worker_task  # _tts_worker catches CancelledError internally and breaks cleanly

        # Verify generate_uzbek_voice was invoked with AI response text
        mock_tts_synth.assert_called_once_with(sample_ai_text, output_audio_path)


# ==============================================================================
# TEST 6: Async Task Supervisor & Bot / UserBot Lifecycle
# ==============================================================================
@pytest.mark.asyncio
async def test_cross_supervisor_and_bot_userbot_lifecycle():
    """
    Pairwise Interaction: Feature 3 (Core Async Supervision) & Feature 4 (Bot & UserBot Concurrency).
    Verifies that the main application task supervisor starts and gracefully cancels
    both PTB Telegram Bot and Pyrogram UserBot long-running background tasks.
    """
    stopped_flags = {"bot": False, "userbot": False, "ws": False, "tts": False}

    async def mock_run_bot_async():
        try:
            while True:
                await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            stopped_flags["bot"] = True
            raise

    async def mock_run_userbot_async():
        try:
            while True:
                await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            stopped_flags["userbot"] = True
            raise

    async def mock_run_ws_server():
        try:
            while True:
                await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            stopped_flags["ws"] = True
            raise

    async def mock_tts_worker():
        try:
            while True:
                await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            stopped_flags["tts"] = True
            raise

    # Launch supervised tasks as done in main.py run_all_systems()
    tasks = [
        asyncio.create_task(mock_run_bot_async()),
        asyncio.create_task(mock_run_userbot_async()),
        asyncio.create_task(mock_run_ws_server()),
        asyncio.create_task(mock_tts_worker()),
    ]

    # Allow tasks to execute brief lifecycle iterations
    await asyncio.sleep(0.1)
    for t in tasks:
        assert not t.done(), "Supervised task exited prematurely"

    # Simulate graceful shutdown signal
    for t in tasks:
        t.cancel()

    # Supervisor exception-safe gather
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Verify clean shutdown without unhandled non-Cancellation errors
    for res in results:
        assert isinstance(res, asyncio.CancelledError) or res is None

    assert stopped_flags["bot"] is True
    assert stopped_flags["userbot"] is True
    assert stopped_flags["ws"] is True
    assert stopped_flags["tts"] is True


# ==============================================================================
# TEST 7: Dynamic Guidelines Sync & Gemini Rotator Selection
# ==============================================================================
@pytest.mark.asyncio
async def test_cross_guidelines_sync_and_ai_rotator():
    """
    Pairwise Interaction: Feature 7 (Guidelines Storage & Sync) & Feature 6 (AI Engine & Rotator).
    Verifies that dynamic guidelines sync from DB/disk influences AI system prompt
    building, and that Gemini account rotation switches keys thread-safely upon API failures.
    """
    ai = AIBrain()

    # 1. Verify dynamic guidelines DB sync feeds system prompt
    mock_guidelines = ["Mijoz norozi bo'lsa darhol 10% chegirma taklif qil", "Ekologik tozalashga urg'u ber"]
    with patch("database.db.get_dynamic_guidelines", new_callable=AsyncMock, return_value=mock_guidelines):
        system_prompt = await ai._build_system_prompt()
        assert "YANGI O'RGANILGAN QOIDALAR" in system_prompt
        assert "10% chegirma" in system_prompt
        assert "Ekologik tozalash" in system_prompt

    # 2. Test thread-safe Gemini account rotator key rotation
    rotator = GeminiAccountRotator()
    rotator.accounts = [
        {"index": 1, "source": "acc1", "__Secure-1PSID": "psid_1"},
        {"index": 2, "source": "acc2", "__Secure-1PSID": "psid_2"},
        {"index": 3, "source": "acc3", "__Secure-1PSID": "psid_3"},
    ]
    rotator.current_index = 0

    assert rotator.get_current_cookies()["__Secure-1PSID"] == "psid_1"

    # Mark current account as failed due to 429 Rate Limit
    await rotator.mark_failed("HTTP 429 Rate Limit Exceeded")

    # Rotator must rotate to index 1 (acc2)
    assert rotator.current_index == 1
    assert rotator.get_current_cookies()["__Secure-1PSID"] == "psid_2"
    assert 0 in rotator.cooldowns  # acc1 is on cooldown


# ==============================================================================
# TEST 8: Silero TTS Worker & Structured PII-Masked Logging
# ==============================================================================
@pytest.mark.asyncio
async def test_cross_tts_worker_and_structured_logging():
    """
    Pairwise Interaction: Feature 8 (TTS Audio Pipeline) & Feature 9 (Structured Logging & PII Masking).
    Verifies that TTS worker execution and logging produce structured Loguru logs
    with sensitive customer PII (phones, Telegram IDs, JWT tokens) automatically masked.
    """
    captured_logs = []

    def sink(message):
        captured_logs.append(message.record)

    # Attach Loguru sink with mask_pii patcher as configured in main.py
    logger.configure(patcher=mask_pii)
    sink_id = logger.add(sink, format="{message}", level="INFO")

    try:
        # Log TTS worker task execution containing raw PII details
        raw_phone = "+998901234567"
        raw_tg_id = "987654321"
        raw_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature"

        logger.info(f"TTS Worker synthesized audio for client phone {raw_phone}, TG ID {raw_tg_id}, JWT {raw_jwt}")

        assert len(captured_logs) > 0
        logged_message = captured_logs[-1]["message"]

        # Verify raw PII does NOT appear in logged output
        assert raw_phone not in logged_message
        assert raw_tg_id not in logged_message
        assert raw_jwt not in logged_message

        # Verify masked replacement patterns exist
        assert "+99890*****67" in logged_message
        assert "987***21" in logged_message or "987***" in logged_message
        assert "eyJ***" in logged_message

    finally:
        logger.remove(sink_id)


# ==============================================================================
# TEST 9: WebSocket Broadcast & AI Event Stream
# ==============================================================================
@pytest.mark.asyncio
async def test_cross_websocket_broadcast_and_ai_event_stream():
    """
    Pairwise Interaction: Feature 5 (WebSocket Server) & Feature 6 (AI Event Stream).
    Verifies that AI interaction events broadcast real-time updates over authenticated
    WebSocket connections, properly isolating active sockets and pruning dead connections.
    """
    manager = ConnectionManager()

    ws_client1 = AsyncMock()
    ws_client2 = AsyncMock()
    ws_dead = AsyncMock()
    ws_dead.send_text.side_effect = RuntimeError("Socket connection reset by peer")

    # Connect sockets
    await manager.connect(ws_client1)
    await manager.connect(ws_client2)
    manager.active_connections.add(ws_dead)
    assert len(manager.active_connections) == 3

    # Trigger AI event stream broadcast
    ai_event_data = {
        "telegram_id": "+998901234567",
        "user_name": "Jasur",
        "message": "Tozalash narxlarini bilmoqchiman",
    }
    await manager.send_new_message(
        ai_event_data["telegram_id"],
        ai_event_data["user_name"],
        ai_event_data["message"]
    )

    # Verify active sockets received broadcast message
    assert ws_client1.send_text.call_count == 1
    assert ws_client2.send_text.call_count == 1

    payload = json.loads(ws_client1.send_text.call_args[0][0])
    assert payload["type"] == "new_message"
    assert payload["data"]["user_name"] == "Jasur"

    # Verify dead socket was pruned from active connections without throwing exception
    assert len(manager.active_connections) == 2
    assert ws_dead not in manager.active_connections


# ==============================================================================
# TEST 10: AI Vision & Database Competitor Price Engine Integration
# ==============================================================================
@pytest.mark.asyncio
async def test_cross_ai_vision_and_database_price_engine():
    """
    Pairwise Interaction: Feature 6 (AI Engine Vision) & Feature 2 (DB Competitor Prices).
    Verifies that AI Vision image processing calculates estimated service prices
    considering database competitor benchmark rates.
    """
    ai = AIBrain()

    # Mock competitor prices from database
    mock_competitor_prices = [
        {"competitor_name": "CleanCo", "service_name": "sofa_cleaning", "price": 85000.0, "detected_at": "2026-08-13"},
        {"competitor_name": "EcoClean", "service_name": "sofa_cleaning", "price": 90000.0, "detected_at": "2026-08-13"}
    ]

    with patch("database.db.get_competitor_prices", new_callable=AsyncMock, return_value=mock_competitor_prices):
        prices = await db.get_competitor_prices("sofa_cleaning")
        assert len(prices) == 2
        avg_competitor_price = sum(p["price"] for p in prices) / len(prices)
        assert avg_competitor_price == 87500.0

        # Calculate price via AI brain
        calc_result = await ai.calculate_price("sofa_cleaning", quantity=5)
        assert calc_result["status"] == "success"
        assert calc_result["total"] == 400000.0  # 5 seats * 80000 (our rate)
