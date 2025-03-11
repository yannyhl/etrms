"""
Enhanced Trading Risk Management System - Correlation Analysis

This module provides functionality to analyze correlations between different assets and markets,
which is useful for portfolio diversification and risk management.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

from utils.logger import get_logger, log_event


class CorrelationAnalyzer:
    """
    Class for analyzing correlations between different assets and markets.
    
    This class provides methods to:
    - Calculate correlation matrices
    - Detect correlation regime changes
    - Analyze correlation breakdowns during market stress
    - Optimize portfolio diversification
    """
    
    def __init__(
        self,
        lookback_periods: int = 60,
        rolling_window: int = 20,
        correlation_threshold_high: float = 0.7,
        correlation_threshold_low: float = 0.3
    ):
        """
        Initialize the CorrelationAnalyzer.
        
        Args:
            lookback_periods: Number of periods to look back for calculations
            rolling_window: Window size for rolling correlation calculations
            correlation_threshold_high: Threshold for high correlation
            correlation_threshold_low: Threshold for low correlation
        """
        self.lookback_periods = lookback_periods
        self.rolling_window = rolling_window
        self.correlation_threshold_high = correlation_threshold_high
        self.correlation_threshold_low = correlation_threshold_low
        self.logger = get_logger(__name__)
        
        log_event(
            self.logger,
            "CORRELATION_ANALYZER_INIT",
            "Correlation analyzer initialized",
            context={
                "lookback_periods": lookback_periods,
                "rolling_window": rolling_window,
                "correlation_threshold_high": correlation_threshold_high,
                "correlation_threshold_low": correlation_threshold_low
            }
        )
    
    def calculate_correlation_matrix(
        self,
        price_data: Dict[str, pd.DataFrame],
        method: str = 'pearson',
        window: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix between multiple assets.
        
        Args:
            price_data: Dictionary mapping asset symbols to DataFrames with OHLCV data
            method: Correlation method ('pearson', 'spearman', or 'kendall')
            window: Window size for calculation (defaults to lookback_periods)
            
        Returns:
            DataFrame containing the correlation matrix
        """
        window = window or self.lookback_periods
        
        # Extract returns for each asset
        returns_dict = {}
        for symbol, data in price_data.items():
            if len(data) < 2:
                log_event(
                    self.logger,
                    "INSUFFICIENT_DATA",
                    f"Insufficient data for {symbol}",
                    context={"symbol": symbol, "required": 2, "available": len(data)}
                )
                continue
            
            # Calculate log returns
            close = data['close'].values
            log_returns = np.diff(np.log(close))
            
            # Use only the last 'window' returns
            if len(log_returns) < window:
                log_event(
                    self.logger,
                    "INSUFFICIENT_DATA",
                    f"Insufficient return data for {symbol}",
                    context={"symbol": symbol, "required": window, "available": len(log_returns)}
                )
                continue
            
            returns_dict[symbol] = log_returns[-window:]
        
        # Create DataFrame of returns
        returns_df = pd.DataFrame(returns_dict)
        
        # Calculate correlation matrix
        corr_matrix = returns_df.corr(method=method)
        
        log_event(
            self.logger,
            "CORRELATION_MATRIX_CALCULATED",
            "Correlation matrix calculated",
            context={
                "method": method,
                "window": window,
                "num_assets": len(returns_dict)
            }
        )
        
        return corr_matrix
    
    def calculate_rolling_correlation(
        self,
        price_data_1: pd.DataFrame,
        price_data_2: pd.DataFrame,
        window: Optional[int] = None,
        method: str = 'pearson'
    ) -> pd.Series:
        """
        Calculate rolling correlation between two assets.
        
        Args:
            price_data_1: DataFrame with OHLCV data for first asset
            price_data_2: DataFrame with OHLCV data for second asset
            window: Window size for rolling calculation (defaults to rolling_window)
            method: Correlation method ('pearson', 'spearman', or 'kendall')
            
        Returns:
            Series containing rolling correlation values
        """
        window = window or self.rolling_window
        
        # Calculate log returns
        close_1 = price_data_1['close'].values
        close_2 = price_data_2['close'].values
        
        log_returns_1 = np.diff(np.log(close_1))
        log_returns_2 = np.diff(np.log(close_2))
        
        # Ensure both return series have the same length
        min_length = min(len(log_returns_1), len(log_returns_2))
        log_returns_1 = log_returns_1[-min_length:]
        log_returns_2 = log_returns_2[-min_length:]
        
        # Create DataFrame of returns
        returns_df = pd.DataFrame({
            'asset1': log_returns_1,
            'asset2': log_returns_2
        })
        
        # Calculate rolling correlation
        rolling_corr = returns_df['asset1'].rolling(window=window).corr(returns_df['asset2'], method=method)
        
        return rolling_corr
    
    def detect_correlation_breakdown(
        self,
        price_data_1: pd.DataFrame,
        price_data_2: pd.DataFrame,
        window: Optional[int] = None,
        threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Detect correlation breakdowns between two assets.
        
        Args:
            price_data_1: DataFrame with OHLCV data for first asset
            price_data_2: DataFrame with OHLCV data for second asset
            window: Window size for calculation (defaults to rolling_window)
            threshold: Threshold for correlation change to be considered a breakdown
            
        Returns:
            List of dictionaries containing breakdown information
        """
        window = window or self.rolling_window
        
        # Calculate rolling correlation
        rolling_corr = self.calculate_rolling_correlation(price_data_1, price_data_2, window)
        
        # Detect breakdowns
        breakdowns = []
        prev_corr = None
        
        for i, corr in enumerate(rolling_corr):
            if pd.isna(corr) or prev_corr is None:
                prev_corr = corr
                continue
            
            # Check for significant correlation change
            if abs(corr - prev_corr) > threshold:
                breakdowns.append({
                    'index': i,
                    'previous_correlation': prev_corr,
                    'new_correlation': corr,
                    'change': corr - prev_corr
                })
            
            prev_corr = corr
        
        log_event(
            self.logger,
            "CORRELATION_BREAKDOWNS_DETECTED",
            f"Detected {len(breakdowns)} correlation breakdowns",
            context={
                "window": window,
                "threshold": threshold,
                "num_breakdowns": len(breakdowns)
            }
        )
        
        return breakdowns
    
    def calculate_diversification_score(
        self,
        correlation_matrix: pd.DataFrame
    ) -> float:
        """
        Calculate a diversification score based on the correlation matrix.
        
        Args:
            correlation_matrix: Correlation matrix between assets
            
        Returns:
            Diversification score (0-1, higher is better)
        """
        # Extract the upper triangle of the correlation matrix (excluding diagonal)
        upper_triangle = np.triu(correlation_matrix.values, k=1)
        
        # Calculate the average absolute correlation
        avg_corr = np.mean(np.abs(upper_triangle[upper_triangle != 0]))
        
        # Convert to a diversification score (1 - avg_corr)
        diversification_score = 1 - avg_corr
        
        log_event(
            self.logger,
            "DIVERSIFICATION_SCORE_CALCULATED",
            f"Diversification score: {diversification_score:.4f}",
            context={
                "diversification_score": diversification_score,
                "avg_correlation": avg_corr,
                "num_assets": len(correlation_matrix)
            }
        )
        
        return diversification_score
    
    def calculate_conditional_correlation(
        self,
        price_data_1: pd.DataFrame,
        price_data_2: pd.DataFrame,
        condition_data: pd.DataFrame,
        condition_threshold: float,
        condition_type: str = 'greater'
    ) -> Dict[str, float]:
        """
        Calculate correlation between two assets conditional on a third variable.
        
        Args:
            price_data_1: DataFrame with OHLCV data for first asset
            price_data_2: DataFrame with OHLCV data for second asset
            condition_data: DataFrame with condition variable (e.g., VIX)
            condition_threshold: Threshold for condition
            condition_type: Type of condition ('greater' or 'less')
            
        Returns:
            Dictionary with conditional and unconditional correlations
        """
        # Calculate log returns
        close_1 = price_data_1['close'].values
        close_2 = price_data_2['close'].values
        
        log_returns_1 = np.diff(np.log(close_1))
        log_returns_2 = np.diff(np.log(close_2))
        
        # Ensure all series have the same length
        condition_values = condition_data['close'].values
        
        min_length = min(len(log_returns_1), len(log_returns_2), len(condition_values) - 1)
        log_returns_1 = log_returns_1[-min_length:]
        log_returns_2 = log_returns_2[-min_length:]
        condition_values = condition_values[-min_length-1:-1]  # Align with returns
        
        # Create DataFrame
        data = pd.DataFrame({
            'asset1': log_returns_1,
            'asset2': log_returns_2,
            'condition': condition_values
        })
        
        # Calculate unconditional correlation
        unconditional_corr = data['asset1'].corr(data['asset2'])
        
        # Calculate conditional correlation
        if condition_type == 'greater':
            condition_mask = data['condition'] > condition_threshold
        else:
            condition_mask = data['condition'] < condition_threshold
        
        conditional_data = data[condition_mask]
        
        if len(conditional_data) < 2:
            log_event(
                self.logger,
                "INSUFFICIENT_DATA",
                "Insufficient data for conditional correlation",
                context={"required": 2, "available": len(conditional_data)}
            )
            conditional_corr = np.nan
        else:
            conditional_corr = conditional_data['asset1'].corr(conditional_data['asset2'])
        
        log_event(
            self.logger,
            "CONDITIONAL_CORRELATION_CALCULATED",
            "Conditional correlation calculated",
            context={
                "unconditional_correlation": unconditional_corr,
                "conditional_correlation": conditional_corr,
                "condition_type": condition_type,
                "condition_threshold": condition_threshold,
                "condition_data_points": len(conditional_data)
            }
        )
        
        return {
            'unconditional_correlation': unconditional_corr,
            'conditional_correlation': conditional_corr,
            'difference': conditional_corr - unconditional_corr
        }
    
    def generate_correlation_heatmap(
        self,
        correlation_matrix: pd.DataFrame,
        title: str = 'Asset Correlation Heatmap'
    ) -> str:
        """
        Generate a correlation heatmap visualization.
        
        Args:
            correlation_matrix: Correlation matrix between assets
            title: Title for the heatmap
            
        Returns:
            Base64-encoded PNG image of the heatmap
        """
        # Create figure
        plt.figure(figsize=(10, 8))
        
        # Create heatmap
        sns.heatmap(
            correlation_matrix,
            annot=True,
            cmap='coolwarm',
            vmin=-1,
            vmax=1,
            center=0,
            square=True,
            fmt='.2f',
            linewidths=0.5
        )
        
        # Set title
        plt.title(title, fontsize=14)
        
        # Save to BytesIO
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close()
        
        # Encode as base64
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return img_str
    
    def optimize_portfolio_weights(
        self,
        returns_data: Dict[str, np.ndarray],
        method: str = 'min_variance'
    ) -> Dict[str, float]:
        """
        Optimize portfolio weights based on correlation and volatility.
        
        Args:
            returns_data: Dictionary mapping asset symbols to arrays of returns
            method: Optimization method ('min_variance', 'equal_weight', or 'risk_parity')
            
        Returns:
            Dictionary mapping asset symbols to optimal weights
        """
        # Create returns DataFrame
        returns_df = pd.DataFrame(returns_data)
        
        # Calculate covariance matrix
        cov_matrix = returns_df.cov()
        
        # Get asset symbols
        symbols = list(returns_data.keys())
        
        if method == 'equal_weight':
            # Equal weight allocation
            weight = 1.0 / len(symbols)
            weights = {symbol: weight for symbol in symbols}
        
        elif method == 'min_variance':
            # Minimum variance portfolio
            try:
                # Calculate inverse of covariance matrix
                inv_cov = np.linalg.inv(cov_matrix.values)
                
                # Calculate weights
                ones = np.ones(len(symbols))
                numerator = np.dot(inv_cov, ones)
                denominator = np.dot(ones, numerator)
                
                raw_weights = numerator / denominator
                
                # Ensure weights sum to 1 and are non-negative
                raw_weights = np.maximum(raw_weights, 0)
                if np.sum(raw_weights) > 0:
                    raw_weights = raw_weights / np.sum(raw_weights)
                
                weights = {symbol: float(weight) for symbol, weight in zip(symbols, raw_weights)}
            
            except np.linalg.LinAlgError:
                log_event(
                    self.logger,
                    "OPTIMIZATION_ERROR",
                    "Error calculating minimum variance weights, using equal weights",
                    context={"method": method, "error": "Singular matrix"}
                )
                weight = 1.0 / len(symbols)
                weights = {symbol: weight for symbol in symbols}
        
        elif method == 'risk_parity':
            # Risk parity allocation
            # Calculate asset volatilities
            vols = returns_df.std().values
            
            # Calculate inverse volatility weights
            inv_vols = 1.0 / vols
            raw_weights = inv_vols / np.sum(inv_vols)
            
            weights = {symbol: float(weight) for symbol, weight in zip(symbols, raw_weights)}
        
        else:
            log_event(
                self.logger,
                "INVALID_METHOD",
                f"Invalid optimization method: {method}",
                context={"method": method}
            )
            weight = 1.0 / len(symbols)
            weights = {symbol: weight for symbol in symbols}
        
        log_event(
            self.logger,
            "PORTFOLIO_WEIGHTS_OPTIMIZED",
            f"Portfolio weights optimized using {method}",
            context={
                "method": method,
                "num_assets": len(symbols),
                "weights": weights
            }
        )
        
        return weights
    
    def calculate_portfolio_metrics(
        self,
        returns_data: Dict[str, np.ndarray],
        weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate portfolio metrics based on asset returns and weights.
        
        Args:
            returns_data: Dictionary mapping asset symbols to arrays of returns
            weights: Dictionary mapping asset symbols to weights
            
        Returns:
            Dictionary with portfolio metrics
        """
        # Create returns DataFrame
        returns_df = pd.DataFrame(returns_data)
        
        # Create weights array
        symbols = list(returns_data.keys())
        weights_array = np.array([weights.get(symbol, 0) for symbol in symbols])
        
        # Normalize weights to sum to 1
        weights_array = weights_array / np.sum(weights_array)
        
        # Calculate portfolio returns
        portfolio_returns = returns_df.dot(weights_array)
        
        # Calculate metrics
        portfolio_mean = portfolio_returns.mean()
        portfolio_std = portfolio_returns.std()
        sharpe_ratio = portfolio_mean / portfolio_std if portfolio_std > 0 else 0
        
        # Calculate maximum drawdown
        cumulative_returns = (1 + portfolio_returns).cumprod()
        running_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns / running_max) - 1
        max_drawdown = drawdown.min()
        
        metrics = {
            'mean_return': float(portfolio_mean),
            'volatility': float(portfolio_std),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown)
        }
        
        log_event(
            self.logger,
            "PORTFOLIO_METRICS_CALCULATED",
            "Portfolio metrics calculated",
            context=metrics
        )
        
        return metrics


