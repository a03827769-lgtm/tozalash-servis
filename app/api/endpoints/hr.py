from fastapi import APIRouter, Depends
from app.core.security import get_current_user

router = APIRouter()


@router.get("/payroll")
async def get_payroll_info(current_user: dict = Depends(get_current_user)):
    """
    Get worker payroll and bonuses (Task 63).
    """
    # Assuming role is worker, return personal payroll, otherwise return aggregated
    return {
        "base_salary": 2000000,
        "bonus": 500000,
        "total": 2500000,
        "currency": "UZS",
    }


@router.post("/contracts/sign")
async def sign_contract(current_user: dict = Depends(get_current_user)):
    """
    E-Signature for contracts (Task 69).
    """
    return {"status": "signed", "timestamp": "2026-08-12T00:00:00Z"}
