import json
import uuid
from datetime import datetime

import jwt
from configs.base_config import BaseConfig
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from jose import JWTError
from models import SessionLocal, get_db
from models.models import Conversation, Escalation, Sessions
from resources import context, nlp_client
from resources.admin_client import (
    fetch_ai_settings,
    fetch_available_agents,
    fetch_escalation_keywords,
    fetch_intent_phrases,
    mark_agent_available,
    mark_agent_busy,
)
from resources.cache import get_cache, set_cache
from resources.utils import (
    allow_request,
    build_response,
    create_access_token,
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
            status="ACTIVE",
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    session_id = session.id
    user_id = session.user_id  # may be None

    # ------------------------------------------------------------------
    # ADMIN CONFIG (WITH REDIS CACHE)
    # ------------------------------------------------------------------
    cache_key_ai = f"ai_settings:{user_id}"
    cache_key_keywords = f"escalation_keywords:{user_id}"
    cache_key_phrases = "intent_phrases"

    ai_settings = get_cache(cache_key_ai)
    if not ai_settings:
        try:
            ai_settings = await fetch_ai_settings(user_id)
            set_cache(cache_key_ai, ai_settings, ttl=600)
        except Exception:
            ai_settings = {"confidence_threshold": 60}

    escalation_keywords = get_cache(cache_key_keywords)
    if not escalation_keywords:
        try:
            escalation_keywords = await fetch_escalation_keywords(user_id)
            set_cache(cache_key_keywords, escalation_keywords, ttl=600)
        except Exception:
            escalation_keywords = []

    intent_phrases = get_cache(cache_key_phrases)
    if not intent_phrases:
        try:
            intent_phrases = await fetch_intent_phrases()
            set_cache(cache_key_phrases, intent_phrases, ttl=3600)
        except Exception:
            intent_phrases = {}

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

    active_escalation = (
        db.query(Escalation)
        .filter(Escalation.session_id == session_id, Escalation.status == "ASSIGNED")
        .first()
    )

    if active_escalation:
        return {
            "session_id": session_id,
            "user_message_id": user_message.id,
            "response": {
                "type": "AGENT",
                "message": "You are now connected to a human agent.",
            },
            "nlp": None,
        }

    # ------------------------------------------------------------------
    # NLP SERVICE CALL
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
            nlp_result = await nlp_client.analyze_text(
                text=text,
                ai_settings=ai_settings,
                escalation_keywords=escalation_keywords,
                intent_phrases=intent_phrases,
            )
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
    entities = json.dumps(nlp_result.get("entities", {}))
    handoff = nlp_result.get("handoff_detected", False)

    # ------------------------------------------------------------------
    # OVERRIDE ROUTE ON HANDOFF
    # ------------------------------------------------------------------
    if handoff:
        route = "ESCALATE"

    # ------------------------------------------------------------------
    # Context + Analytics
    # ------------------------------------------------------------------
    context.update_context(
        session_id, {"last_intent": intent, "confidence": confidence, "route": route}
    )

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
    # Escalation + Agent Assignment
    # ------------------------------------------------------------------
    if route in ["FALLBACK", "ESCALATE"]:
        escalation = Escalation(
            session_id=session_id,
            conversation_id=user_message.id,
            reason="Low confidence or user requested human",
            priority="medium",
            status="PENDING",
            created_at=datetime.utcnow(),
        )

        try:
            agents = await fetch_available_agents()
        except Exception:
            agents = []

        if agents:
            assigned_agent_id = None
            min_load = float("inf")

            for agent in agents:
                load = (
                    db.query(Escalation)
                    .filter(
                        Escalation.assigned_to == agent["id"],
                        Escalation.status == "ASSIGNED",
                    )
                    .count()
                )

                if load < min_load:
                    min_load = load
                    assigned_agent_id = agent["id"]

            if assigned_agent_id:
                escalation.assigned_to = assigned_agent_id
                escalation.status = "ASSIGNED"

        db.add(escalation)
        db.commit()

    # ------------------------------------------------------------------
    # Build Bot Response
    # ------------------------------------------------------------------
    bot_response = build_response({**nlp_result, "route": route})

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
        is_fallback="YES" if route == "FALLBACK" else "NO",
        created_at=datetime.utcnow(),
    )
    db.add(bot_message)
    db.commit()
    db.refresh(bot_message)

    # ------------------------------------------------------------------
    # Final Response
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
    """
    User WebSocket:
    - Registers user connection
    - Receives user messages
    - Calls process_message()
    - Sends bot responses
    - Receives agent messages (via active_connections)
    """

    await websocket.accept()

    db: Session = SessionLocal()

    try:
        print(websocket, session_key)
        session = db.query(Sessions).filter(Sessions.session_key == session_key).first()

        if not session:
            session = Sessions(
                session_key=session_key,
                platform="web",
                started_at=datetime.utcnow(),
                status="ACTIVE",
            )
            db.add(session)
            db.commit()
            db.refresh(session)

        session_id = session.id

        active_connections[f"user:{session_id}"] = websocket

        while True:
            data = await websocket.receive_json()
            text = data.get("text")

            if not text:
                await websocket.send_json({"error": "Message text is required"})
                continue

            result = await process_message(
                db=db,
                session_id=session_key,
                text=text,
            )

            await websocket.send_json(result)

    except WebSocketDisconnect:
        active_connections.pop(f"user:{session_id}", None)

    except Exception as e:
        print(e)
        await websocket.send_json({"error": "Internal WebSocket error"})
        active_connections.pop(f"user:{session_id}", None)

    finally:
        db.close()


