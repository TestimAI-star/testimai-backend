from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from auth import router as auth
from chat import router as chat
from payments import router as payments
from webhooks import router as webhooks

app = FastAPI(title="TestimAI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://testimai-frontend.onrender.com",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
)

# 🔑 THIS HANDLES PREFLIGHT PROPERLY (CRITICAL)
@app.options("/{path:path}")
async def options_handler(path: str, request: Request):
    return Response(status_code=200)

app.include_router(auth, prefix="/auth", tags=["Auth"])
app.include_router(chat, prefix="/chat", tags=["Chat"])
app.include_router(payments, prefix="/payments", tags=["Payments"])
app.include_router(webhooks, prefix="/webhooks", tags=["Webhooks"])

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "TestimAI Backend"
    }

@app.get("/health")
def health():
    return {"ok": True}
