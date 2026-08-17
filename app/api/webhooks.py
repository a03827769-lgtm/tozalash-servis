from fastapi import APIRouter, Header, HTTPException, Request
import hmac
import hashlib
from app.core.config import settings

router = APIRouter(prefix="/webhooks", tags=["Webhooks & Integrations"])

# Example Secret for verifying Payme/Click webhooks
WEBHOOK_SECRET = getattr(settings, "WEBHOOK_SECRET", "super-secret-key").encode()


@router.post("/payment-callback")
async def payment_callback(request: Request, x_signature: str = Header(None)):
    """
    Task 36: Webhook Security & Signature Verification.
    Ensures that incoming webhooks (e.g. from a payment gateway) are actually from the trusted source.
    """
    if not x_signature:
        raise HTTPException(status_code=401, detail="Missing signature header.")

    # Read the raw body for signature verification
    body = await request.body()

    # Calculate HMAC SHA256 signature
    expected_signature = hmac.new(
        WEBHOOK_SECRET, msg=body, digestmod=hashlib.sha256
    ).hexdigest()

    # Securely compare signatures to prevent timing attacks
    if not hmac.compare_digest(expected_signature, x_signature):
        raise HTTPException(status_code=403, detail="Invalid signature.")

    # Signature is valid, process webhook safely
    return {"status": "success", "message": "Webhook verified and processed."}