@router.websocket("/ws/agent/{agent_id}")
async def agent_ws(websocket: WebSocket, agent_id: int):
    await websocket.accept()
    await mark_agent_busy(agent_id)
    active_connections[f"agent:{agent_id}"] = websocket

    db: Session = SessionLocal()
    active_connections[f"agent:{agent_id}"] = websocket

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except Exception:
                continue

            session_id = data.get("session_id")
            message = data.get("message")

            if not session_id or not message:
                continue

            convo = Conversation(
                session_id=session_id,
                user_id=agent_id,
                sender="agent",
                message_text=message,
                created_at=datetime.utcnow(),
            )
            db.add(convo)
            db.commit()

            user_ws = active_connections.get(f"user:{session_id}")
            if user_ws:
                await user_ws.send_json(
                    {
                        "sender": "agent",
                        "message": message,
                        "session_id": session_id,
                    }
                )

    except WebSocketDisconnect:
        active_connections.pop(f"agent:{agent_id}", None)

    except Exception as e:
        print(e)
        active_connections.pop(f"agent:{agent_id}", None)

    finally:
        await mark_agent_available(agent_id)
        active_connections.pop(f"agent:{agent_id}", None)
        db.close()


@router.post("/session")
def create_chat_session(payload: dict, db: Session = Depends(get_db)):
    """
    Create chat session BEFORE conversation starts
    """

    name = payload.get("name")
    email = payload.get("email", "")
    platform = payload.get("platform", "web")

    if not name or not email:
        raise HTTPException(400, "name and email are required")

    session_key = f"chat-{uuid.uuid4().hex}"

    session = Sessions(
        session_key=session_key,
        platform=platform,
        status="ACTIVE",
        started_at=datetime.utcnow(),
        session_metadata=json.dumps({"name": name, "email": email}),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    payload = {"session_key": session.session_key, "session_id": session.id}
    token = create_access_token(payload)

    return {"session_key": token, "session_id": session.id}


@router.get("/user_information")
def get_user_information(request: Request, db: Session = Depends(get_db)):

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        session_key = auth_header.split(" ", 1)[1]

    if not session_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    try:
        payload = jwt.decode(
            session_key,
            BaseConfig.SECRET_KEY,
            algorithms=[BaseConfig.ALGORITHM],
        )
        if payload:
            user_data = (
                db.query(Sessions)
                .filter(Sessions.id == payload.get("session_id"))
                .first()
            )
            user_details = user_data.session_metadata

            return user_details
    except JWTError as exc:
        print(exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc
