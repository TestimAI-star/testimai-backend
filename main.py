import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from auth import router as auth
from chat import router as chat

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    # This ensures your Postgres tables are created automatically
    Base.metadata.create_all(bind=engine)

app.include_router(auth, prefix="/auth")
app.include_router(chat, prefix="/chat")

@app.get("/")
def health_check():
    return {"status": "online"}

if __name__ == "__main__":
    # Render provides the port via the PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
