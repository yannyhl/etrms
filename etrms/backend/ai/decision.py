"""
Decision support module for the AI Trading Assistant.

This module provides functionality for supporting trading decisions,
including risk assessment, scenario modeling, and trade validation.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from ..analysis.regime import MarketRegime
from ..utils.logger import get_logger
from .detection import SetupType
from .recommendation import StrategyType, OrderType, PositionSizing

logger = get_logger(__name__)


class ChecklistCategory(str, Enum):
    """Enum representing different categories of checklist items."""
    SETUP_QUALITY = "setup_quality"
    MARKET_CONDITION = "market_condition"
    RISK_MANAGEMENT = "risk_management"
    ENTRY_TIMING = "entry_timing"
    EXIT_STRATEGY = "exit_strategy"
    POSITION_SIZING = "position_sizing"
    PORTFOLIO_CONTEXT = "portfolio_context"
    PSYCHOLOGICAL = "psychological"


class ScenarioType(str, Enum):
    """Enum representing different types of scenarios."""
    BEST_CASE = "best_case"
    WORST_CASE = "worst_case"
    EXPECTED_CASE = "expected_case"
    BREAKEVEN_CASE = "breakeven_case"
    EARLY_EXIT = "early_exit"
    PARTIAL_EXIT = "partial_exit"
    TRAILING_STOP = "trailing_stop"
    CUSTOM = "custom"


class DecisionSupport:
    """
    Provides decision support for trading decisions.
    
    This class offers tools for risk assessment, scenario modeling,
    trade validation, and post-trade analysis to support trading decisions.
    """
    
    def __init__(
        self,
        default_risk_percent: float = 1.0,
        min_setup_quality: float = 0.6,
        min_risk_reward: float = 1.5,
        use_market_regime: bool = True,
        use_portfolio_context: bool = True
    ):
        """
        Initialize the DecisionSupport.
        
        Args:
            default_risk_percent: Default risk percentage per trade
            min_setup_quality: Minimum setup quality to consider valid
            min_risk_reward: Minimum risk-reward ratio to consider valid
            use_market_regime: Whether to consider market regime in decision support
            use_portfolio_context: Whether to consider portfolio context in decision support
        """
        self.default_risk_percent = default_risk_percent
        self.min_setup_quality = min_setup_quality
        self.min_risk_reward = min_risk_reward
        self.use_market_regime = use_market_regime
        self.use_portfolio_context = use_portfolio_context
        self.logger = logger
        
        self.logger.info(
            f"Initialized DecisionSupport with default_risk_percent={default_risk_percent}, "
            f"min_setup_quality={min_setup_quality}, min_risk_reward={min_risk_reward}, "
            f"use_market_regime={use_market_regime}, use_portfolio_context={use_portfolio_context}"
        ) 

    def assess_trade_risk(
        self,
        setup: Dict[str, Any],
        recommendation: Dict[str, Any],
        portfolio_state: Optional[Dict[str, Any]] = None,
        market_regime: Optional[MarketRegime] = None,
        volatility_regime: Optional[str] = None,
        liquidity_regime: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Assess the risk of a potential trade.
        
        Args:
            setup: The detected trading setup
            recommendation: The strategy recommendation
            portfolio_state: Current portfolio state if available
            market_regime: Current market regime if available
            volatility_regime: Current volatility regime if available
            liquidity_regime: Current liquidity regime if available
            
        Returns:
            Dict with risk assessment results
        """
        self.logger.info(f"Assessing risk for {setup.get('type')} setup")
        
        # Extract key information
        setup_quality = setup.get("quality", 0.7)
        risk_percent = recommendation.get("risk_percent", self.default_risk_percent)
        risk_reward = recommendation.get("risk_reward", 0.0)
        position_sizing = recommendation.get("position_sizing", PositionSizing.NORMAL.value)
        
        # Base risk score (0-100, higher is riskier)
        base_risk_score = 50
        
        # Adjust based on setup quality
        quality_adjustment = (0.7 - setup_quality) * 30  # Lower quality = higher risk
        base_risk_score += quality_adjustment
        
        # Adjust based on risk-reward ratio
        if risk_reward > 0:
            rr_adjustment = (2.0 - risk_reward) * 10  # Lower R:R = higher risk
            base_risk_score += rr_adjustment
        else:
            base_risk_score += 20  # Unknown R:R is risky
        
        # Adjust based on position sizing
        sizing_adjustments = {
            PositionSizing.MAXIMUM.value: 20,
            PositionSizing.INCREASED.value: 10,
            PositionSizing.NORMAL.value: 0,
            PositionSizing.REDUCED.value: -10,
            PositionSizing.MINIMUM.value: -20,
            PositionSizing.AVOID.value: 50  # Avoid is very risky if taken
        }
        base_risk_score += sizing_adjustments.get(position_sizing, 0)
        
        # Adjust based on market regime if available and enabled
        if self.use_market_regime and market_regime:
            regime_adjustments = {
                MarketRegime.TRENDING.value: -5,
                MarketRegime.RANGING.value: 0,
                MarketRegime.VOLATILE.value: 15,
                MarketRegime.REVERSAL.value: 10,
                MarketRegime.BREAKOUT.value: 5
            }
            base_risk_score += regime_adjustments.get(market_regime.value, 0)
        
        # Adjust based on volatility regime if available
        if volatility_regime:
            vol_adjustments = {
                "low": -10,
                "normal": 0,
                "high": 15
            }
            base_risk_score += vol_adjustments.get(volatility_regime, 0)
        
        # Adjust based on liquidity regime if available
        if liquidity_regime:
            liq_adjustments = {
                "high": -5,
                "medium": 0,
                "low": 15
            }
            base_risk_score += liq_adjustments.get(liquidity_regime, 0)
        
        # Adjust based on portfolio context if available and enabled
        portfolio_adjustment = 0
        if self.use_portfolio_context and portfolio_state:
            # Check current exposure
            current_exposure = portfolio_state.get("total_exposure", 0.0)
            if current_exposure > 0.7:  # High exposure
                portfolio_adjustment += 15
            elif current_exposure > 0.5:  # Moderate exposure
                portfolio_adjustment += 5
            
            # Check correlation with existing positions
            avg_correlation = portfolio_state.get("average_correlation", 0.0)
            if avg_correlation > 0.7:  # High correlation
                portfolio_adjustment += 10
            elif avg_correlation > 0.5:  # Moderate correlation
                portfolio_adjustment += 5
            
            # Check drawdown state
            current_drawdown = portfolio_state.get("current_drawdown", 0.0)
            if current_drawdown > 0.1:  # In significant drawdown
                portfolio_adjustment += 15
            elif current_drawdown > 0.05:  # In moderate drawdown
                portfolio_adjustment += 5
        
        base_risk_score += portfolio_adjustment
        
        # Ensure risk score is within bounds
        risk_score = max(0, min(100, base_risk_score))
        
        # Determine risk level
        if risk_score >= 80:
            risk_level = "very_high"
        elif risk_score >= 60:
            risk_level = "high"
        elif risk_score >= 40:
            risk_level = "moderate"
        elif risk_score >= 20:
            risk_level = "low"
        else:
            risk_level = "very_low"
        
        # Generate risk warnings
        warnings = []
        
        if setup_quality < self.min_setup_quality:
            warnings.append("Setup quality below minimum threshold")
        
        if risk_reward < self.min_risk_reward:
            warnings.append("Risk-reward ratio below minimum threshold")
        
        if self.use_market_regime and market_regime == MarketRegime.VOLATILE:
            warnings.append("Volatile market conditions increase risk")
        
        if volatility_regime == "high":
            warnings.append("High volatility increases risk of adverse price movements")
        
        if liquidity_regime == "low":
            warnings.append("Low liquidity increases risk of slippage and execution issues")
        
        if self.use_portfolio_context and portfolio_state:
            if portfolio_state.get("total_exposure", 0.0) > 0.7:
                warnings.append("High portfolio exposure increases overall risk")
            
            if portfolio_state.get("average_correlation", 0.0) > 0.7:
                warnings.append("High correlation with existing positions reduces diversification")
            
            if portfolio_state.get("current_drawdown", 0.0) > 0.1:
                warnings.append("Taking new positions during drawdown may compound losses")
        
        # Compile the risk assessment
        assessment = {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "warnings": warnings,
            "quality_factor": setup_quality,
            "risk_reward_factor": risk_reward,
            "position_sizing": position_sizing,
            "market_regime": market_regime.value if market_regime else None,
            "volatility_regime": volatility_regime,
            "liquidity_regime": liquidity_regime,
            "portfolio_adjustment": portfolio_adjustment,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(
            f"Risk assessment: score={risk_score}, level={risk_level}, "
            f"warnings={len(warnings)}"
        )
        
        return assessment 

    def generate_trade_checklist(
        self,
        setup: Dict[str, Any],
        recommendation: Dict[str, Any],
        risk_assessment: Dict[str, Any],
        market_regime: Optional[MarketRegime] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate a checklist for validating a trade before execution.
        
        Args:
            setup: The detected trading setup
            recommendation: The strategy recommendation
            risk_assessment: The risk assessment results
            market_regime: Current market regime if available
            
        Returns:
            List of checklist items
        """
        self.logger.info(f"Generating trade checklist for {setup.get('type')} setup")
        
        checklist = []
        
        # Setup quality checks
        checklist.append({
            "category": ChecklistCategory.SETUP_QUALITY.value,
            "question": "Is the setup clearly identifiable?",
            "guidance": "The setup should have clear entry, stop loss, and take profit levels.",
            "auto_check": setup.get("quality", 0) >= self.min_setup_quality,
            "importance": "high"
        })
        
        checklist.append({
            "category": ChecklistCategory.SETUP_QUALITY.value,
            "question": "Does the setup have confluence with multiple factors?",
            "guidance": "Look for multiple technical factors confirming the setup.",
            "auto_check": None,  # Requires manual check
            "importance": "medium"
        })
        
        # Market condition checks
        if self.use_market_regime:
            checklist.append({
                "category": ChecklistCategory.MARKET_CONDITION.value,
                "question": "Is the market regime favorable for this setup?",
                "guidance": f"Current regime: {market_regime.value if market_regime else 'Unknown'}",
                "auto_check": market_regime != MarketRegime.VOLATILE if market_regime else None,
                "importance": "high"
            })
        
        checklist.append({
            "category": ChecklistCategory.MARKET_CONDITION.value,
            "question": "Have you checked higher timeframe trends?",
            "guidance": "Ensure the trade aligns with higher timeframe trends.",
            "auto_check": None,  # Requires manual check
            "importance": "high"
        })
        
        # Risk management checks
        checklist.append({
            "category": ChecklistCategory.RISK_MANAGEMENT.value,
            "question": "Is the risk-reward ratio acceptable?",
            "guidance": f"Minimum recommended R:R is {self.min_risk_reward}.",
            "auto_check": risk_assessment.get("risk_reward_factor", 0) >= self.min_risk_reward,
            "importance": "critical"
        })
        
        checklist.append({
            "category": ChecklistCategory.RISK_MANAGEMENT.value,
            "question": "Is the position size appropriate?",
            "guidance": f"Recommended position sizing: {recommendation.get('position_sizing', 'Unknown')}",
            "auto_check": recommendation.get("position_sizing") != PositionSizing.AVOID.value,
            "importance": "critical"
        })
        
        checklist.append({
            "category": ChecklistCategory.RISK_MANAGEMENT.value,
            "question": "Is the risk per trade within your limits?",
            "guidance": f"Recommended risk: {recommendation.get('risk_percent', self.default_risk_percent)}% of capital.",
            "auto_check": recommendation.get("risk_percent", 100) <= 2.0,  # Assuming 2% is max risk
            "importance": "critical"
        })
        
        # Entry timing checks
        checklist.append({
            "category": ChecklistCategory.ENTRY_TIMING.value,
            "question": "Is this an optimal entry point?",
            "guidance": "Check for immediate support/resistance levels.",
            "auto_check": None,  # Requires manual check
            "importance": "medium"
        })
        
        checklist.append({
            "category": ChecklistCategory.ENTRY_TIMING.value,
            "question": "Have you considered the current volatility?",
            "guidance": f"Current volatility regime: {risk_assessment.get('volatility_regime', 'Unknown')}",
            "auto_check": risk_assessment.get("volatility_regime") != "high",
            "importance": "medium"
        })
        
        # Exit strategy checks
        checklist.append({
            "category": ChecklistCategory.EXIT_STRATEGY.value,
            "question": "Do you have a clear exit strategy?",
            "guidance": "Define both stop loss and take profit levels.",
            "auto_check": None,  # Requires manual check
            "importance": "high"
        })
        
        checklist.append({
            "category": ChecklistCategory.EXIT_STRATEGY.value,
            "question": "Have you considered partial profit taking?",
            "guidance": "Consider taking partial profits at key levels.",
            "auto_check": None,  # Requires manual check
            "importance": "low"
        })
        
        # Portfolio context checks
        if self.use_portfolio_context:
            checklist.append({
                "category": ChecklistCategory.PORTFOLIO_CONTEXT.value,
                "question": "Does this trade fit with your overall portfolio?",
                "guidance": "Consider correlation with existing positions.",
                "auto_check": risk_assessment.get("portfolio_adjustment", 0) < 10,
                "importance": "medium"
            })
            
            checklist.append({
                "category": ChecklistCategory.PORTFOLIO_CONTEXT.value,
                "question": "Is your overall exposure at a safe level?",
                "guidance": "Monitor total portfolio exposure.",
                "auto_check": None,  # Requires manual check
                "importance": "high"
            })
        
        # Psychological checks
        checklist.append({
            "category": ChecklistCategory.PSYCHOLOGICAL.value,
            "question": "Are you trading with a clear mind?",
            "guidance": "Avoid trading when emotional or tired.",
            "auto_check": None,  # Requires manual check
            "importance": "high"
        })
        
        checklist.append({
            "category": ChecklistCategory.PSYCHOLOGICAL.value,
            "question": "Are you following your trading plan?",
            "guidance": "Stick to your predefined rules and strategy.",
            "auto_check": None,  # Requires manual check
            "importance": "high"
        })
        
        # Add warning-specific checks
        for warning in risk_assessment.get("warnings", []):
            checklist.append({
                "category": ChecklistCategory.RISK_MANAGEMENT.value,
                "question": f"Have you addressed: {warning}?",
                "guidance": "Consider if this warning is acceptable for your strategy.",
                "auto_check": False,  # Warnings start as unchecked
                "importance": "high"
            })
        
        self.logger.info(f"Generated {len(checklist)} checklist items")
        
        return checklist 

    def model_scenarios(
        self,
        setup: Dict[str, Any],
        recommendation: Dict[str, Any],
        current_price: float,
        scenario_types: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Model different scenarios for a potential trade.
        
        Args:
            setup: The detected trading setup
            recommendation: The strategy recommendation
            current_price: Current price of the asset
            scenario_types: List of scenario types to model
            
        Returns:
            Dict with modeled scenarios
        """
        self.logger.info(f"Modeling scenarios for {setup.get('type')} setup")
        
        # Use default scenario types if none provided
        if scenario_types is None:
            scenario_types = [
                ScenarioType.BEST_CASE.value,
                ScenarioType.WORST_CASE.value,
                ScenarioType.EXPECTED_CASE.value,
                ScenarioType.BREAKEVEN_CASE.value
            ]
        
        # Extract key information
        entry_zone = recommendation.get("entry_zone", {"ideal": current_price})
        entry_price = entry_zone.get("ideal", current_price)
        stop_loss = recommendation.get("stop_loss", entry_price * 0.95)  # Default 5% stop
        take_profit = recommendation.get("take_profit", entry_price * 1.15)  # Default 15% target
        risk_percent = recommendation.get("risk_percent", self.default_risk_percent)
        
        # Calculate base metrics
        risk_amount = abs(entry_price - stop_loss)
        reward_amount = abs(take_profit - entry_price)
        risk_reward = reward_amount / risk_amount if risk_amount > 0 else 0
        
        # Initialize scenarios dict
        scenarios = {}
        
        # Model best case scenario
        if ScenarioType.BEST_CASE.value in scenario_types:
            # In best case, price moves directly to take profit
            best_case = {
                "type": ScenarioType.BEST_CASE.value,
                "description": "Price moves directly to take profit level",
                "entry_price": entry_price,
                "exit_price": take_profit,
                "stop_loss": stop_loss,
                "profit_loss_percent": (take_profit - entry_price) / entry_price * 100,
                "profit_loss_r": 1 * risk_reward,
                "probability": 0.3,  # Estimated probability
                "time_to_completion": "Unknown",
                "notes": ["Represents ideal scenario with no drawdown"]
            }
            scenarios[ScenarioType.BEST_CASE.value] = best_case
        
        # Model worst case scenario
        if ScenarioType.WORST_CASE.value in scenario_types:
            # In worst case, price moves directly to stop loss
            worst_case = {
                "type": ScenarioType.WORST_CASE.value,
                "description": "Price moves directly to stop loss level",
                "entry_price": entry_price,
                "exit_price": stop_loss,
                "stop_loss": stop_loss,
                "profit_loss_percent": (stop_loss - entry_price) / entry_price * 100,
                "profit_loss_r": -1.0,
                "probability": 0.3,  # Estimated probability
                "time_to_completion": "Unknown",
                "notes": ["Represents complete failure of setup"]
            }
            scenarios[ScenarioType.WORST_CASE.value] = worst_case
        
        # Model expected case scenario
        if ScenarioType.EXPECTED_CASE.value in scenario_types:
            # In expected case, we use a weighted average based on win rate
            # Assuming a 60% win rate for this example
            win_rate = 0.6
            expected_exit = (take_profit * win_rate) + (stop_loss * (1 - win_rate))
            expected_case = {
                "type": ScenarioType.EXPECTED_CASE.value,
                "description": "Probability-weighted outcome based on historical win rate",
                "entry_price": entry_price,
                "exit_price": expected_exit,
                "stop_loss": stop_loss,
                "profit_loss_percent": (expected_exit - entry_price) / entry_price * 100,
                "profit_loss_r": (expected_exit - entry_price) / risk_amount,
                "probability": 1.0,  # This is the expected outcome
                "time_to_completion": "Unknown",
                "notes": [f"Based on estimated {win_rate*100}% win rate"]
            }
            scenarios[ScenarioType.EXPECTED_CASE.value] = expected_case
        
        # Model breakeven case scenario
        if ScenarioType.BREAKEVEN_CASE.value in scenario_types:
            # In breakeven case, price moves to entry after some time
            breakeven_case = {
                "type": ScenarioType.BREAKEVEN_CASE.value,
                "description": "Price returns to entry level after some movement",
                "entry_price": entry_price,
                "exit_price": entry_price,
                "stop_loss": stop_loss,
                "profit_loss_percent": 0.0,
                "profit_loss_r": 0.0,
                "probability": 0.1,  # Estimated probability
                "time_to_completion": "Unknown",
                "notes": ["Represents opportunity cost with no direct loss"]
            }
            scenarios[ScenarioType.BREAKEVEN_CASE.value] = breakeven_case
        
        # Model partial exit scenario
        if ScenarioType.PARTIAL_EXIT.value in scenario_types:
            # In partial exit, we take profit on half position at 50% of target
            partial_take_profit = entry_price + (reward_amount * 0.5)
            remaining_take_profit = take_profit
            
            # Calculate blended exit price (50% at partial TP, 50% at full TP)
            blended_exit = (partial_take_profit * 0.5) + (remaining_take_profit * 0.5)
            
            partial_exit_case = {
                "type": ScenarioType.PARTIAL_EXIT.value,
                "description": "Take partial profit at 50% of target, remainder at full target",
                "entry_price": entry_price,
                "exit_price": blended_exit,
                "partial_exit_points": [
                    {"price": partial_take_profit, "portion": 0.5}
                ],
                "stop_loss": stop_loss,
                "profit_loss_percent": (blended_exit - entry_price) / entry_price * 100,
                "profit_loss_r": (blended_exit - entry_price) / risk_amount,
                "probability": 0.4,  # Estimated probability
                "time_to_completion": "Unknown",
                "notes": ["Reduces risk after partial profit taking"]
            }
            scenarios[ScenarioType.PARTIAL_EXIT.value] = partial_exit_case
        
        # Model trailing stop scenario
        if ScenarioType.TRAILING_STOP.value in scenario_types:
            # In trailing stop, we assume price moves 75% toward target then reverses
            trail_exit = entry_price + (reward_amount * 0.75)
            
            trailing_stop_case = {
                "type": ScenarioType.TRAILING_STOP.value,
                "description": "Price moves 75% toward target, then reverses to trailing stop",
                "entry_price": entry_price,
                "exit_price": trail_exit,
                "initial_stop_loss": stop_loss,
                "final_stop_level": entry_price + (reward_amount * 0.5),  # Trail to 50% of move
                "profit_loss_percent": (trail_exit - entry_price) / entry_price * 100,
                "profit_loss_r": (trail_exit - entry_price) / risk_amount,
                "probability": 0.2,  # Estimated probability
                "time_to_completion": "Unknown",
                "notes": ["Captures partial move with trailing stop"]
            }
            scenarios[ScenarioType.TRAILING_STOP.value] = trailing_stop_case
        
        # Calculate expected value across all scenarios
        total_probability = sum(s.get("probability", 0) for s in scenarios.values())
        if total_probability > 0:
            # Normalize probabilities
            for scenario in scenarios.values():
                scenario["normalized_probability"] = scenario.get("probability", 0) / total_probability
            
            # Calculate expected value
            expected_value = sum(
                s.get("profit_loss_r", 0) * s.get("normalized_probability", 0)
                for s in scenarios.values()
            )
            
            # Add to each scenario
            for scenario in scenarios.values():
                scenario["expected_value"] = expected_value
        
        self.logger.info(f"Modeled {len(scenarios)} scenarios")
        
        return scenarios 

    def create_trade_journal_entry(
        self,
        setup: Dict[str, Any],
        recommendation: Dict[str, Any],
        risk_assessment: Dict[str, Any],
        execution_details: Dict[str, Any],
        market_conditions: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a structured trade journal entry for a trade.
        
        Args:
            setup: The detected trading setup
            recommendation: The strategy recommendation
            risk_assessment: The risk assessment results
            execution_details: Details of trade execution
            market_conditions: Market conditions at time of trade
            notes: Additional notes from the trader
            
        Returns:
            Dict with structured trade journal entry
        """
        self.logger.info(f"Creating trade journal entry for {setup.get('type')} setup")
        
        # Extract key information
        setup_type = setup.get("type", "unknown")
        setup_quality = setup.get("quality", 0.0)
        strategy_type = recommendation.get("strategy_type", "unknown")
        position_sizing = recommendation.get("position_sizing", "unknown")
        risk_level = risk_assessment.get("risk_level", "unknown")
        
        # Extract execution details
        entry_price = execution_details.get("entry_price", 0.0)
        entry_time = execution_details.get("entry_time", datetime.now().isoformat())
        position_size = execution_details.get("position_size", 0.0)
        stop_loss = execution_details.get("stop_loss", 0.0)
        take_profit = execution_details.get("take_profit", 0.0)
        
        # Create the journal entry
        journal_entry = {
            "id": f"trade_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "trade_details": {
                "symbol": setup.get("symbol", ""),
                "exchange": setup.get("exchange", ""),
                "direction": execution_details.get("direction", ""),
                "entry_price": entry_price,
                "entry_time": entry_time,
                "position_size": position_size,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "risk_amount": abs(entry_price - stop_loss) * position_size if stop_loss > 0 else 0,
                "risk_percent": execution_details.get("risk_percent", 0.0),
                "timeframe": setup.get("timeframe", "")
            },
            "setup_details": {
                "setup_type": setup_type,
                "setup_quality": setup_quality,
                "setup_id": setup.get("id", ""),
                "detection_time": setup.get("detection_time", "")
            },
            "strategy_details": {
                "strategy_type": strategy_type,
                "position_sizing": position_sizing,
                "risk_reward": recommendation.get("risk_reward", 0.0),
                "notes": recommendation.get("notes", [])
            },
            "risk_assessment": {
                "risk_level": risk_level,
                "risk_score": risk_assessment.get("risk_score", 0),
                "warnings": risk_assessment.get("warnings", [])
            },
            "market_conditions": market_conditions or {
                "market_regime": risk_assessment.get("market_regime", "unknown"),
                "volatility_regime": risk_assessment.get("volatility_regime", "unknown"),
                "liquidity_regime": risk_assessment.get("liquidity_regime", "unknown")
            },
            "trader_notes": {
                "pre_trade_notes": notes or "",
                "emotions": execution_details.get("emotions", ""),
                "confidence_level": execution_details.get("confidence_level", 0.0),
                "trade_plan_adherence": execution_details.get("trade_plan_adherence", True)
            },
            "exit_details": {
                "exit_price": None,
                "exit_time": None,
                "exit_reason": None,
                "profit_loss": None,
                "profit_loss_percent": None,
                "profit_loss_r": None,
                "holding_time": None
            },
            "post_trade_analysis": {
                "completed": False,
                "lessons_learned": [],
                "improvement_areas": [],
                "rating": None
            }
        }
        
        self.logger.info(f"Created trade journal entry with ID: {journal_entry['id']}")
        
        return journal_entry
    
    def update_trade_journal_entry(
        self,
        journal_entry: Dict[str, Any],
        exit_details: Dict[str, Any],
        post_trade_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update a trade journal entry with exit details and post-trade analysis.
        
        Args:
            journal_entry: The original trade journal entry
            exit_details: Details of trade exit
            post_trade_analysis: Post-trade analysis and reflections
            
        Returns:
            Updated trade journal entry
        """
        self.logger.info(f"Updating trade journal entry: {journal_entry.get('id')}")
        
        # Extract key information
        entry_price = journal_entry.get("trade_details", {}).get("entry_price", 0.0)
        entry_time = journal_entry.get("trade_details", {}).get("entry_time", "")
        stop_loss = journal_entry.get("trade_details", {}).get("stop_loss", 0.0)
        position_size = journal_entry.get("trade_details", {}).get("position_size", 0.0)
        
        # Extract exit details
        exit_price = exit_details.get("exit_price", 0.0)
        exit_time = exit_details.get("exit_time", datetime.now().isoformat())
        exit_reason = exit_details.get("exit_reason", "unknown")
        
        # Calculate profit/loss
        profit_loss = (exit_price - entry_price) * position_size
        if entry_price > 0:
            profit_loss_percent = (exit_price - entry_price) / entry_price * 100
        else:
            profit_loss_percent = 0.0
        
        # Calculate R multiple
        risk_amount = abs(entry_price - stop_loss)
        if risk_amount > 0:
            profit_loss_r = (exit_price - entry_price) / risk_amount
        else:
            profit_loss_r = 0.0
        
        # Calculate holding time
        try:
            entry_dt = datetime.fromisoformat(entry_time)
            exit_dt = datetime.fromisoformat(exit_time)
            holding_time = (exit_dt - entry_dt).total_seconds() / 3600  # Hours
        except (ValueError, TypeError):
            holding_time = 0.0
        
        # Update exit details
        journal_entry["exit_details"] = {
            "exit_price": exit_price,
            "exit_time": exit_time,
            "exit_reason": exit_reason,
            "profit_loss": profit_loss,
            "profit_loss_percent": profit_loss_percent,
            "profit_loss_r": profit_loss_r,
            "holding_time": holding_time
        }
        
        # Update post-trade analysis if provided
        if post_trade_analysis:
            journal_entry["post_trade_analysis"] = {
                "completed": True,
                "lessons_learned": post_trade_analysis.get("lessons_learned", []),
                "improvement_areas": post_trade_analysis.get("improvement_areas", []),
                "rating": post_trade_analysis.get("rating", 0),
                "emotions": post_trade_analysis.get("emotions", ""),
                "notes": post_trade_analysis.get("notes", "")
            }
        
        self.logger.info(
            f"Updated trade journal entry: {journal_entry['id']}, "
            f"P/L: {profit_loss_percent:.2f}%, R: {profit_loss_r:.2f}"
        )
        
        return journal_entry 