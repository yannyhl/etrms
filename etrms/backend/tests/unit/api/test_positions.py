"""
Unit tests for the positions API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from api.positions import get_position_summary, get_positions_by_symbol, get_positions_by_exchange
from risk import RiskMonitor


@pytest.mark.asyncio
async def test_get_position_summary_success(mock_risk_monitor: RiskMonitor):
    """Test get_position_summary endpoint with active monitoring."""
    # Call the function directly
    response = await get_position_summary(monitor=mock_risk_monitor)
    
    # Check the response
    assert response["status"] == "success"
    assert "message" in response
    assert "data" in response
    
    # Check data structure
    data = response["data"]
    assert "total_position_value" in data
    assert "total_unrealized_pnl" in data
    assert "exchanges" in data
    assert "positions_by_symbol" in data
    
    # Check exchanges
    assert "binance" in data["exchanges"]
    assert "hyperliquid" in data["exchanges"]
    
    # Check position data
    assert "BTCUSDT" in data["positions_by_symbol"]
    assert "ETHUSDT" in data["positions_by_symbol"]


@pytest.mark.asyncio
async def test_get_position_summary_not_monitoring(mock_risk_monitor: RiskMonitor):
    """Test get_position_summary endpoint when monitoring is not active."""
    # Set monitoring to inactive
    mock_risk_monitor.is_monitoring = False
    
    # Call the function directly
    response = await get_position_summary(monitor=mock_risk_monitor)
    
    # Check the response
    assert response["status"] == "error"
    assert "Position monitoring is not active" in response["message"]
    assert response["data"] is None
    
    # Reset monitoring status
    mock_risk_monitor.is_monitoring = True


@pytest.mark.asyncio
async def test_get_positions_by_symbol_success(mock_risk_monitor: RiskMonitor):
    """Test get_positions_by_symbol endpoint with active monitoring."""
    # Call the function directly
    response = await get_positions_by_symbol(monitor=mock_risk_monitor)
    
    # Check the response
    assert response["status"] == "success"
    assert "message" in response
    assert "data" in response
    
    # Check data structure
    data = response["data"]
    assert "BTCUSDT" in data
    assert "ETHUSDT" in data
    
    # Check position data for BTCUSDT
    btc_data = data["BTCUSDT"]
    assert "total_value" in btc_data
    assert "total_unrealized_pnl" in btc_data
    assert "exchanges" in btc_data
    assert "binance" in btc_data["exchanges"]


@pytest.mark.asyncio
async def test_get_positions_by_symbol_not_monitoring(mock_risk_monitor: RiskMonitor):
    """Test get_positions_by_symbol endpoint when monitoring is not active."""
    # Set monitoring to inactive
    mock_risk_monitor.is_monitoring = False
    
    # Call the function directly
    response = await get_positions_by_symbol(monitor=mock_risk_monitor)
    
    # Check the response
    assert response["status"] == "error"
    assert "Position monitoring is not active" in response["message"]
    assert response["data"] is None
    
    # Reset monitoring status
    mock_risk_monitor.is_monitoring = True


@pytest.mark.asyncio
async def test_get_positions_by_exchange_success(mock_risk_monitor: RiskMonitor):
    """Test get_positions_by_exchange endpoint with active monitoring."""
    # Call the function directly
    response = await get_positions_by_exchange(monitor=mock_risk_monitor)
    
    # Check the response
    assert response["status"] == "success"
    assert "message" in response
    assert "data" in response
    
    # Check data structure
    data = response["data"]
    assert "binance" in data
    assert "hyperliquid" in data
    
    # Check position data for binance
    binance_data = data["binance"]
    assert len(binance_data) == 2  # Two positions: BTCUSDT and ETHUSDT
    assert binance_data[0]["symbol"] == "BTCUSDT"
    assert binance_data[1]["symbol"] == "ETHUSDT"


@pytest.mark.asyncio
async def test_get_positions_by_exchange_not_monitoring(mock_risk_monitor: RiskMonitor):
    """Test get_positions_by_exchange endpoint when monitoring is not active."""
    # Set monitoring to inactive
    mock_risk_monitor.is_monitoring = False
    
    # Call the function directly
    response = await get_positions_by_exchange(monitor=mock_risk_monitor)
    
    # Check the response
    assert response["status"] == "error"
    assert "Position monitoring is not active" in response["message"]
    assert response["data"] is None
    
    # Reset monitoring status
    mock_risk_monitor.is_monitoring = True


def test_positions_api_endpoints(client: TestClient, mock_risk_monitor: RiskMonitor):
    """Test positions API endpoints using the TestClient."""
    # Test get position summary
    response = client.get("/api/v1/positions/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # Test get positions by symbol
    response = client.get("/api/v1/positions/by-symbol")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # Test get positions by exchange
    response = client.get("/api/v1/positions/by-exchange")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # Test get exchange positions
    response = client.get("/api/v1/positions/binance")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # Test get specific position
    response = client.get("/api/v1/positions/binance/BTCUSDT")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


def test_get_nonexistent_exchange(client: TestClient, mock_risk_monitor: RiskMonitor):
    """Test getting positions for a non-existent exchange."""
    response = client.get("/api/v1/positions/nonexistent_exchange")
    assert response.status_code == 200  # Note: We're returning 200 with error status now
    data = response.json()
    assert data["status"] == "error"
    assert "not being monitored" in data["message"]


def test_get_nonexistent_position(client: TestClient, mock_risk_monitor: RiskMonitor):
    """Test getting a non-existent position."""
    response = client.get("/api/v1/positions/binance/NONEXISTENT")
    assert response.status_code == 200  # Note: We're returning 200 with error status now
    data = response.json()
    assert data["status"] == "error"
    assert "No position found" in data["message"] 