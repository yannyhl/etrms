"""
Enhanced Trading Risk Management System - Main Application

This module provides the main FastAPI application for the ETRMS.
"""
import asyncio
import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging

from api.routes import backtesting, risk, accounts, positions, config, auth, backtest, analysis, assistant
from api.routes.auth import router as auth_router
from auth.auth_service import create_default_user
from middleware.auth_middleware import AuthMiddleware
from utils.logger import configure_logging, get_logger
from api.dependencies import get_market_analysis_service, get_ai_assistant_service
from utils.error_handler import setup_exception_handlers


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

# Set up exception handlers
setup_exception_handlers(app)

# Include routers
app.include_router(auth_router)
app.include_router(backtesting.router)
app.include_router(risk.router)
app.include_router(accounts.router)
app.include_router(positions.router)
app.include_router(config.router)
app.include_router(backtest.router, prefix="/api/v1/backtest")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(assistant.router, prefix="/api/v1")


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
    
    # Start the market analysis service
    try:
        market_analysis_service = get_market_analysis_service()
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]  # Default symbols
        exchanges = ["binance", "hyperliquid"]  # Default exchanges
        await market_analysis_service.start(symbols=symbols, exchanges=exchanges)
        logger.info("Started market analysis service")
    except Exception as e:
        logger.error(f"Error starting market analysis service: {e}")
    
    # Start the AI assistant service
    try:
        ai_assistant_service = get_ai_assistant_service()
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]  # Default symbols
        exchanges = ["binance", "hyperliquid"]  # Default exchanges
        await ai_assistant_service.start(symbols=symbols, exchanges=exchanges)
        logger.info("Started AI assistant service")
    except Exception as e:
        logger.error(f"Error starting AI assistant service: {e}")
    
    logger.info("Application startup completed")


@app.on_event("shutdown")
async def shutdown_event():
    """Run cleanup tasks when the application shuts down."""
    logger.info("Shutting down Enhanced Trading Risk Management System")
    
    # Run cleanup tasks here
    
    # Stop the market analysis service
    try:
        market_analysis_service = get_market_analysis_service()
        await market_analysis_service.stop()
        logger.info("Stopped market analysis service")
    except Exception as e:
        logger.error(f"Error stopping market analysis service: {e}")
    
    # Stop the AI assistant service
    try:
        ai_assistant_service = get_ai_assistant_service()
        await ai_assistant_service.stop()
        logger.info("Stopped AI assistant service")
    except Exception as e:
        logger.error(f"Error stopping AI assistant service: {e}")
    
    logger.info("Application shutdown completed")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to the Enhanced Trading Risk Management System API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
    ) 