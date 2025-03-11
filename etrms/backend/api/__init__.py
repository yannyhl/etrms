"""
Enhanced Trading Risk Management System API Module

This module provides the API endpoints for the ETRMS system.
"""
from fastapi import APIRouter

# Create a main API router
api_router = APIRouter()

# Import and include sub-routers
from api.accounts import router as accounts_router
from api.positions import router as positions_router
from api.risk import router as risk_router
from api.config import router as config_router
from api.assistant import router as assistant_router
from api.websocket import router as websocket_router
from api.routes.auth import router as auth_router
from api.routes.backtesting import router as backtesting_router

# Include sub-routers
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(accounts_router, prefix="/accounts", tags=["accounts"])
api_router.include_router(positions_router, prefix="/positions", tags=["positions"])
api_router.include_router(risk_router, prefix="/risk", tags=["risk"])
api_router.include_router(config_router, prefix="/config", tags=["config"])
api_router.include_router(assistant_router, prefix="/assistant", tags=["assistant"])
api_router.include_router(websocket_router, prefix="/ws", tags=["websocket"])
api_router.include_router(backtesting_router, tags=["backtesting"]) 