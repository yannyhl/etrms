"""
Error handling utilities for the ETRMS backend.
"""

import logging
import traceback
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Set up logger
logger = logging.getLogger(__name__)

class ETRMSException(Exception):
    """
    Base exception class for ETRMS-specific exceptions.
    
    Args:
        message: Error message
        status_code: HTTP status code
        detail: Additional error details
    """
    def __init__(
        self, 
        message: str, 
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)

class ValidationException(ETRMSException):
    """
    Exception for validation errors.
    
    Args:
        message: Error message
        detail: Validation error details
    """
    def __init__(
        self, 
        message: str = "Validation error", 
        detail: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    ):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, detail)

class NotFoundException(ETRMSException):
    """
    Exception for resource not found errors.
    
    Args:
        message: Error message
        detail: Additional error details
    """
    def __init__(
        self, 
        message: str = "Resource not found", 
        detail: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    ):
        super().__init__(message, status.HTTP_404_NOT_FOUND, detail)

class UnauthorizedException(ETRMSException):
    """
    Exception for unauthorized access errors.
    
    Args:
        message: Error message
        detail: Additional error details
    """
    def __init__(
        self, 
        message: str = "Unauthorized", 
        detail: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    ):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, detail)

class ForbiddenException(ETRMSException):
    """
    Exception for forbidden access errors.
    
    Args:
        message: Error message
        detail: Additional error details
    """
    def __init__(
        self, 
        message: str = "Forbidden", 
        detail: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    ):
        super().__init__(message, status.HTTP_403_FORBIDDEN, detail)

class ConflictException(ETRMSException):
    """
    Exception for resource conflict errors.
    
    Args:
        message: Error message
        detail: Additional error details
    """
    def __init__(
        self, 
        message: str = "Conflict", 
        detail: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    ):
        super().__init__(message, status.HTTP_409_CONFLICT, detail)

class BadRequestException(ETRMSException):
    """
    Exception for bad request errors.
    
    Args:
        message: Error message
        detail: Additional error details
    """
    def __init__(
        self, 
        message: str = "Bad request", 
        detail: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    ):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, detail)

class InternalServerException(ETRMSException):
    """
    Exception for internal server errors.
    
    Args:
        message: Error message
        detail: Additional error details
    """
    def __init__(
        self, 
        message: str = "Internal server error", 
        detail: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    ):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR, detail)

def setup_exception_handlers(app: FastAPI) -> None:
    """
    Set up exception handlers for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    @app.exception_handler(ETRMSException)
    async def etrms_exception_handler(request: Request, exc: ETRMSException) -> JSONResponse:
        """
        Handle ETRMS-specific exceptions.
        """
        logger.error(f"ETRMS Exception: {exc.message}")
        if exc.detail:
            logger.error(f"Detail: {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": exc.message,
                "detail": exc.detail,
                "status_code": exc.status_code,
            },
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """
        Handle HTTP exceptions.
        """
        logger.error(f"HTTP Exception: {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": str(exc.detail),
                "status_code": exc.status_code,
            },
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """
        Handle request validation errors.
        """
        logger.error(f"Validation Error: {exc.errors()}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "message": "Validation error",
                "detail": exc.errors(),
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            },
        )
    
    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """
        Handle Pydantic validation errors.
        """
        logger.error(f"Pydantic Validation Error: {exc.errors()}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "message": "Validation error",
                "detail": exc.errors(),
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            },
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Handle general exceptions.
        """
        logger.error(f"Unhandled Exception: {str(exc)}")
        logger.error(traceback.format_exc())
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "message": "Internal server error",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            },
        ) 