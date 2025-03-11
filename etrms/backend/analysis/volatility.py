"""
Enhanced Trading Risk Management System - Volatility Analysis

This module provides functionality to analyze market volatility and create volatility models
for risk assessment and position sizing.
"""

import numpy as np
import pandas as pd
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

from utils.logger import get_logger, log_event


class VolatilityModel(str, Enum):
    """Enum representing different volatility models"""
    HISTORICAL = "historical"
    GARCH = "garch"
    EWMA = "ewma"
    PARKINSON = "parkinson"
    ROGERS_SATCHELL = "rogers_satchell"
    YANG_ZHANG = "yang_zhang"


class VolatilityAnalyzer:
    """
    Class for analyzing market volatility and creating volatility models.
    
    This class provides methods to:
    - Calculate historical volatility
    - Estimate implied volatility
    - Create volatility forecasts
    - Analyze volatility regimes
    """
    
    def __init__(
        self,
        lookback_periods: int = 20,
        annualization_factor: float = 252.0,
        ewma_lambda: float = 0.94,
        volatility_threshold_high: float = 0.3,
        volatility_threshold_low: float = 0.1
    ):
        """
        Initialize the VolatilityAnalyzer.
        
        Args:
            lookback_periods: Number of periods to look back for calculations
            annualization_factor: Factor to annualize volatility (252 for daily, 52 for weekly, etc.)
            ewma_lambda: Lambda parameter for EWMA volatility model
            volatility_threshold_high: Threshold for high volatility regime
            volatility_threshold_low: Threshold for low volatility regime
        """
        self.lookback_periods = lookback_periods
        self.annualization_factor = annualization_factor
        self.ewma_lambda = ewma_lambda
        self.volatility_threshold_high = volatility_threshold_high
        self.volatility_threshold_low = volatility_threshold_low
        self.logger = get_logger(__name__)
        
        log_event(
            self.logger,
            "VOLATILITY_ANALYZER_INIT",
            "Volatility analyzer initialized",
            context={
                "lookback_periods": lookback_periods,
                "annualization_factor": annualization_factor,
                "ewma_lambda": ewma_lambda
            }
        )
    
    def calculate_historical_volatility(
        self,
        price_data: pd.DataFrame,
        model: VolatilityModel = VolatilityModel.HISTORICAL,
        window: Optional[int] = None
    ) -> float:
        """
        Calculate historical volatility based on price data.
        
        Args:
            price_data: DataFrame with OHLCV data
            model: Volatility model to use
            window: Window size for calculation (defaults to lookback_periods)
            
        Returns:
            Annualized volatility
        """
        if len(price_data) < 2:
            log_event(
                self.logger,
                "INSUFFICIENT_DATA",
                "Insufficient data for volatility calculation",
                context={"required": 2, "available": len(price_data)}
            )
            return 0.0
        
        window = window or self.lookback_periods
        
        try:
            if model == VolatilityModel.HISTORICAL:
                return self._calculate_standard_deviation(price_data, window)
            elif model == VolatilityModel.EWMA:
                return self._calculate_ewma_volatility(price_data, window)
            elif model == VolatilityModel.PARKINSON:
                return self._calculate_parkinson_volatility(price_data, window)
            elif model == VolatilityModel.ROGERS_SATCHELL:
                return self._calculate_rogers_satchell_volatility(price_data, window)
            elif model == VolatilityModel.YANG_ZHANG:
                return self._calculate_yang_zhang_volatility(price_data, window)
            elif model == VolatilityModel.GARCH:
                return self._calculate_garch_volatility(price_data, window)
            else:
                log_event(
                    self.logger,
                    "INVALID_VOLATILITY_MODEL",
                    f"Invalid volatility model: {model}",
                    context={"model": model}
                )
                return self._calculate_standard_deviation(price_data, window)
        
        except Exception as e:
            log_event(
                self.logger,
                "VOLATILITY_CALCULATION_ERROR",
                f"Error calculating volatility: {str(e)}",
                context={"error": str(e), "model": model}
            )
            return 0.0
    
    def _calculate_standard_deviation(self, price_data: pd.DataFrame, window: int) -> float:
        """
        Calculate volatility using standard deviation of log returns.
        
        Args:
            price_data: DataFrame with OHLCV data
            window: Window size for calculation
            
        Returns:
            Annualized volatility
        """
        # Calculate log returns
        close = price_data['close'].values
        log_returns = np.diff(np.log(close))
        
        # Calculate standard deviation
        if len(log_returns) < window:
            window = len(log_returns)
        
        std_dev = np.std(log_returns[-window:], ddof=1)
        
        # Annualize
        annualized_vol = std_dev * np.sqrt(self.annualization_factor)
        
        return annualized_vol
    
    def _calculate_ewma_volatility(self, price_data: pd.DataFrame, window: int) -> float:
        """
        Calculate volatility using Exponentially Weighted Moving Average (EWMA).
        
        Args:
            price_data: DataFrame with OHLCV data
            window: Window size for calculation
            
        Returns:
            Annualized volatility
        """
        # Calculate log returns
        close = price_data['close'].values
        log_returns = np.diff(np.log(close))
        
        if len(log_returns) < window:
            window = len(log_returns)
        
        # Calculate EWMA variance
        lambda_param = self.ewma_lambda
        weights = np.array([(1 - lambda_param) * lambda_param ** i for i in range(window)])
        weights = weights / weights.sum()
        
        # Reverse the weights to apply more weight to recent observations
        weights = weights[::-1]
        
        # Calculate weighted variance
        returns_subset = log_returns[-window:]
        ewma_var = np.sum(weights * returns_subset ** 2)
        
        # Annualize
        annualized_vol = np.sqrt(ewma_var * self.annualization_factor)
        
        return annualized_vol
    
    def _calculate_parkinson_volatility(self, price_data: pd.DataFrame, window: int) -> float:
        """
        Calculate volatility using Parkinson's formula (high-low range).
        
        Args:
            price_data: DataFrame with OHLCV data
            window: Window size for calculation
            
        Returns:
            Annualized volatility
        """
        high = price_data['high'].values
        low = price_data['low'].values
        
        if len(high) < window:
            window = len(high)
        
        # Calculate log high-low ranges
        log_hl = np.log(high[-window:] / low[-window:])
        
        # Calculate Parkinson's volatility
        parkinson_var = np.sum(log_hl ** 2) / (4 * window * np.log(2))
        
        # Annualize
        annualized_vol = np.sqrt(parkinson_var * self.annualization_factor)
        
        return annualized_vol
    
    def _calculate_rogers_satchell_volatility(self, price_data: pd.DataFrame, window: int) -> float:
        """
        Calculate volatility using Rogers-Satchell formula.
        
        Args:
            price_data: DataFrame with OHLCV data
            window: Window size for calculation
            
        Returns:
            Annualized volatility
        """
        if len(price_data) < window:
            window = len(price_data)
        
        # Extract price data
        high = price_data['high'].values[-window:]
        low = price_data['low'].values[-window:]
        open_price = price_data['open'].values[-window:]
        close = price_data['close'].values[-window:]
        
        # Calculate Rogers-Satchell estimator
        rs_terms = (np.log(high / close) * np.log(high / open_price) +
                   np.log(low / close) * np.log(low / open_price))
        
        rs_var = np.mean(rs_terms)
        
        # Annualize
        annualized_vol = np.sqrt(rs_var * self.annualization_factor)
        
        return annualized_vol
    
    def _calculate_yang_zhang_volatility(self, price_data: pd.DataFrame, window: int) -> float:
        """
        Calculate volatility using Yang-Zhang formula.
        
        Args:
            price_data: DataFrame with OHLCV data
            window: Window size for calculation
            
        Returns:
            Annualized volatility
        """
        if len(price_data) < window + 1:
            window = len(price_data) - 1
        
        # Extract price data
        high = price_data['high'].values[-(window+1):]
        low = price_data['low'].values[-(window+1):]
        open_price = price_data['open'].values[-(window+1):]
        close = price_data['close'].values[-(window+1):]
        
        # Calculate overnight volatility (close to open)
        overnight_returns = np.log(open_price[1:] / close[:-1])
        overnight_var = np.sum(overnight_returns ** 2) / window
        
        # Calculate open to close volatility
        open_close_returns = np.log(close[1:] / open_price[1:])
        open_close_var = np.sum(open_close_returns ** 2) / window
        
        # Calculate Rogers-Satchell volatility
        rs_terms = (np.log(high[1:] / close[1:]) * np.log(high[1:] / open_price[1:]) +
                   np.log(low[1:] / close[1:]) * np.log(low[1:] / open_price[1:]))
        rs_var = np.sum(rs_terms) / window
        
        # Calculate Yang-Zhang volatility
        k = 0.34 / (1.34 + (window + 1) / (window - 1))
        yz_var = overnight_var + k * open_close_var + (1 - k) * rs_var
        
        # Annualize
        annualized_vol = np.sqrt(yz_var * self.annualization_factor)
        
        return annualized_vol
    
    def _calculate_garch_volatility(self, price_data: pd.DataFrame, window: int) -> float:
        """
        Calculate volatility using a simple GARCH(1,1) model.
        
        Args:
            price_data: DataFrame with OHLCV data
            window: Window size for calculation
            
        Returns:
            Annualized volatility
        """
        # Calculate log returns
        close = price_data['close'].values
        log_returns = np.diff(np.log(close))
        
        if len(log_returns) < window:
            window = len(log_returns)
        
        # Use only the last 'window' returns
        returns = log_returns[-window:]
        
        # GARCH(1,1) parameters
        omega = 0.000001
        alpha = 0.1
        beta = 0.8
        
        # Initialize variance
        long_run_var = np.var(returns)
        var = long_run_var
        
        # Run GARCH(1,1) recursion
        for r in returns:
            var = omega + alpha * r**2 + beta * var
        
        # Annualize
        annualized_vol = np.sqrt(var * self.annualization_factor)
        
        return annualized_vol
    
    def detect_volatility_regime(self, volatility: float) -> str:
        """
        Detect the current volatility regime.
        
        Args:
            volatility: Calculated volatility
            
        Returns:
            Volatility regime ('high', 'normal', or 'low')
        """
        if volatility > self.volatility_threshold_high:
            return "high"
        elif volatility < self.volatility_threshold_low:
            return "low"
        else:
            return "normal"
    
    def calculate_volatility_surface(
        self,
        price_data: pd.DataFrame,
        windows: List[int] = [5, 10, 20, 50, 100]
    ) -> Dict[int, float]:
        """
        Calculate volatility for different time windows to create a volatility surface.
        
        Args:
            price_data: DataFrame with OHLCV data
            windows: List of window sizes to calculate volatility for
            
        Returns:
            Dictionary mapping window sizes to volatility values
        """
        surface = {}
        
        for window in windows:
            if len(price_data) >= window:
                vol = self.calculate_historical_volatility(price_data, window=window)
                surface[window] = vol
        
        return surface
    
    def calculate_volatility_cone(
        self,
        price_data: pd.DataFrame,
        windows: List[int] = [5, 10, 20, 50, 100],
        percentiles: List[float] = [5, 25, 50, 75, 95]
    ) -> Dict[str, Dict[int, float]]:
        """
        Calculate volatility cone showing percentiles of volatility across different time windows.
        
        Args:
            price_data: DataFrame with OHLCV data
            windows: List of window sizes to calculate volatility for
            percentiles: List of percentiles to calculate
            
        Returns:
            Dictionary mapping percentile names to dictionaries of window sizes and volatility values
        """
        if len(price_data) < max(windows) + 30:
            log_event(
                self.logger,
                "INSUFFICIENT_DATA",
                "Insufficient data for volatility cone calculation",
                context={"required": max(windows) + 30, "available": len(price_data)}
            )
            return {f"p{p}": {w: 0.0 for w in windows} for p in percentiles}
        
        # Calculate close-to-close returns
        close = price_data['close'].values
        returns = np.diff(np.log(close))
        
        # Calculate rolling volatilities for each window
        rolling_vols = {}
        for window in windows:
            vols = []
            for i in range(len(returns) - window + 1):
                window_returns = returns[i:i+window]
                vol = np.std(window_returns, ddof=1) * np.sqrt(self.annualization_factor)
                vols.append(vol)
            
            rolling_vols[window] = vols
        
        # Calculate percentiles
        cone = {}
        for p in percentiles:
            cone[f"p{p}"] = {}
            for window in windows:
                if rolling_vols[window]:
                    cone[f"p{p}"][window] = np.percentile(rolling_vols[window], p)
                else:
                    cone[f"p{p}"][window] = 0.0
        
        return cone
    
    def calculate_volatility_ratio(
        self,
        price_data: pd.DataFrame,
        short_window: int = 5,
        long_window: int = 20
    ) -> float:
        """
        Calculate the ratio of short-term to long-term volatility.
        
        Args:
            price_data: DataFrame with OHLCV data
            short_window: Window size for short-term volatility
            long_window: Window size for long-term volatility
            
        Returns:
            Ratio of short-term to long-term volatility
        """
        short_vol = self.calculate_historical_volatility(price_data, window=short_window)
        long_vol = self.calculate_historical_volatility(price_data, window=long_window)
        
        if long_vol == 0:
            return 1.0
        
        return short_vol / long_vol
    
    def calculate_position_size(
        self,
        price_data: pd.DataFrame,
        account_size: float,
        risk_per_trade: float,
        stop_loss_percent: float
    ) -> float:
        """
        Calculate position size based on volatility-adjusted risk.
        
        Args:
            price_data: DataFrame with OHLCV data
            account_size: Total account size
            risk_per_trade: Percentage of account to risk per trade
            stop_loss_percent: Stop loss percentage
            
        Returns:
            Position size in units
        """
        # Calculate volatility
        volatility = self.calculate_historical_volatility(price_data)
        
        # Get current price
        current_price = price_data['close'].values[-1]
        
        # Calculate risk amount
        risk_amount = account_size * risk_per_trade
        
        # Calculate stop loss distance
        stop_distance = current_price * stop_loss_percent
        
        # Adjust stop distance based on volatility
        volatility_ratio = volatility / 0.2  # Normalize to 20% annual volatility
        adjusted_stop = stop_distance * volatility_ratio
        
        # Calculate position size
        if adjusted_stop == 0:
            return 0
        
        position_size = risk_amount / adjusted_stop
        
        log_event(
            self.logger,
            "POSITION_SIZE_CALCULATED",
            f"Volatility-adjusted position size calculated: {position_size}",
            context={
                "volatility": volatility,
                "risk_amount": risk_amount,
                "adjusted_stop": adjusted_stop,
                "position_size": position_size
            }
        )
        
        return position_size


