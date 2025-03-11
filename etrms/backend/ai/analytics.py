"""
Performance analytics module for the AI Trading Assistant.

This module provides functionality for analyzing trading performance,
detecting behavioral biases, and generating improvement suggestions.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io
import base64

from ..analysis.regime import MarketRegime
from ..utils.logger import get_logger

logger = get_logger(__name__)


class BiasType(str, Enum):
    """Enum representing different types of trading biases."""
    LOSS_AVERSION = "loss_aversion"
    OVERCONFIDENCE = "overconfidence"
    RECENCY = "recency"
    CONFIRMATION = "confirmation"
    ANCHORING = "anchoring"
    DISPOSITION_EFFECT = "disposition_effect"
    HERDING = "herding"
    GAMBLER_FALLACY = "gambler_fallacy"
    HINDSIGHT = "hindsight"
    OUTCOME = "outcome"


class PerformanceMetric(str, Enum):
    """Enum representing different performance metrics."""
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"
    AVERAGE_WIN = "average_win"
    AVERAGE_LOSS = "average_loss"
    RISK_REWARD = "risk_reward"
    MAX_DRAWDOWN = "max_drawdown"
    SHARPE_RATIO = "sharpe_ratio"
    SORTINO_RATIO = "sortino_ratio"
    CALMAR_RATIO = "calmar_ratio"
    EXPECTANCY = "expectancy"
    RECOVERY_FACTOR = "recovery_factor"
    PROFIT_PER_DAY = "profit_per_day"
    AVERAGE_HOLDING_TIME = "average_holding_time"
    TRADE_FREQUENCY = "trade_frequency"


class PerformanceAnalyzer:
    """
    Analyzes trading performance and identifies improvement opportunities.
    
    This class provides methods to analyze trading history, detect behavioral biases,
    generate performance metrics, and provide improvement suggestions.
    """
    
    def __init__(
        self,
        min_trades_for_analysis: int = 20,
        lookback_periods: int = 100,
        bias_detection_threshold: float = 0.6,
        use_market_regime_analysis: bool = True
    ):
        """
        Initialize the PerformanceAnalyzer.
        
        Args:
            min_trades_for_analysis: Minimum number of trades required for meaningful analysis
            lookback_periods: Number of periods to look back for analysis
            bias_detection_threshold: Threshold for detecting biases (0.0-1.0)
            use_market_regime_analysis: Whether to analyze performance by market regime
        """
        self.min_trades_for_analysis = min_trades_for_analysis
        self.lookback_periods = lookback_periods
        self.bias_detection_threshold = bias_detection_threshold
        self.use_market_regime_analysis = use_market_regime_analysis
        self.logger = logger
        
        self.logger.info(
            f"Initialized PerformanceAnalyzer with min_trades_for_analysis={min_trades_for_analysis}, "
            f"lookback_periods={lookback_periods}, "
            f"bias_detection_threshold={bias_detection_threshold}, "
            f"use_market_regime_analysis={use_market_regime_analysis}"
        )
    
    def analyze_performance(
        self,
        trades: pd.DataFrame,
        market_regimes: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Analyze trading performance and generate comprehensive metrics.
        
        Args:
            trades: DataFrame with trade history
            market_regimes: Optional DataFrame with market regime data
            
        Returns:
            Dict with performance metrics and analysis
        """
        self.logger.info(f"Analyzing performance for {len(trades)} trades")
        
        # Check if we have enough trades for analysis
        if len(trades) < self.min_trades_for_analysis:
            self.logger.warning(
                f"Not enough trades for meaningful analysis. "
                f"Required: {self.min_trades_for_analysis}, Available: {len(trades)}"
            )
            return {
                "status": "insufficient_data",
                "message": f"Need at least {self.min_trades_for_analysis} trades for analysis",
                "trade_count": len(trades)
            }
        
        # Calculate overall performance metrics
        overall_metrics = self._calculate_performance_metrics(trades)
        
        # Detect behavioral biases
        biases = self._detect_biases(trades)
        
        # Analyze performance by market regime if available
        regime_performance = {}
        if self.use_market_regime_analysis and market_regimes is not None:
            regime_performance = self._analyze_by_market_regime(trades, market_regimes)
        
        # Analyze performance by time periods
        time_performance = self._analyze_by_time_period(trades)
        
        # Analyze performance by setup type if available
        setup_performance = {}
        if "setup_type" in trades.columns:
            setup_performance = self._analyze_by_setup_type(trades)
        
        # Generate improvement suggestions
        suggestions = self._generate_improvement_suggestions(
            overall_metrics, biases, regime_performance, time_performance, setup_performance
        )
        
        # Create performance charts
        charts = self._generate_performance_charts(trades)
        
        # Compile the complete analysis
        analysis = {
            "status": "success",
            "trade_count": len(trades),
            "overall_metrics": overall_metrics,
            "biases": biases,
            "regime_performance": regime_performance,
            "time_performance": time_performance,
            "setup_performance": setup_performance,
            "suggestions": suggestions,
            "charts": charts,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(f"Completed performance analysis with {len(suggestions)} improvement suggestions")
        
        return analysis
    
    def _calculate_performance_metrics(self, trades: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate comprehensive performance metrics from trade history.
        
        Args:
            trades: DataFrame with trade history
            
        Returns:
            Dict with performance metrics
        """
        # Placeholder implementation
        # In a real implementation, this would calculate various performance metrics
        # from the trade history, such as win rate, profit factor, etc.
        
        self.logger.debug("Calculating performance metrics")
        
        # For now, return dummy values
        metrics = {
            "win_rate": 0.65,
            "profit_factor": 1.8,
            "average_win": 2.5,
            "average_loss": 1.0,
            "risk_reward": 2.5,
            "max_drawdown": 5.0,
            "sharpe_ratio": 1.2,
            "sortino_ratio": 1.5,
            "calmar_ratio": 3.0,
            "expectancy": 0.975,
            "recovery_factor": 4.0,
            "profit_per_day": 0.5,
            "average_holding_time": 2.5,
            "trade_frequency": 3.0
        }
        
        return metrics
    
    def _detect_biases(self, trades: pd.DataFrame) -> Dict[str, float]:
        """
        Detect behavioral biases in trading history.
        
        Args:
            trades: DataFrame with trade history
            
        Returns:
            Dict with detected biases and their scores
        """
        # Placeholder implementation
        # In a real implementation, this would analyze the trade history
        # to detect various behavioral biases
        
        self.logger.debug("Detecting behavioral biases")
        
        # For now, return dummy values
        biases = {
            BiasType.LOSS_AVERSION.value: 0.7,
            BiasType.DISPOSITION_EFFECT.value: 0.6,
            BiasType.RECENCY.value: 0.5,
            BiasType.OVERCONFIDENCE.value: 0.3,
            BiasType.ANCHORING.value: 0.2
        }
        
        # Filter biases by threshold
        filtered_biases = {
            bias: score for bias, score in biases.items()
            if score >= self.bias_detection_threshold
        }
        
        return filtered_biases
    
    def _analyze_by_market_regime(
        self,
        trades: pd.DataFrame,
        market_regimes: pd.DataFrame
    ) -> Dict[str, Dict[str, float]]:
        """
        Analyze performance by market regime.
        
        Args:
            trades: DataFrame with trade history
            market_regimes: DataFrame with market regime data
            
        Returns:
            Dict with performance metrics by market regime
        """
        # Placeholder implementation
        # In a real implementation, this would join the trade data with
        # market regime data and calculate performance metrics for each regime
        
        self.logger.debug("Analyzing performance by market regime")
        
        # For now, return dummy values
        regime_performance = {
            MarketRegime.TRENDING.value: {
                "win_rate": 0.75,
                "profit_factor": 2.5,
                "average_win": 3.0,
                "average_loss": 1.0,
                "trade_count": 40
            },
            MarketRegime.RANGING.value: {
                "win_rate": 0.60,
                "profit_factor": 1.5,
                "average_win": 2.0,
                "average_loss": 1.0,
                "trade_count": 30
            },
            MarketRegime.VOLATILE.value: {
                "win_rate": 0.50,
                "profit_factor": 1.2,
                "average_win": 3.0,
                "average_loss": 1.5,
                "trade_count": 20
            }
        }
        
        return regime_performance
    
    def _analyze_by_time_period(
        self,
        trades: pd.DataFrame
    ) -> Dict[str, Dict[str, float]]:
        """
        Analyze performance by time period (daily, weekly, monthly).
        
        Args:
            trades: DataFrame with trade history
            
        Returns:
            Dict with performance metrics by time period
        """
        # Placeholder implementation
        # In a real implementation, this would group trades by time period
        # and calculate performance metrics for each period
        
        self.logger.debug("Analyzing performance by time period")
        
        # For now, return dummy values
        time_performance = {
            "daily": {
                "monday": {"win_rate": 0.7, "profit_factor": 2.0, "trade_count": 20},
                "tuesday": {"win_rate": 0.6, "profit_factor": 1.5, "trade_count": 15},
                "wednesday": {"win_rate": 0.65, "profit_factor": 1.8, "trade_count": 18},
                "thursday": {"win_rate": 0.7, "profit_factor": 2.1, "trade_count": 22},
                "friday": {"win_rate": 0.55, "profit_factor": 1.3, "trade_count": 25}
            },
            "session": {
                "asian": {"win_rate": 0.6, "profit_factor": 1.5, "trade_count": 30},
                "european": {"win_rate": 0.7, "profit_factor": 2.0, "trade_count": 40},
                "american": {"win_rate": 0.65, "profit_factor": 1.8, "trade_count": 35}
            },
            "monthly": {
                "january": {"win_rate": 0.7, "profit_factor": 2.0, "trade_count": 10},
                "february": {"win_rate": 0.6, "profit_factor": 1.5, "trade_count": 8},
                # ... other months
            }
        }
        
        return time_performance
    
    def _analyze_by_setup_type(
        self,
        trades: pd.DataFrame
    ) -> Dict[str, Dict[str, float]]:
        """
        Analyze performance by setup type.
        
        Args:
            trades: DataFrame with trade history
            
        Returns:
            Dict with performance metrics by setup type
        """
        # Placeholder implementation
        # In a real implementation, this would group trades by setup type
        # and calculate performance metrics for each setup type
        
        self.logger.debug("Analyzing performance by setup type")
        
        # For now, return dummy values
        setup_performance = {
            "trend_continuation": {
                "win_rate": 0.75,
                "profit_factor": 2.5,
                "average_win": 3.0,
                "average_loss": 1.0,
                "trade_count": 30
            },
            "breakout": {
                "win_rate": 0.60,
                "profit_factor": 1.8,
                "average_win": 2.5,
                "average_loss": 1.2,
                "trade_count": 25
            },
            "range_bounce": {
                "win_rate": 0.70,
                "profit_factor": 2.0,
                "average_win": 2.0,
                "average_loss": 1.0,
                "trade_count": 20
            }
        }
        
        return setup_performance
    
    def _generate_improvement_suggestions(
        self,
        overall_metrics: Dict[str, float],
        biases: Dict[str, float],
        regime_performance: Dict[str, Dict[str, float]],
        time_performance: Dict[str, Dict[str, Dict[str, float]]],
        setup_performance: Dict[str, Dict[str, float]]
    ) -> List[Dict[str, Any]]:
        """
        Generate improvement suggestions based on performance analysis.
        
        Args:
            overall_metrics: Overall performance metrics
            biases: Detected behavioral biases
            regime_performance: Performance metrics by market regime
            time_performance: Performance metrics by time period
            setup_performance: Performance metrics by setup type
            
        Returns:
            List of improvement suggestions
        """
        # Placeholder implementation
        # In a real implementation, this would analyze the performance metrics
        # and generate specific improvement suggestions
        
        self.logger.debug("Generating improvement suggestions")
        
        suggestions = []
        
        # Add suggestions based on biases
        for bias, score in biases.items():
            if bias == BiasType.LOSS_AVERSION.value:
                suggestions.append({
                    "category": "bias",
                    "type": bias,
                    "title": "Loss Aversion Detected",
                    "description": "You tend to cut winners too early and let losers run too long.",
                    "action": "Consider using automated take profit and stop loss orders to remove emotion from exits.",
                    "score": score,
                    "priority": "high" if score > 0.8 else "medium"
                })
            elif bias == BiasType.DISPOSITION_EFFECT.value:
                suggestions.append({
                    "category": "bias",
                    "type": bias,
                    "title": "Disposition Effect Detected",
                    "description": "You tend to sell winners too early and hold losers too long.",
                    "action": "Implement a rule-based exit strategy and stick to it regardless of emotions.",
                    "score": score,
                    "priority": "high" if score > 0.8 else "medium"
                })
        
        # Add suggestions based on regime performance
        if regime_performance:
            best_regime = max(
                regime_performance.items(),
                key=lambda x: x[1].get("profit_factor", 0)
            )[0]
            worst_regime = min(
                regime_performance.items(),
                key=lambda x: x[1].get("profit_factor", 0)
            )[0]
            
            suggestions.append({
                "category": "regime",
                "type": "regime_optimization",
                "title": f"Optimize for {best_regime} Markets",
                "description": f"Your performance is significantly better in {best_regime} markets.",
                "action": f"Consider increasing position size during {best_regime} market conditions.",
                "priority": "medium"
            })
            
            suggestions.append({
                "category": "regime",
                "type": "regime_caution",
                "title": f"Caution in {worst_regime} Markets",
                "description": f"Your performance is weaker in {worst_regime} markets.",
                "action": f"Consider reducing position size or avoiding trading during {worst_regime} market conditions.",
                "priority": "high"
            })
        
        # Add suggestions based on setup performance
        if setup_performance:
            best_setup = max(
                setup_performance.items(),
                key=lambda x: x[1].get("profit_factor", 0)
            )[0]
            worst_setup = min(
                setup_performance.items(),
                key=lambda x: x[1].get("profit_factor", 0)
            )[0]
            
            suggestions.append({
                "category": "setup",
                "type": "setup_focus",
                "title": f"Focus on {best_setup} Setups",
                "description": f"Your performance is significantly better with {best_setup} setups.",
                "action": f"Consider focusing more on {best_setup} setups and increasing position size for these trades.",
                "priority": "medium"
            })
            
            suggestions.append({
                "category": "setup",
                "type": "setup_improvement",
                "title": f"Improve {worst_setup} Setups",
                "description": f"Your performance is weaker with {worst_setup} setups.",
                "action": f"Consider additional training or avoiding {worst_setup} setups until your performance improves.",
                "priority": "medium"
            })
        
        # Add general improvement suggestions
        if overall_metrics.get("win_rate", 0) < 0.5:
            suggestions.append({
                "category": "general",
                "type": "win_rate",
                "title": "Improve Win Rate",
                "description": "Your overall win rate is below 50%.",
                "action": "Focus on improving entry criteria and consider using higher timeframes for confirmation.",
                "priority": "high"
            })
        
        if overall_metrics.get("risk_reward", 0) < 1.5:
            suggestions.append({
                "category": "general",
                "type": "risk_reward",
                "title": "Improve Risk-Reward Ratio",
                "description": "Your risk-reward ratio is below the recommended 1:1.5.",
                "action": "Consider setting wider take profit targets or tighter stop losses.",
                "priority": "high"
            })
        
        return suggestions
    
    def _generate_performance_charts(
        self,
        trades: pd.DataFrame
    ) -> Dict[str, str]:
        """
        Generate performance charts as base64-encoded images.
        
        Args:
            trades: DataFrame with trade history
            
        Returns:
            Dict with chart names and base64-encoded images
        """
        # Placeholder implementation
        # In a real implementation, this would generate various charts
        # using matplotlib or another charting library
        
        self.logger.debug("Generating performance charts")
        
        # For now, return empty dict
        # In a real implementation, this would create charts and encode them as base64
        return {}
    
    def get_bias_explanation(self, bias_type: str) -> Dict[str, str]:
        """
        Get detailed explanation and mitigation strategies for a specific bias.
        
        Args:
            bias_type: Type of bias to explain
            
        Returns:
            Dict with explanation and mitigation strategies
        """
        bias_explanations = {
            BiasType.LOSS_AVERSION.value: {
                "name": "Loss Aversion",
                "description": "The tendency to prefer avoiding losses over acquiring equivalent gains.",
                "impact": "Causes traders to cut winners too early and let losers run too long.",
                "mitigation": [
                    "Use predetermined take profit and stop loss levels",
                    "Implement a mechanical trading system",
                    "Keep a trading journal to track emotional decisions",
                    "Use position sizing rules to limit potential losses"
                ]
            },
            BiasType.OVERCONFIDENCE.value: {
                "name": "Overconfidence",
                "description": "The tendency to overestimate one's abilities and the precision of one's forecasts.",
                "impact": "Leads to excessive trading, taking on too much risk, and ignoring warning signs.",
                "mitigation": [
                    "Maintain a detailed trading journal with post-trade analysis",
                    "Set strict position sizing rules",
                    "Seek feedback from other traders",
                    "Regularly review and analyze losing trades"
                ]
            },
            BiasType.RECENCY.value: {
                "name": "Recency Bias",
                "description": "The tendency to place too much importance on recent events and ignore historical data.",
                "impact": "Causes traders to chase recent winners and avoid recent losers, regardless of edge.",
                "mitigation": [
                    "Maintain a long-term perspective",
                    "Review historical performance regularly",
                    "Use systematic backtesting to validate strategies",
                    "Avoid making decisions based solely on recent trades"
                ]
            },
            BiasType.CONFIRMATION.value: {
                "name": "Confirmation Bias",
                "description": "The tendency to search for and interpret information in a way that confirms one's preconceptions.",
                "impact": "Leads to ignoring contradictory information and reinforcing existing beliefs.",
                "mitigation": [
                    "Actively seek out contradictory information",
                    "Consider alternative scenarios",
                    "Use objective criteria for entries and exits",
                    "Have trading ideas reviewed by others"
                ]
            },
            BiasType.DISPOSITION_EFFECT.value: {
                "name": "Disposition Effect",
                "description": "The tendency to sell assets that have increased in value and hold assets that have decreased in value.",
                "impact": "Results in selling winners too early and holding losers too long.",
                "mitigation": [
                    "Use trailing stops for winning trades",
                    "Implement strict stop loss rules",
                    "Evaluate positions based on future potential, not past performance",
                    "Use a mechanical trading system to remove emotion"
                ]
            }
        }
        
        return bias_explanations.get(bias_type, {
            "name": "Unknown Bias",
            "description": "No information available for this bias type.",
            "impact": "Unknown",
            "mitigation": []
        })
    
    def analyze_trade_journal(
        self,
        journal_entries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze trading journal entries to identify patterns and improvement areas.
        
        Args:
            journal_entries: List of trading journal entries
            
        Returns:
            Dict with analysis results
        """
        # Placeholder implementation
        # In a real implementation, this would analyze journal entries
        # to identify patterns, emotions, and improvement areas
        
        self.logger.info(f"Analyzing {len(journal_entries)} journal entries")
        
        # For now, return dummy values
        return {
            "emotional_patterns": {
                "fear": 0.4,
                "greed": 0.3,
                "frustration": 0.2,
                "excitement": 0.5
            },
            "common_mistakes": [
                "Entering too early",
                "Moving stop loss",
                "Revenge trading"
            ],
            "improvement_areas": [
                "Patience during entry",
                "Discipline with stop losses",
                "Emotional control after losses"
            ],
            "positive_habits": [
                "Good pre-trade planning",
                "Consistent position sizing",
                "Regular review of trades"
            ]
        }
    
    def compare_performance_periods(
        self,
        period1_trades: pd.DataFrame,
        period2_trades: pd.DataFrame,
        period1_name: str = "Period 1",
        period2_name: str = "Period 2"
    ) -> Dict[str, Any]:
        """
        Compare trading performance between two time periods.
        
        Args:
            period1_trades: DataFrame with trades from first period
            period2_trades: DataFrame with trades from second period
            period1_name: Name of the first period
            period2_name: Name of the second period
            
        Returns:
            Dict with comparison results
        """
        # Placeholder implementation
        # In a real implementation, this would calculate performance metrics
        # for both periods and compare them
        
        self.logger.info(
            f"Comparing performance between {period1_name} ({len(period1_trades)} trades) "
            f"and {period2_name} ({len(period2_trades)} trades)"
        )
        
        # Calculate metrics for both periods
        period1_metrics = self._calculate_performance_metrics(period1_trades)
        period2_metrics = self._calculate_performance_metrics(period2_trades)
        
        # Calculate differences
        metric_diffs = {
            metric: period2_metrics.get(metric, 0) - period1_metrics.get(metric, 0)
            for metric in period1_metrics.keys()
        }
        
        # Determine improvements and declines
        improvements = {
            metric: diff for metric, diff in metric_diffs.items() if diff > 0
        }
        declines = {
            metric: diff for metric, diff in metric_diffs.items() if diff < 0
        }
        
        # Generate insights
        insights = []
        if improvements:
            top_improvement = max(improvements.items(), key=lambda x: abs(x[1]))[0]
            insights.append(f"Biggest improvement in {top_improvement}")
        
        if declines:
            top_decline = max(declines.items(), key=lambda x: abs(x[1]))[0]
            insights.append(f"Biggest decline in {top_decline}")
        
        return {
            "period1": {
                "name": period1_name,
                "metrics": period1_metrics,
                "trade_count": len(period1_trades)
            },
            "period2": {
                "name": period2_name,
                "metrics": period2_metrics,
                "trade_count": len(period2_trades)
            },
            "differences": metric_diffs,
            "improvements": improvements,
            "declines": declines,
            "insights": insights
        } 