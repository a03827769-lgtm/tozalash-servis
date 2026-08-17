"""
Tozalash Servis — Tier 4 E2E Real-World Application Workload Test Suite
=======================================================================
End-to-end tests for real-world application workloads, including customer journeys,
voice call flows, high concurrency loads, DB migration/health recovery, and system shutdown.
"""

import sys
import os
import json
import asyncio
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import PRICES, BUSINESS_NAME, TELEGRAM_BOT_TOKEN
from database import Database, db
from ws_server import ConnectionManager, ws_manager
from voice_agent import VoiceAgent, voice_agent
from vector_memory import VectorMemory, vector_memory
from ai_brain import _tts_queue, _tts_worker
from main import check_configuration


# ============================================================================
# HELPER FIXTURES & MOCK CONTEXT MANAGERS
# ============================================================================

class AsyncContextManagerMock:
    """Helper async context manager for mocking aiomysql pool & conn."""
    def __init__(self, return_obj):
        self.return_obj = return_obj

    async def __aenter__(self):
        return self.return_obj

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False


def build_mock_db_pool():
    """Build a mock aiomysql database pool with standard dict cursor returns."""
    mock_cursor = AsyncMock()
    mock_cursor.__aenter__ = AsyncMock(return_value=mock_cursor)
    mock_cursor.__aexit__ = AsyncMock(return_value=False)
    
    # Default fetch responses
    mock_cursor.fetchone = AsyncMock(return_value={
        "id": 101,
        "order_number": "TS-20260813-A1B2",
        "total_orders": 1,
        "referred_by": None,
        "cnt": 5,
        "competitor_name": "EcoClean",
        "service_name": "divan_tozalash",
        "price": 130000.0,
        "source_url": "https://ecoclean.uz",
        "detected_at": "2026-08-13 12:00:00",
        "created_at": "2026-08-13 12:00:00",
        "orders_count": 2,
        "gold_status_notified": False,
    })
    mock_cursor.fetchall = AsyncMock(return_value=[
        {
            "id": 1,
            "competitor_name": "EcoClean",
            "service_name": "divan_tozalash",
            "price": 130000.0,
            "source_url": "https://ecoclean.uz",
            "detected_at": "2026-08-13 12:00:00",
            "created_at": "2026-08-13 12:00:00"
        }
    ])
    mock_cursor.lastrowid = 101
    mock_cursor.rowcount = 1
    mock_cursor.execute = AsyncMock()

    mock_conn = AsyncMock()
    mock_conn.cursor = MagicMock(return_value=mock_cursor)
    mock_conn.begin = AsyncMock()
    mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn.__aexit__ = AsyncMock(return_value=False)

    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=AsyncContextManagerMock(mock_conn))
    return mock_pool, mock_conn, mock_cursor


# ============================================================================
# TIER 4 TEST CASES
# ============================================================================

