"""
Phase 8 - Task 71: Instagram AI Bot handler
Listens to Instagram Webhook events (comments, DMs, story mentions)
and replies automatically using Gemini AI.
"""

from fastapi import APIRouter, Request, HTTPException
from loguru import logger
import hmac
import hashlib
import os

router = APIRouter()

INSTAGRAM_VERIFY_TOKEN = os.getenv("INSTAGRAM_VERIFY_TOKEN", "tozalash_ig_token")
APP_SECRET = os.getenv("INSTAGRAM_APP_SECRET", "")


@router.get("/instagram/webhook")
async def verify_instagram_webhook(request: Request):
    """
    Instagram webhook verification (Challenge handshake).
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if mode == "subscribe" and token == INSTAGRAM_VERIFY_TOKEN:
        logger.info("Instagram webhook verified successfully.")
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/instagram/webhook")
async def handle_instagram_events(request: Request):
    """
    Receives Instagram Webhooks: DMs, comments, story mentions.
    Triggers AI auto-reply via Celery worker.
    """
    # Validate X-Hub-Signature-256
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    expected = (
        "sha256=" + hmac.new(APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
    )
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=400, detail="Invalid signature")

    payload = await request.json()
    logger.info(f"Instagram event received: {payload.get('object')}")
    # TODO: Celery task -> ai_brain.generate_instagram_reply(payload)
    return {"status": "processing"}
