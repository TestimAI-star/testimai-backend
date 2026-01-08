from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI
import os

router = APIRouter()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Temporary in-memory store (we upgrade later)
conversation_memory = {}

class ChatRequest(BaseModel):
    message: str
    user_id: str = "guest"

@router.post("/")
def chat(req: ChatRequest):
    history = conversation_memory.get(req.user_id, [])

    history.append({"role": "user", "content": req.message})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are TestimAI, an expert at scam detection and problem analysis."},
            *history
        ]
    )

    reply = response.choices[0].message.content
    history.append({"role": "assistant", "content": reply})

    conversation_memory[req.user_id] = history[-10:]  # keep last 10 messages

    return {"reply": reply}
