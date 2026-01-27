import httpx
from configs.base_config import ServiceURL


async def fetch_ai_settings(user_id: int) -> dict:
    async with httpx.AsyncClient(timeout=5) as client:
        res = await client.get(
            f"{ServiceURL.ADMIN_BASE_URL}/user/{user_id}/ai-settings"
        )
        res.raise_for_status()
        return res.json()


async def fetch_escalation_keywords(user_id: int) -> list:
    async with httpx.AsyncClient(timeout=5) as client:
        res = await client.get(
            f"{ServiceURL.ADMIN_BASE_URL}/user/{user_id}/escalation-keywords"
        )
        res.raise_for_status()
        data = res.json()
        return data.get("keywords", [])


async def fetch_intent_phrases() -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.get(f"{ServiceURL.ADMIN_BASE_URL}/nlp/export")
        res.raise_for_status()
        data = res.json()

    intent_phrases = {}

    for intent in data.get("intents", []):
        intent_phrases[intent["name"]] = intent.get("phrases", [])

    return intent_phrases
