from datetime import datetime

from configs.base_config import Base
from models import engine
from sqlalchemy import Column, DateTime, Float, Integer, String, Text


class Sessions(Base):

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)

    session_key = Column(String(255), unique=True, nullable=False)
    user_id = Column(Integer, nullable=True)
    platform = Column(String(50), nullable=False)
    ip_address = Column(Text)
    user_agent = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String(50), default=True)
    metadata = Column(Text)


class Conversation(Base):

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)

    session_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=True)
    sender = Column(String(100), nullable=False)
    message_text = Column(Text, nullable=False)
    message_type = Column(String(100))
    intent_detected = Column(String(100))
    confidence_score = Column(Float)
    entities = Column(Text)
    sentiment = Column(String(100), nullable=True)
    language = Column(String(10), default="en")
    response_time_ms = Column(Integer)
    is_fallback = Column(String(100), default=False)
    metadata = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Escalation(Base):

    __tablename__ = "escalations"

    id = Column(Integer, primary_key=True, autoincrement=True)

    session_id = Column(Integer, nullable=False)
    conversation_id = Column(Integer, nullable=True)
    reason = Column(String(255))
    priority = Column(String(100))
    status = Column(String(100), nullable=False)
    assigned_to = Column(Integer, nullable=True)
    assigned_at = Column(DateTime)
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Feedback(Base):

    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)

    session_id = Column(Integer, nullable=False)
    conversation_id = Column(Integer, nullable=True)
    rating = Column(Integer)  # 1–5
    feedback_type = Column(String(100))
    comment = Column(Text)
    sentiment = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)
