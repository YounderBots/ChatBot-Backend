import httpx
from configs.base_config import BaseConfig
from fastapi import APIRouter, HTTPException
from resources.utils import extract_entities, similarity_fallback

router = APIRouter()


@router.post("/parse")
async def parse(payload: dict):
    text = payload.get("text")
    ai_settings = payload.get("ai_settings", {})
    escalation_keywords = payload.get("escalation_keywords", [])
    intent_phrases = payload.get("intent_phrases", {})

    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    # -------------------------------
    # Call Rasa
    # -------------------------------
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.post(
                BaseConfig.RASA_URL,
                json={"text": text},
            )
            response.raise_for_status()
            rasa_result = response.json()
    except Exception as e:
        return {
            "error": e,
            "intent": "system_error",
            "confidence": 0.0,
            "entities": {},
            "route": "FALLBACK",
            "handoff_detected": True,
            "fallback_suggestions": [],
        }

    intent = rasa_result["intent"]["name"]
    confidence = rasa_result["intent"]["confidence"]
    entities = extract_entities(rasa_result.get("entities", []))

    # -------------------------------
    # Confidence routing
    # -------------------------------
    high = ai_settings.get("confidence_high", 0.6)
    medium = ai_settings.get("confidence_medium", 0.4)

    if confidence >= high:
        route = "NORMAL"
    elif confidence >= medium:
        route = "CLARIFY"
    else:
        route = "FALLBACK"

    # -------------------------------
    # Handoff keyword detection
    # -------------------------------
    text_lower = text.lower()
    handoff_detected = any(k.lower() in text_lower for k in escalation_keywords)

    # -------------------------------
    # Similarity fallback
    # -------------------------------
    suggestions = []
    if route == "FALLBACK" and intent_phrases:
        suggestions = similarity_fallback(text, intent_phrases)

    # -------------------------------
    # Final NLP response
    # -------------------------------
    return {
        "intent": intent,
        "confidence": round(confidence, 3),
        "entities": entities,
        "route": route,
        "handoff_detected": handoff_detected,
        "fallback_suggestions": suggestions,
    }


async def parse_text(text: str) -> dict:
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.post(BaseConfig.RASA_URL, json={"text": text})
        response.raise_for_status()
        return response.json()
