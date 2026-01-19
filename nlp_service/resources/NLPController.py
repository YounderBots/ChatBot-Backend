import httpx
from fastapi import APIRouter, HTTPException

from configs.base_config import BaseConfig
from resources import fallback

router = APIRouter()


@router.post("/parse")
async def parse(payload: dict):
    text = payload.get("text")

    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    rasa_result = await parse_text(text)

    intent = rasa_result["intent"]["name"]
    conf = rasa_result["intent"]["confidence"]

    entities = extract_entities(rasa_result.get("entities", []))

    route = classify_route(conf)
    handoff = detect_handoff(text)

    suggestions = []
    if route == "FALLBACK":
        suggestions = fallback.suggest_similar_intents(text)

    return {
        "intent": intent,
        "confidence": round(conf, 3),
        "entities": entities,
        "route": route,
        "handoff_detected": handoff,
        "fallback_suggestions": suggestions,
    }


async def parse_text(text: str) -> dict:
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.post(BaseConfig.RASA_URL, json={"text": text})
        response.raise_for_status()
        return response.json()


def classify_route(confidence: float) -> str:
    if confidence >= BaseConfig.CONFIDENCE_HIGH:
        return "NORMAL"
    elif confidence >= BaseConfig.CONFIDENCE_MEDIUM:
        return "CLARIFY"
    return "FALLBACK"


def detect_handoff(text: str) -> bool:
    text = text.lower()
    return any(keyword in text for keyword in BaseConfig.HANDOFF_KEYWORDS)


def trigger_training():
    """
    Stub for training trigger.
    In real use:
    - Export data from Admin Service
    - Run `rasa train`
    - Update training history
    """
    return {"status": "started", "message": "Training triggered successfully"}


def extract_entities(rasa_entities: list) -> dict:
    entities = {}
    for entity in rasa_entities:
        entities[entity["entity"]] = entity["value"]
    return entities
