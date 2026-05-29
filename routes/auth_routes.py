from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from services.auth_service import register_user, login_user, refresh_access_token
from utils.responses import success_response

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    try:
        result = register_user(db, request.username, request.password)
        return success_response(result, message="User registered successfully", status=201)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    try:
        result = login_user(db, request.username, request.password)
        return success_response(result, message="Login successful")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/refresh")
def refresh(request: RefreshRequest, db: Session = Depends(get_db)):
    try:
        result = refresh_access_token(db, request.refresh_token)
        return success_response(result, message="Token refreshed successfully")
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))