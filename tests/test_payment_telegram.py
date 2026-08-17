import pytest
from fastapi.testclient import TestClient
from app.main import app
from database import get_db
import base64
import os

client = TestClient(app)


class MockCursor:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def execute(self, query, params=None):
        pass


class MockConn:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def cursor(self):
        return MockCursor()

    async def commit(self):
        pass


class MockDB:
    async def get_order(self, order_id):
        if order_id == 99999:
            return {"id": 99999, "status": "yangi"}
        return None

    def get_conn(self):
        return MockConn()


@pytest.fixture(autouse=True)
def override_deps():
    app.dependency_overrides[get_db] = lambda: MockDB()
    yield
    app.dependency_overrides.clear()


def test_payme_webhook_unauthorized():
    response = client.post("/api/v1/payment/payme")
    assert response.status_code == 401


def test_payme_webhook_invalid_scheme():
    response = client.post(
        "/api/v1/payment/payme", headers={"Authorization": "Bearer token"}
    )
    assert response.status_code == 401


def test_payme_webhook_invalid_creds():
    creds = base64.b64encode(b"test:wrong").decode("utf-8")
    response = client.post(
        "/api/v1/payment/payme", headers={"Authorization": f"Basic {creds}"}
    )
    assert response.status_code == 401


def test_payme_webhook_success_check():
    creds = base64.b64encode(b"test:test_payme_key").decode("utf-8")
    response = client.post(
        "/api/v1/payment/payme",
        headers={"Authorization": f"Basic {creds}"},
        json={
            "method": "CheckPerformTransaction",
            "params": {"account": {"order_id": 99999}},
        },
    )
    assert response.status_code == 200


def test_payme_webhook_create():
    creds = base64.b64encode(b"test:test_payme_key").decode("utf-8")
    response = client.post(
        "/api/v1/payment/payme",
        headers={"Authorization": f"Basic {creds}"},
        json={
            "method": "CreateTransaction",
            "params": {"account": {"order_id": 99999}, "id": "tx1", "amount": 10000},
        },
    )
    assert response.status_code == 200


def test_payme_webhook_perform():
    creds = base64.b64encode(b"test:test_payme_key").decode("utf-8")
    response = client.post(
        "/api/v1/payment/payme",
        headers={"Authorization": f"Basic {creds}"},
        json={"method": "PerformTransaction", "params": {"id": "tx1"}},
    )
    assert response.status_code == 200


def test_click_webhook_prepare():
    response = client.post(
        "/api/v1/payment/click",
        data={
            "action": "0",
            "merchant_trans_id": "99999",
            "amount": "10000",
            "click_trans_id": "c1",
        },
    )
    assert response.status_code == 200


def test_click_webhook_complete():
    response = client.post(
        "/api/v1/payment/click",
        data={
            "action": "1",
            "merchant_trans_id": "99999",
            "amount": "10000",
            "click_trans_id": "c1",
        },
    )
    assert response.status_code == 200


def test_click_webhook_unknown():
    response = client.post(
        "/api/v1/payment/click",
        data={
            "action": "9",
            "merchant_trans_id": "99999",
            "amount": "10000",
            "click_trans_id": "c1",
        },
    )
    assert response.status_code == 200


# Telegram Bot TMA & Helpdesk Tests
def test_tma_verify():
    response = client.post(
        "/api/v1/bot/telegram/tma/verify", json={"initData": "hash=123"}
    )
    assert response.status_code == 200


def test_telegram_inline():
    response = client.post(
        "/api/v1/bot/telegram/telegram/inline",
        json={"inline_query": {"id": "1", "query": "test"}},
    )
    assert response.status_code == 200


def test_helpdesk_create():
    response = client.post(
        "/api/v1/bot/telegram/helpdesk/tickets",
        json={"user_id": 1, "subject": "test", "message": "test"},
    )
    assert response.status_code == 200


def test_helpdesk_list():
    response = client.get("/api/v1/bot/telegram/helpdesk/tickets")
    assert response.status_code == 200


def test_helpdesk_resolve():
    response = client.patch("/api/v1/bot/telegram/helpdesk/tickets/1")
    assert response.status_code == 200


def test_helpdesk_resolve_not_found():
    response = client.patch("/api/v1/bot/telegram/helpdesk/tickets/999")
    assert response.status_code == 200
