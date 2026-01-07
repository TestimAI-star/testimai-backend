from fastapi import APIRouter, HTTPException
import requests
import os

router = APIRouter()

PAYSTACK_SECRET = os.getenv("PAYSTACK_SECRET")


@router.post("/paystack/init")
def init_paystack_payment(email: str):
    if not PAYSTACK_SECRET:
        raise HTTPException(status_code=500, detail="Paystack secret not set")

    response = requests.post(
        "https://api.paystack.co/transaction/initialize",
        headers={
            "Authorization": f"Bearer {PAYSTACK_SECRET}",
            "Content-Type": "application/json"
        },
        json={
            "email": email,
            "amount": 500000,  # ₦5,000 (kobo)
            "currency": "NGN",
            "callback_url": "https://testimai.io/payment-success"
        }
    )

    data = response.json()

    if not data.get("status"):
        raise HTTPException(status_code=400, detail="Payment initialization failed")

    return {
        "authorization_url": data["data"]["authorization_url"]
    }
