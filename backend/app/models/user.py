# User model definition
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    """Model for creating a new user"""
    email: EmailStr
    full_name: str
    department: str
    role: str = "user"


class UserDB(UserCreate):
    """Model for user data stored in database"""
    id: str
    is_active: bool = True
    created_at: datetime