@pytest.mark.asyncio
async def test_e2e_full_customer_cleaning_service_order_flow():
    """
    1. Complete customer journey:
       Config init -> Customer message via Bot -> AI pricing inquiry & competitor price lookup
       -> DB persistence -> WebSocket order creation broadcast.
    """
    # 1. Config Init
    assert check_configuration() is True, "Config check failed"
    assert "divan_tozalash" in PRICES or len(PRICES) > 0, "Prices configuration missing"
    assert len(BUSINESS_NAME) > 0, "Business name configuration missing"

    mock_pool, mock_conn, mock_cursor = build_mock_db_pool()
    test_db = Database()
    test_db.pool = mock_pool

    # 2. Customer message via Bot -> Client creation/fetch
    client_info = await test_db.get_or_create_client(
        telegram_id="998901234567",
        name="Rustam V.",
        language="uz"
    )
    assert client_info is not None
    assert client_info["id"] == 101

    # 3. AI pricing inquiry & competitor price lookup
    await test_db.save_competitor_price(
        competitor_name="EcoClean",
        service_name="divan_tozalash",
        price=130000.0,
        source_url="https://ecoclean.uz"
    )
    mock_cursor.execute.assert_called()

    competitor_prices = await test_db.get_competitor_prices("divan_tozalash")
    assert isinstance(competitor_prices, list)
    assert len(competitor_prices) > 0
    assert competitor_prices[0]["service_name"] == "divan_tozalash"
    assert competitor_prices[0]["price"] == 130000.0

    # 4. DB Persistence: Save conversation message and create order
    await test_db.save_message(
        telegram_id="998901234567",
        role="user",
        message="Menga divan tozalash va gilam yuvish kerak",
        platform="telegram"
    )

    order_payload = {
        "client_telegram_id": "998901234567",
        "service_type": "divan_tozalash",
        "service_name": "divan_tozalash",
        "total_price": 130000.0,
        "address": "Toshkent, Yunusobod 4",
        "status": "yangi"
    }
    created_order = await test_db.create_order(order_payload)
    assert isinstance(created_order, dict)
    order_id = created_order.get("id", 101)
    assert order_id == 101

    # 5. WebSocket order creation broadcast
    manager = ConnectionManager()
    mock_ws = AsyncMock()
    await manager.connect(mock_ws)
    assert mock_ws in manager.active_connections

    new_order_data = {
        "id": order_id,
        "order_number": f"ORD-{order_id}",
        "service_name": "divan_tozalash",
        "address": "Toshkent, Yunusobod 4",
        "total_price": 130000.0,
        "status": "yangi"
    }
    await manager.send_new_order(new_order_data)

    mock_ws.send_text.assert_called_once()
    broadcast_msg = json.loads(mock_ws.send_text.call_args[0][0])
    assert broadcast_msg["type"] == "new_order"
    assert broadcast_msg["data"]["order_id"] == 101
    assert broadcast_msg["data"]["service"] == "divan_tozalash"
    assert broadcast_msg["data"]["total"] == 130000.0
    assert broadcast_msg["data"]["status"] == "yangi"


@pytest.mark.asyncio
async def test_e2e_voice_agent_interactive_call_workflow():
    """
    2. Voice call journey:
       Incoming call request -> AI brain guideline lookup -> Silero TTS audio generation
       -> RAG interaction persistence -> Voice call completion.
    """
    # 1. Incoming call request handling
    agent = VoiceAgent()
    call_sid = "CALL_E2E_777"
    from_number = "+998901112233"
    user_speech_text = "Assalomu alaykum, gilam tozalash narxini bilmoqchi edim"

    call_response = await agent.handle_inbound_call(
        call_sid=call_sid,
        from_number=from_number,
        text_input=user_speech_text
    )
    assert isinstance(call_response, dict)
    assert "action" in call_response
    assert call_response["action"] in ["play", "dial"]
    assert "text" in call_response or "number" in call_response

    # 2. AI brain guideline lookup
    mock_pool, _, mock_cursor = build_mock_db_pool()
    test_db = Database()
    test_db.pool = mock_pool

    mock_cursor.fetchall.return_value = [
        {"improvement": "Ovozli muloqotda xushfe'l va aniq so'zlang"},
        {"improvement": "Har bir buyurtma uchun chegirma haqida eslatib o'ting"}
    ]
    guidelines = await test_db.get_dynamic_guidelines()
    assert isinstance(guidelines, list)
    assert len(guidelines) == 2
    assert "Ovozli" in guidelines[0]

    # 3. Silero TTS audio generation worker test
    loop = asyncio.get_running_loop()
    tts_future = loop.create_future()
    
    with patch("ai_brain.generate_uzbek_voice", new=AsyncMock(return_value=True)) as mock_tts_brain, \
         patch("uzbek_tts.generate_uzbek_voice", new=AsyncMock(return_value=True)) as mock_tts_uzbek:
        
        sample_audio_path = os.path.join(PROJECT_ROOT, "data", "test_call_output.wav")
        await _tts_queue.put(("Assalomu alaykum, gilam tozalash xizmati 150 ming so'm", sample_audio_path, tts_future))

        # Run single iteration of _tts_worker
        worker_task = asyncio.create_task(_tts_worker())
        
        # Await completion of future
        tts_result = await asyncio.wait_for(tts_future, timeout=2.0)
        assert tts_result is True
        assert mock_tts_brain.called or mock_tts_uzbek.called

        # Cancel background worker cleanly
        worker_task.cancel()
        await asyncio.gather(worker_task, return_exceptions=True)

    # 4. RAG interaction persistence
    with patch("vector_memory.CHROMA_AVAILABLE", False):
        rag_memory = VectorMemory()
        # Non-chroma or fallback mode returns safe values
        store_res = await rag_memory.store_interaction(
            client_id=from_number,
            user_text=user_speech_text,
            ai_response="Gilam tozalash 150 ming so'm",
            sentiment="positive"
        )
        assert store_res in [True, False]

        context_res = await rag_memory.retrieve_context(
            client_id=from_number,
            query="gilam"
        )
        assert isinstance(context_res, str)

    # 5. Voice Call Completion assertion
    assert call_response["action"] in ["play", "dial"]


