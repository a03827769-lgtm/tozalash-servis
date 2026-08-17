from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.core.security import get_current_user

router = APIRouter()


@router.get("/ltv-cac")
async def get_ltv_cac_metrics(current_user: dict = Depends(get_current_user)):
    """
    Returns LTV (Life Time Value) and CAC (Customer Acquisition Cost) metrics.
    Requires Admin privileges.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not enough privileges")

    # Mock data for demonstration
    return {"LTV": 1500.50, "CAC": 45.20, "ratio": 33.2, "currency": "USD"}


@router.get("/loyalty")
async def get_loyalty_programs(current_user: dict = Depends(get_current_user)):
    """
    Get active loyalty and referral programs.
    """
    return {
        "loyalty_points_multiplier": 1.5,
        "referral_bonus": 50000,
        "currency": "UZS",
    }
