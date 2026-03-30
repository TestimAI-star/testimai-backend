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

# Fix for Python 3.13 Proxy Error
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    http_client=DefaultHttpxClient()
)

JWT_SECRET = os.getenv("JWT_SECRET")

class ChatReq(BaseModel):
    message: str
    guest_id: str | None = None

@router.post("/stream")
async def chat_stream(req: ChatReq, db: Session = Depends(get_db), authorization: str = Header(None)):
    user_id = None
    if authorization:
        try:
            token = authorization.replace("Bearer ", "")
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user_id = payload.get("user_id")
        except: pass

    def stream():
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": req.message}],
            stream=True
        )
        for chunk in completion:
            if chunk.choices.delta.content:
                yield chunk.choices.delta.content

    return StreamingResponse(stream(), media_type="text/plain")
