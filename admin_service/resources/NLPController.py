from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from models import get_db
from models.models import Intent, TrainingPhrase
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/export")
def export_nlp_training_data(db: Session = Depends(get_db)):
    """
    Export approved & active NLP training data
    for NLP Service (RASA training + similarity fallback)
    """

    # 1️⃣ Fetch APPROVED + ACTIVE intents
    intents = (
        db.query(Intent)
        .filter(Intent.status == "ACTIVE", Intent.approval_status == "APPROVED")
        .all()
    )

    export_data = {"intents": []}

    for intent in intents:

        # 2️⃣ Fetch ACTIVE training phrases
        phrases = (
            db.query(TrainingPhrase.phrase)
            .filter(
                TrainingPhrase.intent_id == intent.id, TrainingPhrase.status == "ACTIVE"
            )
            .all()
        )

        phrase_list = [p.phrase for p in phrases]

        # Skip intents without phrases
        if not phrase_list:
            continue

        export_data["intents"].append(
            {"name": intent.intent_name, "phrases": phrase_list}
        )
        print(export_data)

    return export_data
