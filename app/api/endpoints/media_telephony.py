"""
Phase 8 - Task 74: Watermark Service
Task 76: SIP Telephony / Call Tracking
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from PIL import Image, ImageDraw, ImageFont
import io
import os

router = APIRouter()


# --- Task 74: Watermark Service ---
@router.post("/watermark/image")
async def add_watermark(
    image: UploadFile = File(...), text: str = "Tozalash Servis © 2026"
):
    """
    Adds a text watermark to an uploaded image (Task 74).
    """
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are supported")

    contents = await image.read()
    img = Image.open(io.BytesIO(contents)).convert("RGBA")

    txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)

    # Use default font (no external font needed)
    font = ImageFont.load_default()
    w, h = img.size
    text_x, text_y = w - 200, h - 30

    draw.text((text_x, text_y), text, fill=(255, 255, 255, 128), font=font)

    watermarked = Image.alpha_composite(img, txt_layer)
    output = io.BytesIO()
    watermarked.convert("RGB").save(output, format="JPEG", quality=95)
    output.seek(0)

    from fastapi.responses import StreamingResponse

    return StreamingResponse(
        output,
        media_type="image/jpeg",
        headers={"Content-Disposition": "attachment; filename=watermarked.jpg"},
    )


# --- Task 76: SIP/VoIP Call Tracking ---
@router.post("/telephony/call-event")
async def receive_call_event(payload: dict):
    """
    Receives call events from Asterisk / VoIP PBX (Task 76).
    Records call logs for CRM integration.
    """
    call_id = payload.get("call_id")
    caller = payload.get("caller")
    duration = payload.get("duration_seconds", 0)
    # TODO: Save to DB, match caller to CRM client, trigger follow-up
    return {
        "status": "logged",
        "call_id": call_id,
        "caller": caller,
        "duration": duration,
    }
