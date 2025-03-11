"""
Enhanced Trading Risk Management System WebSocket API

This module provides WebSocket endpoints for real-time updates on account, position, 
and risk metrics data.
"""
import json
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
import uuid
from datetime import datetime
import copy

from utils.logger import get_logger
from risk import RiskMonitor
from api.accounts import get_risk_monitor

# Create a router instance
router = APIRouter()

# Create a logger instance
logger = get_logger(__name__)

# Connection manager for WebSockets
class ConnectionManager:
    def __init__(self):
        # Store active connections
        self.active_connections: Dict[str, List[WebSocket]] = {
            "positions": [],
            "accounts": [],
            "risk_metrics": [],
            "alerts": [],
        }
    
    async def connect(self, websocket: WebSocket, channel: str):
        """Connect a client to a specific channel"""
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)
        logger.info(f"Client connected to {channel} channel. Total: {len(self.active_connections[channel])}")
    
    def disconnect(self, websocket: WebSocket, channel: str):
        """Disconnect a client from a specific channel"""
        if channel in self.active_connections:
            if websocket in self.active_connections[channel]:
                self.active_connections[channel].remove(websocket)
                logger.info(f"Client disconnected from {channel} channel. Remaining: {len(self.active_connections[channel])}")
    
    async def broadcast(self, channel: str, message: Dict[str, Any]):
        """Broadcast a message to all clients connected to a specific channel"""
        if channel not in self.active_connections:
            return
        
        # Convert message to JSON
        json_message = json.dumps(message)
        
        # List of disconnected clients to be removed
        disconnected = []
        
        # Send message to all connected clients
        for connection in self.active_connections[channel]:
            try:
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_text(json_message)
                else:
                    disconnected.append(connection)
            except RuntimeError:
                # Connection might be closed or in a bad state
                disconnected.append(connection)
            except Exception as e:
                logger.error(f"Error sending message to websocket: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            if connection in self.active_connections[channel]:
                self.active_connections[channel].remove(connection)

# Create a connection manager instance
manager = ConnectionManager()

@router.websocket("/positions")
async def positions_websocket(
    websocket: WebSocket,
    monitor: RiskMonitor = Depends(get_risk_monitor)
):
    """
    WebSocket endpoint for real-time position updates.
    
    This endpoint sends position updates whenever they change.
    """
    await manager.connect(websocket, "positions")
    try:
        while True:
            # Wait for a message (just to keep the connection alive)
            # We'll ignore the actual message content as we'll push updates automatically
            _ = await websocket.receive_text()
            
            # Send the current position data if monitoring is active
            if monitor.is_monitoring:
                position_summary = await monitor.get_position_summary()
                await websocket.send_json(position_summary)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "positions")
    except Exception as e:
        logger.error(f"Error in positions WebSocket: {e}")
        manager.disconnect(websocket, "positions")

@router.websocket("/accounts")
async def accounts_websocket(
    websocket: WebSocket,
    monitor: RiskMonitor = Depends(get_risk_monitor)
):
    """
    WebSocket endpoint for real-time account updates.
    
    This endpoint sends account updates whenever they change.
    """
    await manager.connect(websocket, "accounts")
    try:
        while True:
            # Wait for a message (just to keep the connection alive)
            _ = await websocket.receive_text()
            
            # Send the current account data if monitoring is active
            if monitor.is_monitoring:
                account_summary = {}
                for exchange_name, exchange in monitor.exchanges.items():
                    account_summary[exchange_name] = await exchange.get_account_info()
                await websocket.send_json({"accounts": account_summary})
    except WebSocketDisconnect:
        manager.disconnect(websocket, "accounts")
    except Exception as e:
        logger.error(f"Error in accounts WebSocket: {e}")
        manager.disconnect(websocket, "accounts")

