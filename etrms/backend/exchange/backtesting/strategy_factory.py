"""
Enhanced Trading Risk Management System Backtesting Strategy Factory

This module provides a factory for creating backtesting strategies and some
pre-defined strategies for use with the backtesting engine.
"""
import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Any, Optional, Callable, Coroutine, Union

import numpy as np

from exchange.backtesting.backtesting_client import BacktestingClient
from risk.monitor import RiskMonitor
from utils.logger import get_logger, log_event


# Simple Moving Average strategy
async def sma_crossover_strategy(
    client: BacktestingClient,
    risk_monitor: RiskMonitor,
    current_time: datetime,
    symbol: str = "BTCUSDT",
    fast_period: int = 20,
    slow_period: int = 50,
    risk_per_trade: float = 0.01,
    lookback_periods: int = 100
) -> None:
    """
    Simple Moving Average (SMA) crossover strategy.
    
    This strategy:
    1. Calculates fast and slow SMAs
    2. Enters a long position when fast SMA crosses above slow SMA
    3. Exits the position when fast SMA crosses below slow SMA
    
    Args:
        client: Backtesting client
        risk_monitor: Risk monitor
        current_time: Current simulation time
        symbol: Trading symbol
        fast_period: Fast SMA period
        slow_period: Slow SMA period
        risk_per_trade: Risk per trade as a percentage of account
        lookback_periods: Number of periods to look back for SMA calculation
    """
    # Get current position
    position = await client.get_position(symbol)
    has_position = position is not None
    
    # Get account info
    account = await client.get_account_info()
    
    # Calculate total equity
    total_equity = account["total_equity"]
    
    # Calculate position size based on risk
    position_size_usd = total_equity * risk_per_trade
    
    # Get historical price data
    now_ms = int(current_time.timestamp() * 1000)
    klines = await client.get_klines(
        symbol=symbol,
        interval="1h",  # Assuming 1-hour candles
        limit=lookback_periods,
        end_time=now_ms
    )
    
    # Extract close prices
    close_prices = [candle["close"] for candle in klines]
    
    # Check if we have enough data
    if len(close_prices) < slow_period:
        return
    
    # Calculate SMAs
    fast_sma = np.mean(close_prices[-fast_period:])
    slow_sma = np.mean(close_prices[-slow_period:])
    
    # Calculate previous SMAs
    if len(close_prices) > fast_period + 1 and len(close_prices) > slow_period + 1:
        prev_fast_sma = np.mean(close_prices[-(fast_period+1):-1])
        prev_slow_sma = np.mean(close_prices[-(slow_period+1):-1])
    else:
        # Not enough data for previous SMAs
        return
    
    # Get current price
    current_price = close_prices[-1]
    
    # Calculate quantity based on position size and current price
    quantity = Decimal(str(position_size_usd / current_price))
    
    # Check for crossover conditions
    fast_above_slow = fast_sma > slow_sma
    prev_fast_above_slow = prev_fast_sma > prev_slow_sma
    
    # SMA crossover strategy logic
    if fast_above_slow and not prev_fast_above_slow:
        # Bullish crossover: fast SMA crosses above slow SMA
        if not has_position:
            # Enter long position
            await client.open_position(
                symbol=symbol,
                side="buy",
                quantity=quantity,
                leverage=1,  # No leverage for this simple strategy
                order_type="MARKET"
            )
    elif not fast_above_slow and prev_fast_above_slow:
        # Bearish crossover: fast SMA crosses below slow SMA
        if has_position and position["side"] == "buy":
            # Close long position
            await client.close_position(
                symbol=symbol,
                order_type="MARKET"
            )


