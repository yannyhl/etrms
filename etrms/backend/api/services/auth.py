"""
Authentication Service

This module provides functions for authenticating users and managing JWT tokens.
"""
from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config.settings import settings
from data.database import get_db
from data.models.users import User
from api.schemas.auth import TokenData

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify that a plain password matches a hashed password.
    
    Args:
        plain_password: The plain password to verify.
        hashed_password: The hashed password to compare against.
        
    Returns:
        True if the passwords match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a plain password.
    
    Args:
        password: The plain password to hash.
        
    Returns:
        The hashed password.
    """
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: The data to encode in the token.
        expires_delta: Optional expiration time delta. If not provided, defaults to 
                       settings.JWT_EXPIRATION_MINUTES.
                       
    Returns:
        The encoded JWT token as a string.
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    
    return encoded_jwt


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Get a user by username.
    
    Args:
        db: The database session.
        username: The username to look up.
        
    Returns:
        The user if found, None otherwise.
    """
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get a user by email.
    
    Args:
        db: The database session.
        email: The email to look up.
        
    Returns:
        The user if found, None otherwise.
    """
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user with username/email and password.
    
    Args:
        db: The database session.
        username: The username or email to authenticate.
        password: The password to verify.
        
    Returns:
        The authenticated user if successful, None otherwise.
    """
    # Try to find user by username
    user = get_user_by_username(db, username)
    
    # If not found, try email
    if not user:
        user = get_user_by_email(db, username)
        
    if not user:
        return None
        
    if not verify_password(password, user.hashed_password):
        return None
        
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from the JWT token.
    
    Args:
        token: The JWT token.
        db: The database session.
        
    Returns:
        The authenticated user.
        
    Raises:
        HTTPException: If authentication fails.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT token
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
            
        token_data = TokenData(username=username, exp=payload.get("exp"))
        
    except JWTError:
        raise credentials_exception
        
    # Get the user from the database
    user = get_user_by_username(db, username=token_data.username)
    
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user.
    
    Args:
        current_user: The current authenticated user.
        
    Returns:
        The current active user.
        
    Raises:
        HTTPException: If the user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current admin user.
    
    Args:
        current_user: The current authenticated user.
        
    Returns:
        The current admin user.
        
    Raises:
        HTTPException: If the user is not an admin.
    """
    if not current_user.is_superuser and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user 