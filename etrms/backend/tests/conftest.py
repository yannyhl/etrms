"""
Enhanced Trading Risk Management System Test Configuration

This module defines fixtures and configuration for testing.
"""
import asyncio
import os
import pytest
import json
from typing import Dict, Any, Generator, AsyncGenerator
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
import websockets
from websockets.legacy.client import WebSocketClientProtocol
from unittest.mock import AsyncMock, Mock, patch

# Import application components
from app import app
from risk import RiskMonitor, CircuitBreaker
from risk.circuit_breaker import CircuitBreakerCondition
from api.accounts import get_risk_monitor
from api.risk import get_circuit_breaker
from exchange import ExchangeInterface, ExchangeClientFactory

# Base URL for API endpoints
API_BASE_URL = "/api/v1"


@pytest.fixture
def test_app() -> FastAPI:
    """
    Fixture that returns the FastAPI application.
    """
    return app


@pytest.fixture
def client(test_app: FastAPI) -> Generator[TestClient, None, None]:
    """
    Fixture that returns a test client for the FastAPI application.
    
    Args:
        test_app: FastAPI application instance
        
    Returns:
        TestClient instance
    """
    with TestClient(test_app) as client:
        yield client


@pytest.fixture
async def async_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture that returns an async test client for the FastAPI application.
    
    Args:
        test_app: FastAPI application instance
        
    Returns:
        AsyncClient instance
    """
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_exchange() -> Mock:
    """
    Fixture that returns a mock exchange.
    
    Returns:
        Mock exchange instance
    """
    exchange = Mock(spec=ExchangeInterface)
    
    # Mock account info
    exchange.get_account_info = AsyncMock(return_value={
        "balance": 10000.0,
        "equity": 10500.0,
        "available": 9000.0,
        "margin_used": 1000.0,
        "unrealized_pnl": 500.0
    })
    
    # Mock position data
    exchange.get_positions = AsyncMock(return_value=[
        {
            "symbol": "BTCUSDT",
            "size": 1.0,
            "entry_price": 50000.0,
            "current_price": 52000.0,
            "unrealized_pnl": 2000.0,
            "position_value": 52000.0,
            "leverage": 5.0,
            "side": "long"
        },
        {
            "symbol": "ETHUSDT",
            "size": 10.0,
            "entry_price": 3000.0,
            "current_price": 2800.0,
            "unrealized_pnl": -2000.0,
            "position_value": 28000.0,
            "leverage": 3.0,
            "side": "long"
        }
    ])
    
    # Mock other methods
    exchange.initialize = AsyncMock(return_value=None)
    exchange.close = AsyncMock(return_value=None)
    
    return exchange


@pytest.fixture
def mock_exchange_factory(mock_exchange: Mock) -> Mock:
    """
    Fixture that returns a mock exchange factory.
    
    Args:
        mock_exchange: Mock exchange instance
        
    Returns:
        Mock exchange factory
    """
    factory = Mock(spec=ExchangeClientFactory)
    factory.get_client = Mock(return_value=mock_exchange)
    factory.get_supported_exchanges = Mock(return_value=["binance", "hyperliquid"])
    
    return factory


@pytest.fixture
def mock_risk_monitor(mock_exchange: Mock) -> AsyncGenerator[RiskMonitor, None]:
    """
    Fixture that returns a mock risk monitor with pre-configured data.
    
    Args:
        mock_exchange: Mock exchange instance
        
    Returns:
        RiskMonitor instance with mock data
    """
    with patch('api.accounts.get_risk_monitor', autospec=True) as mock_get_risk_monitor:
        # Create a RiskMonitor instance
        monitor = RiskMonitor(refresh_interval=1)
        monitor.is_monitoring = True
        
        # Add mock exchanges
        monitor.exchanges = {
            "binance": mock_exchange,
            "hyperliquid": mock_exchange
        }
        
        # Add mock positions
        monitor.positions = {
            "binance": [
                {
                    "symbol": "BTCUSDT",
                    "size": 1.0,
                    "entry_price": 50000.0,
                    "current_price": 52000.0,
                    "unrealized_pnl": 2000.0,
                    "position_value": 52000.0,
                    "leverage": 5.0,
                    "side": "long"
                },
                {
                    "symbol": "ETHUSDT",
                    "size": 10.0,
                    "entry_price": 3000.0,
                    "current_price": 2800.0,
                    "unrealized_pnl": -2000.0,
                    "position_value": 28000.0,
                    "leverage": 3.0,
                    "side": "long"
                }
            ],
            "hyperliquid": [
                {
                    "symbol": "BTCUSD",
                    "size": 0.5,
                    "entry_price": 51000.0,
                    "current_price": 52000.0,
                    "unrealized_pnl": 500.0,
                    "position_value": 26000.0,
                    "leverage": 2.0,
                    "side": "long"
                }
            ]
        }
        
        # Add mock account info
        monitor.account_info = {
            "binance": {
                "balance": 10000.0,
                "equity": 10500.0,
                "available": 9000.0,
                "margin_used": 1000.0,
                "unrealized_pnl": 500.0
            },
            "hyperliquid": {
                "balance": 5000.0,
                "equity": 5200.0,
                "available": 4500.0,
                "margin_used": 500.0,
                "unrealized_pnl": 200.0
            }
        }
        
        # Mock the get_risk_monitor function to return our instance
        mock_get_risk_monitor.return_value = monitor
        
        yield monitor


@pytest.fixture
def mock_circuit_breaker() -> AsyncGenerator[CircuitBreaker, None]:
    """
    Fixture that returns a mock circuit breaker with pre-configured conditions.
    
    Returns:
        CircuitBreaker instance with mock conditions
    """
    with patch('api.risk.get_circuit_breaker', autospec=True) as mock_get_circuit_breaker:
        # Create a CircuitBreaker instance
        breaker = CircuitBreaker()
        
        # Define mock evaluation and action functions
        async def mock_action(exchange, context):
            return {"status": "success", "message": "Action executed"}
        
        def mock_evaluation(context):
            return True
        
        # Add conditions
        condition1 = CircuitBreakerCondition(
            name="max_drawdown_test",
            description="Test max drawdown condition",
            evaluation_fn=mock_evaluation,
            action_fn=mock_action,
            symbols=["BTCUSDT"],
            exchanges=["binance"],
            enabled=True
        )
        
        condition2 = CircuitBreakerCondition(
            name="volatility_test",
            description="Test volatility condition",
            evaluation_fn=mock_evaluation,
            action_fn=mock_action,
            symbols=None,  # Apply to all symbols
            exchanges=None,  # Apply to all exchanges
            enabled=True
        )
        
        # Add conditions to circuit breaker
        breaker.add_condition(condition1)
        breaker.add_condition(condition2)
        
        # Mock the get_circuit_breaker function to return our instance
        mock_get_circuit_breaker.return_value = breaker
        
        yield breaker


class MockWebSocketClient:
    """
    Mock WebSocket client for testing WebSocket endpoints.
    """
    
    def __init__(self):
        self.messages = []
        self.is_connected = False
        self.client_state = "connected"
    
    async def connect(self):
        self.is_connected = True
    
    async def disconnect(self):
        self.is_connected = False
    
    async def send_text(self, message: str):
        pass
    
    async def send_json(self, data: Dict[str, Any]):
        self.messages.append(data)
    
    async def receive_text(self):
        return "ping"
    
    async def receive_json(self):
        if not self.messages:
            return {}
        return self.messages.pop(0)
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()


@pytest.fixture
def mock_websocket_client() -> MockWebSocketClient:
    """
    Fixture that returns a mock WebSocket client.
    
    Returns:
        MockWebSocketClient instance
    """
    return MockWebSocketClient()


@pytest.fixture
def mock_websocket() -> AsyncGenerator[WebSocketClientProtocol, None]:
    """
    Fixture that returns a mock WebSocket connection for testing.
    
    Returns:
        Mock WebSocket connection
    """
    with patch('fastapi.WebSocket', autospec=True) as mock_ws:
        mock_ws.send_text = AsyncMock()
        mock_ws.send_json = AsyncMock()
        mock_ws.receive_text = AsyncMock(return_value="ping")
        mock_ws.receive_json = AsyncMock(return_value={})
        mock_ws.client_state = "connected"
        
        yield mock_ws 