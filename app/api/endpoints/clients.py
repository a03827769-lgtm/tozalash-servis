from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.core.security import get_current_user
from database import get_db, Database

router = APIRouter()


@router.get("/", response_model=List[Dict[str, Any]])
async def get_clients(db: Database = Depends(get_db)):
    """
    Get all clients.
    """
    rows = await db.fetch_all("SELECT * FROM clients ORDER BY created_at DESC")

    result = []
    for r in rows:
        result.append(
            {
                "id": r.get("id"),
                "telegram_id": r.get("telegram_id"),
                "name": r.get("name"),
                "phone": r.get("phone") or "",
                "total_orders": r.get("total_orders", 0) or 0,
                "total_spent": float(r.get("total_spent", 0.0) or 0.0),
                "loyalty_points": r.get("loyalty_points", 0) or 0,
                "last_activity": str(r.get("last_activity", "") or ""),
            }
        )
    return result


@router.delete("/{client_id}")
async def delete_client(client_id: str, db: Database = Depends(get_db)):
    """
    Delete a client.
    """
    await db.execute(
        "DELETE FROM clients WHERE telegram_id = ? OR CAST(id AS TEXT) = ?",
        (str(client_id), str(client_id)),
    )
    return {"status": "success", "message": "Client deleted"}
