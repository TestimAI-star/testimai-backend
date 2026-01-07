from fastapi import APIRouter, Request, Header, HTTPException
import hmac
import hashlib
import os

from database import SessionLocal
from models import User

router = APIRouter()

PAYSTACK_SECRET = os.getenv("PAYSTACK_SECRET")


@router.post("/paystack")
async def paystack_webhook(
    request: Request,
    x_paystack_signature: str = Header(None)
):
    if not PAYSTACK_SECRET:
        raise HTTPException(status_code=500, detail="Paystack secret not set")

    body = await request.body()

    computed_signature = hmac.new(
        PAYSTACK_SECRET.encode(),
        body,
        hashlib.sha512
    ).hexdigest()

    if computed_signature != x_paystack_signature:
        raise HTTPException(status_code=401, detail="Invalid Paystack signature")

    payload = await request.json()

    if payload.get("event") == "charge.success":
        email = payload["data"]["customer"]["email"]

        db = SessionLocal()
        user = db.query(User).filter(User.email == email).first()

        if user:
            user.is_pro = True
            db.commit()

        db.close()

    return {"status": "success"}
