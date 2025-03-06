"""
Authentication Middleware

This module provides middleware for authentication.
"""
from typing import Callable, List, Optional

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from config.settings import settings
from data.database import SessionLocal
from api.services.auth import get_user_by_username

# Public paths that don't require authentication
PUBLIC_PATHS = [
    "/api/health",
    "/api/exchanges",
    "/api/auth/login",
    "/api/auth/register",
    "/api/docs",
    "/api/redoc",
    "/api/openapi.json",
]

# WebSocket paths that don't require authentication during development
# TODO: Implement WebSocket authentication for production
WS_PATHS = [
    "/api/ws/",
]


async def auth_middleware(request: Request, call_next: Callable) -> Response:
    """
    Authentication middleware.
    
    Args:
        request: The incoming request.
        call_next: The next middleware in the chain.
        
    Returns:
        The response from the next middleware.
    """
    # Allow OPTIONS requests for CORS
    if request.method == "OPTIONS":
        return await call_next(request)
    
    # Check if path is public
    path = request.url.path
    if any(path.startswith(public_path) for public_path in PUBLIC_PATHS):
        return await call_next(request)
    
    # During development, allow WebSocket connections without authentication
    # TODO: Implement WebSocket authentication for production
    if any(path.startswith(ws_path) for ws_path in WS_PATHS):
        return await call_next(request)
    
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Not authenticated"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header.split(" ")[1]
    
    try:
        # Decode the JWT token
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        username = payload.get("sub")
        
        if username is None:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get the user from the database
        db = SessionLocal()
        try:
            user = get_user_by_username(db, username=username)
            
            if user is None or not user.is_active:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "User not found or inactive"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Set the user in the request state
            request.state.user = user
            request.state.db = db
            
            # Call the next middleware
            return await call_next(request)
        finally:
            db.close()
    except JWTError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid token"},
            headers={"WWW-Authenticate": "Bearer"},
        ) 