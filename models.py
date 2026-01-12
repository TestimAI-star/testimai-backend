from sqlalchemy import Column, Integer, String, Boolean, Text
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    is_pro = Column(Boolean, default=False)


class ChatMemory(Base):
    __tablename__ = "chat_memory"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
