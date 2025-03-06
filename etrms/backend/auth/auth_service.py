"""
Enhanced Trading Risk Management System Authentication Service

This module provides authentication functionality for the single-user ETRMS system.
It includes utilities for password hashing, verification, and token generation.
"""
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from data.models.user import User
from data.repositories.user_repository import UserRepository
from utils.logger import get_logger, log_event


# Initialize password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token extraction from requests
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Secret key for JWT - in production, this should be a proper secret
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "etrms_development_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours - longer for single-user system

# Logger
logger = get_logger(__name__)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify that a plain password matches a hashed password.
    
    Args:
        plain_password: The plaintext password
        hashed_password: The hashed password to compare against
        
    Returns:
        True if the passwords match, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password for storage.
    
    Args:
        password: The plaintext password to hash
        
    Returns:
        The hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        The encoded JWT token
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Create the JWT token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


async def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    Authenticate a user with username and password.
    
    Args:
        username: The username to authenticate
        password: The plaintext password to verify
        
    Returns:
        The User object if authentication succeeds, None otherwise
    """
    user_repo = UserRepository()
    user = await user_repo.get_by_username(username)
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    # Update last login time
    await user_repo.update_last_login(user.id)
    
    log_event(
        logger,
        "USER_LOGIN",
        f"User {username} authenticated successfully",
        context={"username": username}
    )
    
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Get the current user from a JWT token.
    
    Args:
        token: The JWT token from the Authorization header
        
    Returns:
        The current User object
        
    Raises:
        HTTPException: If the token is invalid or the user doesn't exist
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    # Get the user from the database
    user_repo = UserRepository()
    user = await user_repo.get_by_id(user_id)
    
    if user is None:
        raise credentials_exception
    
    return user


async def create_default_user() -> None:
    """
    Create a default user if no users exist in the system.
    
    This function should be called during application startup.
    For a single-user system, we create a default user if none exists.
    """
    user_repo = UserRepository()
    users_count = await user_repo.count()
    
    if users_count == 0:
        # Create default user with environment variables or defaults
        default_username = os.environ.get("DEFAULT_USERNAME", "admin")
        default_password = os.environ.get("DEFAULT_PASSWORD", "admin")  # Should be changed after first login
        
        # Create the user
        await user_repo.create(
            id=str(uuid.uuid4()),
            username=default_username,
            hashed_password=get_password_hash(default_password)
        )
        
        log_event(
            logger,
            "DEFAULT_USER_CREATED",
            f"Created default user '{default_username}'",
            context={"username": default_username}
        ) 