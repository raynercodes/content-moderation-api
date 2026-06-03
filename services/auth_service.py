from sqlalchemy.orm import Session
from repos.auth_repo import create_user, get_user_by_username, store_refresh_token, get_refresh_token, revoke_refresh_token
from utils.auth import create_access_token, create_refresh_token
from werkzeug.security import generate_password_hash, check_password_hash
from utils.cache import is_ip_locked_out, increment_login_attempts, lockout_ip, clear_login_attempts, get_lockout_remaining
from fastapi import Request

def register_user(db: Session, username: str, password: str) -> dict:
    username = (username or "").strip().lower()
    password = password or ""

    if not username:
        raise ValueError("Username is required")

    if len(username) <= 3:
        raise ValueError("Username must be at least 4 characters")

    if not password:
        raise ValueError("Password is required")

    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters")

    existing = get_user_by_username(db, username)

    if existing:
        raise ValueError("User already exists")

    password_hash = generate_password_hash(password)
    create_user(db, username, password_hash)

    return {"username": username}

def login_user(db: Session, username: str, password: str, ip: str) -> dict:
    username = (username or "").strip().lower()
    password = password or ""

    if not username:
        raise ValueError("Username is required")

    if not password:
        raise ValueError("Password is required")

    if is_ip_locked_out(ip):
        remaining = get_lockout_remaining(ip)
        minutes = remaining // 60
        seconds = remaining % 60
        raise ValueError(f"Too many failed login attempts. Try again in {minutes}m {seconds}s.")

    user = get_user_by_username(db, username)

    if user is None:
        attempts = increment_login_attempts(ip)
        if attempts >= 5:
            ttl = lockout_ip(ip)
            raise ValueError(f"Too many failed login attempts. Please try again in {ttl // 60} minutes.")
        raise ValueError("Invalid credentials")

    if not check_password_hash(user.password_hash, password):
        attempts = increment_login_attempts(ip)
        if attempts >= 5:
            ttl = lockout_ip(ip)
            raise ValueError(f"Too many failed login attempts. Please try again in {ttl // 60} minutes.")
        raise ValueError("Invalid credentials")

    clear_login_attempts(ip)

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token()

    store_refresh_token(db, user.id, refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }

def refresh_access_token(db: Session, refresh_token: str) -> dict:
    refresh_token = (refresh_token or "").strip()

    if not refresh_token:
        raise ValueError("Refresh token is required")

    token = get_refresh_token(db, refresh_token)

    if token is None:
        raise ValueError("Invalid refresh token")

    if token.revoked_at is not None:
        raise ValueError("Invalid refresh token")

    revoke_refresh_token(db, refresh_token)

    new_access_token = create_access_token(token.user_id)
    new_refresh_token = create_refresh_token()

    store_refresh_token(db, token.user_id, new_refresh_token)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token
    }