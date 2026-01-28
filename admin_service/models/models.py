from configs.base_config import Base
from models import engine
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Integer,
    String,
    Text,
    Time,
    func,
)


class Role(Base):

    __tablename__ = "role"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, index=True)
    name = Column(String(50), nullable=False, index=True)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class RolePermission(Base):

    __tablename__ = "role_permission"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, index=True)
    role_id = Column(Integer, nullable=False, index=True)
    menu_id = Column(String(50), nullable=True, index=True)
    add = Column(Boolean, nullable=True)
    edit = Column(Boolean, nullable=True)
    delete = Column(Boolean, nullable=True)
    view = Column(Boolean, nullable=True)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class SideMenuCategory(Base):

    __tablename__ = "sidemenu_category"

    id = Column(Integer, primary_key=True, index=True)
    menu_name = Column(String(255), nullable=False, index=True)
    menu_icon = Column(String(255), nullable=False)
    menu_link = Column(String(255), nullable=False)
    order_no = Column(Integer, nullable=False)
    status = Column(String(255), nullable=False)
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    updated_by = Column(String(255), nullable=False)


class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, index=True)
    fullname = Column(String(100), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True, index=True)
    profile_image = Column(Text, nullable=True)
    password = Column(String(100), nullable=False)
    role = Column(Integer, nullable=False)
    email_notification = Column(String(100), nullable=True)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class Customer(Base):

    __tablename__ = "customer"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True, index=True)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())


class Intent(Base):

    __tablename__ = "intents"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, index=True)
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

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class TrainingPhrase(Base):

    __tablename__ = "training_phrases"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, index=True)
    intent_id = Column(Integer, nullable=False, index=True)
    phrase = Column(Text, nullable=False)
    language = Column(String(10), default="en")
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class Response(Base):

    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, index=True)
    intent_id = Column(Integer, nullable=False, index=True)
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

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, index=True)
    response_id = Column(Integer, nullable=False, index=True)
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

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, index=True)
    name = Column(String(50), nullable=False, index=True)
    order = Column(Integer, unique=True, nullable=False)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class Article(Base):

    __tablename__ = "article"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, index=True)
    title = Column(String(50), nullable=False, index=True)
    category = Column(Integer, nullable=False)
    url = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    contents = Column(Text, nullable=True)
    meta_description = Column(Text, nullable=True)
    featured_image = Column(Text, nullable=True)
    article_status = Column(String(50), default="DRAFT")
    featured_article = Column(String(50), default=False)
    publish_date = Column(Date, nullable=False)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class RelatedQuestion(Base):

    __tablename__ = "related_questions"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, index=True)
    article_id = Column(Integer, nullable=False)
    question = Column(String(50), nullable=False, index=True)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


# -------------------------------------------------
#            SETTINGS & CONFIGURATION
# -------------------------------------------------


class UserGeneralSettings(Base):

    __tablename__ = "user_general_settings"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    bot_name = Column(String(100), nullable=False)
    bot_avatar = Column(Text, nullable=True)
    welcome_message = Column(Text, nullable=True)
    fallback_message = Column(Text, nullable=True)
    offline_message = Column(Text, nullable=True)
    # default_language = Column(String(10), default="en")
    outside_business_hour = Column(String(50), nullable=False)
    # timezone = Column(String(50), default="UTC")
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class UserBusinessHours(Base):

    __tablename__ = "user_business_hours"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    day = Column(String(50), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    timezone = Column(String(50), default="UTC")
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class UserAISettings(Base):

    __tablename__ = "user_ai_settings"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    description = Column(Text, nullable=True)
    confidence_threshold = Column(Integer, default=60)
    context_timeout = Column(Integer, default=40)
    max_conversation_length = Column(Integer, default=50)
    sentiment_analysis = Column(Boolean, nullable=True)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class UserEscalationSettings(Base):

    __tablename__ = "user_escalation_settings"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    auto_escalation_enabled = Column(Boolean, default=True)
    escalate_after_failures = Column(Integer, default=3)
    escalate_on_negative = Column(Boolean, default=False)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class UserEscalationKeywords(Base):

    __tablename__ = "user_escalation_keywords"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    escalation_keyword = Column(String(50), nullable=False)
    escalation_priority = Column(String(20), default="medium")
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class UserNotificationSettings(Base):

    __tablename__ = "user_notification_settings"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    email_notifications_enabled = Column(Boolean, default=True)
    notificaion_events = Column(Text, nullable=True)
    frequency = Column(String(50), nullable=False)
    admin_email = Column(String(255), nullable=True)
    push_notifications_admin = Column(Boolean, default=True)
    push_notificaion_events = Column(Text, nullable=True)
    in_app_notifications = Column(Boolean, default=True)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class UserUISettings(Base):

    __tablename__ = "user_ui_settings"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    widget_color = Column(String(20), nullable=True)
    widget_position = Column(String(20), default="bottom-right")
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class UserIntegrationSettings(Base):

    __tablename__ = "user_integration_settings"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    webhook_url = Column(Text, nullable=True)
    api_key = Column(String(255), nullable=True)
    slack_enabled = Column(Boolean, default=False)
    crm_enabled = Column(Boolean, default=False)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


class UserAdvancedSettings(Base):

    __tablename__ = "user_advanced_settings"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, nullable=False, index=True, unique=True)
    enable_continuous_learning = Column(Boolean, default=False)
    auto_add_to_training = Column(Boolean, default=False)
    review_queue_threshold = Column(Integer, default=40)
    data_retention_days = Column(Integer, default=90)
    enable_data_export = Column(Boolean, default=False)
    enable_data_deletion = Column(Boolean, default=False)
    show_privacy_policy_link = Column(Boolean, default=False)
    privacy_policy_url = Column(Text, nullable=True)
    log_level = Column(String(20), default="Info")
    enable_console_logs = Column(Boolean, default=True)
    enable_database_logs = Column(Boolean, default=False)
    language = Column(String(50), default="English")
    date_format = Column(String(20), default="DD/MM/YYYY")
    time_format = Column(String(20), default="24 Hour")
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    updated_by = Column(String(50), nullable=True)


Base.metadata.create_all(bind=engine)
