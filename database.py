from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Get the URL from your Render Env Vars
DATABASE_URL = os.getenv("DATABASE_URL")

# AUTO-FIX: Convert postgres:// to postgresql:// if needed
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Render External Connections REQUIRE sslmode=require
engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require"},  # This is the "magic" line for Render
    pool_pre_ping=True,                   # Checks if connection is alive before using it
    pool_recycle=300                      # Refreshes connections every 5 mins
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
