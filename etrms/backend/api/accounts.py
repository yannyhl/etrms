"""
Enhanced Trading Risk Management System Accounts API

This module provides endpoints for retrieving account information from exchanges.
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from config.settings import settings
from exchange import ExchangeClientFactory
from risk import RiskMonitor

# Create a router instance
router = APIRouter()

# Create a risk monitor instance
risk_monitor = RiskMonitor()


async def get_risk_monitor():
    """
    Dependency to get the risk monitor instance.
    
    Returns:
        The risk monitor instance.
    """
    return risk_monitor


@router.get("/", summary="Get account summary across all exchanges")
async def get_account_summary(
    monitor: RiskMonitor = Depends(get_risk_monitor)
) -> Dict[str, Any]:
    """
    Get a summary of account information across all monitored exchanges.
    
    Returns:
        Dict containing account summary information.
    """
    # Check if monitoring is active
    if not monitor.is_monitoring:
        raise HTTPException(
            status_code=400,
            detail="Position monitoring is not active. Start monitoring first."
        )
    
    # Get account summary
    return await monitor.get_account_summary()


@router.get("/{exchange}", summary="Get account information for a specific exchange")
async def get_exchange_account(
    exchange: str,
    monitor: RiskMonitor = Depends(get_risk_monitor)
) -> Dict[str, Any]:
    """
    Get account information for a specific exchange.
    
    Args:
        exchange: The name of the exchange (e.g., 'binance', 'hyperliquid').
        
    Returns:
        Dict containing account information.
    """
    # Check if monitoring is active
    if not monitor.is_monitoring:
        raise HTTPException(
            status_code=400,
            detail="Position monitoring is not active. Start monitoring first."
        )
    
    # Check if the exchange is being monitored
    if exchange not in monitor.exchanges:
        raise HTTPException(
            status_code=404,
            detail=f"Exchange {exchange} is not being monitored."
        )
    
    # Get the account summary
    account_summary = await monitor.get_account_summary()
    
    # Return the exchange-specific account info
    if exchange in account_summary["exchanges"]:
        return account_summary["exchanges"][exchange]
    else:
        raise HTTPException(
            status_code=404,
            detail=f"No account information available for exchange {exchange}."
        )


@router.post("/monitor/start", summary="Start account and position monitoring")
async def start_monitoring(
    exchanges: Optional[List[str]] = Query(None, description="List of exchanges to monitor"),
    symbols: Optional[List[str]] = Query(None, description="List of symbols to monitor"),
    monitor: RiskMonitor = Depends(get_risk_monitor)
) -> Dict[str, Any]:
    """
    Start monitoring accounts and positions for the specified exchanges.
    
    Args:
        exchanges: List of exchanges to monitor (None for all).
        symbols: List of symbols to monitor (None for all).
        
    Returns:
        Dict containing status information.
    """
    # If already monitoring, stop first
    if monitor.is_monitoring:
        await monitor.stop_monitoring()
    
    try:
        # If no exchanges specified, use default exchanges from settings
        if not exchanges:
            exchanges = settings.DEFAULT_EXCHANGES
        
        # Add the specified exchanges
        for exchange_name in exchanges:
            try:
                await monitor.add_exchange(exchange_name)
                
                # If specific symbols are requested, add them
                if symbols:
                    for symbol in symbols:
                        await monitor.add_symbol(symbol)
                
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Error adding exchange {exchange_name}: {str(e)}",
                    "exchanges_added": exchanges[:exchanges.index(exchange_name)]
                }
        
        # Start monitoring
        await monitor.start_monitoring()
        
        return {
            "status": "success",
            "message": "Started monitoring accounts and positions",
            "exchanges": exchanges,
            "symbols": symbols if symbols else "all",
            "refresh_interval": monitor.refresh_interval
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error starting monitoring: {str(e)}"
        }


@router.post("/monitor/stop", summary="Stop account and position monitoring")
async def stop_monitoring(
    monitor: RiskMonitor = Depends(get_risk_monitor)
) -> Dict[str, Any]:
    """
    Stop monitoring accounts and positions.
    
    Returns:
        Dict containing status information.
    """
    try:
        # Check if monitoring is active
        if not monitor.is_monitoring:
            return {
                "status": "warning",
                "message": "Monitoring is not active"
            }
        
        # Stop monitoring
        await monitor.stop_monitoring()
        
        return {
            "status": "success",
            "message": "Stopped monitoring accounts and positions"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error stopping monitoring: {str(e)}"
        }


@router.get("/monitor/status", summary="Get monitoring status")
async def get_monitoring_status(
    monitor: RiskMonitor = Depends(get_risk_monitor)
) -> Dict[str, Any]:
    """
    Get the current status of account and position monitoring.
    
    Returns:
        Dict containing monitoring status information.
    """
    # Get the current position risk metrics
    risk_metrics = None
    if monitor.is_monitoring:
        try:
            risk_metrics = await monitor.calculate_risk_metrics()
        except Exception as e:
            risk_metrics = {"error": str(e)}
    
    return {
        "status": "active" if monitor.is_monitoring else "inactive",
        "refresh_interval": monitor.refresh_interval,
        "exchanges_monitored": list(monitor.exchanges.keys()),
        "symbols_monitored": list(monitor.monitored_symbols) if monitor.monitored_symbols else "all",
        "position_count": sum(len(positions) for positions in monitor.positions.values()) if monitor.is_monitoring else 0,
        "last_metrics": risk_metrics
    } 