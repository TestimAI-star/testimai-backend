from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI
import os, time
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from database import get_db, ChatMemory
from models import User

router = APIRouter()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGO = os.getenv("JWT_ALGORITHM")

SYSTEM_PROMPT = "You are TestimAI, an expert in scam detection."

# -------------------------
# RATE LIMIT STORAGE
# -------------------------
guest_message_count = {}   # guest_id -> count
user_rate_limit = {}       # user_id -> timestamps


class ChatRequest(BaseModel):
    message: str
    guest_id: str | None = None


# -------------------------
# AUTH HELPER
# -------------------------
def get_user_id_from_token(auth: str | None):
    if not auth:
        return None
    try:
        token = auth.replace("Bearer ", "")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload.get("user_id")
    except JWTError:
        return None


# =========================
# NORMAL CHAT (JSON)
# =========================
@router.post("/")
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    authorization: str | None = Header(None)
):
    user_id = get_user_id_from_token(authorization)

    if not user_id:
        gid = req.guest_id or "anon"
        count = guest_message_count.get(gid, 0)
        if count >= 1:
            return {"auth_required": True}
        guest_message_count[gid] = count + 1

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({"role": "user", "content": req.message})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    reply = response.choices[0].message.content

    if user_id:
        db.add(ChatMemory(
            user_id=user_id,
            message=req.message,
            response=reply
        ))
        db.commit()

    return {"reply": reply}


# =========================
# STREAMING CHAT (CHATGPT STYLE)
# =========================
@router.post("/chat-stream")
def chat_stream(
    req: ChatRequest,
    db: Session = Depends(get_db),
    authorization: str | None = Header(None)
):
    user_id = get_user_id_from_token(authorization)

    # ---------- GUEST LIMIT ----------
    if not user_id:
        gid = req.guest_id or "anon"
        count = guest_message_count.get(gid, 0)
        if count >= 1:
            async def blocked():
                yield "Please sign in to continue."
            return StreamingResponse(blocked(), media_type="text/plain")
        guest_message_count[gid] = count + 1

    # ---------- USER RATE LIMIT ----------
    if user_id:
        now = time.time()
        hits = user_rate_limit.get(user_id, [])
        hits = [t for t in hits if now - t < 60]

        user = db.query(User).get(user_id)
        limit = 100 if user and user.is_pro else 20

        if len(hits) >= limit:
            raise HTTPException(status_code=429, detail="Too many requests")

        hits.append(now)
        user_rate_limit[user_id] = hits

    # ---------- BUILD PROMPT ----------
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if user_id:
        memory = (
            db.query(ChatMemory)
            .filter(ChatMemory.user_id == user_id)
            .order_by(ChatMemory.id.desc())
            .limit(5)
            .all()
        )
        for m in reversed(memory):
            messages.append({"role": "user", "content": m.message})
            messages.append({"role": "assistant", "content": m.response})

    messages.append({"role": "user", "content": req.message})

    # ---------- STREAM ----------
    def stream():
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            stream=True
        )

        full_reply = ""

        for chunk in response:
            delta = chunk.choices[0].delta
            if delta and delta.get("content"):
                token = delta["content"]
                full_reply += token
                yield token

        if user_id:
            db.add(ChatMemory(
                user_id=user_id,
                message=req.message,
                response=full_reply
            ))
            db.commit()

    return StreamingResponse(stream(), media_type="text/plain")


# =========================
# CHAT HISTORY
# =========================
@router.get("/history")
def chat_history(
    db: Session = Depends(get_db),
    authorization: str | None = Header(None)
):
    user_id = get_user_id_from_token(authorization)

    if not user_id:
        raise HTTPException(status_code=401, detail="Login required")

    records = (
        db.query(ChatMemory)
        .filter(ChatMemory.user_id == user_id)
        .order_by(ChatMemory.id.desc())
        .limit(50)
        .all()
    )

    return [
        {"user": r.message, "assistant": r.response}
        for r in reversed(records)
    ]