@router.websocket("/risk-metrics")
async def risk_metrics_websocket(websocket: WebSocket):
    """WebSocket endpoint for risk metrics data.
    
    Provides real-time updates on risk metrics and circuit breakers.
    """
    # Accept the connection
    await websocket.accept()
    
    # Add to active connections
    client_id = str(uuid.uuid4())
    manager.add_connection(client_id, ConnectionType.RISK_METRICS, websocket)
    logger.info(f"Risk metrics WebSocket client connected: {client_id}")
    
    # Send initial data if available
    monitor = websocket.app.state.risk_monitor
    if monitor and monitor.is_monitoring:
        try:
            # Get current risk metrics
            risk_metrics = await monitor.calculate_risk_metrics()
            
            # Get current circuit breakers
            circuit_breaker = websocket.app.state.circuit_breaker
            breakers_data = None
            if circuit_breaker:
                breakers_data = [condition.to_dict() for condition in circuit_breaker.conditions]
            
            # Send initial data
            await websocket.send_json({
                "type": "initial_data",
                "timestamp": datetime.now().isoformat(),
                "risk_metrics": risk_metrics,
                "circuit_breakers": breakers_data
            })
            
            logger.info(f"Sent initial risk metrics data to client {client_id}")
        except Exception as e:
            logger.error(f"Error sending initial risk metrics data: {str(e)}")
            await websocket.send_json({
                "type": "error",
                "message": "Failed to get initial data",
                "error": str(e)
            })
    
    try:
        # Main connection loop
        while True:
            # Wait for ping or any message
            data = await websocket.receive_text()
            
            # Process ping messages
            if data == "ping":
                await websocket.send_text("pong")
                continue
                
            # Process any client commands
            try:
                message = json.loads(data)
                if message.get("type") == "get_risk_metrics":
                    # Client requested fresh risk metrics
                    if monitor and monitor.is_monitoring:
                        risk_metrics = await monitor.calculate_risk_metrics()
                        await websocket.send_json({
                            "type": "risk_metrics_update",
                            "timestamp": datetime.now().isoformat(),
                            "risk_metrics": risk_metrics
                        })
            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON from client {client_id}")
            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {str(e)}")
                
    except WebSocketDisconnect:
        logger.info(f"Risk metrics WebSocket client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"Error in risk metrics WebSocket: {str(e)}")
    finally:
        # Remove from active connections
        manager.remove_connection(client_id, ConnectionType.RISK_METRICS)

@router.websocket("/alerts")
async def alerts_websocket(websocket: WebSocket):
    """WebSocket endpoint for alerts.
    
    Provides real-time alerts for circuit breaker triggers and other notifications.
    """
    # Accept the connection
    await websocket.accept()
    
    # Add to active connections
    client_id = str(uuid.uuid4())
    manager.add_connection(client_id, ConnectionType.ALERTS, websocket)
    logger.info(f"Alerts WebSocket client connected: {client_id}")
    
    # Send initial data if available
    circuit_breaker = websocket.app.state.circuit_breaker
    
    if circuit_breaker:
        try:
            # Get recent alerts history (last 10)
            alerts_history = getattr(websocket.app.state, 'alerts_history', [])
            if alerts_history:
                await websocket.send_json({
                    "type": "initial_data",
                    "timestamp": datetime.now().isoformat(),
                    "alerts": alerts_history[-10:]  # Last 10 alerts
                })
                
            logger.info(f"Sent initial alerts data to client {client_id}")
        except Exception as e:
            logger.error(f"Error sending initial alerts data: {str(e)}")
            await websocket.send_json({
                "type": "error",
                "message": "Failed to get initial alerts data",
                "error": str(e)
            })
    
    try:
        # Main connection loop
        while True:
            # Wait for ping or any message
            data = await websocket.receive_text()
            
            # Process ping messages
            if data == "ping":
                await websocket.send_text("pong")
                continue
                
            # Process any client commands
            try:
                message = json.loads(data)
                if message.get("type") == "get_alerts_history":
                    # Client requested alerts history
                    limit = message.get("limit", 10)
                    alerts_history = getattr(websocket.app.state, 'alerts_history', [])
                    await websocket.send_json({
                        "type": "alerts_history",
                        "timestamp": datetime.now().isoformat(),
                        "alerts": alerts_history[-limit:] if alerts_history else []
                    })
            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON from client {client_id}")
            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {str(e)}")
                
    except WebSocketDisconnect:
        logger.info(f"Alerts WebSocket client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"Error in alerts WebSocket: {str(e)}")
    finally:
        # Remove from active connections
        manager.remove_connection(client_id, ConnectionType.ALERTS)

async def broadcast_risk_metrics(data: Dict[str, Any]):
    """Broadcast risk metrics update to all connected clients.
    
    Args:
        data: The risk metrics data to broadcast
    """
    # Store the most recent data for new connections
    if data.get("risk_metrics"):
        # Make a deep copy to avoid reference issues
        app_state = get_app_state()
        if app_state:
            app_state.latest_risk_metrics = copy.deepcopy(data)
    
    # Broadcast to all connected clients
    await manager.broadcast(ConnectionType.RISK_METRICS, data)
    logger.debug(f"Broadcast risk metrics to {manager.connection_count(ConnectionType.RISK_METRICS)} clients")

async def broadcast_alert(data: Dict[str, Any]):
    """Broadcast alert to all connected clients.
    
    Args:
        data: The alert data to broadcast
    """
    # Store alert in history
    app_state = get_app_state()
    if app_state:
        if not hasattr(app_state, 'alerts_history'):
            app_state.alerts_history = []
        
        # Add timestamp if not present
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
            
        # Limit history to 100 items
        app_state.alerts_history.append(data)
        if len(app_state.alerts_history) > 100:
            app_state.alerts_history = app_state.alerts_history[-100:]
    
    # Broadcast to all connected clients
    await manager.broadcast(ConnectionType.ALERTS, data)
    logger.info(f"Broadcast alert to {manager.connection_count(ConnectionType.ALERTS)} clients")

def get_app_state():
    """Get the FastAPI app state object."""
    import inspect
    
    # Find the app instance in stack frames
    for frame_info in inspect.stack():
        frame = frame_info.frame
        if 'app' in frame.f_locals and hasattr(frame.f_locals['app'], 'state'):
            return frame.f_locals['app'].state
    
    # Fallback to main app if available
    try:
        from main import app
        return app.state
    except ImportError:
        logger.error("Failed to find app state")
        return None

# Function to broadcast position updates (to be called from RiskMonitor when positions change)
async def broadcast_position_update(position_data: Dict[str, Any]):
    """
    Broadcast position updates to all connected clients on the positions channel.
    
    Args:
        position_data: Dictionary containing position data.
    """
    await manager.broadcast("positions", position_data)

# Function to broadcast account updates (to be called from RiskMonitor when account changes)
async def broadcast_account_update(account_data: Dict[str, Any]):
    """
    Broadcast account updates to all connected clients on the accounts channel.
    
    Args:
        account_data: Dictionary containing account data.
    """
    await manager.broadcast("accounts", account_data)

# Function to broadcast risk metrics updates (to be called from RiskMonitor when metrics change)
async def broadcast_risk_metrics_update(metrics_data: Dict[str, Any]):
    """
    Broadcast risk metrics updates to all connected clients on the risk_metrics channel.
    
    Args:
        metrics_data: Dictionary containing risk metrics data.
    """
    await manager.broadcast("risk_metrics", metrics_data) 