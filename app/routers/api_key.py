from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
# from sqlalchemy.exc import IntegrityError
from app.db.session import get_db
# from fastapi.responses import JSONResponse
from app.schemas.api_key import ApiKeyResponse
from dependencies import get_current_user, check_rate_limit
from app.services.api_service import generate_api_key_value, hash_api_key
from app.models.api_key import APIKey
from sqlalchemy import func, case
from app.models.request_log import RequestLog

router = APIRouter()

@router.post("/generate_api_key", response_model=ApiKeyResponse)
def generate_api_key(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    existing_key = db.query(APIKey).filter(
        APIKey.user_id == user_id,
        APIKey.is_active == True
    ).first()

    if existing_key:
        existing_key.is_active = False
        db.commit()

    raw_key = generate_api_key_value()
    hashed = hash_api_key(raw_key)

    new_key = APIKey(user_id = user_id, hashed_key=hashed, is_active=True)
    db.add(new_key)
    db.commit()

    return ApiKeyResponse(api_key=raw_key)


    
@router.get("/demo")
def demo( _: None = Depends(check_rate_limit)
):
    return {
        "message": "Request Successful"
    }

@router.get("/dashboard")
def dashboard(current_user: int = Depends(get_current_user),db: Session = Depends(get_db)):
    result = (
        db.query(
            RequestLog.api_key_id,
            func.count(RequestLog.id).label("total_requests"),
            func.sum(
                case((RequestLog.status_code<400,1), else_=0)
            ).label("success_requests"),
            func.sum(
                case((RequestLog.status_code>=400, 1), else_=0)
            ).label("failed_requests")
        )
        .filter(RequestLog.user_id == current_user)
        .group_by(RequestLog.api_key_id)
        .all()
    )

    return [
            {
            "api_key_id": row.api_key_id,
            "total_requests": row.total_requests,
            "success_requests": row.success_requests,
            "failed_requests": row.failed_requests,
        }
        for row in result
    ]



