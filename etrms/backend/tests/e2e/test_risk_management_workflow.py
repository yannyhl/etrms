"""
End-to-end tests for the risk management workflow.

These tests simulate a complete workflow from starting monitoring to
evaluating circuit breakers and receiving alerts.
"""
import pytest
import asyncio
import json
import time
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import WebSocket

from app import app
from risk import RiskMonitor, CircuitBreaker
from risk.circuit_breaker import CircuitBreakerCondition
from exchange import ExchangeInterface


class MockWebSocket:
    """Mock WebSocket client for testing."""
    
    def __init__(self):
        self.received_messages = []
        self.closed = False
    
    async def connect(self, url):
        self.url = url
        self.closed = False
        return self
    
    async def send(self, message):
        pass
    
    async def receive(self):
        # Simulate receiving a message
        if not self.received_messages:
            return {"type": "websocket.disconnect"}
        return self.received_messages.pop(0)
    
    async def close(self):
        self.closed = True
    
    def add_message(self, message):
        self.received_messages.append({"type": "websocket.receive", "text": json.dumps(message)})
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


@pytest.mark.asyncio
async def test_risk_management_e2e_workflow():
    """
    Test the complete risk management workflow from setting up monitoring to
    receiving alert notifications.
    """
    # Create a test client
    client = TestClient(app)
    
    # Step 1: Start monitoring
    with patch('api.accounts.get_risk_monitor') as mock_get_risk_monitor:
        # Mock the risk monitor
        mock_monitor = AsyncMock(spec=RiskMonitor)
        mock_monitor.is_monitoring = False
        mock_monitor.add_exchange = AsyncMock(return_value=None)
        mock_monitor.add_symbol = AsyncMock(return_value=None)
        mock_monitor.start_monitoring = AsyncMock(return_value=None)
        mock_get_risk_monitor.return_value = mock_monitor
        
        # Call the start monitoring endpoint
        response = client.post(
            "/api/v1/accounts/monitor/start",
            params={"exchanges": ["binance"], "symbols": ["BTCUSDT", "ETHUSDT"]}
        )
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "started" in data["message"]
        
        # Verify that the monitor methods were called
        mock_monitor.add_exchange.assert_called_with("binance")
        assert mock_monitor.add_symbol.call_count == 2
        mock_monitor.start_monitoring.assert_called_once()
        
        # Set monitoring to active
        mock_monitor.is_monitoring = True
    
    # Step 2: Get monitoring status
    with patch('api.accounts.get_risk_monitor') as mock_get_risk_monitor:
        # Mock the risk monitor
        mock_monitor = AsyncMock(spec=RiskMonitor)
        mock_monitor.is_monitoring = True
        mock_monitor.refresh_interval = 5
        mock_monitor.exchanges = {"binance": AsyncMock()}
        mock_monitor.monitored_symbols = {"BTCUSDT", "ETHUSDT"}
        mock_monitor.calculate_risk_metrics = AsyncMock(return_value={
            "total_exposure": 100000.0,
            "max_drawdown": 10.0,
            "exchange_metrics": {},
            "symbol_metrics": {}
        })
        mock_get_risk_monitor.return_value = mock_monitor
        
        # Call the get monitoring status endpoint
        response = client.get("/api/v1/accounts/monitor/status")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["is_monitoring"] is True
        assert data["data"]["refresh_interval"] == 5
        assert "binance" in data["data"]["exchanges"]
        assert "BTCUSDT" in data["data"]["symbols"]
        assert "ETHUSDT" in data["data"]["symbols"]
    
    # Step 3: Add a circuit breaker condition
    with patch('api.risk.get_circuit_breaker') as mock_get_circuit_breaker:
        # Mock the circuit breaker
        mock_breaker = AsyncMock(spec=CircuitBreaker)
        mock_breaker.add_condition = AsyncMock(return_value=None)
        mock_get_circuit_breaker.return_value = mock_breaker
        
        # Call the add circuit breaker endpoint
        response = client.post(
            "/api/v1/risk/circuit-breakers",
            json={
                "name": "max_drawdown_10pct",
                "description": "Close position when drawdown exceeds 10%",
                "condition_type": "max_drawdown",
                "threshold": 10.0,
                "action": "close_position",
                "symbols": ["BTCUSDT"],
                "exchanges": ["binance"],
                "enabled": True
            }
        )
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "added" in data["message"]
        
        # Verify that the add_condition method was called
        mock_breaker.add_condition.assert_called_once()
    
    # Step 4: Evaluate circuit breakers
    with patch('api.risk.get_circuit_breaker') as mock_get_circuit_breaker, \
         patch('api.risk.get_risk_monitor') as mock_get_risk_monitor, \
         patch('api.websocket.manager.broadcast') as mock_broadcast:
        
        # Mock the circuit breaker
        mock_breaker = AsyncMock(spec=CircuitBreaker)
        
        # Create a mock condition and result
        mock_condition = AsyncMock(spec=CircuitBreakerCondition)
        mock_condition.name = "max_drawdown_10pct"
        mock_condition.description = "Close position when drawdown exceeds 10%"
        
        # Mock evaluate_all to return a triggered condition
        mock_breaker.evaluate_all = AsyncMock(return_value=[
            (mock_condition, {"status": "success", "message": "Position closed"})
        ])
        mock_get_circuit_breaker.return_value = mock_breaker
        
        # Mock the risk monitor
        mock_monitor = AsyncMock(spec=RiskMonitor)
        mock_monitor.is_monitoring = True
        mock_monitor.exchanges = {"binance": AsyncMock()}
        mock_monitor.positions = {
            "binance": [
                {
                    "symbol": "BTCUSDT",
                    "size": 1.0,
                    "entry_price": 50000.0,
                    "current_price": 45000.0,
                    "unrealized_pnl": -5000.0,
                    "position_value": 45000.0,
                    "leverage": 1.0,
                    "side": "long"
                }
            ]
        }
        mock_monitor.calculate_risk_metrics = AsyncMock(return_value={
            "total_exposure": 45000.0,
            "max_drawdown": 10.0,
            "exchange_metrics": {},
            "symbol_metrics": {}
        })
        mock_get_risk_monitor.return_value = mock_monitor
        
        # Mock the broadcast function
        mock_broadcast.return_value = AsyncMock()
        
        # Call the evaluate circuit breakers endpoint
        response = client.post("/api/v1/risk/evaluate")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "conditions" in data["data"]
        assert data["data"]["triggered_count"] == 1
        
        # Verify that the evaluate_all method was called
        mock_breaker.evaluate_all.assert_called_once()
    
    # Step 5: Stop monitoring
    with patch('api.accounts.get_risk_monitor') as mock_get_risk_monitor:
        # Mock the risk monitor
        mock_monitor = AsyncMock(spec=RiskMonitor)
        mock_monitor.is_monitoring = True
        mock_monitor.stop_monitoring = AsyncMock(return_value=None)
        mock_get_risk_monitor.return_value = mock_monitor
        
        # Call the stop monitoring endpoint
        response = client.post("/api/v1/accounts/monitor/stop")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "stopped" in data["message"]
        
        # Verify that the stop_monitoring method was called
        mock_monitor.stop_monitoring.assert_called_once()


