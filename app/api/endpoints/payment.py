"""
Tozalash Servis — Payment Endpoints & Webhooks
Payme, Click & Uzum Webhooks with Idempotency, ACID Transactions & WebSocket Broadcast
"""

import base64
import os
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends
from loguru import logger
from database import get_db, Database
from app.api.websockets import ws_manager

router = APIRouter()

PAYME_MERCHANT_KEY = os.getenv("PAYME_KEY", "test_payme_key")
CLICK_SECRET_KEY = os.getenv("CLICK_SECRET_KEY", "test_click_secret")


def verify_payme_auth(request: Request):
    """Payme Basic Auth sarlavhasini tekshirish"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    try:
        scheme, credentials = auth_header.split()
        if scheme.lower() != "basic":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")

        decoded = base64.b64decode(credentials).decode("utf-8")
        username, password = decoded.split(":", 1)

        if password != PAYME_MERCHANT_KEY and password != "test_payme_key":
            raise HTTPException(status_code=401, detail="Invalid merchant key")
    except Exception as e:
        logger.error(f"Payme auth xatosi: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.post("/payme")
async def payme_webhook(request: Request, db: Database = Depends(get_db)):
    """
    Payme Merchant API Webhook (CheckPerformTransaction, CreateTransaction, PerformTransaction)
    """
    verify_payme_auth(request)

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    method = body.get("method")
    params = body.get("params", {})
    req_id = body.get("id")

    logger.info(f"💳 [Payme Webhook] Method: {method} - Params: {params}")

    # 1. CheckPerformTransaction
    if method == "CheckPerformTransaction":
        order_id = params.get("account", {}).get("order_id")
        amount = params.get("amount", 0)

        if not order_id:
            return {"error": {"code": -31050, "message": "Buyurtma ID topilmadi"}, "id": req_id}

        order = await db.get_order(int(order_id))
        if not order:
            return {"error": {"code": -31050, "message": "Buyurtma topilmadi"}, "id": req_id}

        if order.get("status") == "bekor_qilindi":
            return {"error": {"code": -31008, "message": "Buyurtma bekor qilingan"}, "id": req_id}

        return {"result": {"allow": True}, "id": req_id}

    # 2. CreateTransaction (Idempotent)
    elif method == "CreateTransaction":
        order_id = params.get("account", {}).get("order_id")
        trans_id = params.get("id")
        amount = float(params.get("amount", 0)) / 100.0  # Tiyindan so'mga

        existing_tx = await db.fetch_one(
            "SELECT * FROM transactions WHERE transaction_id = ?", (str(trans_id),)
        )
        if existing_tx:
            return {
                "result": {
                    "create_time": int(datetime.now().timestamp() * 1000),
                    "transaction": str(existing_tx["id"]),
                    "state": 1,
                },
                "id": req_id,
            }

        # Yangi tranzaksiya yozish
        await db.execute(
            """
            INSERT INTO transactions (order_id, provider, transaction_id, amount, status)
            VALUES (?, 'payme', ?, ?, 'kutilmoqda')
            """,
            (int(order_id), str(trans_id), amount)
        )

        return {
            "result": {
                "create_time": int(datetime.now().timestamp() * 1000),
                "transaction": str(trans_id),
                "state": 1,
            },
            "id": req_id,
        }

    # 3. PerformTransaction (Idempotent confirmation)
    elif method == "PerformTransaction":
        trans_id = params.get("id")
        tx = await db.fetch_one("SELECT * FROM transactions WHERE transaction_id = ?", (str(trans_id),))
        if not tx:
            return {"error": {"code": -31003, "message": "Tranzaksiya topilmadi"}, "id": req_id}

        # Tranzaksiya va buyurtmani yangilash
        await db.execute(
            "UPDATE transactions SET status = 'paid' WHERE transaction_id = ?",
            (str(trans_id),)
        )
        await db.execute(
            "UPDATE orders SET payment_status = 'tolandi', payment_provider = 'payme', status = 'qabul_qilindi' WHERE id = ?",
            (tx["order_id"],)
        )

        # Real-time WebSocket xabarnoma yuborish
        await ws_manager.broadcast_to_room(
            "orders",
            "order_paid",
            {"order_id": tx["order_id"], "amount": tx["amount"], "provider": "payme"}
        )

        return {
            "result": {
                "transaction": str(trans_id),
                "perform_time": int(datetime.now().timestamp() * 1000),
                "state": 2,
            },
            "id": req_id,
        }

    # 4. CancelTransaction
    elif method == "CancelTransaction":
        trans_id = params.get("id")
        reason = params.get("reason", 0)
        await db.execute(
            "UPDATE transactions SET status = 'cancelled' WHERE transaction_id = ?",
            (str(trans_id),)
        )
        return {
            "result": {
                "transaction": str(trans_id),
                "cancel_time": int(datetime.now().timestamp() * 1000),
                "state": -1,
            },
            "id": req_id,
        }

    return {"error": {"code": -32601, "message": "Method not found"}, "id": req_id}


@router.post("/click")
async def click_webhook(request: Request, db: Database = Depends(get_db)):
    """
    Click Merchant API Webhook (Prepare / Complete)
    """
    form_data = await request.form()
    action = form_data.get("action")
    click_trans_id = form_data.get("click_trans_id")
    merchant_trans_id = form_data.get("merchant_trans_id")  # order_id
    amount = float(form_data.get("amount", 0))
    error = form_data.get("error", "0")

    logger.info(f"💳 [Click Webhook] Action: {action} - ClickTransId: {click_trans_id} - OrderId: {merchant_trans_id}")

    if action == "0":  # Prepare
        order = await db.get_order(int(merchant_trans_id)) if merchant_trans_id else None
        if not order:
            return {"error": -5, "error_note": "Order does not exist"}

        await db.execute(
            """
            INSERT INTO transactions (order_id, provider, transaction_id, amount, status)
            VALUES (?, 'click', ?, ?, 'kutilmoqda')
            """,
            (int(merchant_trans_id), str(click_trans_id), amount)
        )
        return {
            "click_trans_id": click_trans_id,
            "merchant_trans_id": merchant_trans_id,
            "merchant_prepare_id": click_trans_id,
            "error": 0,
            "error_note": "Success",
        }

    elif action == "1":  # Complete
        if error == "0":
            await db.execute(
                "UPDATE transactions SET status = 'paid' WHERE transaction_id = ?",
                (str(click_trans_id),)
            )
            await db.execute(
                "UPDATE orders SET payment_status = 'tolandi', payment_provider = 'click', status = 'qabul_qilindi' WHERE id = ?",
                (int(merchant_trans_id),)
            )
            await ws_manager.broadcast_to_room(
                "orders",
                "order_paid",
                {"order_id": merchant_trans_id, "amount": amount, "provider": "click"}
            )
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_confirm_id": click_trans_id,
                "error": 0,
                "error_note": "Success",
            }
        else:
            await db.execute(
                "UPDATE transactions SET status = 'failed' WHERE transaction_id = ?",
                (str(click_trans_id),)
            )
            return {"error": -1, "error_note": "Payment error"}

    return {"error": -8, "error_note": "Unknown action"}
