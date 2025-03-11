"""
Enhanced Trading Risk Management System Authentication Routes

This module provides API routes for authentication, user profile management,
and API key management for the single-user ETRMS system.
"""
from datetime import timedelta
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
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
from etrms.backend.models.user import UserCreate, UserUpdate, PasswordUpdate
from etrms.backend.services.user_service import UserService
from etrms.backend.api.dependencies import get_user_service
from etrms.backend.utils.error_handler import (
    UnauthorizedException,
    NotFoundException,
    BadRequestException,
    ValidationException
)


# Set up router
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Logger
logger = get_logger(__name__)

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# JWT settings
SECRET_KEY = "YOUR_SECRET_KEY_HERE"  # In production, use environment variable
ALGORITHM = "HS256"

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


class TokenData(BaseModel):
    username: Optional[str] = None


# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# API routes

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service)
):
    try:
        user = user_service.authenticate_user(form_data.username, form_data.password)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except UnauthorizedException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/register", response_model=User)
async def register_user(
    user_create: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    # Check if username already exists
    existing_user = user_service.get_user_by_username(user_create.username)
    if existing_user:
        raise BadRequestException("Username already registered")
    
    # Create new user
    hashed_password = get_password_hash(user_create.password)
    try:
        user = user_service.create_user(user_create, hashed_password)
        return user
    except Exception as e:
        raise BadRequestException(f"Failed to create user: {str(e)}")


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=User)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    try:
        updated_user = user_service.update_user(current_user.id, user_update)
        return updated_user
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/password")
async def update_password(
    password_update: PasswordUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    # Verify current password
    if not verify_password(password_update.current_password, current_user.hashed_password):
        raise UnauthorizedException("Current password is incorrect")
    
    # Update password
    try:
        hashed_password = get_password_hash(password_update.new_password)
        user_service.update_password(current_user.id, hashed_password)
        return {"message": "Password updated successfully"}
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


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