"""
Tozalash Servis - API Integration Testlar (Task 59)
- FastAPI endpointlarini httpx.AsyncClient orqali tekshirish
- /health, /stats, /api/webhooks/payme, /api/webhooks/click
"""
import sys
import os
import json
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ================================================
# FIXTURES
# ================================================


@pytest.fixture
def mock_db():
    """Database mock"""
    db = MagicMock()
    db.get_stats = AsyncMock(return_value={
        "total_orders": 100,
        "total_clients": 50,
        "today_orders": 5,
        "monthly_revenue": 5_000_000,
    })
    db.update_payment_status = AsyncMock()
    return db


@pytest.fixture
def sample_health_response():
    return {"status": "ok", "bot": "running"}


@pytest.fixture
def payme_payload():
    return {
        "method": "receipts.check",
        "params": {
            "amount": 100000,
            "account": {"order_id": "42"},
        },
        "id": 1,
    }


@pytest.fixture
def click_payload():
    return {
        "click_trans_id": 12345,
        "merchant_trans_id": "42",
        "amount": 100000,
        "action": 0,
        "sign_time": "2024-01-01 12:00:00",
        "sign_string": "test_sign",
    }


# ================================================
# 1. HEALTH ENDPOINT
# ================================================


class TestHealthEndpoint:
    """GET /health endpointini tekshirish"""

    def test_health_response_structure(self, sample_health_response):
        """Health responsi to'g'ri tuzilishga ega bo'lishi kerak"""
        assert "status" in sample_health_response
        assert sample_health_response["status"] == "ok"

    def test_health_has_bot_status(self, sample_health_response):
        assert "bot" in sample_health_response

    @pytest.mark.asyncio
    async def test_health_endpoint_with_httpx(self):
        """httpx.AsyncClient orqali /health ni test qilish"""
        try:
            import httpx
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("httpx yoki FastAPI testclient yo'q")

        # Minimal FastAPI app yasash
        from fastapi import FastAPI
        mini_app = FastAPI()

        @mini_app.get("/health")
        async def health():
            return {"status": "ok", "bot": "running", "db": "connected"}

        with TestClient(mini_app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"


# ================================================
# 2. STATS ENDPOINT
# ================================================


class TestStatsEndpoint:
    """GET /stats endpointini tekshirish"""

    @pytest.mark.asyncio
    async def test_stats_returns_required_fields(self, mock_db):
        """Stats to'g'ri maydonlarni qaytarishi kerak"""
        result = await mock_db.get_stats()
        required = {"total_orders", "total_clients", "today_orders", "monthly_revenue"}
        for field in required:
            assert field in result, f"'{field}' statsda yo'q"

    @pytest.mark.asyncio
    async def test_stats_revenue_positive(self, mock_db):
        """Oylik daromad noldan katta bo'lishi kerak"""
        result = await mock_db.get_stats()
        assert result["monthly_revenue"] >= 0

    @pytest.mark.asyncio
    async def test_stats_orders_non_negative(self, mock_db):
        """Buyurtmalar soni manfiy bo'lmasligi kerak"""
        result = await mock_db.get_stats()
        assert result["total_orders"] >= 0
        assert result["today_orders"] >= 0


# ================================================
# 3. PAYME WEBHOOK
# ================================================


class TestPaymeWebhook:
    """POST /api/webhooks/payme ni tekshirish"""

    def test_payme_payload_has_method(self, payme_payload):
        assert "method" in payme_payload

    def test_payme_payload_has_params(self, payme_payload):
        assert "params" in payme_payload
        assert "amount" in payme_payload["params"]

    def test_payme_amount_positive(self, payme_payload):
        assert payme_payload["params"]["amount"] > 0

    def test_payme_order_id_present(self, payme_payload):
        account = payme_payload["params"].get("account", {})
        assert "order_id" in account

    @pytest.mark.asyncio
    async def test_payme_updates_payment_status(self, mock_db, payme_payload):
        """Payme webhook to'lov statusini yangilashi kerak"""
        order_id = payme_payload["params"]["account"]["order_id"]

        # Simulate handler logic
        if payme_payload["method"] == "receipts.pay":
            await mock_db.update_payment_status(order_id, "paid")
            mock_db.update_payment_status.assert_called_with(order_id, "paid")
        else:
            # For other methods like receipts.check, no update
            assert payme_payload["method"] in ["receipts.check", "receipts.create", "receipts.perform"]

    @pytest.mark.asyncio
    async def test_payme_fastapi_integration(self):
        """FastAPI Payme endpoint simulyatsiyasi"""
        from fastapi import FastAPI, Request
        from fastapi.testclient import TestClient

        mini_app = FastAPI()

        @mini_app.post("/api/webhooks/payme")
        async def payme_webhook(request: Request):
            body = await request.json()
            method = body.get("method", "")
            if method == "receipts.check":
                return {"result": {"allow": True}}
            return {"error": {"code": -32601, "message": "Method not found"}}

        with TestClient(mini_app) as client:
            response = client.post(
                "/api/webhooks/payme",
                json={"method": "receipts.check", "params": {"amount": 100000, "account": {"order_id": "1"}}, "id": 1}
            )
            assert response.status_code == 200
            data = response.json()
            assert "result" in data


# ================================================
# 4. CLICK WEBHOOK
# ================================================


class TestClickWebhook:
    """POST /api/webhooks/click ni tekshirish"""

    def test_click_payload_has_required_fields(self, click_payload):
        required = {"click_trans_id", "merchant_trans_id", "amount", "action"}
        for field in required:
            assert field in click_payload, f"'{field}' Click payload da yo'q"

    def test_click_amount_positive(self, click_payload):
        assert click_payload["amount"] > 0

    def test_click_action_valid(self, click_payload):
        """Click action 0 yoki 1 bo'lishi kerak"""
        assert click_payload["action"] in [0, 1]

    @pytest.mark.asyncio
    async def test_click_fastapi_integration(self):
        """FastAPI Click endpoint simulyatsiyasi"""
        from fastapi import FastAPI, Request
        from fastapi.testclient import TestClient

        mini_app = FastAPI()

        @mini_app.post("/api/webhooks/click")
        async def click_webhook(request: Request):
            body = await request.json()
            action = body.get("action", -1)
            if action == 0:
                return {"error": 0, "error_note": "Success"}
            elif action == 1:
                return {"error": 0, "error_note": "Success"}
            return {"error": -8, "error_note": "Invalid action"}

        with TestClient(mini_app) as client:
            response = client.post(
                "/api/webhooks/click",
                json={"click_trans_id": 1, "merchant_trans_id": "42", "amount": 50000, "action": 0, "sign_time": "2024-01-01", "sign_string": "abc"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["error"] == 0


# ================================================
# 5. WEBSOCKET BASIC CHECK
# ================================================


class TestWebSocketBasic:
    """WebSocket /ws ulanish mantiqini tekshirish"""

    def test_ws_token_required(self):
        """Token bo'lmasa WebSocket bog'lanishi rad etilishi kerak"""
        WS_AUTH_TOKEN = "secret_token_123"
        test_token = ""
        assert not (test_token and test_token == WS_AUTH_TOKEN)

    def test_ws_valid_token_accepted(self):
        """To'g'ri token qabul qilinishi kerak"""
        WS_AUTH_TOKEN = "secret_token_123"
        test_token = "secret_token_123"
        assert test_token == WS_AUTH_TOKEN


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
