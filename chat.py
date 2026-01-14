from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from openai import OpenAI
import os
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from database import get_db, ChatMemory

router = APIRouter()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGO = os.getenv("JWT_ALGORITHM")

SYSTEM_PROMPT = "You are TestimAI, an expert in scam detection."

# In-memory guest limiter (simple & free)
guest_message_count = {}

class ChatRequest(BaseModel):
    message: str
    guest_id: str | None = None


def get_user_id_from_token(auth: str | None):
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
    user_id = get_user_id_from_token(authorization)

    # -------------------------
    # GUEST LIMIT
    # -------------------------
    if not user_id:
        gid = req.guest_id or "anon"
        count = guest_message_count.get(gid, 0)

        if count >= 1:
            return {"auth_required": True}

        guest_message_count[gid] = count + 1

    # -------------------------
    # CHAT LOGIC
    # -------------------------
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({"role": "user", "content": req.message})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    reply = response.choices[0].message.content

    # Save memory if logged in
    if user_id:
        db.add(ChatMemory(
            user_id=user_id,
            message=req.message,
            response=reply
        ))
        db.commit()

    return {"reply": reply}