class CorrelationRegimeDetector:
    """
    Class for detecting changes in correlation regimes over time.
    
    This class tracks correlation regime changes and provides methods to analyze
    their impact on portfolio performance.
    """
    
    def __init__(
        self,
        correlation_analyzer: CorrelationAnalyzer,
        high_threshold: float = 0.7,
        low_threshold: float = 0.3
    ):
        """
        Initialize the CorrelationRegimeDetector.
        
        Args:
            correlation_analyzer: CorrelationAnalyzer instance
            high_threshold: Threshold for high correlation regime
            low_threshold: Threshold for low correlation regime
        """
        self.correlation_analyzer = correlation_analyzer
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold
        self.regime_history = []
        self.logger = get_logger(__name__)
    
    def detect_regime(
        self,
        price_data: Dict[str, pd.DataFrame]
    ) -> str:
        """
        Detect the current correlation regime.
        
        Args:
            price_data: Dictionary mapping asset symbols to DataFrames with OHLCV data
            
        Returns:
            Correlation regime ('high', 'normal', or 'low')
        """
        # Calculate correlation matrix
        corr_matrix = self.correlation_analyzer.calculate_correlation_matrix(price_data)
        
        # Calculate average absolute correlation
        upper_triangle = np.triu(corr_matrix.values, k=1)
        avg_corr = np.mean(np.abs(upper_triangle[upper_triangle != 0]))
        
        # Determine regime
        if avg_corr > self.high_threshold:
            regime = "high"
        elif avg_corr < self.low_threshold:
            regime = "low"
        else:
            regime = "normal"
        
        return regime
    
    def update(
        self,
        price_data: Dict[str, pd.DataFrame],
        timestamp: Optional[datetime] = None
    ) -> Tuple[str, bool]:
        """
        Update the correlation regime history.
        
        Args:
            price_data: Dictionary mapping asset symbols to DataFrames with OHLCV data
            timestamp: Optional timestamp for the update (defaults to current time)
            
        Returns:
            Tuple of (current_regime, regime_changed)
        """
        # Detect regime
        current_regime = self.detect_regime(price_data)
        current_time = timestamp or datetime.utcnow()
        
        # Calculate diversification score
        corr_matrix = self.correlation_analyzer.calculate_correlation_matrix(price_data)
        diversification_score = self.correlation_analyzer.calculate_diversification_score(corr_matrix)
        
        # Check if regime has changed
        regime_changed = False
        if self.regime_history and self.regime_history[-1]['regime'] != current_regime:
            regime_changed = True
            
            log_event(
                self.logger,
                "CORRELATION_REGIME_CHANGE",
                f"Correlation regime changed from {self.regime_history[-1]['regime']} to {current_regime}",
                context={
                    "previous_regime": self.regime_history[-1]['regime'],
                    "new_regime": current_regime,
                    "diversification_score": diversification_score,
                    "previous_time": self.regime_history[-1]['timestamp'].isoformat(),
                    "current_time": current_time.isoformat()
                }
            )
        
        # Add to history
        self.regime_history.append({
            'timestamp': current_time,
            'regime': current_regime,
            'diversification_score': diversification_score
        })
        
        return current_regime, regime_changed
    
    def get_current_regime(self) -> Optional[str]:
        """
        Get the current correlation regime.
        
        Returns:
            Current correlation regime or None if no history
        """
        if not self.regime_history:
            return None
        
        return self.regime_history[-1]['regime']
    
    def get_regime_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about correlation regime occurrences and durations.
        
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
        
        # Calculate average diversification score for each regime
        regime_scores = {
            "high": [],
            "normal": [],
            "low": []
        }
        
        for entry in self.regime_history:
            regime_scores[entry['regime']].append(entry['diversification_score'])
        
        avg_scores = {}
        for regime, scores in regime_scores.items():
            if scores:
                avg_scores[regime] = sum(scores) / len(scores)
            else:
                avg_scores[regime] = 0
        
        # Calculate regime durations
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
            'average_scores': avg_scores,
            'average_durations': avg_durations,
            'total_regimes_detected': len(self.regime_history)
        } 