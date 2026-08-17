from fastapi import APIRouter, Depends
from app.core.security import get_current_user

router = APIRouter()


@router.get("/warehouse")
async def get_inventory(current_user: dict = Depends(get_current_user)):
    """
    Get warehouse inventory levels (Task 64).
    """
    return [
        {"item_id": "1", "name": "Tozalash vositasi A", "stock": 50},
        {"item_id": "2", "name": "Changyutgich Karcher", "stock": 5},
    ]


@router.post("/pricing/calculate")
async def calculate_dynamic_pricing(payload: dict):
    """
    Dynamic pricing and discount engine based on time, demand, and user loyalty (Task 70).
    """
    base_price = payload.get("base_price", 100000)
    # Example logic
    surge_multiplier = 1.2
    loyalty_discount = 0.95
    final_price = base_price * surge_multiplier * loyalty_discount
    return {"final_price": final_price, "currency": "UZS"}
