"""
Unit tests for the WebSocket API.
"""
import pytest
import json
from unittest.mock import patch, AsyncMock
from fastapi import WebSocket

from api.websocket import (
    ConnectionManager,
    positions_websocket,
    accounts_websocket,
    risk_metrics_websocket,
    alerts_websocket,
    broadcast_alert,
    broadcast_position_update,
    broadcast_account_update,
    broadcast_risk_metrics_update
)
from risk import RiskMonitor


@pytest.mark.asyncio
async def test_connection_manager_connect():
    """Test the ConnectionManager connect method."""
    # Create a ConnectionManager instance
    manager = ConnectionManager()
    
    # Create a mock WebSocket
    websocket = AsyncMock(spec=WebSocket)
    
    # Call the connect method
    await manager.connect(websocket, "positions")
    
    # Check that the WebSocket was accepted
    websocket.accept.assert_called_once()
    
    # Check that the WebSocket was added to the active connections
    assert websocket in manager.active_connections["positions"]


@pytest.mark.asyncio
async def test_connection_manager_disconnect():
    """Test the ConnectionManager disconnect method."""
    # Create a ConnectionManager instance
    manager = ConnectionManager()
    
    # Create a mock WebSocket
    websocket = AsyncMock(spec=WebSocket)
    
    # Add the WebSocket to the active connections
    manager.active_connections["positions"].append(websocket)
    
    # Call the disconnect method
    manager.disconnect(websocket, "positions")
    
    # Check that the WebSocket was removed from the active connections
    assert websocket not in manager.active_connections["positions"]


@pytest.mark.asyncio
async def test_connection_manager_broadcast():
    """Test the ConnectionManager broadcast method."""
    # Create a ConnectionManager instance
    manager = ConnectionManager()
    
    # Create mock WebSockets
    websocket1 = AsyncMock(spec=WebSocket)
    websocket1.client_state = "connected"
    websocket2 = AsyncMock(spec=WebSocket)
    websocket2.client_state = "connected"
    
    # Add the WebSockets to the active connections
    manager.active_connections["positions"].append(websocket1)
    manager.active_connections["positions"].append(websocket2)
    
    # Create a test message
    message = {"status": "success", "data": {"test": "data"}}
    
    # Call the broadcast method
    await manager.broadcast("positions", message)
    
    # Check that the message was sent to both WebSockets
    websocket1.send_text.assert_called_once()
    websocket2.send_text.assert_called_once()
    
    # Check that the message was correctly serialized
    expected_message = json.dumps(message)
    websocket1.send_text.assert_called_with(expected_message)
    websocket2.send_text.assert_called_with(expected_message)


@pytest.mark.asyncio
async def test_positions_websocket():
    """Test the positions WebSocket endpoint."""
    # Create a mock WebSocket
    websocket = AsyncMock(spec=WebSocket)
    websocket.receive_text = AsyncMock(side_effect=["subscribe", Exception("Test exception")])
    
    # Create a mock RiskMonitor
    mock_monitor = AsyncMock(spec=RiskMonitor)
    mock_monitor.is_monitoring = True
    mock_monitor.get_position_summary = AsyncMock(return_value={
        "total_position_value": 100000.0,
        "total_unrealized_pnl": 5000.0,
        "exchanges": {},
        "positions_by_symbol": {}
    })
    
    # Patch the ConnectionManager.connect method
    with patch('api.websocket.manager.connect', new_callable=AsyncMock) as mock_connect:
        with patch('api.websocket.manager.disconnect') as mock_disconnect:
            # Call the positions_websocket function
            with pytest.raises(Exception, match="Test exception"):
                await positions_websocket(websocket, mock_monitor)
            
            # Check that the ConnectionManager.connect method was called
            mock_connect.assert_called_once_with(websocket, "positions")
            
            # Check that the ConnectionManager.disconnect method was called
            mock_disconnect.assert_called_once_with(websocket, "positions")
            
            # Check that the WebSocket.send_json method was called with position data
            websocket.send_json.assert_called_once()
            
            # Check that the RiskMonitor.get_position_summary method was called
            mock_monitor.get_position_summary.assert_called_once()


