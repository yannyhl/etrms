from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base user model with common attributes"""
    username: str
    email: Optional[EmailStr] = None
    is_active: bool = True
    theme: str = "dark"
    default_exchange: Optional[str] = None
    default_timeframe: str = "1h"

class UserCreate(UserBase):
    """Model for creating a new user"""
    password: str

class UserUpdate(BaseModel):
    """Model for updating user profile"""
    email: Optional[EmailStr] = None
    theme: Optional[str] = None
    default_exchange: Optional[str] = None
    default_timeframe: Optional[str] = None

class PasswordUpdate(BaseModel):
    """Model for updating user password"""
    current_password: str
    new_password: str

class User(UserBase):
    """Complete user model with all attributes"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True 