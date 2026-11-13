from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    email: str
    full_name: Optional[str] = None


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None


class UserLogin(BaseModel):
    email: str = Field(..., description="User email address")
    password: str


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    role: str = "operator"


class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

