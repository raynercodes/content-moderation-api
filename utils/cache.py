import json
import redis
from config import Config

cache = redis.from_url(Config.REDIS_URL, decode_responses=True)

def get_cached(key: str):
    try:
        value = cache.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception:
        return None

def set_cached(key: str, value: dict, ttl: int = 30):
    try:
        cache.set(key, json.dumps(value), ex=ttl)
    except Exception:
        pass

def delete_cached(key: str):
    try:
        cache.delete(key)
    except Exception:
        pass