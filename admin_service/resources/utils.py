import logging
from datetime import datetime
from time import time

from configs.redis import redis_client

logger = logging.getLogger("chat_analytics")


# Response Builder


def build_response(nlp_result: dict) -> dict:
    route = nlp_result["route"]

    if nlp_result["handoff_detected"]:
        return {"type": "ESCALATE", "message": "Connecting you to a human agent."}

    if route == "NORMAL":
        return {"type": "BOT", "message": f"Handling intent: {nlp_result['intent']}"}

    if route == "CLARIFY":
        return {"type": "CLARIFY", "message": "Can you please clarify your request?"}

    if route == "FALLBACK":
        suggestions = nlp_result.get("fallback_suggestions", [])
        if suggestions:
            return {
                "type": "SUGGEST",
                "message": "Did you mean one of these?",
                "options": suggestions,
            }

        return {"type": "BOT", "message": "I'm sorry, I didn't understand that."}


# Escalation


def should_escalate(nlp_result: dict) -> bool:
    return nlp_result["handoff_detected"] or nlp_result["route"] == "FALLBACK"


# Logging Events


def log_event(event_type: str, payload: dict):
    payload["event"] = event_type
    payload["timestamp"] = datetime.utcnow().isoformat()
    logger.info(payload)


# Circuit Breaker


FAILURE_LIMIT = 5
COOLDOWN_SECONDS = 30


def _failures_key(service: str) -> str:
    return f"cb:{service}:failures"


def _open_until_key(service: str) -> str:
    return f"cb:{service}:open_until"


def allow_request(service: str) -> bool:
    open_until = redis_client.get(_open_until_key(service))
    if not open_until:
        return True
    return time() > float(open_until)


def record_failure(service: str):
    failures = redis_client.incr(_failures_key(service))

    if failures >= FAILURE_LIMIT:
        redis_client.set(
            _open_until_key(service), time() + COOLDOWN_SECONDS, ex=COOLDOWN_SECONDS
        )


def record_success(service: str):
    redis_client.delete(_failures_key(service))
    redis_client.delete(_open_until_key(service))
