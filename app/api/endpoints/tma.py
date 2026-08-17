"""
Tozalash Servis — Telegram Mini App (TMA 2.0) API
Bot ichidagi interaktiv Next.js/React veb-ilovasi uchun xizmatlar, dinamik narx kalkulyatori,
bo'sh vaqt slotlari va 1-bosqichli buyurtma yaratish endpointlari.
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query
from database import get_db, Database
from config import PRICES, BUSINESS_NAME, BUSINESS_PHONE
from smart_dispatch import smart_dispatcher

router = APIRouter(prefix="/tma", tags=["Telegram Mini App"])


class CalculationRequest(BaseModel):
    service_type: str = Field(..., example="regular_cleaning")
    rooms_or_seats: int = Field(default=2, ge=1, le=20)
    area_sqm: Optional[float] = Field(default=60.0)
    has_windows: bool = False
    promo_code: Optional[str] = None


class BookingRequest(BaseModel):
    telegram_id: int
    client_name: str
    client_phone: str
    service_type: str
    scheduled_time: str  # YYYY-MM-DD HH:MM
    address: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    area_sqm: Optional[float] = 60.0
    promo_code: Optional[str] = None
    notes: Optional[str] = None


@router.get("/services")
async def get_tma_services():
    """TMA uchun barcha xizmatlar ro'yxati va rasmlari"""
    services_list = []
    for s_key, s_data in PRICES.items():
        services_list.append({
            "id": s_key,
            "name_uz": s_data.get("name_uz"),
            "name_ru": s_data.get("name_ru"),
            "name_en": s_data.get("name_en"),
            "base_price": s_data.get("price", 150000),
            "unit_uz": s_data.get("unit", "xona"),
            "icon": f"https://tozalash.uz/assets/icons/{s_key}.png"
        })
    return {
        "status": "success",
        "business_name": BUSINESS_NAME,
        "business_phone": BUSINESS_PHONE,
        "services": services_list
    }


@router.get("/slots")
async def get_available_slots(target_date: Optional[str] = None):
    """Tanlangan sana bo'yicha bo'sh vaqt oralig'i (slotlar)"""
    chosen_date = target_date or str(date.today() + timedelta(days=1))
    standard_slots = [
        {"time": "09:00", "available": True},
        {"time": "11:30", "available": True},
        {"time": "14:00", "available": True},
        {"time": "16:30", "available": True},
        {"time": "19:00", "available": True}
    ]
    return {
        "date": chosen_date,
        "slots": standard_slots
    }


@router.post("/calculate")
async def calculate_tma_price(req: CalculationRequest, db: Database = Depends(get_db)):
    """Dinamik narx hisoblagich (Surge multiplier va promo-kodlarni inobatga oladi)"""
    service_info = PRICES.get(req.service_type)
    if not service_info:
        raise HTTPException(status_code=400, detail="Xizmat turi topilmadi")

    base_unit_price = float(service_info.get("price", 150000))
    raw_total = base_unit_price * req.rooms_or_seats

    if req.has_windows:
        raw_total += 80000.0  # Qo'shimcha deraza yuvish

    # Dynamic Surge Pricing
    active_orders = await db.fetch_all("SELECT id FROM orders WHERE status = 'kutilmoqda'")
    active_workers = await db.get_active_workers()
    surge = smart_dispatcher.calculate_surge_multiplier(len(active_orders), len(active_workers))

    total_price = raw_total * surge

    discount = 0.0
    if req.promo_code and req.promo_code.upper() == "VIP2026":
        discount = total_price * 0.15
        total_price -= discount

    return {
        "service_type": req.service_type,
        "base_unit_price": base_unit_price,
        "units": req.rooms_or_seats,
        "surge_multiplier": surge,
        "discount": discount,
        "final_price": round(total_price, -3),  # Minggacha yaxlitlash
        "currency": "UZS"
    }


@router.post("/book")
async def book_tma_order(req: BookingRequest, db: Database = Depends(get_db)):
    """TMA orqali 1-bosqichli to'g'ridan-to'g'ri buyurtma yaratish"""
    calc = await calculate_tma_price(
        CalculationRequest(
            service_type=req.service_type,
            area_sqm=req.area_sqm,
            promo_code=req.promo_code
        ),
        db=db
    )

    final_price = calc["final_price"]

    # Foydalanuvchini DB da tekshirish / yaratish
    client = await db.get_client_by_telegram_id(req.telegram_id)
    if not client:
        await db.create_client({
            "telegram_id": req.telegram_id,
            "name": req.client_name,
            "phone": req.client_phone,
            "address": req.address
        })
        client = await db.get_client_by_telegram_id(req.telegram_id)

    client_id = client["id"] if client else 1

    # Buyurtma yaratish
    order_id = await db.create_order({
        "client_id": client_id,
        "service_type": req.service_type,
        "price": final_price,
        "address": req.address,
        "lat": req.lat or 41.311081,
        "lon": req.lon or 69.240562,
        "scheduled_time": req.scheduled_time,
        "status": "kutilmoqda",
        "notes": f"TMA 2.0 orqali tushdi. Promo: {req.promo_code or 'yoq'}. Izoh: {req.notes or 'yoq'}"
    })

    # Smart Dispatch orqali eng yaxshi xodimni biriktirish
    dispatch_result = await smart_dispatcher.assign_optimal_worker(order_id)

    return {
        "status": "success",
        "order_id": order_id,
        "final_price": final_price,
        "scheduled_time": req.scheduled_time,
        "assigned_worker": dispatch_result.get("worker", {}).get("name") if dispatch_result else "Dispetcher tayinlaydi",
        "payment_links": {
            "payme": f"https://checkout.paycom.uz/{order_id}?amount={int(final_price * 100)}",
            "click": f"https://my.click.uz/services/pay?service_id=12345&merchant_id=54321&amount={final_price}&transaction_param={order_id}"
        }
    }