# RSI mean-reversion strategy
async def rsi_mean_reversion_strategy(
    client: BacktestingClient,
    risk_monitor: RiskMonitor,
    current_time: datetime,
    symbol: str = "BTCUSDT",
    rsi_period: int = 14,
    oversold_threshold: int = 30,
    overbought_threshold: int = 70,
    risk_per_trade: float = 0.01,
    lookback_periods: int = 100
) -> None:
    """
    RSI mean-reversion strategy.
    
    This strategy:
    1. Calculates RSI indicator
    2. Enters a long position when RSI is below oversold threshold
    3. Enters a short position when RSI is above overbought threshold
    4. Exits when RSI returns to neutral zone (40-60)
    
    Args:
        client: Backtesting client
        risk_monitor: Risk monitor
        current_time: Current simulation time
        symbol: Trading symbol
        rsi_period: RSI calculation period
        oversold_threshold: RSI threshold for oversold condition
        overbought_threshold: RSI threshold for overbought condition
        risk_per_trade: Risk per trade as a percentage of account
        lookback_periods: Number of periods to look back for RSI calculation
    """
    # Get current position
    position = await client.get_position(symbol)
    has_position = position is not None
    
    # Get account info
    account = await client.get_account_info()
    
    # Calculate total equity
    total_equity = account["total_equity"]
    
    # Calculate position size based on risk
    position_size_usd = total_equity * risk_per_trade
    
    # Get historical price data
    now_ms = int(current_time.timestamp() * 1000)
    klines = await client.get_klines(
        symbol=symbol,
        interval="1h",  # Assuming 1-hour candles
        limit=lookback_periods,
        end_time=now_ms
    )
    
    # Extract close prices
    close_prices = np.array([float(candle["close"]) for candle in klines])
    
    # Check if we have enough data
    if len(close_prices) < rsi_period + 1:
        return
    
    # Calculate price changes
    price_diffs = np.diff(close_prices)
    
    # Calculate RSI
    gains = np.where(price_diffs > 0, price_diffs, 0)
    losses = np.where(price_diffs < 0, -price_diffs, 0)
    
    avg_gain = np.mean(gains[-rsi_period:])
    avg_loss = np.mean(losses[-rsi_period:])
    
    if avg_loss == 0:
        rs = 100.0
    else:
        rs = avg_gain / avg_loss
    
    rsi = 100 - (100 / (1 + rs))
    
    # Get current price
    current_price = close_prices[-1]
    
    # Calculate quantity based on position size and current price
    quantity = Decimal(str(position_size_usd / current_price))
    
    # RSI mean-reversion strategy logic
    if not has_position:
        if rsi <= oversold_threshold:
            # Enter long position on oversold condition
            await client.open_position(
                symbol=symbol,
                side="buy",
                quantity=quantity,
                leverage=1,  # No leverage for this simple strategy
                order_type="MARKET"
            )
        elif rsi >= overbought_threshold:
            # Enter short position on overbought condition
            await client.open_position(
                symbol=symbol,
                side="sell",
                quantity=quantity,
                leverage=1,  # No leverage for this simple strategy
                order_type="MARKET"
            )
    else:
        # Check exit conditions
        if position["side"] == "buy" and rsi >= 50:
            # Close long position when RSI returns to neutral
            await client.close_position(symbol=symbol, order_type="MARKET")
        elif position["side"] == "sell" and rsi <= 50:
            # Close short position when RSI returns to neutral
            await client.close_position(symbol=symbol, order_type="MARKET")


# Simple stop-loss implementation for demonstration
async def stop_loss_handler(
    client: BacktestingClient,
    risk_monitor: RiskMonitor,
    current_time: datetime,
    symbol: str,
    stop_loss_percent: float = 0.02  # 2% stop loss
) -> bool:
    """
    Implements a basic stop-loss mechanism.
    
    Args:
        client: Backtesting client
        risk_monitor: Risk monitor
        current_time: Current simulation time
        symbol: Trading symbol
        stop_loss_percent: Stop loss percentage
        
    Returns:
        True if stop loss was triggered, False otherwise
    """
    position = await client.get_position(symbol)
    if not position:
        return False
    
    current_price = client.get_current_price(symbol)
    if current_price is None:
        return False
    
    entry_price = position["entry_price"]
    side = position["side"]
    
    # Calculate stop loss price
    if side == "buy":
        stop_price = entry_price * (1 - stop_loss_percent)
        if current_price <= stop_price:
            # Stop loss triggered for long position
            await client.close_position(symbol=symbol, order_type="MARKET")
            return True
    else:
        stop_price = entry_price * (1 + stop_loss_percent)
        if current_price >= stop_price:
            # Stop loss triggered for short position
            await client.close_position(symbol=symbol, order_type="MARKET")
            return True
    
    return False


