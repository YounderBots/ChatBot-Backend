from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from admin_service.models import get_db
from admin_service.models.models import (
    Intent,
    NLPSetting,
    QuickReply,
    Response,
    TrainingPhrase,
)
from admin_service.resources.utils import verify_authentication

router = APIRouter()


# -------------------------------------------------
# INTENTS
# -------------------------------------------------


@router.get("/intents")
def list_intents(request: Request, db: Session = Depends(get_db)):

    try:
        verify_authentication(request)

        intents = db.query(Intent).filter(Intent.status != "DELETED").all()

        return intents

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/intents")
def create_intent(request: Request, payload: dict, db: Session = Depends(get_db)):

    try:
        loginer_name, _, _ = verify_authentication(request)

        intent = Intent(
            name=payload["name"],
            intent_name=payload["intent_name"],
            description=payload.get("description"),
            category=payload.get("category"),
            priority=payload.get("priority"),
            context_requirement=payload.get("context_requirement"),
            context_output=payload.get("context_output"),
            fallback=payload.get("fallback"),
            confidence=payload.get("confidence", 60),
            response_status=payload.get("response_status"),
            status=payload.get("status"),
            created_by=loginer_name,
        )
        db.add(intent)
        db.commit()
        db.refresh(intent)

        phrases = payload.get("phrases")
        responses = payload.get("responses")

        # -------------------------------------------------
        # TRAINING PHRASES
        # -------------------------------------------------

        for phrase in phrases:

            trainingphrase = TrainingPhrase(
                intent_id=intent.id,
                phrase=phrase.get("phrase"),
                language=phrase.get("language"),
                created_by=loginer_name,
            )
            db.add(trainingphrase)

        # -------------------------------------------------
        # RESPONSES
        # -------------------------------------------------

        for response in responses:

            resp = Response(
                intent_id=intent.id,
                response_text=response.get("response_text"),
                response_type=response.get("response_type"),
                priority=response.get("priority"),
                created_by=loginer_name,
            )
            db.add(resp)
            db.refresh(resp)

            # -------------------------------------------------
            # QUICK REPLY
            # -------------------------------------------------

            quick_replies = response.get("quick_reply")

            if quick_replies:

                for reply in quick_replies:
                    quick_reply = QuickReply(
                        response_id=resp.id,
                        button_text=reply.get("button_text"),
                        action_type=reply.get("action_type"),
                        message_value=reply.get("message_value"),
                        created_by=loginer_name,
                    )
                    db.add(quick_reply)
                    db.refresh(quick_reply)

        return JSONResponse(content={"message": "Intent Saved Successfully"})

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/intents/{intent_id}")
def update_intent(intent_id: int, payload: dict, db: Session = Depends(get_db)):
    intent = db.query(Intent).filter(Intent.id == intent_id).first()
    if not intent:
        raise HTTPException(404, "Intent not found")

    intent.name = payload.get("name", intent.name)
    intent.description = payload.get("description", intent.description)
    intent.status = payload.get("status", intent.status)
    intent.confidence = payload.get("min_confidence", intent.confidence)
    intent.updated_at = datetime.utcnow()

    db.commit()
    return intent


@router.post("/intents/{intent_id}")
def delete_intent(intent_id: int, db: Session = Depends(get_db)):
    intent = db.query(Intent).filter(Intent.id == intent_id).first()
    if not intent:
        raise HTTPException(404, "Intent not found")

    db.delete(intent)
    db.commit()
    return {"status": "deleted"}


@router.post("/intents/{intent_id}/phrases")
def add_training_phrase(intent_id: int, payload: dict, db: Session = Depends(get_db)):
    phrase = TrainingPhrase(
        intent_id=intent_id,
        phrase=payload["phrase"],
        language=payload.get("language", "en"),
        created_at=datetime.utcnow(),
    )
    db.add(phrase)
    db.commit()
    db.refresh(phrase)
    return phrase


@router.get("/intents/{intent_id}/phrases")
def list_training_phrases(intent_id: int, db: Session = Depends(get_db)):
    return db.query(TrainingPhrase).filter(TrainingPhrase.intent_id == intent_id).all()


@router.post("/intents/{intent_id}/responses")
def add_response(intent_id: int, payload: dict, db: Session = Depends(get_db)):
    response = Response(
        intent_id=intent_id,
        response_text=payload["response_text"],
        response_type=payload.get("response_type"),
        priority=payload.get("priority", 1),
        language=payload.get("language", "en"),
        status=payload.get("status", True),
        created_at=datetime.utcnow(),
    )
    db.add(response)
    db.commit()
    db.refresh(response)
    return response


@router.get("/intents/{intent_id}/responses")
def list_responses(intent_id: int, db: Session = Depends(get_db)):
    return db.query(Response).filter(Response.intent_id == intent_id).all()


# -------------------------------------------------
# NLP SETTINGS
# -------------------------------------------------


@router.post("/nlp/settings")
def set_nlp_setting(payload: dict, db: Session = Depends(get_db)):
    setting = db.query(NLPSetting).filter(NLPSetting.key == payload["key"]).first()

    if setting:
        setting.value = payload["value"]
    else:
        setting = NLPSetting(
            key=payload["key"], value=payload["value"], created_at=datetime.utcnow()
        )
        db.add(setting)

    db.commit()
    return setting


@router.get("/nlp/settings")
def list_nlp_settings(db: Session = Depends(get_db)):
    return db.query(NLPSetting).all()


# -------------------------------------------------
# NLP TRAINING EXPORT (MOST IMPORTANT)
# -------------------------------------------------


@router.get("/nlp/export")
def export_nlp_training_data(db: Session = Depends(get_db)):
    intents = db.query(Intent).filter(Intent.status == "ACTIVE").all()

    export_data = {"intents": []}

    for intent in intents:
        phrases = (
            db.query(TrainingPhrase.phrase)
            .filter(TrainingPhrase.intent_id == intent.id)
            .all()
        )

        export_data["intents"].append(
            {"name": intent.name, "phrases": [p.phrase for p in phrases]}
        )

    return export_data
