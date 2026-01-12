from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
import models

from auth import router as auth_router
from chat import router as chat_router

# Create tables ON STARTUP
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

app.include_router(auth_router, prefix="/auth")
app.include_router(chat_router, prefix="/chat")


@app.get("/")
def root():
    return {"status": "TestimAI is live"}
