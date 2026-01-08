from fastapi import APIRouter, Depends
from pydantic import BaseModel
from openai import OpenAI
import os
from sqlalchemy.orm import Session

from database import get_db, ChatMemory

router = APIRouter()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are TestimAI, an expert in scam detection, fraud analysis,
and problem solving. Be clear, calm, and helpful.
Learn from previous conversations when possible.
"""

class ChatRequest(BaseModel):
    message: str
    user_id: int | None = None  # None = guest user


@router.post("/")
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Main chat endpoint
    """

    # -------------------------
    # LOAD MEMORY (last 5 chats)
    # -------------------------
    memory_records = (
        db.query(ChatMemory)
        .filter(ChatMemory.user_id == req.user_id)
        .order_by(ChatMemory.id.desc())
        .limit(5)
        .all()
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add memory into context (oldest first)
    for record in reversed(memory_records):
        messages.append({"role": "user", "content": record.message})
        messages.append({"role": "assistant", "content": record.response})

    # Add new user message
    messages.append({"role": "user", "content": req.message})

    # -------------------------
    # CALL OPENAI
    # -------------------------
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    reply = response.choices[0].message.content

    # -------------------------
    # SAVE TO MEMORY
    # -------------------------
    new_memory = ChatMemory(
        user_id=req.user_id,
        message=req.message,
        response=reply
    )

    db.add(new_memory)
    db.commit()

    return {
        "reply": reply,
        "memory_used": len(memory_records)
    }
