from sqlalchemy.orm import Session
from repos.moderation_repo import (
    create_moderation,
    get_moderations_by_user,
    get_moderation_by_id,
    get_moderation_stats,
    get_total_moderations
)
from openai import OpenAI
from config import Config
from utils.logger import logger

client = OpenAI(api_key=Config.OPENAI_API_KEY)

def moderate_content(db: Session, user_id: int, content: str) -> dict:
    content = (content or "").strip()

    if not content:
        raise ValueError("Content is required")

    if len(content) > 5000:
        raise ValueError("Content must be under 5000 characters")

    logger.info(f"Moderating content for user_id={user_id}")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You are a content moderation assistant. 
                Analyze the given text and respond with a JSON object containing:
                - decision: either 'safe', 'flagged', or 'rejected'
                - reason: a brief explanation of your decision
                
                Use these guidelines:
                - safe: content is appropriate and harmless
                - flagged: content is potentially problematic but not clearly harmful
                - rejected: content is clearly harmful, abusive, or violates guidelines
                
                Respond with only the JSON object, no other text."""
            },
            {
                "role": "user",
                "content": content
            }
        ],
        response_format={"type": "json_object"},
        max_tokens=150
    )

    result = response.choices[0].message.content

    import json
    parsed = json.loads(result)

    decision = parsed.get("decision", "flagged")
    reason = parsed.get("reason", "Unable to determine")

    if decision not in ["safe", "flagged", "rejected"]:
        decision = "flagged"

    moderation = create_moderation(db, user_id, content, decision, reason)

    return {
        "id": moderation.id,
        "content": content,
        "decision": decision,
        "reason": reason,
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
    moderation = get_moderation_by_id(db, user_id, moderation_id)

    if moderation is None:
        raise ValueError("Moderation not found")

    return {
        "id": moderation.id,
        "content": moderation.content,
        "decision": moderation.decision,
        "reason": moderation.reason,
        "created_at": moderation.created_at.isoformat()
    }

def get_user_moderation_stats(db: Session, user_id: int) -> dict:
    rows = get_moderation_stats(db, user_id)

    stats = {
        "safe": 0,
        "flagged": 0,
        "rejected": 0
    }

    for decision, count in rows:
        stats[decision] = count

    return stats