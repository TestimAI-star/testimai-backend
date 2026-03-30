from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Get URL from Render Environment Variables
DATABASE_URL = os.getenv("DATABASE_URL")

# AUTO-FIX: Render uses postgres:// but SQLAlchemy 1.4+ needs postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Fallback for local testing if no DB is found
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./testim.db"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
