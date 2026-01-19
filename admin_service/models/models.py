from configs.base_config import Base
from models import engine
from sqlalchemy import Column, DateTime, Integer, String, Text, func


class Role(Base):

    __tablename__ = "role"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class RolePermission(Base):

    __tablename__ = "role_permission"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    role_id = Column(Integer, nullable=False)
    menu = Column(String(50), nullable=True)
    add = Column(String(50), nullable=True)
    edit = Column(String(50), nullable=True)
    delete = Column(String(50), nullable=True)
    view = Column(String(50), nullable=True)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    full_name = Column(String(100), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    profile_image = Column(Text, nullable=True)
    password = Column(String(100), nullable=False)
    role = Column(Integer, nullable=False)
    email_notification = Column(String(100), nullable=True)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class Intent(Base):

    __tablename__ = "intents"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    intent_name = Column(String(100), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(Integer, nullable=False)
    priority = Column(String(50), nullable=False)
    context_requirement = Column(Text)
    context_output = Column(Text)
    fallback = Column(String(50), nullable=False)
    confidence = Column(Integer, default=60)  # percent
    response_status = Column(String(50), nullable=False, default=True)
    approval_status = Column(String(50), default="PENDING")
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class IntentCategory(Base):

    __tablename__ = "intent_category"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class TrainingPhrase(Base):

    __tablename__ = "training_phrases"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    intent_id = Column(Integer, nullable=False)
    phrase = Column(Text, nullable=False)
    language = Column(String(10), default="en")
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class Response(Base):

    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    intent_id = Column(Integer, nullable=False)
    response_text = Column(Text, nullable=False)
    response_type = Column(String(100), nullable=True)
    priority = Column(Integer, default=1)
    language = Column(String(10), default="en")
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class QuickReply(Base):

    __tablename__ = "quick_reply"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    response_id = Column(Integer, nullable=False)
    button_text = Column(String(50), nullable=False)
    action_type = Column(String(50), nullable=False)
    message_value = Column(Text, nullable=False)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class ArticleCategory(Base):

    __tablename__ = "article_category"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    order = Column(Integer, nullable=False)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class NLPSetting(Base):

    __tablename__ = "nlp_settings"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


Base.metadata.create_all(bind=engine)
