from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Optional

from etrms.backend.models.user import User
from etrms.backend.services.user_service import UserService
from etrms.backend.repositories.user_repository import UserRepository
from etrms.backend.services.backtest_service import BacktestService
from etrms.backend.repositories.backtest_repository import BacktestRepository
from etrms.backend.exchange.factory import ExchangeClientFactory
from etrms.backend.services.market_analysis_service import MarketAnalysisService

# JWT settings
SECRET_KEY = "YOUR_SECRET_KEY_HERE"  # In production, use environment variable
ALGORITHM = "HS256"

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def get_user_repository():
    """Dependency to get the user repository"""
    return UserRepository()

def get_user_service():
    """Dependency to get the user service"""
    return UserService(get_user_repository())

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Dependency to get the current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Get the user from the database
    user_service = get_user_service()
    user = user_service.get_user_by_username(username)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Dependency to get the current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_user_from_token(token: str):
    """Get the current user from a token (for WebSocket authentication)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Get the user from the database
    user_service = get_user_service()
    user = user_service.get_user_by_username(username)
    if user is None:
        raise credentials_exception
    
    return user

def get_backtest_repository():
    """Get the backtest repository."""
    return BacktestRepository()

def get_backtest_service(repository: BacktestRepository = Depends(get_backtest_repository)):
    """Get the backtest service."""
    return BacktestService(repository)

def get_exchange_factory():
    """Get the exchange client factory."""
    return ExchangeClientFactory()

def get_market_analysis_service(exchange_factory: ExchangeClientFactory = Depends(get_exchange_factory)):
    """
    Get the market analysis service.
    
    Args:
        exchange_factory: Exchange client factory
        
    Returns:
        MarketAnalysisService instance
    """
    # Create a singleton instance if it doesn't exist
    if not hasattr(get_market_analysis_service, "instance"):
        get_market_analysis_service.instance = MarketAnalysisService(
            exchange_factory=exchange_factory,
            update_interval=60,  # 1 minute
            lookback_periods=100,
            symbols=["BTCUSDT", "ETHUSDT"],  # Default symbols to analyze
            exchanges=["binance", "hyperliquid"]  # Default exchanges to analyze
        )
    
    return get_market_analysis_service.instance

def get_ai_assistant_service(exchange_factory: ExchangeClientFactory = Depends(get_exchange_factory)):
    """
    Get or create a singleton instance of the AIAssistantService.
    
    Args:
        exchange_factory: Factory for creating exchange clients
        
    Returns:
        AIAssistantService instance
    """
    from ..services.ai_assistant_service import AIAssistantService
    
    # Use a global variable to store the singleton instance
    if not hasattr(get_ai_assistant_service, "instance"):
        get_ai_assistant_service.instance = AIAssistantService(
            exchange_factory=exchange_factory,
            update_interval=60,  # 1 minute
            lookback_periods=100,
            min_setup_quality=0.6,
            default_risk_percent=1.0,
            use_market_regime=True
        )
    
    return get_ai_assistant_service.instance 