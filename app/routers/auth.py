from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.services.auth_service import hash_password, verify_password, create_acess_token
from app.schemas.user import UserRegister, UserLogin
from app.models.user import User
from app.db.session import get_db
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/register")
def register(body:UserRegister, db:Session = Depends(get_db)):
    #1. Check if email already exists
    existing_user = db.query(User).filter(User.email == body.email).first()
    if existing_user:
        raise HTTPException(status_code = 400, detail="Email already registered")

    # Create new user with hashed password

    new_user = User(
        username = body.username,
        email = body.email,
        hashed_password = hash_password(body.password),
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")

    return JSONResponse(
        status_code=201,
        content={"message": "User registered successfully"}
    )

@router.post("/login")

def login(body:UserLogin, db:Session = Depends(get_db)):
        user = db.query(User).filter(User.email == body.email).first()
        if not user or not verify_password(body.password, user.hashed_password):
            raise HTTPException(401, "Invalid credentials")
        token = create_acess_token(user.id)
        return JSONResponse(
            status_code = 200,
            content={
                "message" : "User login succcess",
                "acess_token" : token,
                "token_type" : "bearer",
        }
        )

          
          
          
          

                
          
    






