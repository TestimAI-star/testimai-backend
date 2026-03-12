from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from auth import router as auth
from chat import router as chat
from payments import router as payments
from webhooks import router as webhooks

app = FastAPI(title="TestimAI API")

# Updated CORS for 2026 - Add your specific frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Change to your Vercel/Render URL in production
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
