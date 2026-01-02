from __future__ import annotations
from src.app.core.config import settings
from pydantic import BaseModel, EmailStr, Field, constr


class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=8) = Field(..., description="Password, at least 8 characters")

class UserLogin(BaseModel):
    email: EmailStr
    password: constr(min_length=8) = Field(..., description="Password, at least 8 characters")

class UserOut(BaseModel):
    id: str
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = settings.JWT_EXPIRE_MINUTES*60