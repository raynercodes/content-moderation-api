from sqlalchemy.orm import Session
from repos.moderation_repo import (
    create_moderation,
    get_moderations_by_user,
    get_moderation_by_id,
    get_moderation_stats,
    get_total_moderations
)
from openai import AsyncOpenAI
from config import Config
from utils.logger import logger
from utils.cache import get_cached, set_cached, delete_cached
from tasks.moderation_task import process_moderation

client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

async def moderate_content(db: Session, user_id: int, content: str) -> dict:
    content = (content or "").strip()

    if not content:
        raise ValueError("Content is required")

    if len(content) > 5000:
        raise ValueError("Content must be under 5000 characters")

    logger.info(f"Queuing moderation for user_id={user_id}")

    moderation = create_moderation(
        db,
        user_id=user_id,
        content=content,
        decision=None,
        reason=None
    )

    process_moderation.delay(moderation.id, content)

    return {
        "id": moderation.id,
        "content": content,
        "decision": None,
        "reason": None,
        "status": "pending",
        "created_at": moderation.created_at.isoformat()
    }

def get_user_moderations(db: Session, user_id: int, page: int = 1, limit: int = 10) -> dict:
    if page < 1:
        page = 1

    skip = (page - 1) * limit
    moderations = get_moderations_by_user(db, user_id, skip=skip, limit=limit)
    total = get_total_moderations(db, user_id)
    total_pages = (total + limit - 1) // limit

    return {
        "moderations": [
            {
                "id": m.id,
                "content": m.content,
                "decision": m.decision,
                "reason": m.reason,
                "created_at": m.created_at.isoformat()
            }
            for m in moderations
        ],
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    }

def get_user_moderation_by_id(db: Session, user_id: int, moderation_id: int) -> dict:
    cache_key = f"moderation:{user_id}:{moderation_id}"
    cached = get_cached(cache_key)

    if cached:
        return cached

    moderation = get_moderation_by_id(db, user_id, moderation_id)

    if moderation is None:
        raise ValueError("Moderation not found")

    result = {
        "id": moderation.id,
        "content": moderation.content,
        "decision": moderation.decision,
        "reason": moderation.reason,
        "status": moderation.status,
        "created_at": moderation.created_at.isoformat()
    }

    if moderation.status == "completed":
        set_cached(cache_key, result, ttl=300)

    return result

def get_user_moderation_stats(db: Session, user_id: int) -> dict:
    cache_key = f"moderation_stats:{user_id}"
    cached = get_cached(cache_key)

    if cached:
        return cached

    rows = get_moderation_stats(db, user_id)

    stats = {
        "safe": 0,
        "flagged": 0,
        "rejected": 0
    }

    for decision, count in rows:
        if decision:
            stats[decision] = count

    set_cached(cache_key, stats, ttl=30)

    return stats