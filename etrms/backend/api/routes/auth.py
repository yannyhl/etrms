"""
Enhanced Trading Risk Management System Authentication Routes

This module provides API routes for authentication, user profile management,
and API key management for the single-user ETRMS system.
"""
from datetime import timedelta
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from auth.auth_service import (
    get_current_user,
    authenticate_user,
    create_access_token,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from data.models.user import User, ApiKey
from data.repositories.user_repository import UserRepository
from utils.logger import get_logger, log_event


# Set up router
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Logger
logger = get_logger(__name__)


# Pydantic models for request/response validation

class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    """User response model."""
    id: str
    username: str
    theme: str
    default_exchange: str = None
    default_timeframe: str
    last_login: str = None


class UserUpdateRequest(BaseModel):
    """User update request model."""
    theme: str = None
    default_exchange: str = None
    default_timeframe: str = None


class PasswordUpdateRequest(BaseModel):
    """Password update request model."""
    current_password: str
    new_password: str


class ApiKeyRequest(BaseModel):
    """API key request model."""
    exchange: str
    name: str
    api_key: str
    api_secret: str
    passphrase: str = None
    is_testnet: bool = False
    trading_enabled: bool = True


class ApiKeyResponse(BaseModel):
    """API key response model."""
    id: str
    exchange: str
    name: str
    api_key: str
    is_testnet: bool
    trading_enabled: bool
    created_at: str


# API routes

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate a user and return an access token.
    
    Args:
        form_data: The login form data
        
    Returns:
        A JWT token for the authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    user = await authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get the profile of the current authenticated user.
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        The user profile
    """
    return current_user.to_dict()


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_data: UserUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update the profile of the current authenticated user.
    
    Args:
        user_data: The updated user data
        current_user: The current authenticated user
        
    Returns:
        The updated user profile
    """
    # Convert request model to dict
    update_data = user_data.dict(exclude_unset=True)
    
    # Update the user
    user_repo = UserRepository()
    updated_user = await user_repo.update(current_user.id, update_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    log_event(
        logger,
        "USER_PROFILE_UPDATED",
        f"User {current_user.username} updated their profile",
        context={"username": current_user.username}
    )
    
    return updated_user.to_dict()


@router.put("/password")
async def update_password(
    password_data: PasswordUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update the password of the current authenticated user.
    
    Args:
        password_data: The password update data
        current_user: The current authenticated user
        
    Returns:
        A success message
        
    Raises:
        HTTPException: If the current password is incorrect
    """
    # Verify current password
    user = await authenticate_user(current_user.username, password_data.current_password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Update the password
    user_repo = UserRepository()
    hashed_password = get_password_hash(password_data.new_password)
    await user_repo.update_password(current_user.id, hashed_password)
    
    log_event(
        logger,
        "USER_PASSWORD_UPDATED",
        f"User {current_user.username} updated their password",
        context={"username": current_user.username}
    )
    
    return {"message": "Password updated successfully"}


# API Key Management

@router.get("/api-keys", response_model=List[ApiKeyResponse])
async def get_api_keys(current_user: User = Depends(get_current_user)):
    """
    Get all API keys for the current user.
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        List of API keys
    """
    user_repo = UserRepository()
    api_keys = await user_repo.get_api_keys(current_user.id)
    
    return [api_key.to_dict() for api_key in api_keys]


@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(
    api_key_data: ApiKeyRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new API key for the current user.
    
    Args:
        api_key_data: The API key data
        current_user: The current authenticated user
        
    Returns:
        The created API key
    """
    # Convert request model to dict
    data = api_key_data.dict()
    data["user_id"] = current_user.id
    
    # Create the API key
    user_repo = UserRepository()
    api_key = await user_repo.create_api_key(data)
    
    log_event(
        logger,
        "API_KEY_CREATED",
        f"User {current_user.username} created API key {api_key.name} for {api_key.exchange}",
        context={"username": current_user.username, "exchange": api_key.exchange}
    )
    
    return api_key.to_dict()


@router.put("/api-keys/{api_key_id}", response_model=ApiKeyResponse)
async def update_api_key(
    api_key_id: str,
    api_key_data: ApiKeyRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update an API key.
    
    Args:
        api_key_id: The API key ID
        api_key_data: The updated API key data
        current_user: The current authenticated user
        
    Returns:
        The updated API key
        
    Raises:
        HTTPException: If the API key doesn't exist or doesn't belong to the user
    """
    # Get the API key
    user_repo = UserRepository()
    api_key = await user_repo.get_api_key(api_key_id)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Verify ownership
    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this API key"
        )
    
    # Convert request model to dict
    data = api_key_data.dict()
    
    # Update the API key
    updated_api_key = await user_repo.update_api_key(api_key_id, data)
    
    log_event(
        logger,
        "API_KEY_UPDATED",
        f"User {current_user.username} updated API key {updated_api_key.name}",
        context={"username": current_user.username, "exchange": updated_api_key.exchange}
    )
    
    return updated_api_key.to_dict()


@router.delete("/api-keys/{api_key_id}")
async def delete_api_key(
    api_key_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete an API key.
    
    Args:
        api_key_id: The API key ID
        current_user: The current authenticated user
        
    Returns:
        A success message
        
    Raises:
        HTTPException: If the API key doesn't exist or doesn't belong to the user
    """
    # Get the API key
    user_repo = UserRepository()
    api_key = await user_repo.get_api_key(api_key_id)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Verify ownership
    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this API key"
        )
    
    # Delete the API key
    success = await user_repo.delete_api_key(api_key_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete API key"
        )
    
    log_event(
        logger,
        "API_KEY_DELETED",
        f"User {current_user.username} deleted API key {api_key.name}",
        context={"username": current_user.username, "exchange": api_key.exchange}
    )
    
    return {"message": "API key deleted successfully"} 