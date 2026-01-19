from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
import models

from auth import router as auth_router
from chat import router as chat_router
from payments import router as payments_router
from webhooks import router as webhooks_router

# CREATE TABLES
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TestimAI API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ROUTES
app.include_router(auth_router, prefix="/auth")
app.include_router(chat_router, prefix="/chat")
app.include_router(payments_router, prefix="/payments")
app.include_router(webhooks_router, prefix="/webhooks")


@app.get("/")
def root():
    return {"status": "TestimAI is live"}
