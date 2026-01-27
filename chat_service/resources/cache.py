import json

from configs.redis import redis_client


def get_cache(key):
    value = redis_client.get(key)
    return json.loads(value) if value else None


def set_cache(key, value, ttl=300):
    redis_client.setex(key, ttl, json.dumps(value))
