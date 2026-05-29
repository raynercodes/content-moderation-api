from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from services.moderation_service import (
    moderate_content,
    get_user_moderations,
    get_user_moderation_by_id,
    get_user_moderation_stats
)
from utils.auth import require_access_token
from utils.responses import success_response
from slowapi import Limiter
from slowapi.util import get_remote_address
from utils.limiter import limiter

router = APIRouter(prefix="/moderations", tags=["moderations"])

class ModerateRequest(BaseModel):
    content: str

@router.post("/")
@limiter.limit("10/minute")
def moderate(
    request: Request,
    body: ModerateRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_access_token)
):
    try:
        result = moderate_content(db, user_id, body.content)
        return success_response(result, message="Content moderated successfully", status=201)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
def get_moderations(
    db: Session = Depends(get_db),
    user_id: int = Depends(require_access_token),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100)
):
    result = get_user_moderations(db, user_id, page=page, limit=limit)
    return success_response(result, message="Moderations retrieved successfully")

@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    user_id: int = Depends(require_access_token)
):
    result = get_user_moderation_stats(db, user_id)
    return success_response(result, message="Stats retrieved successfully")

@router.get("/{moderation_id}")
def get_moderation(
    moderation_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_access_token)
):
    try:
        result = get_user_moderation_by_id(db, user_id, moderation_id)
        return success_response(result, message="Moderation retrieved successfully")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))