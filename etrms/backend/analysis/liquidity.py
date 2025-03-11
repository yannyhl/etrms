"""
Enhanced Trading Risk Management System - Liquidity Analysis

This module provides functionality to analyze market liquidity and order book depth,
which is useful for optimizing entry/exit timing and estimating slippage.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum

from utils.logger import get_logger, log_event


class LiquidityMetric(str, Enum):
    """Enum representing different liquidity metrics"""
    SPREAD = "spread"
    DEPTH = "depth"
    VOLUME = "volume"
    AMIHUD = "amihud"
    KYLE_LAMBDA = "kyle_lambda"
    FLOW_TOXICITY = "flow_toxicity"


class LiquidityAnalyzer:
    """
    Class for analyzing market liquidity and order book depth.
    
    This class provides methods to:
    - Calculate various liquidity metrics
    - Analyze order book depth
    - Estimate slippage for different order sizes
    - Detect liquidity anomalies
    """
    
    def __init__(
        self,
        lookback_periods: int = 20,
        depth_levels: int = 10,
        volume_window: int = 5,
        low_liquidity_threshold: float = 0.3,
        high_liquidity_threshold: float = 0.7
    ):
        """
        Initialize the LiquidityAnalyzer.
        
        Args:
            lookback_periods: Number of periods to look back for calculations
            depth_levels: Number of order book levels to analyze
            volume_window: Window size for volume-based calculations
            low_liquidity_threshold: Threshold for low liquidity
            high_liquidity_threshold: Threshold for high liquidity
        """
        self.lookback_periods = lookback_periods
        self.depth_levels = depth_levels
        self.volume_window = volume_window
        self.low_liquidity_threshold = low_liquidity_threshold
        self.high_liquidity_threshold = high_liquidity_threshold
        self.logger = get_logger(__name__)
        
        log_event(
            self.logger,
            "LIQUIDITY_ANALYZER_INIT",
            "Liquidity analyzer initialized",
            context={
                "lookback_periods": lookback_periods,
                "depth_levels": depth_levels,
                "volume_window": volume_window
            }
        )
    
    def calculate_spread(self, orderbook_data: Dict[str, Any]) -> float:
        """
        Calculate the bid-ask spread from orderbook data.
        
        Args:
            orderbook_data: Dictionary containing orderbook data with 'bids' and 'asks'
            
        Returns:
            Bid-ask spread as a percentage of mid price
        """
        if not orderbook_data or 'bids' not in orderbook_data or 'asks' not in orderbook_data:
            log_event(
                self.logger,
                "INVALID_ORDERBOOK_DATA",
                "Invalid orderbook data for spread calculation",
                context={"orderbook_data_keys": list(orderbook_data.keys()) if orderbook_data else None}
            )
            return float('nan')
        
        bids = orderbook_data['bids']
        asks = orderbook_data['asks']
        
        if not bids or not asks:
            return float('nan')
        
        # Get best bid and ask
        best_bid = float(bids[0][0]) if isinstance(bids[0], list) else float(bids[0]['price'])
        best_ask = float(asks[0][0]) if isinstance(asks[0], list) else float(asks[0]['price'])
        
        # Calculate mid price
        mid_price = (best_bid + best_ask) / 2
        
        # Calculate spread as percentage of mid price
        spread_pct = (best_ask - best_bid) / mid_price * 100
        
        return spread_pct
    
    def calculate_order_book_depth(
        self,
        orderbook_data: Dict[str, Any],
        price_range_pct: float = 1.0
    ) -> Dict[str, float]:
        """
        Calculate the order book depth within a given price range.
        
        Args:
            orderbook_data: Dictionary containing orderbook data with 'bids' and 'asks'
            price_range_pct: Price range as percentage of mid price
            
        Returns:
            Dictionary with bid depth, ask depth, and total depth
        """
        if not orderbook_data or 'bids' not in orderbook_data or 'asks' not in orderbook_data:
            log_event(
                self.logger,
                "INVALID_ORDERBOOK_DATA",
                "Invalid orderbook data for depth calculation",
                context={"orderbook_data_keys": list(orderbook_data.keys()) if orderbook_data else None}
            )
            return {'bid_depth': 0.0, 'ask_depth': 0.0, 'total_depth': 0.0}
        
        bids = orderbook_data['bids']
        asks = orderbook_data['asks']
        
        if not bids or not asks:
            return {'bid_depth': 0.0, 'ask_depth': 0.0, 'total_depth': 0.0}
        
        # Get best bid and ask
        best_bid = float(bids[0][0]) if isinstance(bids[0], list) else float(bids[0]['price'])
        best_ask = float(asks[0][0]) if isinstance(asks[0], list) else float(asks[0]['price'])
        
        # Calculate mid price
        mid_price = (best_bid + best_ask) / 2
        
        # Calculate price range
        price_range = mid_price * price_range_pct / 100
        lower_bound = mid_price - price_range
        upper_bound = mid_price + price_range
        
        # Calculate depth
        bid_depth = 0.0
        for bid in bids:
            price = float(bid[0]) if isinstance(bid, list) else float(bid['price'])
            quantity = float(bid[1]) if isinstance(bid, list) else float(bid['quantity'])
            
            if price >= lower_bound:
                bid_depth += price * quantity
        
        ask_depth = 0.0
        for ask in asks:
            price = float(ask[0]) if isinstance(ask, list) else float(ask['price'])
            quantity = float(ask[1]) if isinstance(ask, list) else float(ask['quantity'])
            
            if price <= upper_bound:
                ask_depth += price * quantity
        
        total_depth = bid_depth + ask_depth
        
        return {
            'bid_depth': bid_depth,
            'ask_depth': ask_depth,
            'total_depth': total_depth
        }
    
    def calculate_depth_imbalance(self, orderbook_data: Dict[str, Any]) -> float:
        """
        Calculate the order book depth imbalance.
        
        Args:
            orderbook_data: Dictionary containing orderbook data with 'bids' and 'asks'
            
        Returns:
            Depth imbalance (-1 to 1, negative means more bids, positive means more asks)
        """
        depth = self.calculate_order_book_depth(orderbook_data)
        
        bid_depth = depth['bid_depth']
        ask_depth = depth['ask_depth']
        total_depth = depth['total_depth']
        
        if total_depth == 0:
            return 0.0
        
        # Calculate imbalance (-1 to 1)
        imbalance = (ask_depth - bid_depth) / total_depth
        
        return imbalance
    
    def estimate_slippage(
        self,
        orderbook_data: Dict[str, Any],
        order_size: float,
        side: str = 'buy'
    ) -> Dict[str, float]:
        """
        Estimate slippage for a given order size.
        
        Args:
            orderbook_data: Dictionary containing orderbook data with 'bids' and 'asks'
            order_size: Order size in base currency
            side: Order side ('buy' or 'sell')
            
        Returns:
            Dictionary with estimated slippage metrics
        """
        if not orderbook_data or 'bids' not in orderbook_data or 'asks' not in orderbook_data:
            log_event(
                self.logger,
                "INVALID_ORDERBOOK_DATA",
                "Invalid orderbook data for slippage estimation",
                context={"orderbook_data_keys": list(orderbook_data.keys()) if orderbook_data else None}
            )
            return {
                'slippage_pct': float('nan'),
                'avg_execution_price': float('nan'),
                'market_impact': float('nan')
            }
        
        bids = orderbook_data['bids']
        asks = orderbook_data['asks']
        
        if not bids or not asks:
            return {
                'slippage_pct': float('nan'),
                'avg_execution_price': float('nan'),
                'market_impact': float('nan')
            }
        
        # Get best bid and ask
        best_bid = float(bids[0][0]) if isinstance(bids[0], list) else float(bids[0]['price'])
        best_ask = float(asks[0][0]) if isinstance(asks[0], list) else float(asks[0]['price'])
        
        # Calculate mid price
        mid_price = (best_bid + best_ask) / 2
        
        # Determine which side of the book to use
        book_side = asks if side.lower() == 'buy' else bids
        reference_price = best_ask if side.lower() == 'buy' else best_bid
        
        # Calculate average execution price
        remaining_size = order_size
        total_cost = 0.0
        
        for level in book_side:
            price = float(level[0]) if isinstance(level, list) else float(level['price'])
            quantity = float(level[1]) if isinstance(level, list) else float(level['quantity'])
            
            if remaining_size <= quantity:
                total_cost += remaining_size * price
                remaining_size = 0
                break
            else:
                total_cost += quantity * price
                remaining_size -= quantity
        
        # If order size exceeds available liquidity
        if remaining_size > 0:
            log_event(
                self.logger,
                "INSUFFICIENT_LIQUIDITY",
                "Order size exceeds available liquidity",
                context={
                    "order_size": order_size,
                    "unfilled_size": remaining_size,
                    "side": side
                }
            )
            # Use the last price for the remaining size
            last_price = float(book_side[-1][0]) if isinstance(book_side[-1], list) else float(book_side[-1]['price'])
            total_cost += remaining_size * last_price
        
        # Calculate average execution price
        avg_execution_price = total_cost / order_size
        
        # Calculate slippage
        if side.lower() == 'buy':
            slippage_pct = (avg_execution_price - reference_price) / reference_price * 100
        else:
            slippage_pct = (reference_price - avg_execution_price) / reference_price * 100
        
        # Calculate market impact
        market_impact = (avg_execution_price - mid_price) / mid_price * 100
        
        return {
            'slippage_pct': slippage_pct,
            'avg_execution_price': avg_execution_price,
            'market_impact': market_impact
        }
    
    def calculate_amihud_illiquidity(
        self,
        price_data: pd.DataFrame,
        volume_data: pd.DataFrame,
        window: Optional[int] = None
    ) -> float:
        """
        Calculate Amihud's illiquidity measure.
        
        Amihud's measure is defined as the average ratio of absolute returns to trading volume.
        Higher values indicate lower liquidity.
        
        Args:
            price_data: DataFrame with price data
            volume_data: DataFrame with volume data
            window: Window size for calculation (defaults to lookback_periods)
            
        Returns:
            Amihud's illiquidity measure
        """
        window = window or self.lookback_periods
        
        if len(price_data) < 2 or len(volume_data) < 2:
            log_event(
                self.logger,
                "INSUFFICIENT_DATA",
                "Insufficient data for Amihud illiquidity calculation",
                context={
                    "price_data_length": len(price_data),
                    "volume_data_length": len(volume_data),
                    "required": 2
                }
            )
            return float('nan')
        
        # Calculate returns
        close_prices = price_data['close'].values
        returns = np.diff(np.log(close_prices))
        
        # Get volumes
        volumes = volume_data['volume'].values[1:]  # Align with returns
        
        # Ensure data lengths match
        min_length = min(len(returns), len(volumes))
        returns = returns[-min_length:]
        volumes = volumes[-min_length:]
        
        # Use only the last 'window' data points
        if len(returns) > window:
            returns = returns[-window:]
            volumes = volumes[-window:]
        
        # Calculate Amihud measure
        # Avoid division by zero
        valid_indices = volumes > 0
        if not np.any(valid_indices):
            return float('nan')
        
        amihud_values = np.abs(returns[valid_indices]) / volumes[valid_indices]
        amihud = np.mean(amihud_values) * 1e6  # Scale for readability
        
        return amihud
    
    def calculate_kyle_lambda(
        self,
        price_data: pd.DataFrame,
        volume_data: pd.DataFrame,
        window: Optional[int] = None
    ) -> float:
        """
        Calculate Kyle's lambda (price impact coefficient).
        
        Kyle's lambda measures the price impact per unit of order flow.
        Higher values indicate lower liquidity.
        
        Args:
            price_data: DataFrame with price data
            volume_data: DataFrame with volume data
            window: Window size for calculation (defaults to lookback_periods)
            
        Returns:
            Kyle's lambda
        """
        window = window or self.lookback_periods
        
        if len(price_data) < 2 or len(volume_data) < 2:
            log_event(
                self.logger,
                "INSUFFICIENT_DATA",
                "Insufficient data for Kyle's lambda calculation",
                context={
                    "price_data_length": len(price_data),
                    "volume_data_length": len(volume_data),
                    "required": 2
                }
            )
            return float('nan')
        
        # Calculate price changes
        close_prices = price_data['close'].values
        price_changes = np.diff(close_prices)
        
        # Get volumes
        volumes = volume_data['volume'].values[1:]  # Align with price changes
        
        # Ensure data lengths match
        min_length = min(len(price_changes), len(volumes))
        price_changes = price_changes[-min_length:]
        volumes = volumes[-min_length:]
        
        # Use only the last 'window' data points
        if len(price_changes) > window:
            price_changes = price_changes[-window:]
            volumes = volumes[-window:]
        
        # Calculate Kyle's lambda using regression
        try:
            # Reshape for regression
            X = volumes.reshape(-1, 1)
            y = price_changes
            
            # Add constant term
            X = np.hstack([np.ones((X.shape[0], 1)), X])
            
            # Solve for coefficients
            beta = np.linalg.lstsq(X, y, rcond=None)[0]
            
            # Kyle's lambda is the slope coefficient
            kyle_lambda = beta[1]
            
            return kyle_lambda
        
        except np.linalg.LinAlgError:
            log_event(
                self.logger,
                "CALCULATION_ERROR",
                "Error calculating Kyle's lambda",
                context={"error": "Linear algebra error"}
            )
            return float('nan')
    
    def calculate_volume_profile(
        self,
        price_data: pd.DataFrame,
        volume_data: pd.DataFrame,
        num_bins: int = 10
    ) -> Dict[str, List[float]]:
        """
        Calculate volume profile (volume by price level).
        
        Args:
            price_data: DataFrame with price data
            volume_data: DataFrame with volume data
            num_bins: Number of price bins
            
        Returns:
            Dictionary with price levels and corresponding volumes
        """
        if len(price_data) < 2 or len(volume_data) < 2:
            log_event(
                self.logger,
                "INSUFFICIENT_DATA",
                "Insufficient data for volume profile calculation",
                context={
                    "price_data_length": len(price_data),
                    "volume_data_length": len(volume_data),
                    "required": 2
                }
            )
            return {'price_levels': [], 'volumes': []}
        
        # Extract high, low, close prices and volumes
        high_prices = price_data['high'].values
        low_prices = price_data['low'].values
        close_prices = price_data['close'].values
        volumes = volume_data['volume'].values
        
        # Ensure data lengths match
        min_length = min(len(high_prices), len(low_prices), len(close_prices), len(volumes))
        high_prices = high_prices[-min_length:]
        low_prices = low_prices[-min_length:]
        close_prices = close_prices[-min_length:]
        volumes = volumes[-min_length:]
        
        # Define price range
        min_price = np.min(low_prices)
        max_price = np.max(high_prices)
        
        if min_price == max_price:
            return {'price_levels': [float(min_price)], 'volumes': [float(np.sum(volumes))]}
        
        # Create price bins
        price_bins = np.linspace(min_price, max_price, num_bins + 1)
        bin_centers = (price_bins[:-1] + price_bins[1:]) / 2
        
        # Initialize volume profile
        volume_profile = np.zeros(num_bins)
        
        # Distribute volume across price range for each candle
        for i in range(min_length):
            # Skip if volume is zero
            if volumes[i] == 0:
                continue
            
            # Determine which bins this candle spans
            candle_min = low_prices[i]
            candle_max = high_prices[i]
            
            # Find bins that overlap with this candle
            bin_indices = np.where((bin_centers >= candle_min) & (bin_centers <= candle_max))[0]
            
            if len(bin_indices) > 0:
                # Distribute volume equally across the bins
                volume_per_bin = volumes[i] / len(bin_indices)
                volume_profile[bin_indices] += volume_per_bin
        
        return {
            'price_levels': bin_centers.tolist(),
            'volumes': volume_profile.tolist()
        }
    
    def detect_liquidity_anomalies(
        self,
        orderbook_data: Dict[str, Any],
        threshold: float = 2.0
    ) -> Dict[str, Any]:
        """
        Detect anomalies in the order book that might indicate manipulation or unusual activity.
        
        Args:
            orderbook_data: Dictionary containing orderbook data with 'bids' and 'asks'
            threshold: Threshold for anomaly detection (standard deviations)
            
        Returns:
            Dictionary with detected anomalies
        """
        if not orderbook_data or 'bids' not in orderbook_data or 'asks' not in orderbook_data:
            log_event(
                self.logger,
                "INVALID_ORDERBOOK_DATA",
                "Invalid orderbook data for anomaly detection",
                context={"orderbook_data_keys": list(orderbook_data.keys()) if orderbook_data else None}
            )
            return {'anomalies': []}
        
        bids = orderbook_data['bids']
        asks = orderbook_data['asks']
        
        if not bids or not asks:
            return {'anomalies': []}
        
        anomalies = []
        
        # Extract bid and ask prices and quantities
        bid_prices = np.array([float(bid[0]) if isinstance(bid, list) else float(bid['price']) for bid in bids])
        bid_quantities = np.array([float(bid[1]) if isinstance(bid, list) else float(bid['quantity']) for bid in bids])
        
        ask_prices = np.array([float(ask[0]) if isinstance(ask, list) else float(ask['price']) for ask in asks])
        ask_quantities = np.array([float(ask[1]) if isinstance(ask, list) else float(ask['quantity']) for ask in asks])
        
        # Check for large gaps in the order book
        if len(bid_prices) > 1:
            bid_price_diffs = np.diff(bid_prices)
            mean_bid_diff = np.mean(bid_price_diffs)
            std_bid_diff = np.std(bid_price_diffs)
            
            if std_bid_diff > 0:
                large_bid_gaps = np.where(bid_price_diffs > mean_bid_diff + threshold * std_bid_diff)[0]
                
                for gap_idx in large_bid_gaps:
                    anomalies.append({
                        'type': 'large_bid_gap',
                        'index': int(gap_idx),
                        'price_level_1': float(bid_prices[gap_idx]),
                        'price_level_2': float(bid_prices[gap_idx + 1]),
                        'gap_size': float(bid_price_diffs[gap_idx]),
                        'threshold': float(mean_bid_diff + threshold * std_bid_diff)
                    })
        
        if len(ask_prices) > 1:
            ask_price_diffs = np.diff(ask_prices)
            mean_ask_diff = np.mean(ask_price_diffs)
            std_ask_diff = np.std(ask_price_diffs)
            
            if std_ask_diff > 0:
                large_ask_gaps = np.where(ask_price_diffs > mean_ask_diff + threshold * std_ask_diff)[0]
                
                for gap_idx in large_ask_gaps:
                    anomalies.append({
                        'type': 'large_ask_gap',
                        'index': int(gap_idx),
                        'price_level_1': float(ask_prices[gap_idx]),
                        'price_level_2': float(ask_prices[gap_idx + 1]),
                        'gap_size': float(ask_price_diffs[gap_idx]),
                        'threshold': float(mean_ask_diff + threshold * std_ask_diff)
                    })
        
        # Check for unusually large orders
        if len(bid_quantities) > 0:
            mean_bid_qty = np.mean(bid_quantities)
            std_bid_qty = np.std(bid_quantities)
            
            if std_bid_qty > 0:
                large_bid_orders = np.where(bid_quantities > mean_bid_qty + threshold * std_bid_qty)[0]
                
                for order_idx in large_bid_orders:
                    anomalies.append({
                        'type': 'large_bid_order',
                        'index': int(order_idx),
                        'price': float(bid_prices[order_idx]),
                        'quantity': float(bid_quantities[order_idx]),
                        'threshold': float(mean_bid_qty + threshold * std_bid_qty)
                    })
        
        if len(ask_quantities) > 0:
            mean_ask_qty = np.mean(ask_quantities)
            std_ask_qty = np.std(ask_quantities)
            
            if std_ask_qty > 0:
                large_ask_orders = np.where(ask_quantities > mean_ask_qty + threshold * std_ask_qty)[0]
                
                for order_idx in large_ask_orders:
                    anomalies.append({
                        'type': 'large_ask_order',
                        'index': int(order_idx),
                        'price': float(ask_prices[order_idx]),
                        'quantity': float(ask_quantities[order_idx]),
                        'threshold': float(mean_ask_qty + threshold * std_ask_qty)
                    })
        
        # Check for spoofing patterns (large orders far from the mid price)
        best_bid = bid_prices[0]
        best_ask = ask_prices[0]
        mid_price = (best_bid + best_ask) / 2
        
        # Define "far from mid price" as a percentage
        far_threshold_pct = 0.05  # 5% from mid price
        
        far_bids = np.where(bid_prices < mid_price * (1 - far_threshold_pct))[0]
        far_asks = np.where(ask_prices > mid_price * (1 + far_threshold_pct))[0]
        
        # Check for large orders among the far orders
        for idx in far_bids:
            if bid_quantities[idx] > mean_bid_qty + threshold * std_bid_qty:
                anomalies.append({
                    'type': 'potential_spoof_bid',
                    'index': int(idx),
                    'price': float(bid_prices[idx]),
                    'quantity': float(bid_quantities[idx]),
                    'distance_from_mid': float((mid_price - bid_prices[idx]) / mid_price * 100)
                })
        
        for idx in far_asks:
            if ask_quantities[idx] > mean_ask_qty + threshold * std_ask_qty:
                anomalies.append({
                    'type': 'potential_spoof_ask',
                    'index': int(idx),
                    'price': float(ask_prices[idx]),
                    'quantity': float(ask_quantities[idx]),
                    'distance_from_mid': float((ask_prices[idx] - mid_price) / mid_price * 100)
                })
        
        return {'anomalies': anomalies}
    
    def calculate_liquidity_score(
        self,
        orderbook_data: Dict[str, Any],
        price_data: Optional[pd.DataFrame] = None,
        volume_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, float]:
        """
        Calculate an overall liquidity score based on multiple metrics.
        
        Args:
            orderbook_data: Dictionary containing orderbook data with 'bids' and 'asks'
            price_data: Optional DataFrame with price data
            volume_data: Optional DataFrame with volume data
            
        Returns:
            Dictionary with liquidity metrics and overall score
        """
        metrics = {}
        
        # Calculate spread
        spread = self.calculate_spread(orderbook_data)
        if not np.isnan(spread):
            # Normalize: lower spread is better
            spread_score = max(0, min(1, 1 - spread / 5))  # Assume 5% spread is very bad
            metrics['spread_score'] = spread_score
        
        # Calculate depth
        depth = self.calculate_order_book_depth(orderbook_data)
        total_depth = depth['total_depth']
        
        # Normalize depth: higher is better
        # This is very market-dependent, so we use a simple approach
        if total_depth > 0:
            depth_score = min(1, total_depth / 1000000)  # Arbitrary scale
            metrics['depth_score'] = depth_score
        
        # Calculate imbalance: closer to 0 is better
        imbalance = self.calculate_depth_imbalance(orderbook_data)
        imbalance_score = max(0, min(1, 1 - abs(imbalance)))
        metrics['imbalance_score'] = imbalance_score
        
        # Calculate additional metrics if price and volume data are provided
        if price_data is not None and volume_data is not None and len(price_data) > 0 and len(volume_data) > 0:
            # Amihud illiquidity: lower is better
            amihud = self.calculate_amihud_illiquidity(price_data, volume_data)
            if not np.isnan(amihud):
                amihud_score = max(0, min(1, 1 - amihud / 10))  # Arbitrary scale
                metrics['amihud_score'] = amihud_score
            
            # Kyle's lambda: lower is better
            kyle = self.calculate_kyle_lambda(price_data, volume_data)
            if not np.isnan(kyle) and kyle > 0:
                kyle_score = max(0, min(1, 1 - kyle / 0.1))  # Arbitrary scale
                metrics['kyle_score'] = kyle_score
        
        # Calculate overall score as weighted average
        weights = {
            'spread_score': 0.3,
            'depth_score': 0.3,
            'imbalance_score': 0.1,
            'amihud_score': 0.15,
            'kyle_score': 0.15
        }
        
        total_weight = 0
        weighted_sum = 0
        
        for metric, score in metrics.items():
            if metric in weights:
                weighted_sum += score * weights[metric]
                total_weight += weights[metric]
        
        if total_weight > 0:
            overall_score = weighted_sum / total_weight
        else:
            overall_score = 0.5  # Default if no metrics available
        
        # Add overall score to metrics
        metrics['overall_score'] = overall_score
        
        # Classify liquidity
        if overall_score > self.high_liquidity_threshold:
            metrics['liquidity_class'] = 'high'
        elif overall_score < self.low_liquidity_threshold:
            metrics['liquidity_class'] = 'low'
        else:
            metrics['liquidity_class'] = 'medium'
        
        return metrics 


class LiquidityRegimeDetector:
    """
    Class for detecting changes in liquidity regimes over time.
    
    This class tracks liquidity regime changes and provides methods to analyze
    their impact on trading performance.
    """
    
    def __init__(
        self,
        liquidity_analyzer: LiquidityAnalyzer,
        high_threshold: float = 0.7,
        low_threshold: float = 0.3
    ):
        """
        Initialize the LiquidityRegimeDetector.
        
        Args:
            liquidity_analyzer: LiquidityAnalyzer instance
            high_threshold: Threshold for high liquidity regime
            low_threshold: Threshold for low liquidity regime
        """
        self.liquidity_analyzer = liquidity_analyzer
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold
        self.regime_history = []
        self.logger = get_logger(__name__)
    
    def detect_regime(
        self,
        orderbook_data: Dict[str, Any],
        price_data: Optional[pd.DataFrame] = None,
        volume_data: Optional[pd.DataFrame] = None
    ) -> str:
        """
        Detect the current liquidity regime.
        
        Args:
            orderbook_data: Dictionary containing orderbook data with 'bids' and 'asks'
            price_data: Optional DataFrame with price data
            volume_data: Optional DataFrame with volume data
            
        Returns:
            Liquidity regime ('high', 'medium', or 'low')
        """
        # Calculate liquidity score
        liquidity_metrics = self.liquidity_analyzer.calculate_liquidity_score(
            orderbook_data, price_data, volume_data
        )
        
        # Get liquidity class
        liquidity_class = liquidity_metrics.get('liquidity_class', 'medium')
        
        return liquidity_class
    
    def update(
        self,
        orderbook_data: Dict[str, Any],
        price_data: Optional[pd.DataFrame] = None,
        volume_data: Optional[pd.DataFrame] = None,
        timestamp: Optional[datetime] = None
    ) -> Tuple[str, bool]:
        """
        Update the liquidity regime history.
        
        Args:
            orderbook_data: Dictionary containing orderbook data with 'bids' and 'asks'
            price_data: Optional DataFrame with price data
            volume_data: Optional DataFrame with volume data
            timestamp: Optional timestamp for the update (defaults to current time)
            
        Returns:
            Tuple of (current_regime, regime_changed)
        """
        # Detect regime
        current_regime = self.detect_regime(orderbook_data, price_data, volume_data)
        current_time = timestamp or datetime.utcnow()
        
        # Calculate liquidity metrics
        liquidity_metrics = self.liquidity_analyzer.calculate_liquidity_score(
            orderbook_data, price_data, volume_data
        )
        
        # Check if regime has changed
        regime_changed = False
        if self.regime_history and self.regime_history[-1]['regime'] != current_regime:
            regime_changed = True
            
            log_event(
                self.logger,
                "LIQUIDITY_REGIME_CHANGE",
                f"Liquidity regime changed from {self.regime_history[-1]['regime']} to {current_regime}",
                context={
                    "previous_regime": self.regime_history[-1]['regime'],
                    "new_regime": current_regime,
                    "liquidity_score": liquidity_metrics.get('overall_score', 0),
                    "previous_time": self.regime_history[-1]['timestamp'].isoformat(),
                    "current_time": current_time.isoformat()
                }
            )
        
        # Add to history
        self.regime_history.append({
            'timestamp': current_time,
            'regime': current_regime,
            'liquidity_score': liquidity_metrics.get('overall_score', 0),
            'metrics': liquidity_metrics
        })
        
        return current_regime, regime_changed
    
    def get_current_regime(self) -> Optional[str]:
        """
        Get the current liquidity regime.
        
        Returns:
            Current liquidity regime or None if no history
        """
        if not self.regime_history:
            return None
        
        return self.regime_history[-1]['regime']
    
    def get_regime_duration(self) -> Optional[timedelta]:
        """
        Get the duration of the current liquidity regime.
        
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
        Get statistics about liquidity regime occurrences and durations.
        
        Returns:
            Dictionary with regime statistics
        """
        if not self.regime_history:
            return {}
        
        # Count occurrences of each regime
        regime_counts = {
            "high": 0,
            "medium": 0,
            "low": 0
        }
        
        for entry in self.regime_history:
            regime_counts[entry['regime']] += 1
        
        # Calculate average liquidity score for each regime
        regime_scores = {
            "high": [],
            "medium": [],
            "low": []
        }
        
        for entry in self.regime_history:
            if 'liquidity_score' in entry:
                regime_scores[entry['regime']].append(entry['liquidity_score'])
        
        avg_scores = {}
        for regime, scores in regime_scores.items():
            if scores:
                avg_scores[regime] = sum(scores) / len(scores)
            else:
                avg_scores[regime] = 0
        
        # Calculate regime durations
        regime_durations = {
            "high": [],
            "medium": [],
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
    
    def get_trading_recommendations(self) -> Dict[str, Any]:
        """
        Get trading recommendations based on the current liquidity regime.
        
        Returns:
            Dictionary with trading recommendations
        """
        current_regime = self.get_current_regime()
        if not current_regime:
            return {
                'regime': 'unknown',
                'position_size': 'normal',
                'slippage_expectation': 'normal',
                'order_type': 'limit',
                'notes': 'Insufficient data for recommendations'
            }
        
        # Get the most recent liquidity metrics
        recent_metrics = self.regime_history[-1].get('metrics', {})
        
        recommendations = {
            'regime': current_regime,
            'position_size': 'normal',
            'slippage_expectation': 'normal',
            'order_type': 'limit',
            'notes': []
        }
        
        # Adjust recommendations based on regime
        if current_regime == 'high':
            recommendations['position_size'] = 'large'
            recommendations['slippage_expectation'] = 'low'
            recommendations['order_type'] = 'market or limit'
            recommendations['notes'].append('High liquidity environment - larger positions can be executed with minimal market impact')
        
        elif current_regime == 'low':
            recommendations['position_size'] = 'small'
            recommendations['slippage_expectation'] = 'high'
            recommendations['order_type'] = 'limit only'
            recommendations['notes'].append('Low liquidity environment - reduce position sizes and use limit orders to minimize slippage')
            
            # Check for specific issues
            if recent_metrics.get('spread_score', 1) < 0.3:
                recommendations['notes'].append('Wide spreads detected - consider passive limit orders')
            
            if recent_metrics.get('depth_score', 1) < 0.3:
                recommendations['notes'].append('Shallow order book - high risk of slippage for larger orders')
        
        else:  # medium
            recommendations['notes'].append('Normal liquidity conditions - standard position sizing appropriate')
        
        # Check for imbalance
        imbalance_score = recent_metrics.get('imbalance_score', 0.5)
        if imbalance_score < 0.3:
            recommendations['notes'].append('Significant order book imbalance detected - potential price movement incoming')
        
        return recommendations 