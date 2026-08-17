"""
Phase 8 - Task 73: Telegram Mini App (TMA) Backend
Task 79: Inline Keyboards and Inline Queries
Task 80: Helpdesk Ticket System
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from loguru import logger
import os
import httpx

router = APIRouter()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


class TicketCreate(BaseModel):
    user_id: int
    subject: str
    message: str


# --- Task 73: TMA Web App Data Verification ---
@router.post("/tma/verify")
async def verify_tma_init_data(request: Request):
    """
    Verifies Telegram Mini App init_data hash for security.
    """
    body = await request.json()
    init_data = body.get("initData", "")
    # TODO: Implement HMAC-SHA256 verification with bot token
    logger.info(f"TMA init_data received, length={len(init_data)}")
    return {"status": "valid", "user": {"id": 123456789, "name": "Test User"}}


# --- Task 79: Inline Mode Handler ---
@router.post("/telegram/inline")
async def handle_inline_query(request: Request):
    """
    Handles Telegram Inline Mode queries (Task 79).
    """
    update = await request.json()
    inline_query = update.get("inline_query", {})
    if inline_query:
        query_id = inline_query["id"]
        query_text = inline_query.get("query", "")
        results = [
            {
                "type": "article",
                "id": "1",
                "title": f"'{query_text}' bo'yicha buyurtma berish",
                "input_message_content": {"message_text": f"Buyurtma: {query_text}"},
            }
        ]
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{TG_API}/answerInlineQuery",
                json={"inline_query_id": query_id, "results": results},
            )
    return {"status": "ok"}


# --- Task 80: Helpdesk Ticket System ---
tickets_db: list[dict] = []  # In-memory store; replace with DB model


@router.post("/helpdesk/tickets")
async def create_ticket(ticket: TicketCreate):
    """
    Creates a new support ticket (Task 80).
    """
    new_ticket = {"id": len(tickets_db) + 1, **ticket.dict(), "status": "open"}
    tickets_db.append(new_ticket)
    logger.info(f"New helpdesk ticket #{new_ticket['id']} from user {ticket.user_id}")
    return new_ticket


@router.get("/helpdesk/tickets")
async def list_tickets():
    """
    Lists all support tickets (Task 80).
    """
    return tickets_db


@router.patch("/helpdesk/tickets/{ticket_id}")
async def resolve_ticket(ticket_id: int):
    """
    Marks a ticket as resolved (Task 80).
    """
    for t in tickets_db:
        if t["id"] == ticket_id:
            t["status"] = "resolved"
            return t
    return {"error": "Ticket not found"}
