"""
Authentication Controller

This module provides controller functions for user authentication and profile management.
"""
from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from data.database import get_db
from data.models.users import User
from api.schemas.auth import UserCreate, UserUpdate, UserResponse
from api.services.auth import get_password_hash, get_user_by_username, get_user_by_email


def register_user(user: UserCreate, db: Session = Depends(get_db)) -> User:
    """
    Register a new user.
    
    Args:
        user: The user data to register.
        db: The database session.
        
    Returns:
        The created user.
        
    Raises:
        HTTPException: If the username or email already exists.
    """
    # Check if username already exists
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False,
        role="user",
        created_at=datetime.utcnow(),
    )
    
    # Add to database
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


def update_user_profile(
    user_id: int,
    user_update: UserUpdate,
    current_user: User,
    db: Session = Depends(get_db)
) -> User:
    """
    Update a user's profile.
    
    Args:
        user_id: The ID of the user to update.
        user_update: The updated user data.
        current_user: The current authenticated user.
        db: The database session.
        
    Returns:
        The updated user.
        
    Raises:
        HTTPException: If the user does not exist or the current user does not have permission.
    """
    # Check if user exists
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if the current user has permission to update this profile
    if current_user.id != user_id and not current_user.is_superuser and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update email if provided
    if user_update.email:
        # Check if email already exists for another user
        existing_user = get_user_by_email(db, email=user_update.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        db_user.email = user_update.email
    
    # Update password if provided
    if user_update.password:
        db_user.hashed_password = get_password_hash(user_update.password)
    
    # Commit changes
    db.commit()
    db.refresh(db_user)
    
    return db_user


def get_user_profile(
    user_id: Optional[int] = None,
    current_user: User = None,
    db: Session = Depends(get_db)
) -> User:
    """
    Get a user's profile.
    
    Args:
        user_id: The ID of the user to get. If None, returns the current user's profile.
        current_user: The current authenticated user.
        db: The database session.
        
    Returns:
        The user profile.
        
    Raises:
        HTTPException: If the user does not exist or the current user does not have permission.
    """
    if user_id is None:
        return current_user
    
    # Check if user exists
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Regular users can only view their own profile
    if current_user.id != user_id and not current_user.is_superuser and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return db_user


def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = None,
    db: Session = Depends(get_db)
) -> list[User]:
    """
    Get a list of users.
    
    Args:
        skip: Number of users to skip.
        limit: Maximum number of users to return.
        current_user: The current authenticated user.
        db: The database session.
        
    Returns:
        A list of users.
        
    Raises:
        HTTPException: If the current user does not have permission.
    """
    # Only admins and superusers can list all users
    if not current_user.is_superuser and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return db.query(User).offset(skip).limit(limit).all()


def deactivate_user(
    user_id: int,
    current_user: User,
    db: Session = Depends(get_db)
) -> User:
    """
    Deactivate a user.
    
    Args:
        user_id: The ID of the user to deactivate.
        current_user: The current authenticated user.
        db: The database session.
        
    Returns:
        The deactivated user.
        
    Raises:
        HTTPException: If the user does not exist or the current user does not have permission.
    """
    # Check if user exists
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Only admins and superusers can deactivate users
    if not current_user.is_superuser and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Cannot deactivate yourself or a superuser
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself"
        )
    
    if db_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate a superuser"
        )
    
    # Deactivate user
    db_user.is_active = False
    db.commit()
    db.refresh(db_user)
    
    return db_user 