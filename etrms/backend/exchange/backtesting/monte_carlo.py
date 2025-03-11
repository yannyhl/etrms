"""
Enhanced Trading Risk Management System Monte Carlo Simulation

This module provides Monte Carlo simulation functionality for backtesting.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

from utils.logger import get_logger, log_event


logger = get_logger(__name__)


class MonteCarloSimulator:
    """
    Monte Carlo simulator for trading strategies.
    
    This class simulates alternative performance scenarios by randomizing
    the order of trades, enabling statistical analysis of strategy robustness.
    """
    
    def __init__(
        self,
        trades: List[Dict[str, Any]],
        initial_balance: float = 10000.0,
        simulations: int = 1000,
        random_seed: Optional[int] = None
    ):
        """
        Initialize the Monte Carlo simulator.
        
        Args:
            trades: List of trade dictionaries with at least 'pnl' or 'pnl_percentage' fields
            initial_balance: Initial account balance
            simulations: Number of simulations to run
            random_seed: Optional random seed for reproducibility
        """
        self.trades = trades
        self.initial_balance = initial_balance
        self.simulations = simulations
        
        # Set random seed if provided
        if random_seed is not None:
            np.random.seed(random_seed)
        
        # Check if we have trades to analyze
        if not trades:
            log_event(
                logger,
                "MONTE_CARLO_NO_TRADES",
                "No trades provided for Monte Carlo simulation",
                level="WARNING"
            )
        
        # Results storage
        self.results = None
        self.metrics = None
    
    def run(self) -> Dict[str, Any]:
        """
        Run the Monte Carlo simulation.
        
        Returns:
            Dict containing simulation results and metrics
        """
        if not self.trades:
            return {
                "error": "No trades provided for simulation",
                "success": False
            }
        
        # Determine if we're using absolute PnL or percentage PnL
        use_percentage = 'pnl_percentage' in self.trades[0]
        pnl_field = 'pnl_percentage' if use_percentage else 'pnl'
        
        # Extract PnL values from trades
        pnl_values = [trade[pnl_field] for trade in self.trades]
        
        # Storage for simulation results
        all_equity_curves = []
        final_balances = []
        max_drawdowns = []
        max_drawdown_pcts = []
        
        # Run simulations
        for _ in range(self.simulations):
            # Shuffle the PnL values to simulate different trade orderings
            shuffled_pnl = np.random.choice(pnl_values, len(pnl_values), replace=False)
            
            # Calculate equity curve
            equity_curve = self._calculate_equity_curve(shuffled_pnl, use_percentage)
            all_equity_curves.append(equity_curve)
            
            # Calculate metrics for this simulation
            final_balances.append(equity_curve[-1])
            
            # Calculate drawdown
            drawdown, max_dd, max_dd_pct = self._calculate_drawdown(equity_curve)
            max_drawdowns.append(max_dd)
            max_drawdown_pcts.append(max_dd_pct)
        
        # Calculate percentiles
        percentiles = [5, 10, 25, 50, 75, 90, 95]
        balance_percentiles = {p: np.percentile(final_balances, p) for p in percentiles}
        drawdown_percentiles = {p: np.percentile(max_drawdown_pcts, p) for p in percentiles}
        
        # Calculate probability of profit and loss
        profit_probability = np.mean([1 if b > self.initial_balance else 0 for b in final_balances])
        loss_probability = 1 - profit_probability
        
        # Calculate average final balance and drawdown
        avg_final_balance = np.mean(final_balances)
        avg_drawdown_pct = np.mean(max_drawdown_pcts)
        
        # Store results
        self.results = {
            "equity_curves": all_equity_curves,
            "final_balances": final_balances,
            "max_drawdowns": max_drawdowns,
            "max_drawdown_pcts": max_drawdown_pcts
        }
        
        # Store metrics
        self.metrics = {
            "initial_balance": self.initial_balance,
            "avg_final_balance": avg_final_balance,
            "avg_return_pct": (avg_final_balance / self.initial_balance - 1) * 100,
            "median_final_balance": balance_percentiles[50],
            "median_return_pct": (balance_percentiles[50] / self.initial_balance - 1) * 100,
            "min_final_balance": min(final_balances),
            "max_final_balance": max(final_balances),
            "balance_percentiles": balance_percentiles,
            "avg_max_drawdown_pct": avg_drawdown_pct,
            "median_max_drawdown_pct": drawdown_percentiles[50],
            "drawdown_percentiles": drawdown_percentiles,
            "profit_probability": profit_probability,
            "loss_probability": loss_probability,
            "trades_count": len(self.trades),
            "simulations_count": self.simulations
        }
        
        return {
            "results": self.results,
            "metrics": self.metrics,
            "success": True
        }
    
    def _calculate_equity_curve(
        self,
        pnl_values: List[float],
        use_percentage: bool
    ) -> List[float]:
        """
        Calculate the equity curve for a sequence of PnL values.
        
        Args:
            pnl_values: List of PnL values (absolute or percentage)
            use_percentage: Whether the PnL values are percentages
            
        Returns:
            List representing the equity curve
        """
        equity = [self.initial_balance]
        current_balance = self.initial_balance
        
        for pnl in pnl_values:
            if use_percentage:
                # Calculate balance change based on PnL percentage
                current_balance = current_balance * (1 + pnl / 100)
            else:
                # Use absolute PnL value
                current_balance = current_balance + pnl
            
            equity.append(current_balance)
        
        return equity
    
    def _calculate_drawdown(
        self,
        equity_curve: List[float]
    ) -> Tuple[List[float], float, float]:
        """
        Calculate the drawdown for an equity curve.
        
        Args:
            equity_curve: List representing the equity curve
            
        Returns:
            Tuple containing:
            - List of drawdown values
            - Maximum drawdown in absolute terms
            - Maximum drawdown as a percentage
        """
        # Calculate running maximum
        running_max = np.maximum.accumulate(equity_curve)
        
        # Calculate drawdown
        drawdown = [running_max[i] - equity_curve[i] for i in range(len(equity_curve))]
        drawdown_pct = [d / running_max[i] * 100 if running_max[i] > 0 else 0 for i, d in enumerate(drawdown)]
        
        # Find maximum drawdown
        max_drawdown = max(drawdown) if drawdown else 0
        max_drawdown_pct = max(drawdown_pct) if drawdown_pct else 0
        
        return drawdown, max_drawdown, max_drawdown_pct
    
    def get_percentile_curves(self, percentiles: List[int] = [5, 25, 50, 75, 95]) -> Dict[int, List[float]]:
        """
        Get equity curves at specified percentiles.
        
        Args:
            percentiles: List of percentiles to calculate
            
        Returns:
            Dict mapping percentiles to equity curves
        """
        if self.results is None:
            raise ValueError("Must run simulation before getting percentile curves")
        
        # Convert list of equity curves to a numpy array
        all_curves = np.array(self.results["equity_curves"])
        
        # Calculate percentiles at each point in time
        percentile_curves = {}
        for p in percentiles:
            percentile_curves[p] = np.percentile(all_curves, p, axis=0).tolist()
        
        return percentile_curves
    
    def get_var(self, confidence_level: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR) at the specified confidence level.
        
        Args:
            confidence_level: Confidence level for VaR (e.g., 0.95 for 95% VaR)
            
        Returns:
            VaR value representing the maximum percentage loss at the given confidence level
        """
        if self.results is None:
            raise ValueError("Must run simulation before calculating VaR")
        
        # Calculate percentage returns
        returns = [(b - self.initial_balance) / self.initial_balance * 100 for b in self.results["final_balances"]]
        
        # Calculate VaR
        var = np.percentile(returns, 100 * (1 - confidence_level))
        
        return -var if var < 0 else 0
    
    def get_cvar(self, confidence_level: float = 0.95) -> float:
        """
        Calculate Conditional Value at Risk (CVaR) at the specified confidence level.
        
        CVaR is the expected loss given that the loss exceeds VaR.
        
        Args:
            confidence_level: Confidence level for CVaR (e.g., 0.95 for 95% CVaR)
            
        Returns:
            CVaR value representing the expected percentage loss in the worst cases
        """
        if self.results is None:
            raise ValueError("Must run simulation before calculating CVaR")
        
        # Calculate percentage returns
        returns = [(b - self.initial_balance) / self.initial_balance * 100 for b in self.results["final_balances"]]
        
        # Sort returns in ascending order
        sorted_returns = np.sort(returns)
        
        # Determine the cutoff index for VaR
        cutoff_index = int(len(sorted_returns) * (1 - confidence_level))
        
        # Calculate CVaR as the mean of returns below VaR
        cvar = np.mean(sorted_returns[:cutoff_index]) if cutoff_index > 0 else sorted_returns[0]
        
        return -cvar if cvar < 0 else 0
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the Monte Carlo simulation metrics.
        
        Returns:
            Dict containing the summary metrics
        """
        if self.metrics is None:
            raise ValueError("Must run simulation before getting metrics summary")
        
        # Calculate VaR and CVaR
        var_95 = self.get_var(0.95)
        var_99 = self.get_var(0.99)
        cvar_95 = self.get_cvar(0.95)
        cvar_99 = self.get_cvar(0.99)
        
        # Create summary
        summary = {
            "initial_balance": self.metrics["initial_balance"],
            "avg_final_balance": self.metrics["avg_final_balance"],
            "avg_return_pct": self.metrics["avg_return_pct"],
            "median_return_pct": self.metrics["median_return_pct"],
            "profit_probability": self.metrics["profit_probability"] * 100,
            "avg_max_drawdown_pct": self.metrics["avg_max_drawdown_pct"],
            "var_95": var_95,
            "var_99": var_99,
            "cvar_95": cvar_95,
            "cvar_99": cvar_99,
            "worst_case_return_pct": (self.metrics["min_final_balance"] / self.metrics["initial_balance"] - 1) * 100,
            "best_case_return_pct": (self.metrics["max_final_balance"] / self.metrics["initial_balance"] - 1) * 100,
            "trades_count": self.metrics["trades_count"],
            "simulations_count": self.metrics["simulations_count"]
        }
        
        return summary


def run_monte_carlo_simulation(
    trades: List[Dict[str, Any]],
    initial_balance: float = 10000.0,
    simulations: int = 1000,
    random_seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run a Monte Carlo simulation for a set of trades.
    
    Args:
        trades: List of trade dictionaries with at least 'pnl' or 'pnl_percentage' fields
        initial_balance: Initial account balance
        simulations: Number of simulations to run
        random_seed: Optional random seed for reproducibility
        
    Returns:
        Dict containing the simulation results and metrics
    """
    simulator = MonteCarloSimulator(
        trades=trades,
        initial_balance=initial_balance,
        simulations=simulations,
        random_seed=random_seed
    )
    
    # Run simulation
    simulator.run()
    
    # Get percentile curves
    percentile_curves = simulator.get_percentile_curves()
    
    # Get metrics summary
    metrics_summary = simulator.get_metrics_summary()
    
    return {
        "percentile_curves": percentile_curves,
        "metrics": metrics_summary,
        "var_95": simulator.get_var(0.95),
        "var_99": simulator.get_var(0.99),
        "cvar_95": simulator.get_cvar(0.95),
        "cvar_99": simulator.get_cvar(0.99),
        "simulation_count": simulations,
        "trade_count": len(trades),
        "initial_balance": initial_balance
    } 