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

def get_login_attempts(ip: str) -> int:
    try:
        value = cache.get(f"login_attempts:{ip}")
        return int(value) if value else 0
    except Exception:
        return 0

def increment_login_attempts(ip: str) -> int:
    try:
        key = f"login_attempts:{ip}"
        attempts = cache.incr(key)
        return attempts
    except Exception:
        return 0

def get_lockout_count(ip: str) -> int:
    try:
        value = cache.get(f"lockout_count:{ip}")
        return int(value) if value else 0
    except Exception:
        return 0

def lockout_ip(ip: str) -> int:
    try:
        lockout_key = f"lockout_count:{ip}"
        lockout_count = cache.incr(lockout_key)
        
        if lockout_count == 1:
            ttl = 900
        elif lockout_count == 2:
            ttl = 1800
        elif lockout_count == 3:
            ttl = 3600
        else:
            ttl = 86400

        cache.set(f"login_attempts:{ip}", 5, ex=ttl)
        cache.expire(lockout_key, 86400)
        return ttl
    except Exception:
        return 900

def clear_login_attempts(ip: str) -> None:
    try:
        cache.delete(f"login_attempts:{ip}")
    except Exception:
        pass

def is_ip_locked_out(ip: str) -> bool:
    try:
        attempts = get_login_attempts(ip)
        return attempts >= 5
    except Exception:
        return False
    
def get_lockout_remaining(ip: str) -> int:
    try:
        ttl = cache.ttl(f"login_attempts:{ip}")
        return ttl if ttl > 0 else 0
    except Exception:
        return 0