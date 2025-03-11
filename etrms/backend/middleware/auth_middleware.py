"""
Enhanced Trading Risk Management System Authentication Middleware

This module provides middleware for protecting API routes in the FastAPI application.
It checks for the JWT token in the request header and verifies it.
"""
import os
from typing import List, Optional, Callable

import jwt
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from utils.logger import get_logger, log_event


# Get the JWT secret key from environment variable
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "etrms_development_secret_key")
ALGORITHM = "HS256"

# Logger
logger = get_logger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for authenticating requests using JWT tokens.
    
    This middleware checks for the JWT token in the Authorization header,
    verifies it, and adds the user ID to the request state if valid.
    """
    
    def __init__(
        self,
        app,
        public_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None
    ):
        """
        Initialize the middleware.
        
        Args:
            app: The FastAPI application
            public_paths: List of paths that don't require authentication
            exclude_paths: List of paths to exclude from authentication checking
        """
        super().__init__(app)
        
        # Paths that don't require authentication
        self.public_paths = public_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/login",
            "/health"
        ]
        
        # Paths to exclude from authentication checking entirely
        self.exclude_paths = exclude_paths or []
        
        # Logger
        self.logger = get_logger(__name__)
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ):
        """
        Process the request and check for authentication.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            The response from the next middleware or route handler
        """
        # Skip authentication for excluded paths
        if self._is_path_excluded(request.url.path):
            return await call_next(request)
        
        # Skip authentication for public paths
        if self._is_path_public(request.url.path):
            return await call_next(request)
        
        # Get the JWT token from the Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return self._create_unauthorized_response("Missing Authorization header")
        
        # Check that the Authorization header starts with "Bearer "
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return self._create_unauthorized_response("Invalid Authorization header format")
        
        token = parts[1]
        
        try:
            # Decode and verify the JWT token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            
            if not user_id:
                return self._create_unauthorized_response("Invalid token payload")
            
            # Add the user ID to the request state
            request.state.user_id = user_id
            
        except jwt.ExpiredSignatureError:
            return self._create_unauthorized_response("Token has expired")
        except jwt.InvalidTokenError:
            return self._create_unauthorized_response("Invalid token")
        except Exception as e:
            log_event(
                self.logger,
                "AUTH_MIDDLEWARE_ERROR",
                f"Error in authentication middleware: {str(e)}",
                level="ERROR"
            )
            return self._create_unauthorized_response("Authentication error")
        
        # Continue with the request
        return await call_next(request)
    
    def _is_path_public(self, path: str) -> bool:
        """
        Check if a path is public (doesn't require authentication).
        
        Args:
            path: The request path
            
        Returns:
            True if the path is public, False otherwise
        """
        return any(
            path.startswith(public_path) for public_path in self.public_paths
        )
    
    def _is_path_excluded(self, path: str) -> bool:
        """
        Check if a path is excluded from authentication checking.
        
        Args:
            path: The request path
            
        Returns:
            True if the path is excluded, False otherwise
        """
        return any(
            path.startswith(excluded_path) for excluded_path in self.exclude_paths
        )
    
    def _create_unauthorized_response(self, detail: str) -> JSONResponse:
        """
        Create a 401 Unauthorized response.
        
        Args:
            detail: The error detail
            
        Returns:
            A JSON response with 401 status code
        """
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": detail},
            headers={"WWW-Authenticate": "Bearer"}
        ) 