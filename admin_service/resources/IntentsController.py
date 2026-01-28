from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from models import get_db
from models.models import Intent, IntentCategory, QuickReply, Response, TrainingPhrase
from resources.utils import verify_authentication
from sqlalchemy.orm import Session

router = APIRouter()


# -------------------------------------------------
# INTENTS
# -------------------------------------------------


@router.get("/intents")
def list_intents(request: Request, db: Session = Depends(get_db)):

    try:
        verify_authentication(request)

        intents = db.query(Intent).filter(Intent.status != "DELETED").all()

        result = []

        for intent in intents:
            phrases = (
                db.query(TrainingPhrase)
                .filter(
                    TrainingPhrase.intent_id == intent.id,
                    TrainingPhrase.status != "DELETED",
                )
                .count()
            )
            responses = (
                db.query(Response)
                .filter(Response.intent_id == intent.id, Response.status != "DELETED")
                .count()
            )

            category = (
                db.query(IntentCategory)
                .filter(
                    IntentCategory.id == intent.category,
                    IntentCategory.status != "DELETED",
                )
                .first()
            )
            result.append(
                {
                    "id": intent.id,
                    "intent_name": intent.intent_name,
                    "name": intent.name,
                    "description": intent.description,
                    "category": intent.category,
                    "category_name": category.name if category else intent.category,
                    "priority": intent.priority,
                    "fallback": intent.fallback,
                    "confidence": intent.confidence,
                    "response_status": intent.response_status,
                    "approval_status": intent.approval_status,
                    "status": intent.status,
                    "phrases": phrases,
                    "responses": responses,
                    "usage": 0,
                    "last_modified": (
                        intent.updated_at if intent.updated_at else intent.created_at
                    ),
                }
            )

        return result

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/intents")
def create_intent(request: Request, payload: dict, db: Session = Depends(get_db)):

    try:
        user_id, _, _ = verify_authentication(request)

        print(payload)

        existing_intent = (
            db.query(Intent)
            .filter(
                (Intent.intent_name == payload["intent_name"]),
                Intent.status != "DELETED",
            )
            .first()
        )

        if existing_intent:
            raise HTTPException(
                status_code=409,
                detail="Intent with same intent_name already exists",
            )

        intent = Intent(
            name=payload["name"],
            intent_name=payload["intent_name"],
            description=payload.get("description"),
            category=payload.get("category"),
            priority=payload.get("priority"),
            fallback=payload.get("fallback"),
            confidence=payload.get("confidence", 60),
            response_status=payload.get("response_status"),
            status=payload.get("status"),
            created_by=user_id,
        )

        # -----------------------------
        # CONTEXT REQUIREMENT
        # -----------------------------
        value = payload.get("context_requirement")
        if isinstance(value, list):
            intent.context_requirement = ", ".join(value) if value else None
        elif isinstance(value, str):
            intent.context_requirement = value

        # -----------------------------
        # CONTEXT OUTPUT
        # -----------------------------
        value = payload.get("context_output")
        if isinstance(value, list):
            intent.context_output = ", ".join(value) if value else None
        elif isinstance(value, str):
            intent.context_output = value

        db.add(intent)
        db.flush()

        phrases = payload.get("phrases", [])
        responses = payload.get("responses", [])

        # -------------------------------------------------
        # TRAINING PHRASES
        # -------------------------------------------------

        for phrase in phrases:

            trainingphrase = TrainingPhrase(
                intent_id=intent.id,
                phrase=phrase.get("phrase"),
                language=phrase.get("language"),
                created_by=user_id,
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
                created_by=user_id,
            )
            db.add(resp)
            db.flush()

            # -------------------------------------------------
            # QUICK REPLY
            # -------------------------------------------------

            quick_replies = response.get("quick_reply", [])

            if quick_replies:

                for reply in quick_replies:
                    quick_reply = QuickReply(
                        response_id=resp.id,
                        button_text=reply.get("button_text"),
                        action_type=reply.get("action_type"),
                        message_value=reply.get("message_value"),
                        created_by=user_id,
                    )
                    db.add(quick_reply)

        db.commit()

        return {
            "status": "Success",
            "message": "Intent Saved Successfully",
            "intent_id": intent.id,
        }

    except Exception as e:
        print(e)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/updateintent/{intent_id}")
