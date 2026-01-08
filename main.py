from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import router as auth_router
from chat import router as chat_router
from payments import router as payments_router
from webhooks import router as webhook_router
from database import Base, engine

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TestimAI API",
    description="AI-powered scam detection & analysis platform",
    version="1.0.0"
)

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(payments_router, prefix="/payments", tags=["Payments"])
app.include_router(webhook_router, prefix="/webhooks", tags=["Webhooks"])

@app.get("/")
def root():
    return {
        "name": "TestimAI",
        "status": "live",
        "message": "Welcome to TestimAI API"
    }
