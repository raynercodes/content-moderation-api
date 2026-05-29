from sqlalchemy.orm import Session
from models import User, RefreshToken
from datetime import datetime, UTC

def create_user(db: Session, username: str, password_hash: str) -> User:
    user = User(username=username, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()

def store_refresh_token(db: Session, user_id: int, token: str) -> RefreshToken:
    refresh_token = RefreshToken(user_id=user_id, token=token)
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    return refresh_token

def get_refresh_token(db: Session, token: str) -> RefreshToken | None:
    return db.query(RefreshToken).filter(RefreshToken.token == token).first()

def revoke_refresh_token(db: Session, token: str) -> None:
    refresh_token = get_refresh_token(db, token)
    if refresh_token:
        refresh_token.revoked_at = datetime.now(UTC)
        db.commit()