class StrategyFactory:
    """
    Factory for creating and configuring backtesting strategies.
    """
    
    @staticmethod
    def get_strategy(
        strategy_name: str, 
        **kwargs
    ) -> Callable[[BacktestingClient, RiskMonitor, datetime], Coroutine[Any, Any, None]]:
        """
        Get a strategy by name with the specified parameters.
        
        Args:
            strategy_name: Name of the strategy to get.
            **kwargs: Additional parameters to pass to the strategy.
            
        Returns:
            A coroutine function implementing the strategy.
            
        Raises:
            ValueError: If the strategy name is not recognized.
        """
        if strategy_name.lower() == "sma_crossover":
            symbol = kwargs.get("symbol", "BTCUSDT")
            fast_period = kwargs.get("fast_period", 20)
            slow_period = kwargs.get("slow_period", 50)
            risk_per_trade = kwargs.get("risk_per_trade", 0.01)
            lookback_periods = kwargs.get("lookback_periods", 100)
            use_stop_loss = kwargs.get("use_stop_loss", True)
            stop_loss_percent = kwargs.get("stop_loss_percent", 0.02)
            
            async def _strategy(
                client: BacktestingClient,
                risk_monitor: RiskMonitor,
                current_time: datetime
            ) -> None:
                # Apply SMA crossover strategy
                await sma_crossover_strategy(
                    client=client,
                    risk_monitor=risk_monitor,
                    current_time=current_time,
                    symbol=symbol,
                    fast_period=fast_period,
                    slow_period=slow_period,
                    risk_per_trade=risk_per_trade,
                    lookback_periods=lookback_periods
                )
                
                # Apply stop loss if enabled
                if use_stop_loss:
                    await stop_loss_handler(
                        client=client,
                        risk_monitor=risk_monitor,
                        current_time=current_time,
                        symbol=symbol,
                        stop_loss_percent=stop_loss_percent
                    )
            
            return _strategy
            
        elif strategy_name.lower() == "rsi_mean_reversion":
            symbol = kwargs.get("symbol", "BTCUSDT")
            rsi_period = kwargs.get("rsi_period", 14)
            oversold_threshold = kwargs.get("oversold_threshold", 30)
            overbought_threshold = kwargs.get("overbought_threshold", 70)
            risk_per_trade = kwargs.get("risk_per_trade", 0.01)
            lookback_periods = kwargs.get("lookback_periods", 100)
            use_stop_loss = kwargs.get("use_stop_loss", True)
            stop_loss_percent = kwargs.get("stop_loss_percent", 0.02)
            
            async def _strategy(
                client: BacktestingClient,
                risk_monitor: RiskMonitor,
                current_time: datetime
            ) -> None:
                # Apply RSI mean-reversion strategy
                await rsi_mean_reversion_strategy(
                    client=client,
                    risk_monitor=risk_monitor,
                    current_time=current_time,
                    symbol=symbol,
                    rsi_period=rsi_period,
                    oversold_threshold=oversold_threshold,
                    overbought_threshold=overbought_threshold,
                    risk_per_trade=risk_per_trade,
                    lookback_periods=lookback_periods
                )
                
                # Apply stop loss if enabled
                if use_stop_loss:
                    await stop_loss_handler(
                        client=client,
                        risk_monitor=risk_monitor,
                        current_time=current_time,
                        symbol=symbol,
                        stop_loss_percent=stop_loss_percent
                    )
            
            return _strategy
            
        else:
            raise ValueError(f"Unknown strategy: {strategy_name}")
    
    @staticmethod
    def get_available_strategies() -> List[Dict[str, Any]]:
        """
        Get a list of available strategies with their descriptions.
        
        Returns:
            List of dictionaries containing strategy information.
        """
        return [
            {
                "name": "sma_crossover",
                "description": "Simple Moving Average Crossover Strategy",
                "parameters": {
                    "symbol": {"type": "string", "default": "BTCUSDT", "description": "Trading symbol"},
                    "fast_period": {"type": "integer", "default": 20, "description": "Fast SMA period"},
                    "slow_period": {"type": "integer", "default": 50, "description": "Slow SMA period"},
                    "risk_per_trade": {"type": "float", "default": 0.01, "description": "Risk per trade (% of equity)"},
                    "lookback_periods": {"type": "integer", "default": 100, "description": "Number of candles to look back"},
                    "use_stop_loss": {"type": "boolean", "default": True, "description": "Enable stop loss"},
                    "stop_loss_percent": {"type": "float", "default": 0.02, "description": "Stop loss percentage"}
                }
            },
            {
                "name": "rsi_mean_reversion",
                "description": "RSI Mean-Reversion Strategy",
                "parameters": {
                    "symbol": {"type": "string", "default": "BTCUSDT", "description": "Trading symbol"},
                    "rsi_period": {"type": "integer", "default": 14, "description": "RSI calculation period"},
                    "oversold_threshold": {"type": "integer", "default": 30, "description": "RSI oversold threshold"},
                    "overbought_threshold": {"type": "integer", "default": 70, "description": "RSI overbought threshold"},
                    "risk_per_trade": {"type": "float", "default": 0.01, "description": "Risk per trade (% of equity)"},
                    "lookback_periods": {"type": "integer", "default": 100, "description": "Number of candles to look back"},
                    "use_stop_loss": {"type": "boolean", "default": True, "description": "Enable stop loss"},
                    "stop_loss_percent": {"type": "float", "default": 0.02, "description": "Stop loss percentage"}
                }
            }
        ] 