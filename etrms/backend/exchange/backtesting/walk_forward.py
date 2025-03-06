"""
Enhanced Trading Risk Management System Walk-Forward Analysis

This module provides walk-forward analysis functionality for backtesting strategies.
"""
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union

import numpy as np
import pandas as pd

from exchange.backtesting.backtesting_engine import run_backtest
from exchange.backtesting.parameter_optimizer import ParameterOptimizer
from exchange.backtesting.strategy_factory import StrategyFactory
from utils.logger import get_logger, log_event


logger = get_logger(__name__)


class WalkForwardAnalyzer:
    """
    Walk-forward analysis for trading strategies.
    
    This class performs walk-forward analysis by optimizing strategy parameters
    on in-sample periods and testing on out-of-sample periods.
    """
    
    def __init__(
        self,
        strategy_name: str,
        parameter_grid: Dict[str, List[Any]],
        start_date: str,
        end_date: str,
        symbols: List[str],
        timeframe: str = "1h",
        initial_balance: float = 10000.0,
        fee_rate: float = 0.0004,
        slippage: float = 0.0001,
        risk_per_trade: float = 0.01,
        optimization_metric: str = "sharpe_ratio",
        window_size_days: int = 90,
        step_size_days: int = 30,
        in_sample_pct: float = 0.7,
        parallel: bool = False,
        max_workers: int = 4
    ):
        """
        Initialize the walk-forward analyzer.
        
        Args:
            strategy_name: Name of the strategy to analyze
            parameter_grid: Dictionary mapping parameter names to lists of values
            start_date: Start date for analysis in 'YYYY-MM-DD' format
            end_date: End date for analysis in 'YYYY-MM-DD' format
            symbols: List of symbols to include in the analysis
            timeframe: Timeframe for historical data
            initial_balance: Initial account balance
            fee_rate: Trading fee rate
            slippage: Simulated slippage
            risk_per_trade: Risk per trade as a percentage of account balance
            optimization_metric: Metric to optimize during in-sample periods
            window_size_days: Size of each window in days
            step_size_days: Number of days to step forward between windows
            in_sample_pct: Percentage of each window to use for in-sample optimization
            parallel: Whether to run backtests in parallel
            max_workers: Maximum number of parallel workers (if parallel=True)
        """
        self.strategy_name = strategy_name
        self.parameter_grid = parameter_grid
        self.start_date = start_date
        self.end_date = end_date
        self.symbols = symbols
        self.timeframe = timeframe
        self.initial_balance = initial_balance
        self.fee_rate = fee_rate
        self.slippage = slippage
        self.risk_per_trade = risk_per_trade
        self.optimization_metric = optimization_metric
        self.window_size_days = window_size_days
        self.step_size_days = step_size_days
        self.in_sample_pct = in_sample_pct
        self.parallel = parallel
        self.max_workers = max_workers
        
        # Validate that strategy exists
        available_strategies = StrategyFactory.get_available_strategies()
        if not any(s["id"] == strategy_name for s in available_strategies):
            raise ValueError(f"Strategy '{strategy_name}' not found")
        
        # Validate optimization metric
        valid_metrics = [
            "sharpe_ratio", "total_return", "total_return_percentage", 
            "max_drawdown_percentage", "win_rate", "profit_factor",
            "calmar_ratio", "recovery_factor"
        ]
        if optimization_metric not in valid_metrics:
            raise ValueError(f"Invalid optimization metric: {optimization_metric}. Valid options: {valid_metrics}")
        
        # Validate date range parameters
        try:
            self.start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
            self.end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"Invalid date format. Expected 'YYYY-MM-DD': {e}")
        
        if self.start_date_dt >= self.end_date_dt:
            raise ValueError("Start date must be before end date")
        
        # Validate window parameters
        if window_size_days <= 0:
            raise ValueError("Window size must be positive")
        
        if step_size_days <= 0:
            raise ValueError("Step size must be positive")
        
        if in_sample_pct <= 0 or in_sample_pct >= 1:
            raise ValueError("In-sample percentage must be between 0 and 1")
        
        # Results storage
        self.windows = []
        self.in_sample_results = []
        self.out_of_sample_results = []
        self.combined_results = None
        
        log_event(
            logger,
            "WALK_FORWARD_ANALYZER_INIT",
            f"Walk-forward analyzer initialized for strategy '{strategy_name}'",
            context={
                "strategy": strategy_name,
                "parameter_grid": parameter_grid,
                "optimization_metric": optimization_metric,
                "symbols": symbols,
                "window_size_days": window_size_days,
                "step_size_days": step_size_days,
                "in_sample_pct": in_sample_pct
            }
        )
    
    async def run_analysis(self) -> Dict[str, Any]:
        """
        Run the walk-forward analysis.
        
        This method performs the following steps:
        1. Generate time windows
        2. For each window:
           a. Optimize parameters on the in-sample period
           b. Test the best parameters on the out-of-sample period
        3. Combine results and calculate performance metrics
        
        Returns:
            Dictionary containing analysis results
        """
        # Generate time windows
        self._generate_windows()
        
        log_event(
            logger,
            "WALK_FORWARD_ANALYSIS_START",
            f"Starting walk-forward analysis with {len(self.windows)} windows",
            context={
                "strategy": self.strategy_name,
                "windows_count": len(self.windows)
            }
        )
        
        # Process windows
        if self.parallel and len(self.windows) > 1:
            # Process windows in parallel
            tasks = []
            for window in self.windows:
                tasks.append(self._process_window(window))
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks)
        else:
            # Process windows sequentially
            for window in self.windows:
                await self._process_window(window)
        
        # Combine and analyze results
        self._combine_results()
        
        log_event(
            logger,
            "WALK_FORWARD_ANALYSIS_COMPLETE",
            f"Walk-forward analysis complete for strategy '{self.strategy_name}'",
            context={
                "strategy": self.strategy_name,
                "windows_count": len(self.windows),
                "combined_metrics": self.combined_results.get("metrics") if self.combined_results else None
            }
        )
        
        return {
            "strategy": self.strategy_name,
            "parameter_grid": self.parameter_grid,
            "optimization_metric": self.optimization_metric,
            "windows": self.windows,
            "in_sample_results": self.in_sample_results,
            "out_of_sample_results": self.out_of_sample_results,
            "combined_results": self.combined_results
        }
    
    def _generate_windows(self) -> None:
        """
        Generate time windows for walk-forward analysis.
        """
        self.windows = []
        current_start = self.start_date_dt
        
        while current_start + timedelta(days=self.window_size_days) <= self.end_date_dt:
            window_end = current_start + timedelta(days=self.window_size_days)
            
            # Calculate in-sample and out-of-sample splits
            in_sample_days = int(self.window_size_days * self.in_sample_pct)
            in_sample_end = current_start + timedelta(days=in_sample_days)
            
            # Create window
            window = {
                "window_start": current_start.strftime("%Y-%m-%d"),
                "window_end": window_end.strftime("%Y-%m-%d"),
                "in_sample_start": current_start.strftime("%Y-%m-%d"),
                "in_sample_end": in_sample_end.strftime("%Y-%m-%d"),
                "out_of_sample_start": (in_sample_end + timedelta(days=1)).strftime("%Y-%m-%d"),
                "out_of_sample_end": window_end.strftime("%Y-%m-%d")
            }
            
            self.windows.append(window)
            
            # Move to next window
            current_start += timedelta(days=self.step_size_days)
    
    async def _process_window(self, window: Dict[str, str]) -> None:
        """
        Process a single time window.
        
        Args:
            window: Dictionary containing window timeframes
        """
        window_id = f"{window['window_start']}_to_{window['window_end']}"
        
        log_event(
            logger,
            "WALK_FORWARD_WINDOW_START",
            f"Processing window {window_id}",
            context={
                "window": window
            }
        )
        
        try:
            # 1. Optimize parameters on in-sample period
            in_sample_result = await self._optimize_in_sample(
                window["in_sample_start"],
                window["in_sample_end"]
            )
            
            # Store in-sample results
            self.in_sample_results.append({
                "window": window,
                "result": in_sample_result
            })
            
            # Extract best parameters
            best_parameters = in_sample_result.get("best_parameters")
            
            if not best_parameters:
                log_event(
                    logger,
                    "WALK_FORWARD_NO_PARAMETERS",
                    f"No best parameters found for window {window_id}",
                    level="WARNING",
                    context={"window": window}
                )
                return
            
            # 2. Test on out-of-sample period
            out_of_sample_result = await self._test_out_of_sample(
                window["out_of_sample_start"],
                window["out_of_sample_end"],
                best_parameters
            )
            
            # Store out-of-sample results
            self.out_of_sample_results.append({
                "window": window,
                "parameters": best_parameters,
                "result": out_of_sample_result
            })
            
            log_event(
                logger,
                "WALK_FORWARD_WINDOW_COMPLETE",
                f"Completed window {window_id}",
                context={
                    "window": window,
                    "best_parameters": best_parameters,
                    "in_sample_metrics": in_sample_result.get("best_result"),
                    "out_of_sample_metrics": out_of_sample_result.get("performance_metrics")
                }
            )
        except Exception as e:
            log_event(
                logger,
                "WALK_FORWARD_WINDOW_ERROR",
                f"Error processing window {window_id}: {str(e)}",
                level="ERROR",
                context={
                    "window": window,
                    "error": str(e)
                }
            )
    
    async def _optimize_in_sample(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Optimize parameters on the in-sample period.
        
        Args:
            start_date: Start date for in-sample period
            end_date: End date for in-sample period
            
        Returns:
            Dictionary containing optimization results
        """
        # Create parameter optimizer
        optimizer = ParameterOptimizer(
            strategy_name=self.strategy_name,
            parameter_grid=self.parameter_grid,
            start_date=start_date,
            end_date=end_date,
            symbols=self.symbols,
            timeframe=self.timeframe,
            initial_balance=self.initial_balance,
            fee_rate=self.fee_rate,
            slippage=self.slippage,
            risk_per_trade=self.risk_per_trade,
            optimization_metric=self.optimization_metric,
            parallel=self.parallel,
            max_workers=self.max_workers
        )
        
        # Run optimization
        return await optimizer.run_optimization()
    
    async def _test_out_of_sample(
        self,
        start_date: str,
        end_date: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Test strategy with optimized parameters on out-of-sample period.
        
        Args:
            start_date: Start date for out-of-sample period
            end_date: End date for out-of-sample period
            parameters: Strategy parameters to test
            
        Returns:
            Dictionary containing backtest results
        """
        # Get strategy with specified parameters
        strategy = StrategyFactory.get_strategy(
            strategy_name=self.strategy_name,
            **parameters
        )
        
        # Run backtest
        return await run_backtest(
            start_date=start_date,
            end_date=end_date,
            symbols=self.symbols,
            timeframe=self.timeframe,
            initial_balance=self.initial_balance,
            fee_rate=self.fee_rate,
            slippage=self.slippage,
            risk_per_trade=self.risk_per_trade,
            strategy=strategy,
            save_results=False,
            generate_report=False
        )
    
    def _combine_results(self) -> None:
        """
        Combine results from all out-of-sample periods and calculate performance metrics.
        """
        if not self.out_of_sample_results:
            self.combined_results = {
                "metrics": {},
                "equity_curve": [],
                "parameters_evolution": []
            }
            return
        
        # Extract key metrics from each out-of-sample period
        equity_histories = []
        trade_histories = []
        parameters_evolution = []
        
        for result in self.out_of_sample_results:
            # Extract data
            window = result["window"]
            parameters = result["parameters"]
            out_of_sample = result["result"]
            
            # Get equity history
            equity_history = out_of_sample.get("equity_history", [])
            if equity_history:
                equity_histories.extend(equity_history)
            
            # Get trade history
            trade_history = out_of_sample.get("trade_history", [])
            if trade_history:
                trade_histories.extend(trade_history)
            
            # Record parameter evolution
            parameters_evolution.append({
                "window_start": window["window_start"],
                "window_end": window["window_end"],
                "in_sample_start": window["in_sample_start"],
                "in_sample_end": window["in_sample_end"],
                "out_of_sample_start": window["out_of_sample_start"],
                "out_of_sample_end": window["out_of_sample_end"],
                "parameters": parameters
            })
        
        # Sort equity history by timestamp
        if equity_histories:
            equity_histories.sort(key=lambda x: x[0])
        
        # Calculate combined metrics
        metrics = self._calculate_combined_metrics(equity_histories, trade_histories)
        
        # Create combined results
        self.combined_results = {
            "metrics": metrics,
            "equity_curve": equity_histories,
            "trade_history": trade_histories,
            "parameters_evolution": parameters_evolution
        }
    
    def _calculate_combined_metrics(
        self,
        equity_history: List[List[Union[str, float]]],
        trade_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate performance metrics from combined results.
        
        Args:
            equity_history: Combined equity history
            trade_history: Combined trade history
            
        Returns:
            Dictionary containing performance metrics
        """
        metrics = {}
        
        # Return empty metrics if no data
        if not equity_history or not trade_history:
            return metrics
        
        # Calculate total return
        initial_equity = equity_history[0][1] if equity_history else self.initial_balance
        final_equity = equity_history[-1][1] if equity_history else self.initial_balance
        
        metrics["total_return"] = final_equity - initial_equity
        metrics["total_return_percentage"] = (final_equity / initial_equity - 1) * 100
        
        # Count trades
        metrics["total_trades"] = len(trade_history)
        
        # Calculate win rate
        winning_trades = [t for t in trade_history if t.get("pnl", 0) > 0]
        metrics["winning_trades"] = len(winning_trades)
        metrics["win_rate"] = len(winning_trades) / len(trade_history) * 100 if trade_history else 0
        
        # Calculate average trade
        if trade_history:
            metrics["avg_trade"] = sum(t.get("pnl", 0) for t in trade_history) / len(trade_history)
        else:
            metrics["avg_trade"] = 0
        
        # Calculate profit factor
        gross_profit = sum(t.get("pnl", 0) for t in trade_history if t.get("pnl", 0) > 0)
        gross_loss = abs(sum(t.get("pnl", 0) for t in trade_history if t.get("pnl", 0) < 0))
        metrics["gross_profit"] = gross_profit
        metrics["gross_loss"] = gross_loss
        metrics["profit_factor"] = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Calculate drawdown
        if equity_history:
            # Calculate running maximum
            running_max = np.maximum.accumulate([e[1] for e in equity_history])
            
            # Calculate drawdown
            drawdowns = [running_max[i] - equity_history[i][1] for i in range(len(equity_history))]
            drawdown_pcts = [d / running_max[i] * 100 if running_max[i] > 0 else 0 for i, d in enumerate(drawdowns)]
            
            # Find maximum drawdown
            max_drawdown = max(drawdowns) if drawdowns else 0
            max_drawdown_pct = max(drawdown_pcts) if drawdown_pcts else 0
            
            metrics["max_drawdown"] = max_drawdown
            metrics["max_drawdown_percentage"] = max_drawdown_pct
        
        return metrics
    
    def get_results_dataframe(self) -> Dict[str, pd.DataFrame]:
        """
        Convert analysis results to pandas DataFrames.
        
        Returns:
            Dictionary containing DataFrames for in-sample, out-of-sample, and combined results
        """
        # Create in-sample results DataFrame
        in_sample_data = []
        for result in self.in_sample_results:
            window = result["window"]
            best_params = result["result"].get("best_parameters", {})
            best_result = result["result"].get("best_result", {})
            
            in_sample_data.append({
                "window_start": window["window_start"],
                "window_end": window["window_end"],
                "in_sample_start": window["in_sample_start"],
                "in_sample_end": window["in_sample_end"],
                **{f"param_{k}": v for k, v in best_params.items()},
                **{k: v for k, v in best_result.items() if k != "parameters"}
            })
        
        in_sample_df = pd.DataFrame(in_sample_data) if in_sample_data else pd.DataFrame()
        
        # Create out-of-sample results DataFrame
        out_of_sample_data = []
        for result in self.out_of_sample_results:
            window = result["window"]
            params = result["parameters"]
            metrics = result["result"].get("performance_metrics", {})
            
            out_of_sample_data.append({
                "window_start": window["window_start"],
                "window_end": window["window_end"],
                "out_of_sample_start": window["out_of_sample_start"],
                "out_of_sample_end": window["out_of_sample_end"],
                **{f"param_{k}": v for k, v in params.items()},
                **metrics
            })
        
        out_of_sample_df = pd.DataFrame(out_of_sample_data) if out_of_sample_data else pd.DataFrame()
        
        # Create combined results DataFrame (for metrics only)
        combined_data = {}
        if self.combined_results and self.combined_results.get("metrics"):
            combined_data = self.combined_results["metrics"]
        
        combined_df = pd.DataFrame([combined_data]) if combined_data else pd.DataFrame()
        
        return {
            "in_sample": in_sample_df,
            "out_of_sample": out_of_sample_df,
            "combined": combined_df
        }
    
    def save_results(self, filename: str) -> None:
        """
        Save analysis results to a file.
        
        Args:
            filename: Path to save the results
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Prepare data for serialization (convert numpy types to Python types)
        def convert_for_json(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, list):
                return [convert_for_json(item) for item in obj]
            if isinstance(obj, dict):
                return {key: convert_for_json(value) for key, value in obj.items()}
            return obj
        
        results = {
            "strategy": self.strategy_name,
            "parameter_grid": self.parameter_grid,
            "optimization_metric": self.optimization_metric,
            "window_size_days": self.window_size_days,
            "step_size_days": self.step_size_days,
            "in_sample_pct": self.in_sample_pct,
            "windows": self.windows,
            "in_sample_results": convert_for_json(self.in_sample_results),
            "out_of_sample_results": convert_for_json(self.out_of_sample_results),
            "combined_results": convert_for_json(self.combined_results)
        }
        
        # Save to file
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)
        
        log_event(
            logger,
            "WALK_FORWARD_RESULTS_SAVED",
            f"Walk-forward analysis results saved to {filename}",
            context={"filename": filename}
        )


async def run_walk_forward_analysis(
    strategy_name: str,
    parameter_grid: Dict[str, List[Any]],
    start_date: str,
    end_date: str,
    symbols: List[str],
    timeframe: str = "1h",
    initial_balance: float = 10000.0,
    fee_rate: float = 0.0004,
    slippage: float = 0.0001,
    risk_per_trade: float = 0.01,
    optimization_metric: str = "sharpe_ratio",
    window_size_days: int = 90,
    step_size_days: int = 30,
    in_sample_pct: float = 0.7,
    parallel: bool = False,
    max_workers: int = 4,
    save_results: bool = True,
    results_dir: str = "results/walk_forward"
) -> Dict[str, Any]:
    """
    Run walk-forward analysis for a trading strategy.
    
    Args:
        strategy_name: Name of the strategy to analyze
        parameter_grid: Dictionary mapping parameter names to lists of values
        start_date: Start date for analysis in 'YYYY-MM-DD' format
        end_date: End date for analysis in 'YYYY-MM-DD' format
        symbols: List of symbols to include in the analysis
        timeframe: Timeframe for historical data
        initial_balance: Initial account balance
        fee_rate: Trading fee rate
        slippage: Simulated slippage
        risk_per_trade: Risk per trade as a percentage of account balance
        optimization_metric: Metric to optimize during in-sample periods
        window_size_days: Size of each window in days
        step_size_days: Number of days to step forward between windows
        in_sample_pct: Percentage of each window to use for in-sample optimization
        parallel: Whether to run backtests in parallel
        max_workers: Maximum number of parallel workers
        save_results: Whether to save results to a file
        results_dir: Directory to save results
        
    Returns:
        Dictionary containing analysis results
    """
    # Create analyzer
    analyzer = WalkForwardAnalyzer(
        strategy_name=strategy_name,
        parameter_grid=parameter_grid,
        start_date=start_date,
        end_date=end_date,
        symbols=symbols,
        timeframe=timeframe,
        initial_balance=initial_balance,
        fee_rate=fee_rate,
        slippage=slippage,
        risk_per_trade=risk_per_trade,
        optimization_metric=optimization_metric,
        window_size_days=window_size_days,
        step_size_days=step_size_days,
        in_sample_pct=in_sample_pct,
        parallel=parallel,
        max_workers=max_workers
    )
    
    # Run analysis
    results = await analyzer.run_analysis()
    
    # Save results if requested
    if save_results:
        os.makedirs(results_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{results_dir}/{strategy_name}_walk_forward_{timestamp}.json"
        analyzer.save_results(filename)
        results["results_file"] = filename
    
    return results 