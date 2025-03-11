"""
Strategy recommendation module for the AI Trading Assistant.

This module provides functionality for suggesting optimal trading strategies
and parameters based on market conditions, detected setups, and historical performance.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from ..analysis.regime import MarketRegime
from ..utils.logger import get_logger
from .detection import SetupType, PatternType

logger = get_logger(__name__)


class StrategyType(str, Enum):
    """Enum representing different trading strategy types."""
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    PATTERN_BASED = "pattern_based"
    SCALPING = "scalping"
    SWING = "swing"
    POSITION = "position"
    CUSTOM = "custom"


class OrderType(str, Enum):
    """Enum representing different order types."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"
    OCO = "oco"  # One-Cancels-Other


class PositionSizing(str, Enum):
    """Enum representing different position sizing recommendations."""
    REDUCED = "reduced"
    NORMAL = "normal"
    INCREASED = "increased"
    MAXIMUM = "maximum"
    MINIMUM = "minimum"
    AVOID = "avoid"


class StrategyRecommender:
    """
    Recommends optimal trading strategies and parameters based on market conditions,
    detected setups, and historical performance.
    
    This class provides methods to generate trading recommendations, optimize strategy
    parameters, and suggest risk management settings based on current market conditions.
    """
    
    def __init__(
        self,
        default_risk_percent: float = 1.0,
        max_risk_percent: float = 2.0,
        min_risk_percent: float = 0.5,
        default_risk_reward: float = 2.0,
        use_market_regime: bool = True,
        use_volatility_adjustment: bool = True,
        use_liquidity_adjustment: bool = True,
        use_correlation_adjustment: bool = True
    ):
        """
        Initialize the StrategyRecommender.
        
        Args:
            default_risk_percent: Default risk percentage per trade
            max_risk_percent: Maximum risk percentage per trade
            min_risk_percent: Minimum risk percentage per trade
            default_risk_reward: Default risk-reward ratio
            use_market_regime: Whether to adjust recommendations based on market regime
            use_volatility_adjustment: Whether to adjust position sizing based on volatility
            use_liquidity_adjustment: Whether to adjust order types based on liquidity
            use_correlation_adjustment: Whether to adjust portfolio exposure based on correlations
        """
        self.default_risk_percent = default_risk_percent
        self.max_risk_percent = max_risk_percent
        self.min_risk_percent = min_risk_percent
        self.default_risk_reward = default_risk_reward
        self.use_market_regime = use_market_regime
        self.use_volatility_adjustment = use_volatility_adjustment
        self.use_liquidity_adjustment = use_liquidity_adjustment
        self.use_correlation_adjustment = use_correlation_adjustment
        self.logger = logger
        
        self.logger.info(
            f"Initialized StrategyRecommender with default_risk_percent={default_risk_percent}, "
            f"max_risk_percent={max_risk_percent}, min_risk_percent={min_risk_percent}, "
            f"default_risk_reward={default_risk_reward}"
        )
    
    def recommend_strategy(
        self,
        setup: Dict[str, Any],
        market_regime: Optional[MarketRegime] = None,
        volatility_regime: Optional[str] = None,
        liquidity_regime: Optional[str] = None,
        correlation_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Recommend a trading strategy based on the detected setup and market conditions.
        
        Args:
            setup: The detected trading setup
            market_regime: Current market regime if available
            volatility_regime: Current volatility regime if available
            liquidity_regime: Current liquidity regime if available
            correlation_data: Correlation data if available
            
        Returns:
            Dict with strategy recommendations
        """
        self.logger.info(f"Generating strategy recommendation for setup: {setup.get('type')}")
        
        setup_type = setup.get("type")
        setup_quality = setup.get("quality", 0.7)
        
        # Determine the base strategy type based on setup type
        strategy_type = self._map_setup_to_strategy(setup_type)
        
        # Determine position sizing based on setup quality and market conditions
        position_sizing = self._recommend_position_sizing(
            setup_quality, market_regime, volatility_regime, liquidity_regime
        )
        
        # Determine risk percentage based on position sizing
        risk_percent = self._calculate_risk_percent(position_sizing, setup_quality)
        
        # Determine order type based on liquidity and strategy
        order_type = self._recommend_order_type(strategy_type, liquidity_regime)
        
        # Determine entry, stop loss, and take profit levels
        entry_zone, stop_loss, take_profit = self._calculate_trade_levels(setup)
        
        # Calculate risk-reward ratio
        risk_reward = self._calculate_risk_reward(entry_zone, stop_loss, take_profit)
        
        # Generate notes and warnings
        notes = self._generate_recommendation_notes(
            setup, market_regime, volatility_regime, liquidity_regime, correlation_data
        )
        
        # Create the recommendation
        recommendation = {
            "strategy_type": strategy_type.value,
            "position_sizing": position_sizing.value,
            "risk_percent": risk_percent,
            "order_type": order_type.value,
            "entry_zone": entry_zone,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "risk_reward": risk_reward,
            "setup_quality": setup_quality,
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
            "setup_id": setup.get("id", ""),
            "exchange": setup.get("exchange", ""),
            "symbol": setup.get("symbol", ""),
            "timeframe": setup.get("timeframe", "")
        }
        
        self.logger.info(
            f"Generated recommendation: {strategy_type.value} strategy with "
            f"{position_sizing.value} position sizing"
        )
        
        return recommendation
    
    def _map_setup_to_strategy(self, setup_type: str) -> StrategyType:
        """
        Map a setup type to an appropriate strategy type.
        
        Args:
            setup_type: The type of trading setup
            
        Returns:
            Appropriate strategy type
        """
        # Define mapping from setup types to strategy types
        setup_to_strategy = {
            SetupType.TREND_CONTINUATION.value: StrategyType.TREND_FOLLOWING,
            SetupType.TREND_REVERSAL.value: StrategyType.MEAN_REVERSION,
            SetupType.BREAKOUT.value: StrategyType.BREAKOUT,
            SetupType.RANGE_BOUNCE.value: StrategyType.MEAN_REVERSION,
            SetupType.SUPPORT_RESISTANCE.value: StrategyType.MEAN_REVERSION,
            SetupType.DIVERGENCE.value: StrategyType.MEAN_REVERSION,
            SetupType.VOLATILITY_EXPANSION.value: StrategyType.VOLATILITY,
            SetupType.VOLATILITY_CONTRACTION.value: StrategyType.BREAKOUT,
            SetupType.PATTERN_BASED.value: StrategyType.PATTERN_BASED,
            SetupType.CUSTOM.value: StrategyType.CUSTOM
        }
        
        # Get the strategy type or default to CUSTOM
        return setup_to_strategy.get(setup_type, StrategyType.CUSTOM)
    
    def _recommend_position_sizing(
        self,
        setup_quality: float,
        market_regime: Optional[MarketRegime] = None,
        volatility_regime: Optional[str] = None,
        liquidity_regime: Optional[str] = None
    ) -> PositionSizing:
        """
        Recommend position sizing based on setup quality and market conditions.
        
        Args:
            setup_quality: Quality score of the setup (0.0-1.0)
            market_regime: Current market regime if available
            volatility_regime: Current volatility regime if available
            liquidity_regime: Current liquidity regime if available
            
        Returns:
            Position sizing recommendation
        """
        # Base position sizing on setup quality
        if setup_quality >= 0.8:
            base_sizing = PositionSizing.INCREASED
        elif setup_quality >= 0.6:
            base_sizing = PositionSizing.NORMAL
        elif setup_quality >= 0.4:
            base_sizing = PositionSizing.REDUCED
        else:
            base_sizing = PositionSizing.MINIMUM
        
        # Adjust based on market regime if available and enabled
        if self.use_market_regime and market_regime:
            if market_regime == MarketRegime.VOLATILE:
                # Reduce position size in volatile markets
                if base_sizing == PositionSizing.INCREASED:
                    base_sizing = PositionSizing.NORMAL
                elif base_sizing == PositionSizing.NORMAL:
                    base_sizing = PositionSizing.REDUCED
                elif base_sizing == PositionSizing.REDUCED:
                    base_sizing = PositionSizing.MINIMUM
            elif market_regime == MarketRegime.TRENDING:
                # Potentially increase position size in trending markets
                if setup_quality >= 0.7 and base_sizing != PositionSizing.MAXIMUM:
                    if base_sizing == PositionSizing.NORMAL:
                        base_sizing = PositionSizing.INCREASED
        
        # Adjust based on volatility regime if available and enabled
        if self.use_volatility_adjustment and volatility_regime:
            if volatility_regime == "high":
                # Reduce position size in high volatility
                if base_sizing == PositionSizing.INCREASED:
                    base_sizing = PositionSizing.NORMAL
                elif base_sizing == PositionSizing.NORMAL:
                    base_sizing = PositionSizing.REDUCED
            elif volatility_regime == "low" and setup_quality >= 0.7:
                # Potentially increase position size in low volatility
                if base_sizing == PositionSizing.NORMAL:
                    base_sizing = PositionSizing.INCREASED
        
        # Adjust based on liquidity regime if available and enabled
        if self.use_liquidity_adjustment and liquidity_regime:
            if liquidity_regime == "low":
                # Reduce position size in low liquidity
                if base_sizing == PositionSizing.INCREASED:
                    base_sizing = PositionSizing.NORMAL
                elif base_sizing == PositionSizing.NORMAL:
                    base_sizing = PositionSizing.REDUCED
                elif base_sizing == PositionSizing.REDUCED:
                    base_sizing = PositionSizing.MINIMUM
        
        return base_sizing
    
    def _calculate_risk_percent(
        self,
        position_sizing: PositionSizing,
        setup_quality: float
    ) -> float:
        """
        Calculate the recommended risk percentage based on position sizing.
        
        Args:
            position_sizing: Position sizing recommendation
            setup_quality: Quality score of the setup (0.0-1.0)
            
        Returns:
            Recommended risk percentage
        """
        # Base risk on position sizing
        if position_sizing == PositionSizing.MAXIMUM:
            risk_percent = self.max_risk_percent
        elif position_sizing == PositionSizing.INCREASED:
            risk_percent = min(
                self.default_risk_percent * 1.5,
                self.max_risk_percent
            )
        elif position_sizing == PositionSizing.NORMAL:
            risk_percent = self.default_risk_percent
        elif position_sizing == PositionSizing.REDUCED:
            risk_percent = self.default_risk_percent * 0.7
        elif position_sizing == PositionSizing.MINIMUM:
            risk_percent = self.min_risk_percent
        else:  # AVOID
            risk_percent = 0.0
        
        # Fine-tune based on setup quality
        quality_adjustment = (setup_quality - 0.5) * 0.5  # -0.25 to +0.25
        risk_percent = max(
            min(risk_percent + quality_adjustment, self.max_risk_percent),
            self.min_risk_percent
        )
        
        return round(risk_percent, 2)
    
    def _recommend_order_type(
        self,
        strategy_type: StrategyType,
        liquidity_regime: Optional[str] = None
    ) -> OrderType:
        """
        Recommend an order type based on strategy and liquidity.
        
        Args:
            strategy_type: The type of trading strategy
            liquidity_regime: Current liquidity regime if available
            
        Returns:
            Recommended order type
        """
        # Default order types based on strategy
        strategy_order_types = {
            StrategyType.TREND_FOLLOWING: OrderType.LIMIT,
            StrategyType.MEAN_REVERSION: OrderType.LIMIT,
            StrategyType.BREAKOUT: OrderType.STOP,
            StrategyType.MOMENTUM: OrderType.MARKET,
            StrategyType.VOLATILITY: OrderType.STOP,
            StrategyType.PATTERN_BASED: OrderType.LIMIT,
            StrategyType.SCALPING: OrderType.MARKET,
            StrategyType.SWING: OrderType.LIMIT,
            StrategyType.POSITION: OrderType.LIMIT,
            StrategyType.CUSTOM: OrderType.LIMIT
        }
        
        # Get default order type for the strategy
        order_type = strategy_order_types.get(strategy_type, OrderType.LIMIT)
        
        # Adjust based on liquidity if available and enabled
        if self.use_liquidity_adjustment and liquidity_regime:
            if liquidity_regime == "low":
                # In low liquidity, prefer limit orders to avoid slippage
                if order_type == OrderType.MARKET:
                    order_type = OrderType.LIMIT
                elif order_type == OrderType.STOP:
                    order_type = OrderType.STOP_LIMIT
            elif liquidity_regime == "high" and strategy_type in [
                StrategyType.BREAKOUT, StrategyType.MOMENTUM
            ]:
                # In high liquidity, market orders may be fine for breakouts and momentum
                order_type = OrderType.MARKET
        
        return order_type
    
    def _calculate_trade_levels(
        self,
        setup: Dict[str, Any]
    ) -> Tuple[Dict[str, float], float, float]:
        """
        Calculate entry zone, stop loss, and take profit levels.
        
        Args:
            setup: The detected trading setup
            
        Returns:
            Tuple of (entry_zone, stop_loss, take_profit)
        """
        # Placeholder implementation
        # In a real implementation, this would analyze the setup details
        # to determine appropriate entry, stop loss, and take profit levels
        
        # For now, return dummy values
        entry_zone = {
            "min": 100.0,
            "max": 102.0,
            "ideal": 101.0
        }
        stop_loss = 98.0
        take_profit = 106.0
        
        return entry_zone, stop_loss, take_profit
    
    def _calculate_risk_reward(
        self,
        entry_zone: Dict[str, float],
        stop_loss: float,
        take_profit: float
    ) -> float:
        """
        Calculate the risk-reward ratio for the trade.
        
        Args:
            entry_zone: Entry price zone
            stop_loss: Stop loss level
            take_profit: Take profit level
            
        Returns:
            Risk-reward ratio
        """
        # Use the ideal entry price if available, otherwise use the middle of the zone
        entry_price = entry_zone.get("ideal", (entry_zone.get("min", 0) + entry_zone.get("max", 0)) / 2)
        
        # Calculate risk and reward
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        # Calculate risk-reward ratio
        if risk > 0:
            risk_reward = reward / risk
        else:
            risk_reward = 0.0
        
        return round(risk_reward, 2)
    
    def _generate_recommendation_notes(
        self,
        setup: Dict[str, Any],
        market_regime: Optional[MarketRegime] = None,
        volatility_regime: Optional[str] = None,
        liquidity_regime: Optional[str] = None,
        correlation_data: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Generate notes and warnings for the recommendation.
        
        Args:
            setup: The detected trading setup
            market_regime: Current market regime if available
            volatility_regime: Current volatility regime if available
            liquidity_regime: Current liquidity regime if available
            correlation_data: Correlation data if available
            
        Returns:
            List of notes and warnings
        """
        notes = []
        
        # Add setup-specific notes
        setup_type = setup.get("type")
        if setup_type:
            notes.append(f"Setup type: {setup_type}")
        
        # Add market regime notes
        if market_regime:
            notes.append(f"Current market regime: {market_regime.value}")
            
            if market_regime == MarketRegime.VOLATILE:
                notes.append("Consider wider stop losses due to high volatility")
            elif market_regime == MarketRegime.RANGING:
                notes.append("Consider taking profits at range boundaries")
            elif market_regime == MarketRegime.TRENDING:
                notes.append("Consider trailing stops to capture trend continuation")
        
        # Add volatility regime notes
        if volatility_regime:
            notes.append(f"Volatility regime: {volatility_regime}")
            
            if volatility_regime == "high":
                notes.append("Consider reducing position size due to high volatility")
            elif volatility_regime == "low":
                notes.append("Be cautious of potential volatility expansion")
        
        # Add liquidity regime notes
        if liquidity_regime:
            notes.append(f"Liquidity regime: {liquidity_regime}")
            
            if liquidity_regime == "low":
                notes.append("Use limit orders to minimize slippage in low liquidity")
                notes.append("Be prepared for wider spreads and potential slippage")
        
        # Add correlation notes
        if correlation_data and self.use_correlation_adjustment:
            correlation = correlation_data.get("correlation", 0)
            if abs(correlation) > 0.7:
                notes.append(
                    f"High correlation ({correlation:.2f}) with other positions. "
                    "Consider portfolio exposure."
                )
        
        return notes
    
    def optimize_parameters(
        self,
        strategy_type: StrategyType,
        historical_data: pd.DataFrame,
        market_regime: Optional[MarketRegime] = None,
        parameter_ranges: Optional[Dict[str, Tuple[float, float, float]]] = None
    ) -> Dict[str, Any]:
        """
        Optimize strategy parameters based on historical data.
        
        Args:
            strategy_type: The type of trading strategy
            historical_data: Historical price data
            market_regime: Current market regime if available
            parameter_ranges: Dict of parameter ranges (min, max, step)
            
        Returns:
            Dict with optimized parameters
        """
        # Placeholder implementation
        # In a real implementation, this would perform a grid search or other
        # optimization technique to find the best parameters for the strategy
        
        self.logger.info(f"Optimizing parameters for {strategy_type.value} strategy")
        
        # For now, return dummy values
        optimized_params = {
            "entry_threshold": 0.5,
            "exit_threshold": 0.7,
            "stop_loss_percent": 2.0,
            "take_profit_percent": 4.0,
            "trailing_stop_percent": 1.5,
            "lookback_periods": 20
        }
        
        return optimized_params
    
    def get_strategy_performance(
        self,
        strategy_type: StrategyType,
        market_regime: Optional[MarketRegime] = None
    ) -> Dict[str, Any]:
        """
        Get historical performance metrics for a strategy in a specific market regime.
        
        Args:
            strategy_type: The type of trading strategy
            market_regime: Market regime to filter by
            
        Returns:
            Dict with performance metrics
        """
        # Placeholder implementation
        # In a real implementation, this would query a database of historical
        # strategy performance data, filtered by market regime if specified
        
        self.logger.info(
            f"Getting performance data for {strategy_type.value} strategy "
            f"in {market_regime.value if market_regime else 'all'} regime(s)"
        )
        
        # For now, return dummy values
        performance = {
            "win_rate": 0.65,
            "profit_factor": 1.8,
            "average_win": 2.5,
            "average_loss": 1.0,
            "max_drawdown": 5.0,
            "sharpe_ratio": 1.2,
            "total_trades": 100,
            "market_regime": market_regime.value if market_regime else "all"
        }
        
        return performance 