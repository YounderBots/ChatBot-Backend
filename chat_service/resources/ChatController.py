from datetime import datetime

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from models import SessionLocal
from models.models import Conversation, Escalation, Sessions
from resources import context, nlp_client
from resources.utils import (
    allow_request,
    build_response,
    log_event,
    record_failure,
    record_success,
)
from sqlalchemy.orm import Session

router = APIRouter()


# ------------------------------------------------------------------
# Websocket
# ------------------------------------------------------------------


@router.websocket("/ws/chat/{session_key}")
async def websocket_chat(websocket: WebSocket, session_key: str):
    await chat_ws(websocket, session_key)


@router.post("/message")
async def chat(payload: dict):
    session_key = payload.get("session_id")
    text = payload.get("text")

    if not session_key or not text:
        raise HTTPException(400, "session_id and text required")

    db: Session = SessionLocal()
    try:
        return await process_message(db=db, session_id=session_key, text=text)
    finally:
        db.close()


# ------------------------------------------------------------------
# Process Message Helper Function
# ------------------------------------------------------------------
async def process_message(db: Session, session_id: str, text: str, platform="web"):
    """
    Core chat processing pipeline.
    All DB operations are INLINE as requested.
    """

    # ------------------------------------------------------------------
    # Get or Create Session
    # ------------------------------------------------------------------
    session = db.query(Sessions).filter(Sessions.session_key == session_id).first()

    if not session:
        session = Sessions(
            session_key=session_id,
            platform=platform,
            started_at=datetime.utcnow(),
            is_active=True,
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    session_id = session.id

    # ------------------------------------------------------------------
    # Save USER message
    # ------------------------------------------------------------------
    user_message = Conversation(
        session_id=session_id,
        sender="user",
        message_text=text,
        created_at=datetime.utcnow(),
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # ------------------------------------------------------------------
    # NLP SERVICE CALL WITH CIRCUIT BREAKER
    # ------------------------------------------------------------------
    service_name = "nlp_service"

    if not allow_request(service_name):
        nlp_result = {
            "intent": "system_unavailable",
            "confidence": 0.0,
            "route": "FALLBACK",
            "handoff_detected": True,
        }
    else:
        try:
            nlp_result = await nlp_client.analyze_text(text)
            record_success(service_name)
        except Exception:
            record_failure(service_name)
            nlp_result = {
                "intent": "system_error",
                "confidence": 0.0,
                "route": "FALLBACK",
                "handoff_detected": True,
            }

    intent = nlp_result.get("intent")
    confidence = nlp_result.get("confidence")
    route = nlp_result.get("route")
    entities = nlp_result.get("entities", {})
    handoff = nlp_result.get("handoff_detected", False)

    # ------------------------------------------------------------------
    # Update Redis Context
    # ------------------------------------------------------------------
    context.update_context(
        session_id, {"last_intent": intent, "confidence": confidence, "route": route}
    )

    # ------------------------------------------------------------------
    # Analytics Hook (NON-BLOCKING)
    # ------------------------------------------------------------------
    log_event(
        "nlp_processed",
        {
            "session_id": session_id,
            "intent": intent,
            "confidence": confidence,
            "route": route,
        },
    )

    # ------------------------------------------------------------------
    # Escalation Logic (INLINE DB WRITE)
    # ------------------------------------------------------------------
    if handoff or route == "FALLBACK":
        escalation = Escalation(
            session_id=session_id,
            conversation_id=user_message.id,
            reason="Low confidence or user requested human",
            priority="medium",
            status="pending",
            created_at=datetime.utcnow(),
        )
        db.add(escalation)
        db.commit()

    # ------------------------------------------------------------------
    # Build Bot Response (Decision Engine)
    # ------------------------------------------------------------------
    bot_response = build_response(nlp_result)

    # ------------------------------------------------------------------
    # Save BOT message
    # ------------------------------------------------------------------
    bot_message = Conversation(
        session_id=session_id,
        sender="bot",
        message_text=bot_response["message"],
        intent_detected=intent,
        confidence_score=confidence,
        entities=entities,
        is_fallback=(route == "FALLBACK"),
        created_at=datetime.utcnow(),
    )
    db.add(bot_message)
    db.commit()
    db.refresh(bot_message)

    # ------------------------------------------------------------------
    # Final Response to Client
    # ------------------------------------------------------------------
    return {
        "session_id": session_id,
        "user_message_id": user_message.id,
        "bot_message_id": bot_message.id,
        "response": bot_response,
        "nlp": {"intent": intent, "confidence": confidence, "route": route},
    }


# ------------------------------------------------------------------
# Websocket Helper Function
# ------------------------------------------------------------------


active_connections = {}


async def chat_ws(websocket: WebSocket, session_key: str):
    await websocket.accept()
    active_connections[session_key] = websocket

    db: Session = SessionLocal()

    try:
        while True:
            data = await websocket.receive_json()
            text = data.get("text")

            result = await process_message(db=db, session_id=session_key, text=text)

            await websocket.send_json(result)

    except WebSocketDisconnect:
        active_connections.pop(session_key, None)
    finally:
        db.close()
