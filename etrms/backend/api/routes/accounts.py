from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any

from etrms.backend.models.user import User
from etrms.backend.api.dependencies import get_current_user
from etrms.backend.exchange.factory import ExchangeClientFactory

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.get("/exchanges")
async def get_exchanges():
    """
    Get a list of supported exchanges
    
    Returns:
        List of supported exchanges with their IDs and names
    """
    factory = ExchangeClientFactory()
    exchanges = factory.get_supported_exchanges()
    
    return [
        {"id": exchange, "name": exchange.capitalize()} 
        for exchange in exchanges
    ]

@router.get("/summary")
async def get_account_summary(current_user: User = Depends(get_current_user)):
    """
    Get a summary of the user's account information across all exchanges
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        Account summary including total balance, daily PnL, and positions
    """
    # This is a placeholder implementation
    # In a real implementation, we would fetch data from the exchanges
    
    # Mock data for demonstration
    return {
        "totalBalance": 10000.00,
        "dailyPnl": 250.75,
        "positions": [
            {
                "symbol": "BTCUSDT",
                "exchange": "binance",
                "side": "LONG",
                "size": 0.05,
                "entryPrice": 45000.00,
                "markPrice": 46000.00,
                "unrealizedPnl": 50.00,
                "leverage": 5
            },
            {
                "symbol": "ETHUSDT",
                "exchange": "binance",
                "side": "SHORT",
                "size": 0.5,
                "entryPrice": 3000.00,
                "markPrice": 2950.00,
                "unrealizedPnl": 25.00,
                "leverage": 3
            }
        ]
    }

@router.get("/api-keys")
async def get_api_keys(current_user: User = Depends(get_current_user)):
    """
    Get the user's API keys
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        List of API keys
    """
    # This is a placeholder implementation
    # In a real implementation, we would fetch API keys from the database
    
    # Mock data for demonstration
    return [
        {
            "id": "1",
            "exchange": "binance",
            "name": "Binance Main",
            "is_testnet": False,
            "created_at": "2023-01-01T00:00:00Z"
        },
        {
            "id": "2",
            "exchange": "hyperliquid",
            "name": "Hyperliquid Test",
            "is_testnet": True,
            "created_at": "2023-01-02T00:00:00Z"
        }
    ] 