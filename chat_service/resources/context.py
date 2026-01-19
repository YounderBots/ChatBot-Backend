import json

from configs.redis import redis_client

TTL_SECONDS = 1800  # 30 minutes


def get_context(session_id: int) -> dict:
    data = redis_client.get(f"context:{session_id}")
    return json.loads(data) if data else {}


def update_context(session_id: int, updates: dict):
    context = get_context(session_id)
    context.update(updates)
    redis_client.setex(f"context:{session_id}", TTL_SECONDS, json.dumps(context))


def clear_context(session_id: int):
    redis_client.delete(f"context:{session_id}")
