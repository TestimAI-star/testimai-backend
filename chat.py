from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from openai import OpenAI
import os

from database import get_db
from models import User, Memory

router = APIRouter()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT_FREE = """
You are TestimAI, created by Anderson Testimony.
You analyze messages and give basic scam and risk advice.
Be concise.
"""

SYSTEM_PROMPT_PRO = """
You are TestimAI PRO, created by Anderson Testimony.
You deeply analyze messages, detect scams, risks, manipulation,
and give step-by-step actionable advice.
Be detailed and precise.
"""


def get_current_user(db: Session = Depends(get_db)):
    # TEMP: single-user fallback
    # JWT validation will be added in deployment
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=401, detail="No user found")
    return user


@router.post("/")
def chat(message: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    prompt = SYSTEM_PROMPT_PRO if user.is_pro else SYSTEM_PROMPT_FREE

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": message}
        ]
    )

    reply = response.choices[0].message.content

    memory = Memory(
        user_id=user.id,
        user_message=message,
        ai_response=reply
    )
    db.add(memory)
    db.commit()

    return {"reply": reply, "pro": user.is_pro}
