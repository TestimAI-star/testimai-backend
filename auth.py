from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import User
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os

router = APIRouter()

# ========================
# SECURITY CONFIG
# ========================

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-this")
JWT_ALGO = os.getenv("JWT_ALGORITHM", "HS256")
TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ========================
# SCHEMAS
# ========================

class AuthRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    token: str
    is_pro: bool

# ========================
# HELPERS
# ========================

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)

def create_token(user_id: int):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

def get_current_user(token: str = Depends(lambda: None), db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=401, detail="Token missing")

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401)

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401)

        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ========================
# ROUTES
# ========================

@router.post("/signup", response_model=TokenResponse)
def signup(data: AuthRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(
        email=data.email,
        password=hash_password(data.password),
        is_pro=False
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "token": create_token(user.id),
        "is_pro": user.is_pro
    }

@router.post("/login", response_model=TokenResponse)
def login(data: AuthRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "token": create_token(user.id),
        "is_pro": user.is_pro
    }

