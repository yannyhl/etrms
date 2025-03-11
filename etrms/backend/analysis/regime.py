"""
Enhanced Trading Risk Management System - Market Regime Detection

This module provides functionality to identify market regimes (trending, ranging, volatile)
based on price data and various technical indicators.
"""

import numpy as np
import pandas as pd
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

from utils.logger import get_logger, log_event


class MarketRegime(str, Enum):
    """Enum representing different market regimes"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"
    UNKNOWN = "unknown"


class MarketRegimeDetector:
    """
    Class for detecting market regimes based on price data and technical indicators.
    
    This class uses a combination of indicators to classify the current market regime:
    - ADX for trend strength
    - Bollinger Bands for volatility
    - RSI for overbought/oversold conditions
    - Moving averages for trend direction
    """
    
    def __init__(
        self,
        lookback_periods: int = 20,
        adx_threshold: float = 25.0,
        volatility_threshold: float = 1.5,
        rsi_overbought: float = 70.0,
        rsi_oversold: float = 30.0
    ):
        """
        Initialize the MarketRegimeDetector.
        
        Args:
            lookback_periods: Number of periods to look back for calculations
            adx_threshold: Threshold for ADX to indicate a trending market
            volatility_threshold: Threshold for volatility (BB width) to indicate a volatile market
            rsi_overbought: RSI threshold for overbought condition
            rsi_oversold: RSI threshold for oversold condition
        """
        self.lookback_periods = lookback_periods
        self.adx_threshold = adx_threshold
        self.volatility_threshold = volatility_threshold
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.logger = get_logger(__name__)
        
        log_event(
            self.logger,
            "REGIME_DETECTOR_INIT",
            "Market regime detector initialized",
            context={
                "lookback_periods": lookback_periods,
                "adx_threshold": adx_threshold,
                "volatility_threshold": volatility_threshold
            }
        )
    
    def detect_regime(self, price_data: pd.DataFrame) -> MarketRegime:
        """
        Detect the current market regime based on price data.
        
        Args:
            price_data: DataFrame with OHLCV data
            
        Returns:
            MarketRegime enum value representing the detected regime
        """
        if len(price_data) < self.lookback_periods * 2:
            log_event(
                self.logger,
                "INSUFFICIENT_DATA",
                "Insufficient data for regime detection",
                context={"required": self.lookback_periods * 2, "available": len(price_data)}
            )
            return MarketRegime.UNKNOWN
        
        try:
            # Calculate indicators
            adx = self._calculate_adx(price_data)
            bb_width = self._calculate_bollinger_band_width(price_data)
            rsi = self._calculate_rsi(price_data)
            ma_trend = self._calculate_ma_trend(price_data)
            
            # Determine regime based on indicators
            if adx > self.adx_threshold:
                # Trending market
                if ma_trend > 0:
                    regime = MarketRegime.TRENDING_UP
                else:
                    regime = MarketRegime.TRENDING_DOWN
            elif bb_width > self.volatility_threshold:
                # Volatile market
                regime = MarketRegime.VOLATILE
            else:
                # Ranging market
                regime = MarketRegime.RANGING
            
            # Check for breakouts or reversals
            if self._is_breakout(price_data, bb_width):
                regime = MarketRegime.BREAKOUT
            elif self._is_reversal(price_data, rsi):
                regime = MarketRegime.REVERSAL
            
            log_event(
                self.logger,
                "REGIME_DETECTED",
                f"Market regime detected: {regime}",
                context={
                    "regime": regime,
                    "adx": adx,
                    "bb_width": bb_width,
                    "rsi": rsi,
                    "ma_trend": ma_trend
                }
            )
            
            return regime
        
        except Exception as e:
            log_event(
                self.logger,
                "REGIME_DETECTION_ERROR",
                f"Error detecting market regime: {str(e)}",
                context={"error": str(e)}
            )
            return MarketRegime.UNKNOWN
    
    def _calculate_adx(self, price_data: pd.DataFrame) -> float:
        """
        Calculate the Average Directional Index (ADX) for trend strength.
        
        Args:
            price_data: DataFrame with OHLCV data
            
        Returns:
            ADX value (0-100)
        """
        # Extract price data
        high = price_data['high'].values
        low = price_data['low'].values
        close = price_data['close'].values
        
        # Calculate +DI and -DI
        plus_dm = np.zeros_like(high)
        minus_dm = np.zeros_like(high)
        
        for i in range(1, len(high)):
            h_diff = high[i] - high[i-1]
            l_diff = low[i-1] - low[i]
            
            if h_diff > l_diff and h_diff > 0:
                plus_dm[i] = h_diff
            else:
                plus_dm[i] = 0
                
            if l_diff > h_diff and l_diff > 0:
                minus_dm[i] = l_diff
            else:
                minus_dm[i] = 0
        
        # Calculate True Range
        tr = np.zeros_like(high)
        for i in range(1, len(high)):
            tr[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i-1]),
                abs(low[i] - close[i-1])
            )
        
        # Smooth with EMA
        period = self.lookback_periods
        tr_ema = self._exponential_moving_average(tr, period)
        plus_di = 100 * self._exponential_moving_average(plus_dm, period) / tr_ema
        minus_di = 100 * self._exponential_moving_average(minus_dm, period) / tr_ema
        
        # Calculate ADX
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = self._exponential_moving_average(dx, period)
        
        return adx[-1]
    
    def _calculate_bollinger_band_width(self, price_data: pd.DataFrame) -> float:
        """
        Calculate the Bollinger Band width for volatility.
        
        Args:
            price_data: DataFrame with OHLCV data
            
        Returns:
            Bollinger Band width (normalized)
        """
        close = price_data['close'].values
        period = self.lookback_periods
        
        # Calculate SMA
        sma = np.mean(close[-period:])
        
        # Calculate standard deviation
        std = np.std(close[-period:])
        
        # Calculate BB width
        upper_band = sma + 2 * std
        lower_band = sma - 2 * std
        bb_width = (upper_band - lower_band) / sma
        
        return bb_width
    
    def _calculate_rsi(self, price_data: pd.DataFrame) -> float:
        """
        Calculate the Relative Strength Index (RSI).
        
        Args:
            price_data: DataFrame with OHLCV data
            
        Returns:
            RSI value (0-100)
        """
        close = price_data['close'].values
        period = self.lookback_periods
        
        # Calculate price changes
        delta = np.diff(close)
        
        # Separate gains and losses
        gains = np.where(delta > 0, delta, 0)
        losses = np.where(delta < 0, -delta, 0)
        
        # Calculate average gains and losses
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_ma_trend(self, price_data: pd.DataFrame) -> float:
        """
        Calculate the moving average trend direction.
        
        Args:
            price_data: DataFrame with OHLCV data
            
        Returns:
            Trend direction (positive for up, negative for down)
        """
        close = price_data['close'].values
        short_period = self.lookback_periods // 2
        long_period = self.lookback_periods
        
        # Calculate short and long MAs
        short_ma = np.mean(close[-short_period:])
        long_ma = np.mean(close[-long_period:])
        
        # Calculate trend direction
        return short_ma - long_ma
    
    def _is_breakout(self, price_data: pd.DataFrame, bb_width: float) -> bool:
        """
        Detect if a breakout is occurring.
        
        Args:
            price_data: DataFrame with OHLCV data
            bb_width: Current Bollinger Band width
            
        Returns:
            True if a breakout is detected, False otherwise
        """
        close = price_data['close'].values
        period = self.lookback_periods
        
        # Calculate SMA
        sma = np.mean(close[-period:])
        
        # Calculate standard deviation
        std = np.std(close[-period:])
        
        # Calculate Bollinger Bands
        upper_band = sma + 2 * std
        lower_band = sma - 2 * std
        
        # Check for breakout
        current_close = close[-1]
        previous_close = close[-2]
        
        # Breakout if price crosses outside bands with increasing volatility
        breakout_up = previous_close < upper_band and current_close > upper_band and bb_width > self.volatility_threshold
        breakout_down = previous_close > lower_band and current_close < lower_band and bb_width > self.volatility_threshold
        
        return breakout_up or breakout_down
    
    def _is_reversal(self, price_data: pd.DataFrame, rsi: float) -> bool:
        """
        Detect if a reversal is occurring.
        
        Args:
            price_data: DataFrame with OHLCV data
            rsi: Current RSI value
            
        Returns:
            True if a reversal is detected, False otherwise
        """
        close = price_data['close'].values
        
        # Check for overbought/oversold conditions
        overbought = rsi > self.rsi_overbought
        oversold = rsi < self.rsi_oversold
        
        # Check for price reversal
        current_close = close[-1]
        previous_close = close[-2]
        price_reversal_up = current_close > previous_close and oversold
        price_reversal_down = current_close < previous_close and overbought
        
        return price_reversal_up or price_reversal_down
    
    def _exponential_moving_average(self, data: np.ndarray, period: int) -> np.ndarray:
        """
        Calculate the Exponential Moving Average (EMA).
        
        Args:
            data: Input data array
            period: EMA period
            
        Returns:
            EMA values
        """
        alpha = 2 / (period + 1)
        ema = np.zeros_like(data)
        ema[0] = data[0]
        
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
        
        return ema


class RegimeChangeDetector:
    """
    Class for detecting changes in market regimes over time.
    
    This class tracks regime changes and provides methods to analyze regime transitions
    and their impact on trading performance.
    """
    
    def __init__(self, regime_detector: MarketRegimeDetector):
        """
        Initialize the RegimeChangeDetector.
        
        Args:
            regime_detector: MarketRegimeDetector instance
        """
        self.regime_detector = regime_detector
        self.regime_history = []
        self.logger = get_logger(__name__)
    
    def update(self, price_data: pd.DataFrame, timestamp: Optional[datetime] = None) -> Tuple[MarketRegime, bool]:
        """
        Update the regime history with the current regime.
        
        Args:
            price_data: DataFrame with OHLCV data
            timestamp: Optional timestamp for the update (defaults to current time)
            
        Returns:
            Tuple of (current_regime, regime_changed)
        """
        current_regime = self.regime_detector.detect_regime(price_data)
        current_time = timestamp or datetime.utcnow()
        
        # Check if regime has changed
        regime_changed = False
        if self.regime_history and self.regime_history[-1]['regime'] != current_regime:
            regime_changed = True
            
            log_event(
                self.logger,
                "REGIME_CHANGE",
                f"Market regime changed from {self.regime_history[-1]['regime']} to {current_regime}",
                context={
                    "previous_regime": self.regime_history[-1]['regime'],
                    "new_regime": current_regime,
                    "previous_time": self.regime_history[-1]['timestamp'].isoformat(),
                    "current_time": current_time.isoformat()
                }
            )
        
        # Add to history
        self.regime_history.append({
            'timestamp': current_time,
            'regime': current_regime
        })
        
        return current_regime, regime_changed
    
    def get_current_regime(self) -> Optional[MarketRegime]:
        """
        Get the current market regime.
        
        Returns:
            Current market regime or None if no history
        """
        if not self.regime_history:
            return None
        
        return self.regime_history[-1]['regime']
    
    def get_regime_duration(self) -> Optional[timedelta]:
        """
        Get the duration of the current regime.
        
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
        Get statistics about regime occurrences and durations.
        
        Returns:
            Dictionary with regime statistics
        """
        if not self.regime_history:
            return {}
        
        # Count occurrences of each regime
        regime_counts = {}
        for regime in MarketRegime:
            regime_counts[regime] = 0
        
        for entry in self.regime_history:
            regime_counts[entry['regime']] += 1
        
        # Calculate average duration of each regime
        regime_durations = {}
        regime_start_times = {}
        
        current_regime = self.regime_history[0]['regime']
        regime_start_times[current_regime] = self.regime_history[0]['timestamp']
        
        for i in range(1, len(self.regime_history)):
            entry = self.regime_history[i]
            prev_entry = self.regime_history[i - 1]
            
            if entry['regime'] != prev_entry['regime']:
                # Regime changed, calculate duration
                duration = entry['timestamp'] - regime_start_times[prev_entry['regime']]
                
                if prev_entry['regime'] not in regime_durations:
                    regime_durations[prev_entry['regime']] = []
                
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
            'average_durations': avg_durations,
            'total_regimes_detected': len(self.regime_history)
        } 