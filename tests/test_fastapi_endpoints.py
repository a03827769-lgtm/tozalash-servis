from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_all_get_endpoints():
    endpoints = [
        "/api/v1/bot/telegram/webhook",
        "/api/v1/bot/instagram/webhook",
        "/api/v1/media/transcribe",
        "/api/v1/data/sensors",
        "/api/v1/finance/revenue",
        "/api/v1/hr/workers",
        "/api/v1/messaging/send",
    ]
    for endpoint in endpoints:
        client.get(endpoint)
        client.post(endpoint, json={})
