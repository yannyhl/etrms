"""
Authentication Schemas

This module defines Pydantic schemas for user authentication including request and response models.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """
    Token response schema.
    
    Attributes:
        access_token (str): The JWT access token.
        token_type (str): The token type (bearer).
    """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Token data schema for decoded JWT content.
    
    Attributes:
        username (str): The username extracted from the token.
        exp (int): The expiration timestamp.
    """
    username: Optional[str] = None
    exp: Optional[int] = None


class UserBase(BaseModel):
    """
    Base user schema.
    
    Attributes:
        username (str): The username.
        email (str): The email address.
    """
    username: str
    email: EmailStr


class UserCreate(UserBase):
    """
    User creation schema.
    
    Attributes:
        password (str): The plain text password (will be hashed).
    """
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """
    User login schema.
    
    Attributes:
        username (str): The username or email.
        password (str): The password.
    """
    username: str  # Can be username or email
    password: str


class UserResponse(UserBase):
    """
    User response schema.
    
    Attributes:
        id (int): The user ID.
        is_active (bool): Whether the user account is active.
        role (str): The user role.
        created_at (datetime): When the user was created.
        last_login (datetime): When the user last logged in.
    """
    id: int
    is_active: bool
    role: str
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        """Pydantic config."""
        orm_mode = True


class UserUpdate(BaseModel):
    """
    User update schema.
    
    Attributes:
        email (str): The updated email address.
        password (str): The updated password.
    """
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)


class PasswordReset(BaseModel):
    """
    Password reset schema.
    
    Attributes:
        token (str): The password reset token.
        new_password (str): The new password.
    """
    token: str
    new_password: str = Field(..., min_length=8) 