@pytest.mark.asyncio
async def test_accounts_websocket():
    """Test the accounts WebSocket endpoint."""
    # Create a mock WebSocket
    websocket = AsyncMock(spec=WebSocket)
    websocket.receive_text = AsyncMock(side_effect=["subscribe", Exception("Test exception")])
    
    # Create a mock RiskMonitor
    mock_monitor = AsyncMock(spec=RiskMonitor)
    mock_monitor.is_monitoring = True
    mock_monitor.exchanges = {
        "binance": AsyncMock(),
        "hyperliquid": AsyncMock()
    }
    mock_monitor.exchanges["binance"].get_account_info = AsyncMock(return_value={
        "balance": 10000.0,
        "equity": 10500.0
    })
    mock_monitor.exchanges["hyperliquid"].get_account_info = AsyncMock(return_value={
        "balance": 5000.0,
        "equity": 5200.0
    })
    
    # Patch the ConnectionManager.connect method
    with patch('api.websocket.manager.connect', new_callable=AsyncMock) as mock_connect:
        with patch('api.websocket.manager.disconnect') as mock_disconnect:
            # Call the accounts_websocket function
            with pytest.raises(Exception, match="Test exception"):
                await accounts_websocket(websocket, mock_monitor)
            
            # Check that the ConnectionManager.connect method was called
            mock_connect.assert_called_once_with(websocket, "accounts")
            
            # Check that the ConnectionManager.disconnect method was called
            mock_disconnect.assert_called_once_with(websocket, "accounts")
            
            # Check that the WebSocket.send_json method was called with account data
            websocket.send_json.assert_called_once()
            
            # Check that the exchange.get_account_info method was called for each exchange
            mock_monitor.exchanges["binance"].get_account_info.assert_called_once()
            mock_monitor.exchanges["hyperliquid"].get_account_info.assert_called_once()


@pytest.mark.asyncio
async def test_risk_metrics_websocket():
    """Test the risk_metrics WebSocket endpoint."""
    # Create a mock WebSocket
    websocket = AsyncMock(spec=WebSocket)
    websocket.receive_text = AsyncMock(side_effect=["subscribe", Exception("Test exception")])
    
    # Create a mock RiskMonitor
    mock_monitor = AsyncMock(spec=RiskMonitor)
    mock_monitor.is_monitoring = True
    mock_monitor.calculate_risk_metrics = AsyncMock(return_value={
        "total_exposure": 100000.0,
        "max_drawdown": 10.0,
        "exchange_metrics": {},
        "symbol_metrics": {}
    })
    
    # Patch the ConnectionManager.connect method
    with patch('api.websocket.manager.connect', new_callable=AsyncMock) as mock_connect:
        with patch('api.websocket.manager.disconnect') as mock_disconnect:
            # Call the risk_metrics_websocket function
            with pytest.raises(Exception, match="Test exception"):
                await risk_metrics_websocket(websocket, mock_monitor)
            
            # Check that the ConnectionManager.connect method was called
            mock_connect.assert_called_once_with(websocket, "risk_metrics")
            
            # Check that the ConnectionManager.disconnect method was called
            mock_disconnect.assert_called_once_with(websocket, "risk_metrics")
            
            # Check that the WebSocket.send_json method was called with risk metrics data
            websocket.send_json.assert_called_once()
            
            # Check that the RiskMonitor.calculate_risk_metrics method was called
            mock_monitor.calculate_risk_metrics.assert_called_once()


