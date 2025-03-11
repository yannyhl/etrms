"""
Enhanced Trading Risk Management System Parameter Optimizer

This module provides parameter optimization functionality for backtesting strategies.
"""
import asyncio
import itertools
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Tuple, Union

import numpy as np
import pandas as pd

from exchange.backtesting.backtesting_engine import run_backtest
from exchange.backtesting.strategy_factory import StrategyFactory
from utils.logger import get_logger, log_event


logger = get_logger(__name__)


class ParameterOptimizer:
    """
    Optimizer for trading strategy parameters.
    
    This class performs grid search over parameter spaces to find optimal
    strategy parameters based on selected performance metrics.
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
        parallel: bool = False,
        max_workers: int = 4
    ):
        """
        Initialize the parameter optimizer.
        
        Args:
            strategy_name: Name of the strategy to optimize
            parameter_grid: Dictionary mapping parameter names to lists of values
            start_date: Start date for backtesting in 'YYYY-MM-DD' format
            end_date: End date for backtesting in 'YYYY-MM-DD' format
            symbols: List of symbols to include in backtests
            timeframe: Timeframe for historical data
            initial_balance: Initial account balance
            fee_rate: Trading fee rate
            slippage: Simulated slippage
            risk_per_trade: Risk per trade as a percentage of account balance
            optimization_metric: Metric to optimize ('sharpe_ratio', 'total_return_percentage', etc.)
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
        
        # Results storage
        self.results = []
        self.best_parameters = None
        self.best_result = None
        
        log_event(
            logger,
            "PARAMETER_OPTIMIZER_INIT",
            f"Parameter optimizer initialized for strategy '{strategy_name}'",
            context={
                "strategy": strategy_name,
                "parameter_grid": parameter_grid,
                "optimization_metric": optimization_metric,
                "symbols": symbols,
                "timeframe": timeframe
            }
        )
    
    async def run_optimization(self) -> Dict[str, Any]:
        """
        Run the parameter optimization.
        
        This method performs a grid search over the parameter space and returns the best parameters.
        
        Returns:
            Dictionary containing optimization results
        """
        # Generate all parameter combinations
        param_names = list(self.parameter_grid.keys())
        param_values = list(self.parameter_grid.values())
        param_combinations = list(itertools.product(*param_values))
        
        log_event(
            logger,
            "PARAMETER_OPTIMIZATION_START",
            f"Starting parameter optimization with {len(param_combinations)} combinations",
            context={
                "strategy": self.strategy_name,
                "combinations_count": len(param_combinations)
            }
        )
        
        # Run backtests for all parameter combinations
        if self.parallel and len(param_combinations) > 1:
            # Run in parallel
            results = []
            chunk_size = max(1, len(param_combinations) // self.max_workers)
            chunks = [param_combinations[i:i + chunk_size] for i in range(0, len(param_combinations), chunk_size)]
            
            # Create tasks for each chunk
            tasks = []
            for chunk in chunks:
                tasks.append(self._run_parameter_chunk(param_names, chunk))
            
            # Run tasks and collect results
            chunk_results = await asyncio.gather(*tasks)
            for chunk_result in chunk_results:
                results.extend(chunk_result)
        else:
            # Run sequentially
            results = await self._run_parameter_chunk(param_names, param_combinations)
        
        # Store all results
        self.results = results
        
        # Find best parameters
        self._find_best_parameters()
        
        log_event(
            logger,
            "PARAMETER_OPTIMIZATION_COMPLETE",
            f"Parameter optimization complete for strategy '{self.strategy_name}'",
            context={
                "strategy": self.strategy_name,
                "best_parameters": self.best_parameters,
                "best_metric_value": self.best_result[self.optimization_metric] if self.best_result else None
            }
        )
        
        return {
            "strategy": self.strategy_name,
            "optimization_metric": self.optimization_metric,
            "all_results": self.results,
            "best_parameters": self.best_parameters,
            "best_result": self.best_result
        }
    
    async def _run_parameter_chunk(
        self,
        param_names: List[str],
        param_combinations: List[Tuple]
    ) -> List[Dict[str, Any]]:
        """
        Run backtests for a chunk of parameter combinations.
        
        Args:
            param_names: Names of the parameters
            param_combinations: List of parameter value combinations to test
            
        Returns:
            List of dictionaries containing backtest results
        """
        results = []
        
        for i, combination in enumerate(param_combinations):
            # Create parameter dictionary
            params = {param_names[j]: combination[j] for j in range(len(param_names))}
            
            # Log progress
            if i % 10 == 0:
                log_event(
                    logger,
                    "PARAMETER_OPTIMIZATION_PROGRESS",
                    f"Testing combination {i+1}/{len(param_combinations)}",
                    context={"parameters": params}
                )
            
            try:
                # Get strategy
                strategy = StrategyFactory.get_strategy(
                    strategy_name=self.strategy_name,
                    **params
                )
                
                # Run backtest
                backtest_result = await run_backtest(
                    start_date=self.start_date,
                    end_date=self.end_date,
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
                
                # Extract performance metrics
                performance_metrics = backtest_result.get("performance_metrics", {})
                
                # Store result with parameters
                result = {
                    "parameters": params,
                    **performance_metrics,
                    "trade_count": performance_metrics.get("total_trades", 0)
                }
                
                results.append(result)
            except Exception as e:
                log_event(
                    logger,
                    "PARAMETER_OPTIMIZATION_ERROR",
                    f"Error testing parameters: {str(e)}",
                    level="ERROR",
                    context={"parameters": params, "error": str(e)}
                )
        
        return results
    
    def _find_best_parameters(self) -> None:
        """
        Find the best parameters based on the optimization metric.
        """
        if not self.results:
            return
        
        # Filter out results with invalid metrics
        valid_results = [r for r in self.results if self.optimization_metric in r and r[self.optimization_metric] is not None]
        
        if not valid_results:
            return
        
        # Determine if the metric should be maximized or minimized
        minimize_metrics = ["max_drawdown", "max_drawdown_percentage"]
        should_minimize = self.optimization_metric in minimize_metrics
        
        # Sort results
        sorted_results = sorted(
            valid_results,
            key=lambda x: x[self.optimization_metric],
            reverse=not should_minimize
        )
        
        # Get best result
        self.best_result = sorted_results[0]
        self.best_parameters = self.best_result["parameters"]
    
    def get_results_dataframe(self) -> pd.DataFrame:
        """
        Convert optimization results to a pandas DataFrame.
        
        Returns:
            DataFrame containing all optimization results
        """
        if not self.results:
            return pd.DataFrame()
        
        # Flatten the parameters into columns
        flattened_results = []
        for result in self.results:
            flat_result = {
                **{f"param_{k}": v for k, v in result.get("parameters", {}).items()},
                **{k: v for k, v in result.items() if k != "parameters"}
            }
            flattened_results.append(flat_result)
        
        return pd.DataFrame(flattened_results)
    
    def save_results(self, filename: str) -> None:
        """
        Save optimization results to a file.
        
        Args:
            filename: Path to save the results
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Save results
        with open(filename, "w") as f:
            json.dump({
                "strategy": self.strategy_name,
                "optimization_metric": self.optimization_metric,
                "parameter_grid": self.parameter_grid,
                "best_parameters": self.best_parameters,
                "results": self.results
            }, f, indent=2)
        
        log_event(
            logger,
            "PARAMETER_OPTIMIZATION_SAVED",
            f"Parameter optimization results saved to {filename}",
            context={"filename": filename}
        )


async def run_parameter_optimization(
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
    parallel: bool = False,
    max_workers: int = 4,
    save_results: bool = True,
    results_dir: str = "results/optimizations"
) -> Dict[str, Any]:
    """
    Run parameter optimization for a trading strategy.
    
    Args:
        strategy_name: Name of the strategy to optimize
        parameter_grid: Dictionary mapping parameter names to lists of values
        start_date: Start date for backtesting in 'YYYY-MM-DD' format
        end_date: End date for backtesting in 'YYYY-MM-DD' format
        symbols: List of symbols to include in backtests
        timeframe: Timeframe for historical data
        initial_balance: Initial account balance
        fee_rate: Trading fee rate
        slippage: Simulated slippage
        risk_per_trade: Risk per trade as a percentage of account balance
        optimization_metric: Metric to optimize
        parallel: Whether to run backtests in parallel
        max_workers: Maximum number of parallel workers
        save_results: Whether to save results to a file
        results_dir: Directory to save results
        
    Returns:
        Dictionary containing optimization results
    """
    # Create optimizer
    optimizer = ParameterOptimizer(
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
        parallel=parallel,
        max_workers=max_workers
    )
    
    # Run optimization
    results = await optimizer.run_optimization()
    
    # Save results if requested
    if save_results and results.get("best_parameters"):
        os.makedirs(results_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{results_dir}/{strategy_name}_optimization_{timestamp}.json"
        optimizer.save_results(filename)
        results["results_file"] = filename
    
    return results 