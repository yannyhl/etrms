"""
WebSocket manager for handling real-time updates in the ETRMS system.
"""

import asyncio
import json
import logging
from typing import Dict, Set, Callable, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Manages WebSocket connections and message broadcasting.
    """
    def __init__(self):
        # Active connections by channel
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # User ID to WebSocket mapping
        self.user_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, channel: str, user_id: str):
        """
        Connect a WebSocket client to a specific channel.
        
        Args:
            websocket: The WebSocket connection
            channel: The channel to connect to
            user_id: The ID of the authenticated user
        """
        await websocket.accept()
        
        # Initialize channel if it doesn't exist
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        
        # Initialize user connections if they don't exist
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        
        # Add connection to channel and user mappings
        self.active_connections[channel].add(websocket)
        self.user_connections[user_id].add(websocket)
        
        logger.info(f"Client connected to channel '{channel}' (User ID: {user_id})")
    
    def disconnect(self, websocket: WebSocket, channel: str, user_id: str):
        """
        Disconnect a WebSocket client from a specific channel.
        
        Args:
            websocket: The WebSocket connection
            channel: The channel to disconnect from
            user_id: The ID of the authenticated user
        """
        # Remove from channel connections
        if channel in self.active_connections:
            if websocket in self.active_connections[channel]:
                self.active_connections[channel].remove(websocket)
            
            # Clean up empty channels
            if not self.active_connections[channel]:
                del self.active_connections[channel]
        
        # Remove from user connections
        if user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            
            # Clean up empty user connections
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        logger.info(f"Client disconnected from channel '{channel}' (User ID: {user_id})")
    
    async def broadcast_to_channel(self, channel: str, message: Any):
        """
        Broadcast a message to all connections in a specific channel.
        
        Args:
            channel: The channel to broadcast to
            message: The message to broadcast (will be JSON-serialized)
        """
        if channel not in self.active_connections:
            return
        
        disconnected = set()
        json_message = json.dumps(message)
        
        for connection in self.active_connections[channel]:
            try:
                await connection.send_text(json_message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.add(connection)
        
        # Clean up any disconnected connections
        for connection in disconnected:
            # We don't know the user_id here, so we'll just remove from the channel
            if channel in self.active_connections and connection in self.active_connections[channel]:
                self.active_connections[channel].remove(connection)
    
    async def broadcast_to_user(self, user_id: str, message: Any):
        """
        Broadcast a message to all connections for a specific user.
        
        Args:
            user_id: The ID of the user to broadcast to
            message: The message to broadcast (will be JSON-serialized)
        """
        if user_id not in self.user_connections:
            return
        
        disconnected = set()
        json_message = json.dumps(message)
        
        for connection in self.user_connections[user_id]:
            try:
                await connection.send_text(json_message)
            except Exception as e:
                logger.error(f"Error broadcasting to user connection: {e}")
                disconnected.add(connection)
        
        # Clean up any disconnected connections
        for connection in disconnected:
            if user_id in self.user_connections and connection in self.user_connections[user_id]:
                self.user_connections[user_id].remove(connection)

# Global connection manager instance
manager = ConnectionManager()

class WebSocketManager:
    """
    Manages WebSocket connections and message handling for the ETRMS system.
    """
    def __init__(self):
        self.connection_manager = manager
        self.tasks = set()
    
    async def handle_websocket(self, websocket: WebSocket, channel: str, user_id: str):
        """
        Handle a WebSocket connection for a specific channel.
        
        Args:
            websocket: The WebSocket connection
            channel: The channel to connect to
            user_id: The ID of the authenticated user
        """
        await self.connection_manager.connect(websocket, channel, user_id)
        
        try:
            # Send initial connection confirmation
            await websocket.send_json({
                "type": "connection_established",
                "channel": channel,
                "message": f"Connected to {channel} channel"
            })
            
            # Handle incoming messages (if needed)
            while True:
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    # Process message if needed
                    await websocket.send_json({
                        "type": "acknowledgement",
                        "message": "Message received"
                    })
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid JSON format"
                    })
        except WebSocketDisconnect:
            self.connection_manager.disconnect(websocket, channel, user_id)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            self.connection_manager.disconnect(websocket, channel, user_id)
    
    async def broadcast_risk_metrics(self, user_id: str, metrics: Dict[str, Any]):
        """
        Broadcast risk metrics to a specific user.
        
        Args:
            user_id: The ID of the user to broadcast to
            metrics: The risk metrics to broadcast
        """
        await self.connection_manager.broadcast_to_user(user_id, {
            "type": "risk_metrics",
            "data": metrics,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def broadcast_positions(self, user_id: str, positions: Dict[str, Any]):
        """
        Broadcast positions to a specific user.
        
        Args:
            user_id: The ID of the user to broadcast to
            positions: The positions to broadcast
        """
        await self.connection_manager.broadcast_to_user(user_id, {
            "type": "positions",
            "data": positions,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def broadcast_account_info(self, user_id: str, account_info: Dict[str, Any]):
        """
        Broadcast account information to a specific user.
        
        Args:
            user_id: The ID of the user to broadcast to
            account_info: The account information to broadcast
        """
        await self.connection_manager.broadcast_to_user(user_id, {
            "type": "account_info",
            "data": account_info,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def broadcast_circuit_breaker_event(self, user_id: str, event: Dict[str, Any]):
        """
        Broadcast a circuit breaker event to a specific user.
        
        Args:
            user_id: The ID of the user to broadcast to
            event: The circuit breaker event to broadcast
        """
        await self.connection_manager.broadcast_to_user(user_id, {
            "type": "circuit_breaker_event",
            "data": event,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    def start_background_task(self, coro):
        """
        Start a background task and keep track of it.
        
        Args:
            coro: The coroutine to run as a background task
        """
        task = asyncio.create_task(coro)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return task

# Global WebSocket manager instance
websocket_manager = WebSocketManager() 