@pytest.mark.asyncio
async def test_alerts_websocket():
    """Test the alerts WebSocket endpoint."""
    # Create a mock WebSocket
    websocket = AsyncMock(spec=WebSocket)
    websocket.receive_text = AsyncMock(side_effect=["subscribe", Exception("Test exception")])
    
    # Create a mock RiskMonitor
    mock_monitor = AsyncMock(spec=RiskMonitor)
    mock_monitor.is_monitoring = True
    
    # Patch the ConnectionManager.connect method
    with patch('api.websocket.manager.connect', new_callable=AsyncMock) as mock_connect:
        with patch('api.websocket.manager.disconnect') as mock_disconnect:
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                # Call the alerts_websocket function
                with pytest.raises(Exception, match="Test exception"):
                    await alerts_websocket(websocket, mock_monitor)
                
                # Check that the ConnectionManager.connect method was called
                mock_connect.assert_called_once_with(websocket, "alerts")
                
                # Check that the ConnectionManager.disconnect method was called
                mock_disconnect.assert_called_once_with(websocket, "alerts")
                
                # Check that asyncio.sleep was called (for keeping the connection active)
                mock_sleep.assert_called_once_with(30)


@pytest.mark.asyncio
async def test_broadcast_alert():
    """Test the broadcast_alert function."""
    # Create a test alert
    alert_data = {
        "type": "circuit_breaker",
        "condition_name": "max_drawdown_test",
        "description": "Test alert",
        "exchange": "binance",
        "symbol": "BTCUSDT",
        "triggered_at": 1234567890,
        "context": {"test": "data"},
        "action_result": "Test action result"
    }
    
    # Patch the ConnectionManager.broadcast method
    with patch('api.websocket.manager.broadcast', new_callable=AsyncMock) as mock_broadcast:
        # Call the broadcast_alert function
        await broadcast_alert(alert_data)
        
        # Check that the ConnectionManager.broadcast method was called with the alert data
        mock_broadcast.assert_called_once_with("alerts", alert_data)


@pytest.mark.asyncio
async def test_broadcast_position_update():
    """Test the broadcast_position_update function."""
    # Create test position data
    position_data = {
        "total_position_value": 100000.0,
        "total_unrealized_pnl": 5000.0,
        "exchanges": {},
        "positions_by_symbol": {}
    }
    
    # Patch the ConnectionManager.broadcast method
    with patch('api.websocket.manager.broadcast', new_callable=AsyncMock) as mock_broadcast:
        # Call the broadcast_position_update function
        await broadcast_position_update(position_data)
        
        # Check that the ConnectionManager.broadcast method was called with the position data
        mock_broadcast.assert_called_once_with("positions", position_data)


@pytest.mark.asyncio
async def test_broadcast_account_update():
    """Test the broadcast_account_update function."""
    # Create test account data
    account_data = {
        "accounts": {
            "binance": {
                "balance": 10000.0,
                "equity": 10500.0
            },
            "hyperliquid": {
                "balance": 5000.0,
                "equity": 5200.0
            }
        }
    }
    
    # Patch the ConnectionManager.broadcast method
    with patch('api.websocket.manager.broadcast', new_callable=AsyncMock) as mock_broadcast:
        # Call the broadcast_account_update function
        await broadcast_account_update(account_data)
        
        # Check that the ConnectionManager.broadcast method was called with the account data
        mock_broadcast.assert_called_once_with("accounts", account_data)


@pytest.mark.asyncio
async def test_broadcast_risk_metrics_update():
    """Test the broadcast_risk_metrics_update function."""
    # Create test risk metrics data
    metrics_data = {
        "risk_metrics": {
            "total_exposure": 100000.0,
            "max_drawdown": 10.0,
            "exchange_metrics": {},
            "symbol_metrics": {}
        }
    }
    
    # Patch the ConnectionManager.broadcast method
    with patch('api.websocket.manager.broadcast', new_callable=AsyncMock) as mock_broadcast:
        # Call the broadcast_risk_metrics_update function
        await broadcast_risk_metrics_update(metrics_data)
        
        # Check that the ConnectionManager.broadcast method was called with the risk metrics data
        mock_broadcast.assert_called_once_with("risk_metrics", metrics_data) 