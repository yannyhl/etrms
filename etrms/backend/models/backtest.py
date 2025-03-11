"""
Models for the backtesting module.
"""

from enum import Enum
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
from datetime import datetime

class TimeFrame(str, Enum):
    """Time frame for backtesting"""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"
    WEEK_1 = "1w"

class BacktestType(str, Enum):
    """Type of backtest"""
    STANDARD = "standard"
    MONTE_CARLO = "monte_carlo"
    WALK_FORWARD = "walk_forward"
    OPTIMIZATION = "optimization"

class CircuitBreakerConfig(BaseModel):
    """Circuit breaker configuration for backtesting"""
    type: str
    threshold: float
    action: str
    enabled: bool = True
    symbols: Optional[List[str]] = None
    exchanges: Optional[List[str]] = None
    description: Optional[str] = None

class BacktestConfig(BaseModel):
    """Configuration for a backtest"""
    name: str
    description: Optional[str] = None
    type: BacktestType = BacktestType.STANDARD
    start_date: datetime
    end_date: datetime
    exchanges: List[str]
    symbols: List[str]
    timeframe: TimeFrame = TimeFrame.HOUR_1
    initial_capital: float = 10000.0
    circuit_breakers: List[CircuitBreakerConfig] = []
    parameters: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class BacktestStatus(str, Enum):
    """Status of a backtest"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BacktestResult(BaseModel):
    """Result of a backtest"""
    id: str
    config_id: str
    status: BacktestStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metrics: Optional[Dict[str, Any]] = None
    trades: Optional[List[Dict[str, Any]]] = None
    circuit_breaker_events: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

class BacktestCreate(BaseModel):
    """Model for creating a new backtest"""
    name: str
    description: Optional[str] = None
    type: BacktestType = BacktestType.STANDARD
    start_date: datetime
    end_date: datetime
    exchanges: List[str]
    symbols: List[str]
    timeframe: TimeFrame = TimeFrame.HOUR_1
    initial_capital: float = 10000.0
    circuit_breakers: List[CircuitBreakerConfig] = []
    parameters: Optional[Dict[str, Any]] = None

class BacktestUpdate(BaseModel):
    """Model for updating a backtest"""
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    exchanges: Optional[List[str]] = None
    symbols: Optional[List[str]] = None
    timeframe: Optional[TimeFrame] = None
    initial_capital: Optional[float] = None
    circuit_breakers: Optional[List[CircuitBreakerConfig]] = None
    parameters: Optional[Dict[str, Any]] = None

class BacktestResponse(BaseModel):
    """Response model for a backtest"""
    id: str
    name: str
    description: Optional[str] = None
    type: BacktestType
    start_date: datetime
    end_date: datetime
    exchanges: List[str]
    symbols: List[str]
    timeframe: TimeFrame
    initial_capital: float
    circuit_breakers: List[CircuitBreakerConfig]
    parameters: Optional[Dict[str, Any]] = None
    status: BacktestStatus
    created_at: datetime
    updated_at: datetime
    result: Optional[BacktestResult] = None

class BacktestListResponse(BaseModel):
    """Response model for a list of backtests"""
    backtests: List[BacktestResponse]
    total: int 