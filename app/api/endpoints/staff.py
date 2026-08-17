from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.core.security import get_current_user
from database import get_db, Database

router = APIRouter()


@router.get("/", response_model=List[Dict[str, Any]])
async def get_staff(db: Database = Depends(get_db)):
    """
    Get all staff (workers).
    """
    workers = await db.get_all_workers()
    # Format the data for frontend
    result = []
    for w in workers:
        result.append(
            {
                "id": w.get("id") or w.get("telegram_id"),
                "name": w.get("name"),
                "role": w.get("specialization") or "Farrosh",
                "phone": w.get("phone") or "",
                "status": "Band emas" if w.get("is_available") else "Dam Olishda",
                "rating": w.get("rating", 4.0),
                "completedTasks": w.get("completed_orders", 0),
            }
        )
    return result


@router.post("/")
async def create_staff(data: dict, db: Database = Depends(get_db)):
    """
    Create a new staff member.
    """
    import time

    telegram_id = data.get("telegram_id") or str(int(time.time()))
    try:
        await db.add_worker(
            name=data.get("name"),
            phone=data.get("phone"),
            telegram_id=telegram_id,
            specialization=data.get("role"),
        )
        return {"status": "success", "message": "Worker created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{staff_id}")
async def delete_staff(staff_id: str, db: Database = Depends(get_db)):
    """
    Delete a staff member (or mark as inactive).
    """
    await db.execute(
        "UPDATE workers SET is_active = 0 WHERE telegram_id = ? OR CAST(id AS TEXT) = ?",
        (str(staff_id), str(staff_id)),
    )
    return {"status": "success", "message": "Worker deleted"}