class VolatilityRegimeDetector:
    """
    Class for detecting changes in volatility regimes over time.
    
    This class tracks volatility regime changes and provides methods to analyze
    their impact on trading performance.
    """
    
    def __init__(self, volatility_analyzer: VolatilityAnalyzer):
        """
        Initialize the VolatilityRegimeDetector.
        
        Args:
            volatility_analyzer: VolatilityAnalyzer instance
        """
        self.volatility_analyzer = volatility_analyzer
        self.regime_history = []
        self.logger = get_logger(__name__)
    
    def update(
        self,
        price_data: pd.DataFrame,
        timestamp: Optional[datetime] = None
    ) -> Tuple[str, bool]:
        """
        Update the volatility regime history.
        
        Args:
            price_data: DataFrame with OHLCV data
            timestamp: Optional timestamp for the update (defaults to current time)
            
        Returns:
            Tuple of (current_regime, regime_changed)
        """
        # Calculate volatility
        volatility = self.volatility_analyzer.calculate_historical_volatility(price_data)
        
        # Detect regime
        current_regime = self.volatility_analyzer.detect_volatility_regime(volatility)
        current_time = timestamp or datetime.utcnow()
        
        # Check if regime has changed
        regime_changed = False
        if self.regime_history and self.regime_history[-1]['regime'] != current_regime:
            regime_changed = True
            
            log_event(
                self.logger,
                "VOLATILITY_REGIME_CHANGE",
                f"Volatility regime changed from {self.regime_history[-1]['regime']} to {current_regime}",
                context={
                    "previous_regime": self.regime_history[-1]['regime'],
                    "new_regime": current_regime,
                    "volatility": volatility,
                    "previous_time": self.regime_history[-1]['timestamp'].isoformat(),
                    "current_time": current_time.isoformat()
                }
            )
        
        # Add to history
        self.regime_history.append({
            'timestamp': current_time,
            'regime': current_regime,
            'volatility': volatility
        })
        
        return current_regime, regime_changed
    
    def get_current_regime(self) -> Optional[str]:
        """
        Get the current volatility regime.
        
        Returns:
            Current volatility regime or None if no history
        """
        if not self.regime_history:
            return None
        
        return self.regime_history[-1]['regime']
    
    def get_regime_duration(self) -> Optional[timedelta]:
        """
        Get the duration of the current volatility regime.
        
        Returns:
            Duration of the current regime or None if no history
        """
        if not self.regime_history:
            return None
        
        current_regime = self.regime_history[-1]['regime']
        
        # Find the most recent regime change
        for i in range(len(self.regime_history) - 2, -1, -1):
            if self.regime_history[i]['regime'] != current_regime:
                regime_start = self.regime_history[i + 1]['timestamp']
                current_time = self.regime_history[-1]['timestamp']
                return current_time - regime_start
        
        # If no regime change found, return duration since first record
        return self.regime_history[-1]['timestamp'] - self.regime_history[0]['timestamp']
    
    def get_regime_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about volatility regime occurrences and durations.
        
        Returns:
            Dictionary with regime statistics
        """
        if not self.regime_history:
            return {}
        
        # Count occurrences of each regime
        regime_counts = {
            "high": 0,
            "normal": 0,
            "low": 0
        }
        
        for entry in self.regime_history:
            regime_counts[entry['regime']] += 1
        
        # Calculate average volatility for each regime
        regime_volatilities = {
            "high": [],
            "normal": [],
            "low": []
        }
        
        for entry in self.regime_history:
            regime_volatilities[entry['regime']].append(entry['volatility'])
        
        avg_volatilities = {}
        for regime, vols in regime_volatilities.items():
            if vols:
                avg_volatilities[regime] = sum(vols) / len(vols)
            else:
                avg_volatilities[regime] = 0
        
        # Calculate average duration of each regime
        regime_durations = {
            "high": [],
            "normal": [],
            "low": []
        }
        
        regime_start_times = {}
        
        current_regime = self.regime_history[0]['regime']
        regime_start_times[current_regime] = self.regime_history[0]['timestamp']
        
        for i in range(1, len(self.regime_history)):
            entry = self.regime_history[i]
            prev_entry = self.regime_history[i - 1]
            
            if entry['regime'] != prev_entry['regime']:
                # Regime changed, calculate duration
                duration = entry['timestamp'] - regime_start_times[prev_entry['regime']]
                regime_durations[prev_entry['regime']].append(duration.total_seconds())
                regime_start_times[entry['regime']] = entry['timestamp']
        
        # Calculate average durations
        avg_durations = {}
        for regime, durations in regime_durations.items():
            if durations:
                avg_durations[regime] = sum(durations) / len(durations)
            else:
                avg_durations[regime] = 0
        
        return {
            'counts': regime_counts,
            'average_volatilities': avg_volatilities,
            'average_durations': avg_durations,
            'total_regimes_detected': len(self.regime_history)
        } 