from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from models import get_db
from models.models import (
    UserAdvancedSettings,
    UserAISettings,
    UserBusinessHours,
    UserEscalationKeywords,
    UserEscalationSettings,
    UserGeneralSettings,
    UserNotificationSettings,
)
from resources.utils import verify_authentication
from sqlalchemy.orm import Session

router = APIRouter()


# --------------------------------------------------------
#                       GENERAL SETTINGS
# --------------------------------------------------------


@router.get("/general_settings")
def general_settings(request: Request, db: Session = Depends(get_db)):
    try:
        user_id, _, _ = verify_authentication(request)

        # -----------------------------
        # GENERAL SETTINGS
        # -----------------------------
        general = (
            db.query(UserGeneralSettings)
            .filter(UserGeneralSettings.user_id == int(user_id))
            .first()
        )

        if not general:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There is no Existing Settings for User {user_id}",
            )

        general_data = {
            "bot_name": general.bot_name,
            "bot_avatar": general.bot_avatar,
            "welcome_message": general.welcome_message,
            "fallback_message": general.fallback_message,
            "offline_message": general.offline_message,
            "outside_business_hour": general.outside_business_hour,
        }

        # -----------------------------
        # BUSINESS HOURS
        # -----------------------------
        business_hours = (
            db.query(UserBusinessHours)
            .filter(
                UserBusinessHours.user_id == int(user_id),
                UserBusinessHours.status == "ACTIVE",
            )
            .order_by(UserBusinessHours.id)
            .all()
        )

        hours = []
        timezone = "UTC"

        for bh in business_hours:
            timezone = bh.timezone or timezone
            hours.append(
                {
                    "day": bh.day,
                    "start_time": bh.start_time.strftime("%H:%M"),
                    "end_time": bh.start_end.strftime("%H:%M"),
                }
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "general": general_data,
                "business_hours": {"timezone": timezone, "hours": hours},
            },
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/general_settings")
def post_general_settings(
    request: Request, payload: dict, db: Session = Depends(get_db)
):
    try:
        user_id, _, _ = verify_authentication(request)

        # -----------------------------
        #       GENERAL SETTINGS
        # -----------------------------
        bot_config = payload.get("bot_configuration", {})

        existing = (
            db.query(UserGeneralSettings)
            .filter(UserGeneralSettings.user_id == int(user_id))
            .first()
        )

        if existing:
            existing.bot_name = bot_config.get("bot_name")
            existing.bot_avatar = bot_config.get("bot_avatar")
            existing.welcome_message = bot_config.get("welcome_message")
            existing.fallback_message = bot_config.get("fallback_message")
            existing.offline_message = bot_config.get("offline_message")
            existing.outside_business_hour = bot_config.get("outside_business_hour")

        else:
            new_settings = UserGeneralSettings(
                user_id=int(user_id),
                bot_name=bot_config.get("bot_name"),
                bot_avatar=bot_config.get("bot_avatar"),
                welcome_message=bot_config.get("welcome_message"),
                fallback_message=bot_config.get("fallback_message"),
                offline_message=bot_config.get("offline_message"),
                outside_business_hour=bot_config.get("outside_business_hour"),
            )
            db.add(new_settings)

        # -----------------------------
        #       BUSINESS HOURS
        # -----------------------------

        business_hours = payload.get("business_hours")

        if business_hours:
            timezone = business_hours.get("timezone", "UTC")
            hours = business_hours.get("hours", [])

            for bh in hours:
                raw_day = bh.get("day")

                if not raw_day:
                    raise HTTPException(
                        status_code=400, detail="Day is required for business hours"
                    )

                day = raw_day.strip().capitalize()

                start_time = bh.get("start_time")
                end_time = bh.get("end_time")

                if not start_time or not end_time:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Start Time and End Time are required for {day}",
                    )

                if start_time >= end_time:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Start Time must be before End Time for {day}",
                    )

                existing = (
                    db.query(UserBusinessHours)
                    .filter(
                        UserBusinessHours.user_id == int(user_id),
                        UserBusinessHours.day == day,
                        UserBusinessHours.status == "ACTIVE",
                    )
                    .first()
                )

                if existing:
                    # UPDATE
                    existing.start_time = start_time
                    existing.end_time = end_time
                    existing.timezone = timezone
                    existing.updated_by = str(user_id)

                else:
                    # INSERT
                    new_hour = UserBusinessHours(
                        user_id=int(user_id),
                        day=day,
                        start_time=start_time,
                        start_end=end_time,
                        timezone=timezone,
                        status="ACTIVE",
                        created_by=str(user_id),
                    )
                    db.add(new_hour)

        db.commit()

        return {"status": "Success", "message": "General settings saved successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


# --------------------------------------------------------
#                 CONVERSATION SETTINGS
# --------------------------------------------------------


@router.get("/conversation")
def get_conversation_settings(request: Request, db: Session = Depends(get_db)):
    try:
        user_id, _, _ = verify_authentication(request)

        # -----------------------------
        # AI SETTINGS
        # -----------------------------
        ai_settings = (
            db.query(UserAISettings)
            .filter(
                UserAISettings.user_id == int(user_id),
                UserAISettings.status == "ACTIVE",
            )
            .first()
        )

        if not ai_settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There is no Existing Settings for User {user_id}",
            )

        ai_configuration = {
            "description": ai_settings.description,
            "confidence_threshold": ai_settings.confidence_threshold,
            "context_timeout": ai_settings.context_timeout,
            "max_conversation_length": ai_settings.max_conversation_length,
            "sentiment_analysis": ai_settings.sentiment_analysis,
        }

        # -----------------------------
        # ESCALATION SETTINGS
        # -----------------------------
        escalation = (
            db.query(UserEscalationSettings)
            .filter(
                UserEscalationSettings.user_id == int(user_id),
                UserEscalationSettings.status == "ACTIVE",
            )
            .first()
        )

        auto_escalation = None
        if escalation:
            auto_escalation = {
                "auto_escalation_enabled": escalation.auto_escalation_enabled,
                "escalate_after_failures": escalation.escalate_after_failures,
                "escalate_on_negative": escalation.escalate_on_negative,
            }

        # -----------------------------
        # ESCALATION KEYWORDS
        # -----------------------------
        escalation_keywords_db = (
            db.query(UserEscalationKeywords)
            .filter(
                UserEscalationKeywords.user_id == int(user_id),
                UserEscalationKeywords.status == "ACTIVE",
            )
            .order_by(UserEscalationKeywords.id)
            .all()
        )

        escalation_keywords = [
            {
                "keyword": ek.escalation_keyword,
                "priority": ek.escalation_priority,
            }
            for ek in escalation_keywords_db
        ]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "ai_configuration": ai_configuration,
                "auto_escalation": auto_escalation,
                "escalation_keywords": escalation_keywords,
            },
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/conversation")
def post_conversation_settings(
    request: Request, payload: dict, db: Session = Depends(get_db)
):
    try:
        user_id, _, _ = verify_authentication(request)

        # -----------------------------
        #           AI SETTINGS
        # -----------------------------
        ai_config = payload.get("ai_configuration", {})

        ai_settings = (
            db.query(UserAISettings)
            .filter(
                UserAISettings.user_id == int(user_id),
                UserAISettings.status == "ACTIVE",
            )
            .first()
        )

        if ai_settings:
            # UPDATE
            ai_settings.description = (
                ai_config.get("description")
                if ai_config.get("description") is not None
                else ai_settings.description
            )

            ai_settings.confidence_threshold = (
                ai_config.get("confidence_threshold")
                if ai_config.get("confidence_threshold") is not None
                else ai_settings.confidence_threshold
            )

            ai_settings.context_timeout = (
                ai_config.get("context_timeout")
                if ai_config.get("context_timeout") is not None
                else ai_settings.context_timeout
            )

            ai_settings.max_conversation_length = (
                ai_config.get("max_conversation_length")
                if ai_config.get("max_conversation_length") is not None
                else ai_settings.max_conversation_length
            )

            ai_settings.sentiment_analysis = (
                ai_config.get("sentiment_analysis")
                if ai_config.get("sentiment_analysis") is not None
                else ai_settings.sentiment_analysis
            )

            ai_settings.updated_by = str(user_id)

        else:
            # ADD
            ai_settings = UserAISettings(
                user_id=int(user_id),
                description=ai_config.get("description"),
                confidence_threshold=ai_config.get("confidence_threshold", 60),
                context_timeout=ai_config.get("context_timeout", 40),
                max_conversation_length=ai_config.get("max_conversation_length", 50),
                sentiment_analysis=ai_config.get("sentiment_analysis"),
                status="ACTIVE",
                created_by=str(user_id),
            )
            db.add(ai_settings)

        # -----------------------------
        #     ESCALATION SETTINGS
        # -----------------------------
        escalation_config = payload.get("auto_escalation", {})

        escalation = (
            db.query(UserEscalationSettings)
            .filter(
                UserEscalationSettings.user_id == int(user_id),
                UserEscalationSettings.status == "ACTIVE",
            )
            .first()
        )

        if escalation:
            escalation.auto_escalation_enabled = (
                escalation_config.get("auto_escalation_enabled")
                if escalation_config.get("auto_escalation_enabled") is not None
                else escalation.auto_escalation_enabled
            )

            escalation.escalate_after_failures = (
                escalation_config.get("escalate_after_failures")
                if escalation_config.get("escalate_after_failures") is not None
                else escalation.escalate_after_failures
            )

            escalation.escalate_on_negative = (
                escalation_config.get("escalate_on_negative")
                if escalation_config.get("escalate_on_negative") is not None
                else escalation.escalate_on_negative
            )

            escalation.updated_by = str(user_id)

        else:
            # ADD
            escalation = UserEscalationSettings(
                user_id=int(user_id),
                auto_escalation_enabled=escalation_config.get(
                    "auto_escalation_enabled", True
                ),
                escalate_after_failures=escalation_config.get(
                    "escalate_after_failures", 3
                ),
                escalate_on_negative=escalation_config.get(
                    "escalate_on_negative", False
                ),
                status="ACTIVE",
                created_by=str(user_id),
            )
            db.add(escalation)

        db.commit()

        return {
            "status": "Success",
            "message": "Conversation settings saved successfully",
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/escalation/keywords")
def post_escalation_keywords(
    request: Request, payload: dict, db: Session = Depends(get_db)
):
    try:
        user_id, _, _ = verify_authentication(request)

        keywords = payload.get("keywords", [])

        if not keywords:
            raise HTTPException(400, "Keywords list cannot be empty")

        for item in keywords:
            raw_keyword = item.get("keyword")
            priority = item.get("priority")

            if not raw_keyword:
                continue

            keyword = raw_keyword.strip().lower()

            existing = (
                db.query(UserEscalationKeywords)
                .filter(
                    UserEscalationKeywords.user_id == int(user_id),
                    UserEscalationKeywords.escalation_keyword == keyword,
                    UserEscalationKeywords.status == "ACTIVE",
                )
                .first()
            )

            if existing:
                if priority is not None:
                    existing.escalation_priority = priority
                existing.updated_by = str(user_id)
            else:
                db.add(
                    UserEscalationKeywords(
                        user_id=int(user_id),
                        escalation_keyword=keyword,
                        escalation_priority=priority or "medium",
                        status="ACTIVE",
                        created_by=str(user_id),
                    )
                )

        db.commit()

        return {
            "status": "Success",
            "message": "Escalation keywords saved successfully",
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(500, "Internal Server Error") from e


# --------------------------------------------------------
#                 NOTIFICATION SETTINGS
# --------------------------------------------------------


@router.get("/notification_settings")
def notification_settings(request: Request, db: Session = Depends(get_db)):
    try:
        user_id, _, _ = verify_authentication(request)

        # -----------------------------
        # GENERAL SETTINGS
        # -----------------------------
        notification = (
            db.query(UserNotificationSettings)
            .filter(UserNotificationSettings.user_id == int(user_id))
            .first()
        )

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There is no Existing Settings for User {user_id}",
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"notification": notification},
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/notification_settings")
def post_notification_settings(
    request: Request, payload: dict, db: Session = Depends(get_db)
):
    try:
        user_id, _, _ = verify_authentication(request)

        notification_config = payload.get("notification", {})

        email_notifications = notification_config.get("email_notifications", {})
        push_notifications = notification_config.get("push_notifications", {})
        email_notifications = notification_config.get("email_notifications", {})

        events = email_notifications.get("notificaion_events")
        push_notification_events = push_notifications.get("notificaion_events")

        notification_events = ",".join(event for event in events)

        notification = (
            db.query(UserNotificationSettings)
            .filter(UserNotificationSettings.user_id == int(user_id))
            .first()
        )

        if notification:
            # -----------------------------
            # UPDATE
            # -----------------------------

            notification.email_notifications_enabled = (
                email_notifications.get("email_notification")
                if email_notifications.get("email_notification") is not None
                else notification.email_notifications_enabled
            )
            notification.admin_email = (
                email_notifications.get("admin_email")
                if email_notifications.get("admin_email") is not None
                else notification.admin_email
            )
            notification.notificaion_events = (
                notification_events
                if email_notifications.get("notificaion_events") is not None
                else notification.notificaion_events
            )
            notification.frequency = (
                notification_events
                if email_notifications.get("frequency") is not None
                else notification.frequency
            )
            notification.push_notifications_admin = (
                push_notifications.get("push_notification")
                if push_notifications.get("push_notifications") is not None
                else notification.push_notifications_admin
            )
            notification.push_notificaion_events = (
                push_notification_events
                if push_notifications.get("notificaion_events") is not None
                else notification.push_notificaion_events
            )
            notification.in_app_notifications = (
                notification_config.get("in_app")
                if notification_config.get("in_app")
                else notification.in_app_notifications
            )

            notification.updated_by = str(user_id)

        else:
            # -----------------------------
            # ADD
            # -----------------------------
            notification = UserNotificationSettings(
                user_id=int(user_id),
                email_notifications_enabled=(
                    email_notifications.get("email_notification")
                    if email_notifications.get("email_notification") is not None
                    else None
                ),
                admin_email=(
                    email_notifications.get("admin_email")
                    if email_notifications.get("admin_email") is not None
                    else None
                ),
                notificaion_events=(
                    notification_events
                    if email_notifications.get("notificaion_events") is not None
                    else None
                ),
                frequency=(
                    notification_events
                    if email_notifications.get("frequency") is not None
                    else None
                ),
                push_notifications_admin=(
                    push_notifications.get("push_notification")
                    if push_notifications.get("push_notifications") is not None
                    else None
                ),
                push_notificaion_events=(
                    push_notification_events
                    if push_notifications.get("notificaion_events") is not None
                    else None
                ),
                in_app_notifications=(
                    notification_config.get("in_app")
                    if notification_config.get("in_app")
                    else None
                ),
                status="ACTIVE",
                created_by=str(user_id),
            )
            db.add(notification)

        db.commit()

        return {
            "status": "Success",
            "message": "Notification settings saved successfully",
        }

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.get("/advanced_settings")
def get_advanced_settings(request: Request, db: Session = Depends(get_db)):
    try:
        user_id, _, _ = verify_authentication(request)

        settings = (
            db.query(UserAdvancedSettings)
            .filter(
                UserAdvancedSettings.user_id == int(user_id),
                UserAdvancedSettings.status == "ACTIVE",
            )
            .first()
        )

        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No advanced settings found for user {user_id}",
            )

        return {
            "training_learning": {
                "enable_continuous_learning": settings.enable_continuous_learning,
                "auto_add_to_training": settings.auto_add_to_training,
                "review_queue_threshold": settings.review_queue_threshold,
            },
            "data_privacy": {
                "data_retention_days": settings.data_retention_days,
                "enable_data_export": settings.enable_data_export,
                "enable_data_deletion": settings.enable_data_deletion,
                "show_privacy_policy_link": settings.show_privacy_policy_link,
                "privacy_policy_url": settings.privacy_policy_url,
            },
            "logging": {
                "log_level": settings.log_level,
                "enable_console_logs": settings.enable_console_logs,
                "enable_database_logs": settings.enable_database_logs,
            },
            "system": {
                "language": settings.language,
                "date_format": settings.date_format,
                "time_format": settings.time_format,
            },
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/advanced_settings")
def post_advanced_settings(
    request: Request, payload: dict, db: Session = Depends(get_db)
):
    try:
        user_id, _, _ = verify_authentication(request)

        training = payload.get("training_learning", {})
        privacy = payload.get("data_privacy", {})
        logging_cfg = payload.get("logging", {})
        system = payload.get("system", {})

        settings = (
            db.query(UserAdvancedSettings)
            .filter(
                UserAdvancedSettings.user_id == int(user_id),
                UserAdvancedSettings.status == "ACTIVE",
            )
            .first()
        )

        # -----------------------------
        # UPDATE
        # -----------------------------
        if settings:

            # Training & Learning
            if training.get("enable_continuous_learning") is not None:
                settings.enable_continuous_learning = training.get(
                    "enable_continuous_learning"
                )

            if training.get("auto_add_to_training") is not None:
                settings.auto_add_to_training = training.get("auto_add_to_training")

            if training.get("review_queue_threshold") is not None:
                settings.review_queue_threshold = training.get("review_queue_threshold")

            # Data & Privacy
            if privacy.get("data_retention_days") is not None:
                settings.data_retention_days = privacy.get("data_retention_days")

            if privacy.get("enable_data_export") is not None:
                settings.enable_data_export = privacy.get("enable_data_export")

            if privacy.get("enable_data_deletion") is not None:
                settings.enable_data_deletion = privacy.get("enable_data_deletion")

            if privacy.get("show_privacy_policy_link") is not None:
                settings.show_privacy_policy_link = privacy.get(
                    "show_privacy_policy_link"
                )

            if privacy.get("privacy_policy_url") is not None:
                settings.privacy_policy_url = privacy.get("privacy_policy_url")

            # Logging
            if logging_cfg.get("log_level") is not None:
                settings.log_level = logging_cfg.get("log_level")

            if logging_cfg.get("enable_console_logs") is not None:
                settings.enable_console_logs = logging_cfg.get("enable_console_logs")

            if logging_cfg.get("enable_database_logs") is not None:
                settings.enable_database_logs = logging_cfg.get("enable_database_logs")

            # System
            if system.get("language") is not None:
                settings.language = system.get("language")

            if system.get("date_format") is not None:
                settings.date_format = system.get("date_format")

            if system.get("time_format") is not None:
                settings.time_format = system.get("time_format")

            settings.updated_by = str(user_id)

        else:
            settings = UserAdvancedSettings(
                user_id=int(user_id),
                # Training & Learning
                enable_continuous_learning=training.get(
                    "enable_continuous_learning", False
                ),
                auto_add_to_training=training.get("auto_add_to_training", False),
                review_queue_threshold=training.get("review_queue_threshold", 40),
                # Data & Privacy
                data_retention_days=privacy.get("data_retention_days", 90),
                enable_data_export=privacy.get("enable_data_export", False),
                enable_data_deletion=privacy.get("enable_data_deletion", False),
                show_privacy_policy_link=privacy.get("show_privacy_policy_link", False),
                privacy_policy_url=privacy.get("privacy_policy_url"),
                # Logging
                log_level=logging_cfg.get("log_level", "Info"),
                enable_console_logs=logging_cfg.get("enable_console_logs", True),
                enable_database_logs=logging_cfg.get("enable_database_logs", False),
                # System
                language=system.get("language", "English"),
                date_format=system.get("date_format", "DD/MM/YYYY"),
                time_format=system.get("time_format", "24 Hour"),
                status="ACTIVE",
                created_by=str(user_id),
            )
            db.add(settings)

        db.commit()

        return {
            "status": "Success",
            "message": "Advanced settings saved successfully",
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e
