from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from database import get_db
from models import User
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import os

router = APIRouter()
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGO = os.getenv("JWT_ALGORITHM")

class AuthIn(BaseModel):
    email: EmailStr
    password: str

def create_token(user_id: int):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

@router.post("/signup")
def signup(data: AuthIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Email already exists")

    user = User(
        email=data.email,
        password=pwd.hash(data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "token": create_token(user.id),
        "is_pro": False
    }

@router.post("/login")
def login(data: AuthIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not pwd.verify(data.password, user.password):
        raise HTTPException(401, "Invalid credentials")

    return {
        "token": create_token(user.id),
        "is_pro": user.is_pro
    }
