"""
WebSocket routes for real-time updates in the ETRMS system.
"""

from fastapi import APIRouter, WebSocket, Depends, HTTPException, status
from typing import Optional

from etrms.backend.models.user import User
from etrms.backend.api.dependencies import get_current_user_from_token
from etrms.backend.websocket.websocket_manager import websocket_manager

router = APIRouter(prefix="/ws", tags=["websocket"])

@router.websocket("/risk-metrics")
async def websocket_risk_metrics(websocket: WebSocket, token: Optional[str] = None):
    """
    WebSocket endpoint for real-time risk metrics updates.
    
    Args:
        websocket: The WebSocket connection
        token: The authentication token
    """
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    try:
        # Authenticate the user
        user = await get_current_user_from_token(token)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Handle the WebSocket connection
        await websocket_manager.handle_websocket(websocket, "risk_metrics", user.id)
    except Exception as e:
        # Log the error and close the connection
        print(f"WebSocket error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)

@router.websocket("/positions")
async def websocket_positions(websocket: WebSocket, token: Optional[str] = None):
    """
    WebSocket endpoint for real-time position updates.
    
    Args:
        websocket: The WebSocket connection
        token: The authentication token
    """
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    try:
        # Authenticate the user
        user = await get_current_user_from_token(token)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Handle the WebSocket connection
        await websocket_manager.handle_websocket(websocket, "positions", user.id)
    except Exception as e:
        # Log the error and close the connection
        print(f"WebSocket error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)

@router.websocket("/account-info")
async def websocket_account_info(websocket: WebSocket, token: Optional[str] = None):
    """
    WebSocket endpoint for real-time account information updates.
    
    Args:
        websocket: The WebSocket connection
        token: The authentication token
    """
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    try:
        # Authenticate the user
        user = await get_current_user_from_token(token)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Handle the WebSocket connection
        await websocket_manager.handle_websocket(websocket, "account_info", user.id)
    except Exception as e:
        # Log the error and close the connection
        print(f"WebSocket error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)

@router.websocket("/circuit-breaker-events")
async def websocket_circuit_breaker_events(websocket: WebSocket, token: Optional[str] = None):
    """
    WebSocket endpoint for real-time circuit breaker event updates.
    
    Args:
        websocket: The WebSocket connection
        token: The authentication token
    """
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    try:
        # Authenticate the user
        user = await get_current_user_from_token(token)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Handle the WebSocket connection
        await websocket_manager.handle_websocket(websocket, "circuit_breaker_events", user.id)
    except Exception as e:
        # Log the error and close the connection
        print(f"WebSocket error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR) 