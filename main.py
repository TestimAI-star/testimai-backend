import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from auth import router as auth
from chat import router as chat
from payments import router as payments
from webhooks import router as webhooks

app = FastAPI(title="TestimAI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

app.include_router(auth, prefix="/auth")
app.include_router(chat, prefix="/chat")
app.include_router(payments, prefix="/payments")
app.include_router(webhooks, prefix="/webhooks")

@app.get("/")
def home():
    return {"message": "TestimAI Online", "status": "Secure"}

# This block is the "Render Secret Sauce" for Python 3.13
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
