from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from auth import router as auth
from chat import router as chat
from payments import router as payments
from webhooks import router as webhooks

app = FastAPI(title="TestimAI Backend")

# ✅ CORS (correct)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://testimai-frontend.onrender.com"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ CREATE TABLES ON STARTUP
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

app.include_router(auth, prefix="/auth", tags=["Auth"])
app.include_router(chat, prefix="/chat", tags=["Chat"])
app.include_router(payments, prefix="/payments", tags=["Payments"])
app.include_router(webhooks, prefix="/webhooks", tags=["Webhooks"])

@app.get("/")
def root():
    return {"status": "ok", "service": "TestimAI Backend"}

@app.get("/health")
def health():
    return {"ok": True}
