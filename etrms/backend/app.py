"""
Enhanced Trading Risk Management System - Main Application

This module provides the main FastAPI application for the ETRMS.
"""
import asyncio
import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from api.routes import backtesting, risk, accounts, positions, config
from api.routes.auth import router as auth_router
from auth.auth_service import create_default_user
from middleware.auth_middleware import AuthMiddleware
from utils.logger import configure_logging, get_logger


# Configure logging
configure_logging()
logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Enhanced Trading Risk Management System API",
    description="API for the Enhanced Trading Risk Management System",
    version="0.1.0",
)

# Add CORS middleware
origins = [
    "http://localhost",
    "http://localhost:3000",  # React development server
    "http://localhost:8000",  # FastAPI development server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
app.add_middleware(
    AuthMiddleware,
    public_paths=[
        "/docs",
        "/redoc",
        "/openapi.json",
        "/auth/login",
        "/health",
    ],
    exclude_paths=[
        "/static",
    ],
)

# Include routers
app.include_router(auth_router)
app.include_router(backtesting.router)
app.include_router(risk.router)
app.include_router(accounts.router)
app.include_router(positions.router)
app.include_router(config.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    """Run startup tasks when the application starts."""
    logger.info("Starting Enhanced Trading Risk Management System")
    
    # Create default user if none exists
    await create_default_user()
    
    logger.info("Application startup completed")


@app.on_event("shutdown")
async def shutdown_event():
    """Run cleanup tasks when the application shuts down."""
    logger.info("Shutting down Enhanced Trading Risk Management System")
    
    # Run cleanup tasks here
    
    logger.info("Application shutdown completed")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
    ) 