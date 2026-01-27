import httpx
from configs.base_config import ServiceURL


async def analyze_text(
    text: str, ai_settings: dict, escalation_keywords: list, intent_phrases: dict
) -> dict:

    payload = {
        "text": text,
        "ai_settings": {
            "confidence_high": ai_settings.get("confidence_threshold", 60) / 100,
            "confidence_medium": (ai_settings.get("confidence_threshold", 60) - 20)
            / 100,
        },
        "escalation_keywords": escalation_keywords,
        "intent_phrases": intent_phrases,
    }

    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.post(ServiceURL.NLP_URL, json=payload)
        response.raise_for_status()
        return response.json()