def update_intent(
    request: Request,
    intent_id: int,
    payload: dict,
    db: Session = Depends(get_db),
):
    try:
        user_id, _, _ = verify_authentication(request)

        intent = (
            db.query(Intent)
            .filter(Intent.id == intent_id, Intent.status != "DELETED")
            .first()
        )
        if not intent:
            raise HTTPException(404, "Intent not found")

        existing_intent = (
            db.query(Intent)
            .filter(
                (Intent.intent_name == payload["intent_name"]), Intent.id != intent.id
            )
            .first()
        )

        if existing_intent:
            raise HTTPException(
                status_code=409,
                detail="Intent with same intent_name already exists",
            )

        # -----------------------------
        # UPDATE INTENT
        # -----------------------------
        intent.name = payload.get("name", intent.name)
        intent.intent_name = payload.get("intent_name", intent.intent_name)
        intent.description = payload.get("description", intent.description)
        intent.category = payload.get("category", intent.category)
        intent.priority = payload.get("priority", intent.priority)
        intent.fallback = payload.get("fallback", intent.fallback)
        intent.confidence = payload.get("confidence", intent.confidence)
        intent.response_status = payload.get("response_status", intent.response_status)
        intent.status = payload.get("status", intent.status)
        intent.updated_at = datetime.utcnow()

        # -----------------------------
        # CONTEXT REQUIREMENT
        # -----------------------------
        if "context_requirement" in payload:
            value = payload.get("context_requirement")

            if isinstance(value, list):
                intent.context_requirement = ", ".join(value) if value else None
            elif isinstance(value, str):
                intent.context_requirement = value
            else:
                intent.context_requirement = None

        # -----------------------------
        # CONTEXT OUTPUT
        # -----------------------------

        if "context_output" in payload:
            value = payload.get("context_output")

            if isinstance(value, list):
                intent.context_output = ", ".join(value) if value else None
            elif isinstance(value, str):
                intent.context_output = value
            else:
                intent.context_output = None

        # -----------------------------
        # DELETE OLD DATA
        # -----------------------------
        db.query(TrainingPhrase).filter(TrainingPhrase.intent_id == intent_id).delete()

        responses = db.query(Response).filter(Response.intent_id == intent_id).all()

        for resp in responses:
            db.query(QuickReply).filter(QuickReply.response_id == resp.id).delete()

        db.query(Response).filter(Response.intent_id == intent_id).delete()

        # -----------------------------
        # ADD NEW TRAINING PHRASES
        # -----------------------------
        for phrase in payload.get("phrases", []):
            db.add(
                TrainingPhrase(
                    intent_id=intent.id,
                    phrase=phrase["phrase"],
                    language=phrase.get("language", "en"),
                    created_by=user_id,
                )
            )

        # -----------------------------
        # ADD NEW RESPONSES + QUICK REPLIES
        # -----------------------------
        for response in payload.get("responses", []):

            resp = Response(
                intent_id=intent.id,
                response_text=response.get("response_text"),
                response_type=response.get("response_type"),
                priority=response.get("priority", 1),
                created_by=user_id,
            )

            db.add(resp)
            db.flush()

            for reply in response.get("quick_reply", []):
                db.add(
                    QuickReply(
                        response_id=resp.id,
                        button_text=reply.get("button_text"),
                        action_type=reply.get("action_type"),
                        message_value=reply.get("message_value"),
                        created_by=user_id,
                    )
                )

        db.commit()

        return {"status": "Success", "message": "Intent Updated Successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(500, "Internal Server Error") from e


@router.post("/deleteintent/{intent_id}")
def delete_intent(request: Request, intent_id: int, db: Session = Depends(get_db)):

    try:
        user_id, _, _ = verify_authentication(request)
        intent = (
            db.query(Intent)
            .filter(Intent.id == intent_id, Intent.status != "DELETED")
            .first()
        )
        if not intent:
            raise HTTPException(404, "Intent not found")

        intent.status = "DELETED"
        intent.updated_by = user_id

        phrases = (
            db.query(TrainingPhrase).filter(TrainingPhrase.intent_id == intent.id).all()
        )

        for phrase in phrases:
            phrase.status = "DELETED"

        responses = db.query(Response).filter(Response.intent_id == intent.id).all()

        for response in responses:

            response.status = "DELETED"

            replies = (
                db.query(QuickReply).filter(QuickReply.response_id == response.id).all()
            )

            for reply in replies:
                reply.status = "DELETED"

        db.commit()
        return {"status": "Success", "message": "Intent Deleted Successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.get("/intents/{intent_id}/phrases")
def list_training_phrases(
    request: Request, intent_id: int, db: Session = Depends(get_db)
):

    try:
        verify_authentication(request)

        intent = (
            db.query(Intent)
            .filter(Intent.id == intent_id, Intent.status != "DELETED")
            .first()
        )

        if not intent:
            return {"message": f"Unable to Fetch Phrase for Intent ID {intent_id}"}

        phrase = (
            db.query(TrainingPhrase).filter(TrainingPhrase.intent_id == intent.id).all()
        )

        return phrase

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.get("/intents/{intent_id}/responses")
def list_responses(request: Request, intent_id: int, db: Session = Depends(get_db)):

    try:
        verify_authentication(request)

        intent = (
            db.query(Intent)
            .filter(Intent.id == intent_id, Intent.status != "DELETED")
            .first()
        )

        if not intent:
            return {"message": f"Unable to Fetch Response for Intent ID {intent_id}"}

        response = db.query(Response).filter(Response.intent_id == intent.id).all()

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.get("/intents/responses/{response_id}/quick_reply")
def list_quick_reply(request: Request, response_id: int, db: Session = Depends(get_db)):

    try:
        verify_authentication(request)

        response = (
            db.query(Response)
            .filter(Response.id == response_id, Response.status == "ACTIVE")
            .first()
        )

        if not response:
            return {
                "message": f"Unable to Fetch Quick Reply for Response ID {response_id}"
            }

        replies = (
            db.query(QuickReply).filter(QuickReply.response_id == response.id).all()
        )

        return replies

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.get("/category")
def list_intent_category(request: Request, db: Session = Depends(get_db)):

    try:
        verify_authentication(request)

        categories = (
            db.query(IntentCategory).filter(IntentCategory.status != "DELETED").all()
        )

        result = []

        for category in categories:
            result.append(
                {
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "last_modified": (
                        category.updated_at
                        if category.updated_at
                        else category.created_at
                    ),
                }
            )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/category")
def create_intent_category(
    request: Request, payload: dict, db: Session = Depends(get_db)
):

    try:
        user_id, _, _ = verify_authentication(request)

        existing_category = (
            db.query(IntentCategory)
            .filter(
                (IntentCategory.name == payload["name"]),
                IntentCategory.status != "DELETED",
            )
            .first()
        )

        if existing_category:
            raise HTTPException(
                status_code=409,
                detail="Intent with same category name already exists",
            )

        category = IntentCategory(
            name=payload["name"],
            description=payload["description"],
            created_by=user_id,
        )

        db.add(category)
        db.commit()

        return {
            "status": "Success",
            "message": "Category Saved Successfully",
            "category_id": category.id,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/updatecategory/{category_id}")
def update_intent_category(
    request: Request,
    category_id: int,
    payload: dict,
    db: Session = Depends(get_db),
):
    try:
        user_id, _, _ = verify_authentication(request)

        category = (
            db.query(IntentCategory)
            .filter(
                IntentCategory.id == category_id, IntentCategory.status != "DELETED"
            )
            .first()
        )
        if not category:
            raise HTTPException(404, "Intent not found")

        existing_category = (
            db.query(IntentCategory)
            .filter(
                (IntentCategory.name == payload["name"]),
                IntentCategory.id != category.id,
            )
            .first()
        )

        if existing_category:
            raise HTTPException(
                status_code=409,
                detail="Intent with same intent_name already exists",
            )

        # -----------------------------
        # UPDATE INTENT
        # -----------------------------
        category.name = payload.get("name", category.name)
        category.description = payload.get("description", category.description)
        category.updated_by = user_id

        db.commit()

        return {"status": "Success", "message": "Category Updated Successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(500, "Internal Server Error") from e


@router.post("/deletecategory/{category_id}")
def delete_intent_category(
    request: Request, category_id: int, db: Session = Depends(get_db)
):

    try:
        user_id, _, _ = verify_authentication(request)
        category = (
            db.query(IntentCategory)
            .filter(
                IntentCategory.id == category_id, IntentCategory.status != "DELETED"
            )
            .first()
        )
        if not category:
            raise HTTPException(404, "Intent not found")

        category.status = "DELETED"
        category.updated_by = user_id

        db.commit()
        return {"status": "Success", "message": "Category Deleted Successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e
