from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import pyotp
import qrcode
import io
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/auth", tags=["Security & Auth"])


class Verify2FARequest(BaseModel):
    user_id: int
    totp_code: str


# In a real database, store this secret securely per user (Task 34 Vault Integration)
# Simulated DB storage:
USER_2FA_SECRETS = {}


@router.post("/setup-2fa")
async def setup_2fa(user_id: int):
    """
    Task 33: Setup 2FA. Generates a TOTP secret and returns a QR code.
    """
    secret = pyotp.random_base32()
    USER_2FA_SECRETS[user_id] = secret

    # Generate Provisioning URI for Google Authenticator
    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=f"User_{user_id}@TozalashServis", issuer_name="Tozalash Servis App"
    )

    qr = qrcode.make(uri)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")


@router.post("/verify-2fa")
async def verify_2fa(request: Verify2FARequest):
    """
    Task 33: Verify the 2FA code provided by the user.
    """
    secret = USER_2FA_SECRETS.get(request.user_id)
    if not secret:
        raise HTTPException(status_code=400, detail="2FA is not setup for this user.")

    totp = pyotp.TOTP(secret)
    if totp.verify(request.totp_code):
        # Code is valid. Proceed to issue JWT.
        return {"status": "success", "message": "2FA verification passed."}
    else:
        raise HTTPException(status_code=401, detail="Invalid 2FA code.")