@pytest.mark.asyncio
async def test_websocket_alerts_e2e():
    """
    Test receiving alerts via WebSocket after a circuit breaker is triggered.
    """
    # Mock WebSocket connection
    mock_ws = MockWebSocket()
    
    # Mock the WSGIApp's handling of WebSocket upgrades
    async def mock_websocket_connect(url, subprotocols=None):
        return mock_ws
    
    # Create a test client
    client = TestClient(app)
    
    with patch('api.websocket.manager.broadcast') as mock_broadcast, \
         patch('websockets.connect', side_effect=mock_websocket_connect):
        
        # Mock broadcasting an alert
        def broadcast_alert_effect(channel, message):
            if channel == "alerts":
                mock_ws.add_message(message)
        
        mock_broadcast.side_effect = broadcast_alert_effect
        
        # Simulate a circuit breaker alert
        alert = {
            "type": "circuit_breaker",
            "condition_name": "max_drawdown_10pct",
            "description": "Close position when drawdown exceeds 10%",
            "exchange": "binance",
            "symbol": "BTCUSDT",
            "triggered_at": time.time(),
            "context": {
                "current_drawdown": 12.5,
                "threshold": 10.0
            },
            "action_result": "Position closed successfully"
        }
        
        # Broadcast the alert
        from api.websocket import broadcast_alert
        asyncio.create_task(broadcast_alert(alert))
        
        # Wait a moment for the broadcast to happen
        await asyncio.sleep(0.1)
        
        # Check that the alert was broadcasted to the WebSocket
        assert len(mock_ws.received_messages) > 0
        
        # Verify message was received by the client
        message = mock_ws.received_messages[0]
        message_data = json.loads(message["text"])
        assert message_data["type"] == "circuit_breaker"
        assert message_data["condition_name"] == "max_drawdown_10pct"
        assert message_data["symbol"] == "BTCUSDT" 