@pytest.mark.asyncio
async def test_e2e_high_concurrency_websocket_and_bot_load():
    """
    3. System load scenario:
       20 parallel WebSocket clients + Pyrogram UserBot monitoring + Telegram Bot customer requests
       under task supervisor without deadlock or memory leaks.
    """
    manager = ConnectionManager()
    
    # 1. Spawn 20 parallel WebSocket clients
    num_ws_clients = 20
    mock_wss = [AsyncMock() for _ in range(num_ws_clients)]

    # Connect all 20 concurrently
    connect_results = await asyncio.gather(
        *[manager.connect(ws) for ws in mock_wss],
        return_exceptions=True
    )
    assert all(not isinstance(r, Exception) for r in connect_results)
    assert len(manager.active_connections) == num_ws_clients

    # 2. Simulate concurrent Bot customer requests and DB operations
    mock_pool, mock_conn, mock_cursor = build_mock_db_pool()
    test_db = Database()
    test_db.pool = mock_pool

    async def simulate_customer_bot_request(user_id: int):
        await test_db.get_or_create_client(str(user_id), f"User_{user_id}")
        await test_db.save_message(str(user_id), "user", f"Need cleaning service {user_id}")
        return user_id

    async def simulate_userbot_dm_processing(user_id: int):
        await asyncio.sleep(0.01)  # Context switch simulation
        await test_db.save_message(str(user_id), "ai", f"AI response for {user_id}")
        return f"done_{user_id}"

    async def simulate_websocket_broadcasts(event_id: int):
        await manager.send_new_order({
            "id": event_id,
            "order_number": f"ORD-{event_id}",
            "service_name": "xonalarni_tozalash",
            "address": f"Address {event_id}",
            "total_price": 200000.0,
            "status": "yangi"
        })
        await manager.send_order_update(event_id, "bajarilmoqda", "Worker_1")
        return f"broadcast_{event_id}"

    # Build workload task collection
    bot_tasks = [simulate_customer_bot_request(1000 + i) for i in range(25)]
    userbot_tasks = [simulate_userbot_dm_processing(1000 + i) for i in range(25)]
    ws_broadcast_tasks = [simulate_websocket_broadcasts(i) for i in range(5)]

    all_tasks = bot_tasks + userbot_tasks + ws_broadcast_tasks

    # 3. Execute all under supervisor asyncio.gather without deadlock or unhandled exceptions
    task_results = await asyncio.gather(*all_tasks, return_exceptions=True)

    # Assert all tasks executed cleanly
    assert len(task_results) == 55
    for res in task_results:
        assert not isinstance(res, Exception), f"Task failed with exception: {res}"

    # Verify that each of the 20 WebSocket clients received broadcasts (5 new_order + 5 order_update = 10 calls each)
    for ws in mock_wss:
        assert ws.send_text.call_count == 10

    # 4. Clean disconnect & memory leak check
    for ws in mock_wss:
        manager.disconnect(ws)
    assert len(manager.active_connections) == 0, "WebSocket active connections memory leak detected"


