from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    is_pro = Column(Boolean, default=False)

class ChatMemory(Base):
    __tablename__ = "chat_memory"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    message = Column(Text)
    response = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
