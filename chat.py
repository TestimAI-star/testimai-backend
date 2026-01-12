from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import os
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from database import get_db
from models import ChatMemory

router = APIRouter()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGO = os.getenv("JWT_ALGORITHM")

SYSTEM_PROMPT = """
You are TestimAI, an expert in scam detection, fraud analysis,
and problem solving. Be clear, calm, and helpful.
Learn from previous conversations when possible.
"""

class ChatRequest(BaseModel):
    message: str


def get_user_id_from_token(auth: str | None):
    """
    Extract user_id from JWT
    """
    if not auth:
        return None

    try:
        token = auth.replace("Bearer ", "")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload.get("user_id")
    except JWTError:
        return None


@router.post("/")
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    authorization: str | None = Header(None)
):
    # -------------------------
    # AUTH
    # -------------------------
    user_id = get_user_id_from_token(authorization)

    # -------------------------
    # LOAD MEMORY (last 5)
    # -------------------------
    memory_records = []

    if user_id:
        memory_records = (
            db.query(ChatMemory)
            .filter(ChatMemory.user_id == user_id)
            .order_by(ChatMemory.id.desc())
            .limit(5)
            .all()
        )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for record in reversed(memory_records):
        messages.append({"role": "user", "content": record.message})
        messages.append({"role": "assistant", "content": record.response})

    messages.append({"role": "user", "content": req.message})

    # -------------------------
    # OPENAI CALL
    # -------------------------
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    reply = response.choices[0].message.content

    # -------------------------
    # SAVE MEMORY
    # -------------------------
    if user_id:
        db.add(ChatMemory(
            user_id=user_id,
            message=req.message,
            response=reply
        ))
        db.commit()

    return {
        "reply": reply,
        "user": "logged_in" if user_id else "guest",
        "memory_used": len(memory_records)
    }

