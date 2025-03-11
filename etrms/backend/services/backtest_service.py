"""
Service for backtesting operations.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from etrms.backend.models.backtest import (
    BacktestConfig,
    BacktestCreate,
    BacktestUpdate,
    BacktestResult,
    BacktestStatus,
    BacktestResponse,
    BacktestListResponse
)
from etrms.backend.repositories.backtest_repository import BacktestRepository
from etrms.backend.utils.error_handler import NotFoundException, ConflictException

logger = logging.getLogger(__name__)

class BacktestService:
    """Service for backtest operations"""
    
    def __init__(self, backtest_repository: BacktestRepository):
        self.backtest_repository = backtest_repository
        self.running_tasks = {}
    
    def get_backtest(self, backtest_id: str) -> BacktestResponse:
        """Get a backtest by ID"""
        try:
            return self.backtest_repository.get_backtest_response(backtest_id)
        except NotFoundException as e:
            logger.error(f"Error getting backtest: {str(e)}")
            raise
    
    def get_all_backtests(self, skip: int = 0, limit: int = 100) -> BacktestListResponse:
        """Get all backtests with pagination"""
        backtests = self.backtest_repository.get_all_backtest_responses(skip, limit)
        total = self.backtest_repository.count_configs()
        return BacktestListResponse(backtests=backtests, total=total)
    
    def create_backtest(self, backtest_create: BacktestCreate) -> BacktestResponse:
        """Create a new backtest"""
        try:
            config = self.backtest_repository.create_config(backtest_create)
            response = self.backtest_repository.get_backtest_response(config.id)
            
            # Start the backtest in the background
            self._start_backtest(config.id)
            
            return response
        except ConflictException as e:
            logger.error(f"Error creating backtest: {str(e)}")
            raise
    
    def update_backtest(self, backtest_id: str, backtest_update: BacktestUpdate) -> BacktestResponse:
        """Update a backtest"""
        try:
            # Check if the backtest is running
            response = self.backtest_repository.get_backtest_response(backtest_id)
            if response.status == BacktestStatus.RUNNING:
                raise ConflictException("Cannot update a running backtest")
            
            config = self.backtest_repository.update_config(backtest_id, backtest_update)
            return self.backtest_repository.get_backtest_response(config.id)
        except (NotFoundException, ConflictException) as e:
            logger.error(f"Error updating backtest: {str(e)}")
            raise
    
    def delete_backtest(self, backtest_id: str) -> None:
        """Delete a backtest"""
        try:
            # Check if the backtest is running
            response = self.backtest_repository.get_backtest_response(backtest_id)
            if response.status == BacktestStatus.RUNNING:
                # Cancel the running task
                if backtest_id in self.running_tasks:
                    self.running_tasks[backtest_id].cancel()
                    del self.running_tasks[backtest_id]
            
            self.backtest_repository.delete_config(backtest_id)
        except NotFoundException as e:
            logger.error(f"Error deleting backtest: {str(e)}")
            raise
    
    def cancel_backtest(self, backtest_id: str) -> BacktestResponse:
        """Cancel a running backtest"""
        try:
            # Check if the backtest is running
            response = self.backtest_repository.get_backtest_response(backtest_id)
            if response.status != BacktestStatus.RUNNING:
                raise ConflictException("Backtest is not running")
            
            # Cancel the running task
            if backtest_id in self.running_tasks:
                self.running_tasks[backtest_id].cancel()
                del self.running_tasks[backtest_id]
            
            # Update the result
            self.backtest_repository.update_result(
                backtest_id,
                BacktestStatus.CANCELLED,
                {"end_time": datetime.utcnow()}
            )
            
            return self.backtest_repository.get_backtest_response(backtest_id)
        except (NotFoundException, ConflictException) as e:
            logger.error(f"Error cancelling backtest: {str(e)}")
            raise
    
    def _start_backtest(self, backtest_id: str) -> None:
        """Start a backtest in the background"""
        # Create a task for the backtest
        task = asyncio.create_task(self._run_backtest(backtest_id))
        self.running_tasks[backtest_id] = task
        
        # Add a callback to remove the task when it's done
        task.add_done_callback(lambda t: self._cleanup_task(backtest_id, t))
    
    async def _run_backtest(self, backtest_id: str) -> None:
        """Run a backtest"""
        try:
            # Update the result to running
            self.backtest_repository.update_result(
                backtest_id,
                BacktestStatus.RUNNING,
                {"start_time": datetime.utcnow()}
            )
            
            # Get the backtest configuration
            config = self.backtest_repository.get_config_by_id(backtest_id)
            if not config:
                logger.error(f"Backtest configuration not found: {backtest_id}")
                return
            
            logger.info(f"Starting backtest: {config.name}")
            
            # Import the backtesting engine
            from exchange.backtesting.backtesting_engine import BacktestingEngine
            from risk.circuit_breaker import CircuitBreakerCondition
            
            # Convert circuit breaker configurations to conditions
            circuit_breaker_conditions = []
            for cb_config in config.circuit_breakers:
                # Create the appropriate condition function based on the type
                if cb_config.type == "MAX_DRAWDOWN":
                    from risk.circuit_breaker import max_drawdown_condition
                    condition_fn = max_drawdown_condition(cb_config.threshold)
                elif cb_config.type == "MAX_POSITION_SIZE":
                    from risk.circuit_breaker import max_position_size_condition
                    condition_fn = max_position_size_condition(cb_config.threshold)
                elif cb_config.type == "PNL":
                    from risk.circuit_breaker import create_pnl_condition
                    condition_fn = create_pnl_condition(cb_config.threshold)
                elif cb_config.type == "CONSECUTIVE_LOSSES":
                    from risk.circuit_breaker import consecutive_losses_condition
                    condition_fn = consecutive_losses_condition(int(cb_config.threshold))
                elif cb_config.type == "TIME_BASED":
                    from risk.circuit_breaker import time_based_condition
                    condition_fn = time_based_condition(cb_config.threshold)
                elif cb_config.type == "VOLATILITY":
                    from risk.circuit_breaker import volatility_condition
                    condition_fn = volatility_condition(cb_config.threshold)
                else:
                    logger.warning(f"Unknown circuit breaker type: {cb_config.type}")
                    continue
                
                # Create the appropriate action function based on the action
                if cb_config.action == "CLOSE_POSITIONS":
                    from risk.circuit_breaker import close_position_action
                    action_fn = close_position_action
                elif cb_config.action == "CANCEL_ORDERS":
                    from risk.circuit_breaker import cancel_all_orders_action
                    action_fn = cancel_all_orders_action
                elif cb_config.action == "REDUCE_POSITION":
                    from risk.circuit_breaker import reduce_position_size_action
                    action_fn = reduce_position_size_action
                else:
                    logger.warning(f"Unknown circuit breaker action: {cb_config.action}")
                    continue
                
                # Create the condition
                condition = CircuitBreakerCondition(
                    name=cb_config.description or f"{cb_config.type}_{cb_config.threshold}",
                    description=cb_config.description or f"{cb_config.type} threshold: {cb_config.threshold}",
                    evaluation_fn=condition_fn,
                    action_fn=action_fn,
                    symbols=cb_config.symbols,
                    exchanges=cb_config.exchanges,
                    enabled=cb_config.enabled
                )
                
                circuit_breaker_conditions.append(condition)
            
            # Create the backtesting engine
            engine = BacktestingEngine(
                start_date=config.start_date.strftime("%Y-%m-%d"),
                end_date=config.end_date.strftime("%Y-%m-%d"),
                initial_balance=config.initial_capital,
                symbols=config.symbols,
                timeframe=config.timeframe.value,
                # Add any additional parameters from config.parameters
                **(config.parameters or {})
            )
            
            # Set up the engine
            await engine.setup()
            
            # Add circuit breaker conditions to the risk monitor
            for condition in circuit_breaker_conditions:
                engine.risk_monitor.circuit_breaker.add_condition(condition)
            
            # Run the backtest
            results = await engine.run()
            
            # Format the results
            metrics = results["performance_metrics"]
            
            # Format trades
            trades = []
            for trade in results["trade_history"]:
                trades.append({
                    "id": trade["id"],
                    "symbol": trade["symbol"],
                    "exchange": trade["exchange"],
                    "side": trade["side"],
                    "entry_price": trade["entry_price"],
                    "exit_price": trade["exit_price"],
                    "quantity": trade["quantity"],
                    "entry_time": trade["entry_time"],
                    "exit_time": trade["exit_time"],
                    "pnl": trade["pnl"],
                    "pnl_percent": trade["pnl_percent"]
                })
            
            # Format circuit breaker events
            circuit_breaker_events = []
            for event in engine.risk_monitor.circuit_breaker_events:
                circuit_breaker_events.append({
                    "id": event["id"],
                    "circuit_breaker_id": event["circuit_breaker_id"],
                    "circuit_breaker_name": event["circuit_breaker_name"],
                    "timestamp": event["timestamp"],
                    "type": event["type"],
                    "condition": event["condition"],
                    "threshold": event["threshold"],
                    "value": event["value"],
                    "action": event["action"]
                })
            
            # Update the result to completed
            self.backtest_repository.update_result(
                backtest_id,
                BacktestStatus.COMPLETED,
                {
                    "end_time": datetime.utcnow(),
                    "metrics": metrics,
                    "trades": trades,
                    "circuit_breaker_events": circuit_breaker_events
                }
            )
            
            logger.info(f"Backtest completed: {config.name}")
        except asyncio.CancelledError:
            logger.info(f"Backtest cancelled: {backtest_id}")
            raise
        except Exception as e:
            logger.error(f"Error running backtest: {str(e)}")
            
            # Update the result to failed
            try:
                self.backtest_repository.update_result(
                    backtest_id,
                    BacktestStatus.FAILED,
                    {
                        "end_time": datetime.utcnow(),
                        "error": str(e)
                    }
                )
            except Exception as update_error:
                logger.error(f"Error updating backtest result: {str(update_error)}")
    
    def _cleanup_task(self, backtest_id: str, task: asyncio.Task) -> None:
        """Clean up a completed task"""
        if backtest_id in self.running_tasks:
            del self.running_tasks[backtest_id]
        
        # Check if the task raised an exception
        if task.exception() and not isinstance(task.exception(), asyncio.CancelledError):
            logger.error(f"Backtest task raised an exception: {str(task.exception())}")
            
            # Update the result to failed
            try:
                self.backtest_repository.update_result(
                    backtest_id,
                    BacktestStatus.FAILED,
                    {
                        "end_time": datetime.utcnow(),
                        "error": str(task.exception())
                    }
                )
            except Exception as e:
                logger.error(f"Error updating backtest result: {str(e)}") 