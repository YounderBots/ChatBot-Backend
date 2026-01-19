from datetime import datetime

from configs.base_config import Base
from models import engine
from sqlalchemy import Column, DateTime, Integer, String, Text


class Intent(Base):

    __tablename__ = "intents"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    status = Column(String(50), default=True)
    min_confidence = Column(Integer, default=60)  # percent
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class TrainingPhrase(Base):

    __tablename__ = "training_phrases"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    intent_id = Column(Integer, nullable=False)
    phrase = Column(Text, nullable=False)
    language = Column(String(10), default="en")
    created_at = Column(DateTime, default=datetime.utcnow)


class Response(Base):

    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    intent_id = Column(Integer, nullable=False)
    response_text = Column(Text, nullable=False)
    response_type = Column(String(100), nullable=True)
    priority = Column(Integer, default=1)
    language = Column(String(10), default="en")
    status = Column(String(50), default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class NLPSetting(Base):

    __tablename__ = "nlp_settings"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)
