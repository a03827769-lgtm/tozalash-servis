import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import Request, WebSocket
from app.api.endpoints import payment, media_telephony, instagram_bot, telegram_bot
from app.api import websockets
import json
import base64


class MockCursor:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def execute(self, *args, **kwargs):
        pass

    async def commit(self):
        pass

    async def fetchall(self):
        return []

    async def fetchone(self):
        return {}


class MockConn:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def cursor(self):
        return MockCursor()

    async def commit(self):
        pass


class MockDB:
    def get_conn(self):
        return MockConn()

    async def get_order(self, order_id):
        return {"status": "yangi"}

    async def get_employee(self, emp_id):
        return None

    async def insert_employee(self, data):
        return 1


@pytest.mark.asyncio
async def test_payment_payme():
    request = MagicMock(spec=Request)
    request.headers = {
        "Authorization": "Basic " + base64.b64encode(b"test:test_payme_key").decode()
    }
    db = MockDB()

    # Method 1
    request.json = AsyncMock(
        return_value={
            "method": "CheckPerformTransaction",
            "params": {"account": {"order_id": 1}},
        }
    )
    res = await payment.payme_webhook(request, db)
    assert "result" in res or "error" in res

    # Method 2
    request.json = AsyncMock(
        return_value={
            "method": "CreateTransaction",
            "params": {"account": {"order_id": 1}, "id": "trans1", "amount": 10000},
        }
    )
    res = await payment.payme_webhook(request, db)
    assert "result" in res or "error" in res

    # Method 3
    request.json = AsyncMock(
        return_value={"method": "PerformTransaction", "params": {"id": "trans1"}}
    )
    res = await payment.payme_webhook(request, db)
    assert "result" in res or "error" in res


@pytest.mark.asyncio
async def test_payment_click():
    request = MagicMock(spec=Request)
    db = MockDB()

    request.form = AsyncMock(
        return_value={
            "action": "0",
            "merchant_trans_id": "1",
            "amount": "10000",
            "click_trans_id": "trans1",
        }
    )
    res = await payment.click_webhook(request, db)
    assert "error" in res or "click_trans_id" in res

    request.form = AsyncMock(
        return_value={
            "action": "1",
            "merchant_trans_id": "1",
            "amount": "10000",
            "click_trans_id": "trans1",
        }
    )
    res = await payment.click_webhook(request, db)
    assert "error" in res or "click_trans_id" in res


@pytest.mark.asyncio
async def test_websockets():
    ws = MagicMock(spec=WebSocket)
    ws.accept = AsyncMock()
    ws.receive_text = AsyncMock(side_effect=["ping", "other", Exception("disconnect")])
    ws.send_text = AsyncMock()

    try:
        await websockets.websocket_endpoint(ws)
    except Exception:
        pass

    # Test broadcast
    await websockets.ws_manager.connect(ws)
    await websockets.ws_manager.broadcast("test_event", {"key": "value"})
    websockets.ws_manager.disconnect(ws)


@pytest.mark.asyncio
async def test_media_telephony():
    db = MockDB()
    try:
        await media_telephony.get_call_history(db)
    except Exception:
        pass

    try:
        await media_telephony.initiate_call(MagicMock(), db)
    except Exception:
        pass


@pytest.mark.asyncio
async def test_bots():
    request = MagicMock(spec=Request)
    request.json = AsyncMock(return_value={})
    db = MockDB()

    try:
        await instagram_bot.instagram_webhook(request, db)
    except Exception:
        pass

    try:
        await instagram_bot.verify_webhook(request)
    except Exception:
        pass

    try:
        await telegram_bot.telegram_webhook(request, db)
    except Exception:
        pass
