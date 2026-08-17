from fastapi import APIRouter

from app.api.endpoints import (
    telegram_bot,
    instagram_bot,
    media_telephony,
    bigdata_iot,
    crm,
    finance,
    hr,
    inventory,
    messaging,
    payment,
    staff,
    clients,
    orders,
)

api_router = APIRouter()

api_router.include_router(
    telegram_bot.router, prefix="/bot/telegram", tags=["Telegram Bot"]
)
api_router.include_router(
    instagram_bot.router, prefix="/bot/instagram", tags=["Instagram Bot"]
)
api_router.include_router(
    media_telephony.router, prefix="/media", tags=["Media & Telephony"]
)
api_router.include_router(bigdata_iot.router, prefix="/data", tags=["Big Data & IoT"])
api_router.include_router(crm.router, prefix="/crm", tags=["CRM"])
api_router.include_router(
    finance.router, prefix="/finance", tags=["Moliya va Buxgalteriya"]
)
api_router.include_router(hr.router, prefix="/hr", tags=["Xodimlar (HR)"])
api_router.include_router(
    inventory.router, prefix="/inventory", tags=["Ombor va Inventar"]
)
api_router.include_router(
    messaging.router, prefix="/messaging", tags=["Xabarlar va E-mail"]
)
api_router.include_router(payment.router, prefix="/payment", tags=["Payment Webhooks"])
api_router.include_router(staff.router, prefix="/staff", tags=["Xodimlar"])
api_router.include_router(clients.router, prefix="/clients", tags=["Mijozlar"])
api_router.include_router(orders.router, prefix="/orders", tags=["Buyurtmalar"])
