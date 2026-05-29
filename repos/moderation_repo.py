from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Moderation

def create_moderation(db: Session, user_id: int, content: str, decision: str, reason: str) -> Moderation:
    moderation = Moderation(
        user_id=user_id,
        content=content,
        decision=decision,
        reason=reason
    )
    db.add(moderation)
    db.commit()
    db.refresh(moderation)
    return moderation

def get_moderations_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 10) -> list[Moderation]:
    return (
        db.query(Moderation)
        .filter(Moderation.user_id == user_id)
        .order_by(Moderation.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_moderation_by_id(db: Session, user_id: int, moderation_id: int) -> Moderation | None:
    return (
        db.query(Moderation)
        .filter(Moderation.user_id == user_id, Moderation.id == moderation_id)
        .first()
    )

def get_moderation_stats(db: Session, user_id: int) -> list:
    return (
        db.query(Moderation.decision, func.count(Moderation.id))
        .filter(Moderation.user_id == user_id)
        .group_by(Moderation.decision)
        .all()
    )

def get_total_moderations(db: Session, user_id: int) -> int:
    return db.query(Moderation).filter(Moderation.user_id == user_id).count()