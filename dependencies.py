from fastapi import Depends, HTTPException, Header, Request
import jwt
import time
from app.db.session import get_db
from app.services.auth_service import decode_access_token
from app.db.redis_client import redis_client
import hashlib
from sqlalchemy.orm import Session
from app.models.api_key import APIKey
from app.models.user import User


def get_current_user(request: Request, authorization: str = Header(...))  -> int:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code = 401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "")

    try:
        user_id = decode_access_token(token)
        request.state.user_id = user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user_id

def get_redis():
    return redis_client


def check_api_key(request:Request, x_api_key: str = Header(...), current_user: int = Depends(get_current_user), db:Session = Depends(get_db)):
    hashed_key = hashlib.sha256(x_api_key.encode()).hexdigest()
    api_key = (db.query(APIKey).filter(APIKey.hashed_key == hashed_key).first())

    if api_key is None:
        raise HTTPException(
            status_code = 401,
            detail="Invalid API key"
        )

    if not api_key.is_active:
        raise HTTPException(
            status_code=401,
            detail="API key is inactive"
        )

    if api_key.user_id != current_user:
        raise HTTPException(
            status_code=403,
            detail="API key does not belong to current user"
        )
    request.state.api_key_id = api_key.id
    return api_key



RATE_LIMIT_SCRIPT = """
local current_key = KEYS[1]
local previous_key = KEYS[2]

local elapsed = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])

-- Increment current windo
local current_count = redis.call("INCR", current_key)

-- Set expiration only when key is created
if current_count == 1 then
    redis.call("EXPIRE", current_key, window*2)
end

-- Get previous window count
local previous_count = redis.call("GET", previous_key)

if not previous_count then
    previous_count = 0
else
    previous_count = tonumber(previous_count)
end

-- Calculate how much of previous window
-- overalps with the current sliding window

local overlap_percentage = (window-elapsed) / window


-- Sliding window counter
local estimated_count = 
    current_count + (previous_count * overlap_percentage)

if estimated_count > limit then
    return {
        0,
        current_count,
        previous_count,
        estimated_count
    }
end
return {
    1,
    current_count,
    previous_count,
    estimated_count
}
"""

async def check_rate_limit(api_key:APIKey = Depends(check_api_key), redis = Depends(get_redis)):
    LIMIT = 100
    WINDOW = 60

    now = int(time.time())

    # Identify current 60-second window
    current_window = now // WINDOW

    current_key = (
        f"rate_limit:api_key:{api_key.id}:{current_window}"
    )

    previous_key = (
            f"rate_limit:api_key:{api_key.id}:{current_window-1}"
        )

    #How many seconds have passed in current window

    elapsed = now % WINDOW

    result = await redis.eval(
        RATE_LIMIT_SCRIPT,
        2,
        current_key,
        previous_key,
        elapsed,
        WINDOW,
        LIMIT
    )

    print(
    "allowed:", result[0],
    "current:", result[1],
    "previous:", result[2],
    "estimated:", result[3])

    allowed = result[0]

    if allowed == 0:
        raise HTTPException(
            status_code=429,
            detail = "Rate limit exceeded. Please try again later"
        )

