from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from jose import jwt
import os, time
from openai import OpenAI

from database import get_db
from models import ChatMemory, User

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGO = os.getenv("JWT_ALGORITHM")

guest_limit = {}
user_hits = {}

class ChatReq(BaseModel):
    message: str
    guest_id: str | None = None

def get_user(auth):
    if not auth:
        return None
    try:
        token = auth.replace("Bearer ", "")
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])["user_id"]
    except:
        return None

@router.post("/chat-stream")
def chat(req: ChatReq, db: Session = Depends(get_db), authorization: str = Header(None)):
    user_id = get_user(authorization)

    if not user_id:
        gid = req.guest_id or "anon"
        if guest_limit.get(gid, 0) >= 1:
            return StreamingResponse(iter(["Please sign in to continue."]))
        guest_limit[gid] = 1

    if user_id:
        now = time.time()
        hits = user_hits.get(user_id, [])
        hits = [t for t in hits if now - t < 60]

        user = db.query(User).get(user_id)
        limit = 100 if user.is_pro else 20

        if len(hits) >= limit:
            raise HTTPException(429, "Rate limit exceeded")

        hits.append(now)
        user_hits[user_id] = hits

    messages = [{"role": "system", "content": "You are TestimAI, an expert in scam detection."}]
    messages.append({"role": "user", "content": req.message})

    def stream():
        full = ""
        for chunk in client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            stream=True
        ):
            if chunk.choices[0].delta.get("content"):
                text = chunk.choices[0].delta["content"]
                full += text
                yield text

        if user_id:
            db.add(ChatMemory(user_id=user_id, message=req.message, response=full))
            db.commit()

    return StreamingResponse(stream(), media_type="text/plain")
