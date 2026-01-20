from fastapi import APIRouter, Depends, Header, HTTPException
import requests, os
from database import get_db
from models import User
from jose import jwt

router = APIRouter()

PAYSTACK_SECRET = os.getenv("PAYSTACK_SECRET")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGO = os.getenv("JWT_ALGORITHM")

@router.post("/verify")
def verify_payment(
    reference: str,
    authorization: str = Header(...),
    db=Depends(get_db)
):
    token = authorization.replace("Bearer ", "")
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    user_id = payload["user_id"]

    res = requests.get(
        f"https://api.paystack.co/transaction/verify/{reference}",
        headers={"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    )

    data = res.json()

    if data.get("data", {}).get("status") == "success":
        user = db.query(User).get(user_id)
        user.is_pro = True
        db.commit()
        return {"status": "pro_activated"}

    raise HTTPException(400, "Payment not verified")
