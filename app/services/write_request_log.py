from app.db.session import SessionLocal
from app.models.request_log import RequestLog

def write_request_log(user_id: int | None, api_key_id: int | None, status_code: int):
    db = SessionLocal()
    try:
        log = RequestLog(
            user_id=user_id,
            api_key_id=api_key_id,
            status_code=status_code,
        )
        db.add(log)
        db.commit()
    finally:
        db.close()


