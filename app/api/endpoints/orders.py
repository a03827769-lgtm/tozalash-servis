from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.core.security import get_current_user
from database import get_db, Database

router = APIRouter()


@router.get("/", response_model=List[Dict[str, Any]])
async def get_orders(db: Database = Depends(get_db)):
    """
    Get all orders.
    """
    rows = await db.fetch_all("""
        SELECT o.*, c.name as client_name, c.phone as client_phone
        FROM orders o
        LEFT JOIN clients c ON o.client_telegram_id = c.telegram_id
        ORDER BY o.created_at DESC
    """)

    result = []
    for r in rows:
        result.append(
            {
                "id": r.get("id"),
                "order_number": r.get("order_number") or f"TS-{r.get('id', 0)}",
                "client_name": r.get("client_name") or "Noma'lum",
                "client_phone": r.get("client_phone") or "",
                "service_name": r.get("service_name") or r.get("service_type") or "Tozalash",
                "total_price": float(r.get("total_price") or 0.0),
                "status": r.get("status") or "yangi",
                "scheduled_date": str(r.get("scheduled_date") or ""),
                "created_at": str(r.get("created_at") or ""),
            }
        )
    return result


@router.put("/{order_id}/status")
async def update_order_status(
    order_id: int, status_data: dict, db: Database = Depends(get_db)
):
    """
    Update order status.
    """
    status = status_data.get("status")
    if not status:
        raise HTTPException(status_code=400, detail="Status is required")

    await db.update_order_status(order_id, status)
    return {"status": "success", "message": "Order updated"}
