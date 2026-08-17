from fastapi import APIRouter, Depends, HTTPException
from database import db
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/charts/revenue")
async def get_revenue_chart():
    """Task 84: Admin panelda real-time diagrammalar uchun API"""
    try:
        # Oxirgi 7 kunlik daromadni hisoblash (simulyatsiya)
        labels = []
        data = []
        for i in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            labels.append(date)
            # DB dan real ma'lumot olish mumkin, hozircha static format
            data.append(100000 * (i + 1))
            
        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "Daromad (UZS)",
                    "data": data,
                    "borderColor": "rgb(75, 192, 192)",
                    "tension": 0.1
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workers/{worker_id}/rate")
async def rate_worker(worker_id: int, rating: int, client_id: int):
    """Task 90: HR & Ishchi baholash API si"""
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        
    async with db.get_conn() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO worker_ratings (worker_id, client_id, rating) VALUES (%s, %s, %s)",
                (worker_id, client_id, rating)
            )
            # O'rtacha reytingni yangilash
            await cursor.execute(
                """
                UPDATE workers 
                SET total_ratings = total_ratings + 1,
                    average_rating = (average_rating * total_ratings + %s) / (total_ratings + 1)
                WHERE id = %s
                """,
                (rating, worker_id)
            )
    return {"status": "success", "message": "Rating saved"}
