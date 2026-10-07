from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from backend.app.models.user import UserRole


class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole = UserRole.OPERATOR


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None


class UserRead(UserBase):
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
