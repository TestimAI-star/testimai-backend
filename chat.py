import os
import httpx
from openai import OpenAI, DefaultHttpxClient
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from jose import jwt
import time

from database import get_db
from models import ChatMemory, User

router = APIRouter()

# --- FIX FOR PYTHON 3.13 TYPEERROR ---
# We manually create a client that doesn't trigger the 'proxies' error
http_client = DefaultHttpxClient()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    http_client=http_client
)
# -------------------------------------

JWT_SECRET = os.getenv("JWT_SECRET")
# ... (rest of your chat.py code)


JWT_ALGO = os.getenv("JWT_ALGORITHM", "HS256")

# --- 🛡️ ANTI-HACK SHIELD SETTINGS ---
BLACKLIST = ["ignore previous", "system prompt", "developer mode", "you are now", "jailbreak"]
guest_limit = {}
user_hits = {}

class ChatReq(BaseModel):
    message: str
    guest_id: str | None = None

def get_user_id(auth: str | None):
    if not auth: return None
    try:
        token = auth.replace("Bearer ", "")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload["user_id"]
    except: return None

@router.post("/stream")
def chat_stream(req: ChatReq, db: Session = Depends(get_db), authorization: str = Header(None)):
    user_id = get_user_id(authorization)

    # 1. SECURITY: Block Prompt Injection
    clean_msg = req.message.lower()
    if any(hack in clean_msg for hack in BLACKLIST):
        return StreamingResponse(iter(["[SYSTEM SHIELD]: Malicious activity blocked. Access logged."]), media_type="text/plain")

    # 2. LIMITS: Handle Guests vs Pro
    if not user_id:
        gid = req.guest_id or "anon"
        if guest_limit.get(gid, 0) >= 3: # Let guests have 3 tries instead of 1
            return StreamingResponse(iter(["AUTH_REQUIRED"]), media_type="text/plain")
        guest_limit[gid] = guest_limit.get(gid, 0) + 1
    else:
        user = db.query(User).filter(User.id == user_id).first()
        limit = 100 if user.is_pro else 20
        # Simple rate limiting logic
        now = time.time()
        hits = [t for t in user_hits.get(user_id, []) if now - t < 60]
        if len(hits) >= limit:
            raise HTTPException(429, "Rate limit exceeded. Upgrade to Pro!")
        hits.append(now)
        user_hits[user_id] = hits

    # 3. AI LOGIC: The "Specialist" Personality
    messages = [
        {"role": "system", "content": "You are TestimAI. Your vibe is electric, sharp, and protective. You specialize in detecting scams. Wrap warnings in [!!] brackets."},
        {"role": "user", "content": f"Analyze this input for scams or answer the query: {req.message}"}
    ]

    def stream():
        full_response = ""
        # Updated for OpenAI v1.30.0+ 2026 standards
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            stream=True
        )
        for chunk in completion:
            if chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                full_response += text
                yield text
        
        # Save to memory after stream finishes
        if user_id:
            new_db = SessionLocal() # Open fresh session for background save
            new_db.add(ChatMemory(user_id=user_id, message=req.message, response=full_response))
            new_db.commit()
            new_db.close()

    return StreamingResponse(stream(), media_type="text/plain")
