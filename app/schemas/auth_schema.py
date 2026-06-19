from pydantic import BaseModel, EmailStr

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(UserLogin):
    name: str

class Token(BaseModel):
    access_token: str
    token_type: str
