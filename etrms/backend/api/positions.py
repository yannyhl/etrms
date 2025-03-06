"""
Enhanced Trading Risk Management System Positions API

This module provides endpoints for retrieving position information from exchanges.
"""
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path

from config.settings import settings
from exchange import ExchangeClientFactory
from risk import RiskMonitor
from api.accounts import get_risk_monitor

# Create a router instance
router = APIRouter()


@router.get("/", summary="Get position summary across all exchanges")
async def get_position_summary(
    monitor: RiskMonitor = Depends(get_risk_monitor)
) -> Dict[str, Any]:
    """
    Get a summary of positions across all monitored exchanges.
    
    Returns:
        Dict containing position summary information.
    """
    # Check if monitoring is active
    if not monitor.is_monitoring:
        return {
            "status": "error",
            "message": "Position monitoring is not active. Start monitoring first.",
            "data": None
        }
    
    try:
        # Get position summary
        position_summary = await monitor.get_position_summary()
        
        return {
            "status": "success",
            "message": "Position summary retrieved successfully",
            "data": position_summary
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error retrieving position summary: {str(e)}",
            "data": None
        }


@router.get("/by-symbol", summary="Get positions grouped by symbol")
async def get_positions_by_symbol(
    monitor: RiskMonitor = Depends(get_risk_monitor)
) -> Dict[str, Any]:
    """
    Get positions grouped by symbol across all exchanges.
    
    Returns:
        Dict containing positions grouped by symbol.
    """
    # Check if monitoring is active
    if not monitor.is_monitoring:
        return {
            "status": "error",
            "message": "Position monitoring is not active. Start monitoring first.",
            "data": None
        }
    
    try:
        # Get position summary
        position_summary = await monitor.get_position_summary()
        
        # Return positions grouped by symbol
        return {
            "status": "success",
            "message": "Positions by symbol retrieved successfully",
            "data": position_summary["positions_by_symbol"]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error retrieving positions by symbol: {str(e)}",
            "data": None
        }


@router.get("/by-exchange", summary="Get positions grouped by exchange")
async def get_positions_by_exchange(
    monitor: RiskMonitor = Depends(get_risk_monitor)
) -> Dict[str, Any]:
    """
    Get positions grouped by exchange.
    
    Returns:
        Dict containing positions grouped by exchange.
    """
    # Check if monitoring is active
    if not monitor.is_monitoring:
        return {
            "status": "error",
            "message": "Position monitoring is not active. Start monitoring first.",
            "data": None
        }
    
    try:
        # Get position summary
        position_summary = await monitor.get_position_summary()
        
        # Extract exchange positions
        exchange_positions = {}
        for exchange_name, exchange_data in position_summary["exchanges"].items():
            exchange_positions[exchange_name] = exchange_data["positions"]
        
        return {
            "status": "success",
            "message": "Positions by exchange retrieved successfully",
            "data": exchange_positions
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error retrieving positions by exchange: {str(e)}",
            "data": None
        }


@router.get("/{exchange}", summary="Get positions for a specific exchange")
async def get_exchange_positions(
    exchange: str = Path(..., description="Exchange name (e.g., 'binance', 'hyperliquid')"),
    monitor: RiskMonitor = Depends(get_risk_monitor)
) -> Dict[str, Any]:
    """
    Get positions for a specific exchange.
    
    Args:
        exchange: The name of the exchange.
        
    Returns:
        Dict containing positions for the specified exchange.
    """
    # Check if monitoring is active
    if not monitor.is_monitoring:
        return {
            "status": "error",
            "message": "Position monitoring is not active. Start monitoring first.",
            "data": None
        }
    
    # Check if the exchange is being monitored
    if exchange not in monitor.exchanges:
        return {
            "status": "error",
            "message": f"Exchange {exchange} is not being monitored.",
            "data": None
        }
    
    try:
        # Get positions for the exchange
        if exchange in monitor.positions:
            return {
                "status": "success",
                "message": f"Positions for exchange {exchange} retrieved successfully",
                "data": monitor.positions[exchange]
            }
        else:
            return {
                "status": "success",
                "message": f"No positions found for exchange {exchange}",
                "data": []
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error retrieving positions for exchange {exchange}: {str(e)}",
            "data": None
        }


@router.get("/{exchange}/{symbol}", summary="Get a specific position")
async def get_specific_position(
    exchange: str = Path(..., description="Exchange name (e.g., 'binance', 'hyperliquid')"),
    symbol: str = Path(..., description="Symbol (e.g., 'BTCUSDT')"),
    monitor: RiskMonitor = Depends(get_risk_monitor)
) -> Dict[str, Any]:
    """
    Get a specific position by exchange and symbol.
    
    Args:
        exchange: The name of the exchange.
        symbol: The symbol.
        
    Returns:
        Dict containing position information.
    """
    # Check if monitoring is active
    if not monitor.is_monitoring:
        return {
            "status": "error",
            "message": "Position monitoring is not active. Start monitoring first.",
            "data": None
        }
    
    # Check if the exchange is being monitored
    if exchange not in monitor.exchanges:
        return {
            "status": "error",
            "message": f"Exchange {exchange} is not being monitored.",
            "data": None
        }
    
    try:
        # Get exchange positions
        if exchange not in monitor.positions:
            return {
                "status": "error",
                "message": f"No positions found for exchange {exchange}.",
                "data": None
            }
        
        # Find the position for the symbol
        for position in monitor.positions[exchange]:
            if position.get("symbol").upper() == symbol.upper():
                return {
                    "status": "success",
                    "message": f"Position for {symbol} on {exchange} retrieved successfully",
                    "data": position
                }
        
        # Position not found
        return {
            "status": "error",
            "message": f"No position found for symbol {symbol} on exchange {exchange}.",
            "data": None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error retrieving position for {symbol} on {exchange}: {str(e)}",
            "data": None
        } 