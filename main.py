from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
import models
from auth import router as auth
from chat import router as chat
from payments import router as payments
from webhooks import router as webhooks

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth, prefix="/auth")
app.include_router(chat, prefix="/chat")
app.include_router(payments, prefix="/payments")
app.include_router(webhooks, prefix="/webhooks")

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "TestimAI Backend",
        "message": "Backend is running"
    }

