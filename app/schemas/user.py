from pydantic import BaseModel, EmailStr, Field

class UserRegister(BaseModel):
    username:str
    password:str
    email:EmailStr

class UserLogin(BaseModel):
    email:EmailStr
    password:str