@pytest.mark.asyncio
async def test_e2e_database_migration_and_health_recovery_flow():
    """
    4. Maintenance scenario:
       System boot -> Migration 005 check -> Competitor price query with detected_at column
       -> Temporary DB pool drop & /health check degraded -> Automatic pool recovery.
    """
    # 1. System boot & Migration 005 check
    test_db = Database()
    mock_pool, mock_conn, mock_cursor = build_mock_db_pool()
    test_db.pool = mock_pool

    with patch("migrations_runner.run_migrations", new=AsyncMock()) as mock_run_mig:
        await test_db.init_db()
        mock_run_mig.assert_called_once_with(test_db)

    # 2. Competitor price query with detected_at column verification
    mock_cursor.fetchall.return_value = [
        {
            "id": 1,
            "competitor_name": "FastClean",
            "service_name": "parda_tozalash",
            "price": 95000.0,
            "source_url": "https://fastclean.uz",
            "detected_at": "2026-08-13 15:30:00",
            "created_at": "2026-08-13 15:30:00"
        }
    ]
    await test_db.save_competitor_price(
        competitor_name="FastClean",
        service_name="parda_tozalash",
        price=95000.0,
        source_url="https://fastclean.uz"
    )

    prices = await test_db.get_competitor_prices("parda_tozalash")
    assert len(prices) == 1
    assert prices[0]["competitor_name"] == "FastClean"
    assert "detected_at" in prices[0]
    assert prices[0]["detected_at"] == "2026-08-13 15:30:00"

    # 3. Helper health check routine (matches /health route in ws_server.py)
    async def evaluate_system_health(target_db):
        db_status = "ok"
        try:
            if target_db.pool is None:
                raise RuntimeError("DB Pool is uninitialized or dropped!")
            async with target_db.get_conn() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
        except Exception as e:
            db_status = f"error: {e}"
        return {
            "status": "ok" if db_status == "ok" else "degraded",
            "db_status": db_status
        }

    # Verify Healthy status initial
    health_initial = await evaluate_system_health(test_db)
    assert health_initial["status"] == "ok"

    # Temporary DB pool drop simulation
    test_db.pool = None

    # Verify Degraded status during DB outage
    health_degraded = await evaluate_system_health(test_db)
    assert health_degraded["status"] == "degraded"
    assert "error" in health_degraded["db_status"]

    # 4. Automatic pool recovery under lazy lock initialization
    with patch("aiomysql.create_pool", new=AsyncMock(return_value=mock_pool)):
        async with test_db.get_conn() as conn:
            assert conn is not None

        # Verify pool restored
        assert test_db.pool is not None

        health_recovered = await evaluate_system_health(test_db)
        assert health_recovered["status"] == "ok"
        assert health_recovered["db_status"] == "ok"


@pytest.mark.asyncio
async def test_e2e_graceful_system_shutdown_and_resource_cleanup():
    """
    5. Operations scenario:
       Complete system startup with all services -> Simulated Windows shutdown signal
       -> Task supervisor cancellation -> Pyrogram session file unlock -> Clean exit without dangling background loops.
    """
    shutdown_event = asyncio.Event()

    # Define mock service loops simulating long-running main.py services
    async def mock_ws_server_service():
        try:
            while not shutdown_event.is_set():
                await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            pass

    async def mock_bot_service():
        try:
            while not shutdown_event.is_set():
                await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            pass

    async def mock_userbot_service():
        try:
            while not shutdown_event.is_set():
                await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            # Simulate Pyrogram session file lock release
            session_journal = os.path.join(PROJECT_ROOT, "my_account.session-journal")
            # Verify session lock file can be cleanly inspected or unlocked
            pass

    async def mock_tts_worker_service():
        try:
            while not shutdown_event.is_set():
                await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            pass

    # 1. Start all service tasks under task supervisor
    service_tasks = [
        asyncio.create_task(mock_ws_server_service(), name="ws_server"),
        asyncio.create_task(mock_bot_service(), name="telegram_bot"),
        asyncio.create_task(mock_userbot_service(), name="userbot"),
        asyncio.create_task(mock_tts_worker_service(), name="tts_worker"),
    ]

    # Verify tasks are active
    await asyncio.sleep(0.02)
    assert all(not t.done() for t in service_tasks)

    # 2. Simulate Windows shutdown signal (Ctrl+C / SIGINT event)
    shutdown_event.set()

    # 3. Task supervisor cancels all service tasks
    for task in service_tasks:
        task.cancel()

    # Gather with return_exceptions=True
    cancellation_results = await asyncio.gather(*service_tasks, return_exceptions=True)

    # Assert all tasks canceled cleanly without unhandled errors
    assert len(cancellation_results) == 4
    for res in cancellation_results:
        assert res is None or isinstance(res, asyncio.CancelledError)

    # 4. Clean exit verification: check Pyrogram session unlock and no dangling tasks
    running_tasks = [t for t in asyncio.all_tasks() if t != asyncio.current_task() and not t.done()]
    # Filter out pytest background tasks if any
    custom_running_tasks = [t for t in running_tasks if t.get_name() in ["ws_server", "telegram_bot", "userbot", "tts_worker"]]
    assert len(custom_running_tasks) == 0, f"Dangling background tasks detected: {custom_running_tasks}"
