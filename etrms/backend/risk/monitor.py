"""
Enhanced Trading Risk Management System Risk Monitor

This module provides the RiskMonitor class which is responsible for:
1. Monitoring trading positions across exchanges
2. Calculating risk metrics
3. Checking for risk limit violations
4. Triggering circuit breakers when appropriate
"""
import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Callable, Set

from data.models.accounts import Account
from data.models.circuit_breakers import CircuitBreaker
from data.repositories.accounts import AccountRepository
from data.repositories.circuit_breakers import CircuitBreakerRepository
from exchange.factory import ExchangeClientFactory
from exchange.common.exchange_interface import ExchangeInterface
from utils.logger import get_logger, log_event


class RiskMonitor:
    """
    The RiskMonitor class monitors trading positions and calculates risk metrics.
    It continuously checks for risk limit violations and triggers circuit breakers when necessary.
    """
    
    def __init__(
        self,
        account_id: str,
        account_repository: Optional[AccountRepository] = None,
        circuit_breaker_repository: Optional[CircuitBreakerRepository] = None,
        polling_interval: int = 5  # in seconds
    ):
        """
        Initialize the RiskMonitor.
        
        Args:
            account_id: The ID of the account to monitor
            account_repository: Repository for account data access
            circuit_breaker_repository: Repository for circuit breaker data access
            polling_interval: How often to poll for updates (in seconds)
        """
        self.account_id = account_id
        self.account_repository = account_repository or AccountRepository()
        self.circuit_breaker_repository = circuit_breaker_repository or CircuitBreakerRepository()
        self.polling_interval = polling_interval
        self.logger = get_logger(__name__)
        
        # State variables
        self.running = False
        self.monitoring_task = None
        self.exchange_clients: Dict[str, ExchangeInterface] = {}
        self.account_info: Dict[str, Dict[str, Any]] = {}  # Exchange -> account info
        self.positions: Dict[str, Dict[str, Dict[str, Any]]] = {}  # Exchange -> Symbol -> Position
        self.balance_history: List[Dict[str, Any]] = []  # For tracking equity over time
        self.max_equity = Decimal('0')  # For calculating drawdown
        self.last_update_time = None
        
        # Callback registrations
        self.on_risk_update_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.on_circuit_breaker_callbacks: List[Callable[[CircuitBreaker, Dict[str, Any]], None]] = []
        self.on_position_update_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        
        log_event(
            self.logger,
            "RISK_MONITOR_INIT",
            f"Risk monitor initialized for account {account_id}",
            context={"account_id": account_id, "polling_interval": polling_interval}
        )
    
    async def start(self) -> None:
        """Start the risk monitoring process."""
        if self.running:
            log_event(
                self.logger,
                "RISK_MONITOR_ALREADY_RUNNING",
                f"Risk monitor already running for account {self.account_id}"
            )
            return
        
        self.running = True
        
        try:
            # Initialize exchange clients
            await self._initialize_exchange_clients()
            
            # Start the monitoring task
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            log_event(
                self.logger,
                "RISK_MONITOR_STARTED",
                f"Risk monitor started for account {self.account_id}",
                context={"account_id": self.account_id}
            )
        except Exception as e:
            self.running = False
            log_event(
                self.logger,
                "RISK_MONITOR_START_ERROR",
                f"Error starting risk monitor: {str(e)}",
                level="ERROR",
                context={"account_id": self.account_id, "error": str(e)}
            )
            raise
    
    async def stop(self) -> None:
        """Stop the risk monitoring process."""
        if not self.running:
            return
        
        self.running = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
        
        # Close exchange clients
        for exchange_id, client in self.exchange_clients.items():
            try:
                await client.close()
            except Exception as e:
                log_event(
                    self.logger,
                    "EXCHANGE_CLIENT_CLOSE_ERROR",
                    f"Error closing {exchange_id} client: {str(e)}",
                    level="ERROR",
                    context={"exchange_id": exchange_id, "error": str(e)}
                )
        
        self.exchange_clients = {}
        
        log_event(
            self.logger,
            "RISK_MONITOR_STOPPED",
            f"Risk monitor stopped for account {self.account_id}",
            context={"account_id": self.account_id}
        )
    
    async def _initialize_exchange_clients(self) -> None:
        """Initialize exchange clients for all exchanges associated with the account."""
        try:
            # Get account from repository
            account = await self.account_repository.get_by_id(self.account_id)
            if not account:
                raise ValueError(f"Account not found: {self.account_id}")
            
            # Get exchanges associated with the account
            exchanges = account.exchanges or []
            
            if not exchanges:
                log_event(
                    self.logger,
                    "RISK_MONITOR_NO_EXCHANGES",
                    f"No exchanges configured for account {self.account_id}",
                    level="WARNING",
                    context={"account_id": self.account_id}
                )
                return
            
            # Initialize clients for each exchange
            for exchange_config in exchanges:
                exchange_id = exchange_config.get("exchange_id")
                api_key = exchange_config.get("api_key")
                api_secret = exchange_config.get("api_secret")
                
                if not exchange_id:
                    continue
                
                try:
                    client = ExchangeClientFactory.get_client(
                        exchange_name=exchange_id,
                        api_key=api_key,
                        api_secret=api_secret
                    )
                    
                    await client.initialize()
                    self.exchange_clients[exchange_id] = client
                    
                    log_event(
                        self.logger,
                        "EXCHANGE_CLIENT_INITIALIZED",
                        f"Initialized {exchange_id} client for account {self.account_id}",
                        context={"account_id": self.account_id, "exchange_id": exchange_id}
                    )
                except Exception as e:
                    log_event(
                        self.logger,
                        "EXCHANGE_CLIENT_INIT_ERROR",
                        f"Error initializing {exchange_id} client: {str(e)}",
                        level="ERROR",
                        context={
                            "account_id": self.account_id,
                            "exchange_id": exchange_id,
                            "error": str(e)
                        }
                    )
        except Exception as e:
            log_event(
                self.logger,
                "EXCHANGE_CLIENTS_INIT_ERROR",
                f"Error initializing exchange clients: {str(e)}",
                level="ERROR",
                context={"account_id": self.account_id, "error": str(e)}
            )
            raise
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop that periodically checks positions and risk metrics."""
        while self.running:
            try:
                await self._update_account_information()
                await self._update_positions()
                await self._calculate_risk_metrics()
                await self._check_circuit_breakers()
                
                # Update last update time
                self.last_update_time = datetime.utcnow()
                
            except Exception as e:
                log_event(
                    self.logger,
                    "RISK_MONITORING_ERROR",
                    f"Error in risk monitoring loop: {str(e)}",
                    level="ERROR",
                    context={"account_id": self.account_id, "error": str(e)}
                )
            
            # Wait for the next polling interval
            await asyncio.sleep(self.polling_interval)
    
    async def _update_account_information(self) -> None:
        """Update account information from all exchanges."""
        for exchange_id, client in self.exchange_clients.items():
            try:
                account_info = await client.get_account_info()
                self.account_info[exchange_id] = account_info
                
                # Update max equity for drawdown calculation
                current_equity = Decimal(str(account_info.get("total_equity", 0)))
                if current_equity > self.max_equity:
                    self.max_equity = current_equity
                
                # Add to balance history
                self.balance_history.append({
                    "timestamp": datetime.utcnow(),
                    "exchange": exchange_id,
                    "equity": float(current_equity),
                    "available_balance": float(account_info.get("available_balance", 0)),
                    "margin_balance": float(account_info.get("margin_balance", 0)),
                    "unrealized_pnl": float(account_info.get("unrealized_pnl", 0))
                })
                
                # Limit history size to avoid memory issues
                if len(self.balance_history) > 1000:
                    self.balance_history = self.balance_history[-1000:]
                
            except Exception as e:
                log_event(
                    self.logger,
                    "ACCOUNT_INFO_UPDATE_ERROR",
                    f"Error updating account info for {exchange_id}: {str(e)}",
                    level="ERROR",
                    context={
                        "account_id": self.account_id,
                        "exchange_id": exchange_id,
                        "error": str(e)
                    }
                )
    
    async def _update_positions(self) -> None:
        """Update position information from all exchanges."""
        for exchange_id, client in self.exchange_clients.items():
            try:
                # Initialize positions dict for this exchange if not exists
                if exchange_id not in self.positions:
                    self.positions[exchange_id] = {}
                
                # Get all positions
                positions = await client.get_positions()
                
                # Update positions dict
                current_symbols = set()
                for position in positions:
                    symbol = position.get("symbol")
                    if not symbol:
                        continue
                    
                    self.positions[exchange_id][symbol] = position
                    current_symbols.add(symbol)
                    
                    # Notify position update callbacks
                    for callback in self.on_position_update_callbacks:
                        try:
                            callback({
                                "account_id": self.account_id,
                                "exchange_id": exchange_id,
                                "position": position
                            })
                        except Exception as callback_e:
                            log_event(
                                self.logger,
                                "POSITION_CALLBACK_ERROR",
                                f"Error in position update callback: {str(callback_e)}",
                                level="ERROR"
                            )
                
                # Remove closed positions
                symbols_to_remove = []
                for symbol in self.positions[exchange_id]:
                    if symbol not in current_symbols:
                        symbols_to_remove.append(symbol)
                
                for symbol in symbols_to_remove:
                    del self.positions[exchange_id][symbol]
                
            except Exception as e:
                log_event(
                    self.logger,
                    "POSITIONS_UPDATE_ERROR",
                    f"Error updating positions for {exchange_id}: {str(e)}",
                    level="ERROR",
                    context={
                        "account_id": self.account_id,
                        "exchange_id": exchange_id,
                        "error": str(e)
                    }
                )
    
    async def _calculate_risk_metrics(self) -> None:
        """Calculate risk metrics based on current account and position information."""
        try:
            # Initialize metrics
            metrics = {
                "account_id": self.account_id,
                "timestamp": datetime.utcnow().isoformat(),
                "total_equity": 0.0,
                "total_available_balance": 0.0,
                "total_margin_balance": 0.0,
                "total_unrealized_pnl": 0.0,
                "total_position_size": 0.0,
                "total_position_value": 0.0,
                "position_count": 0,
                "exchanges": {},
                "positions": [],
                "max_drawdown": 0.0,
                "current_drawdown": 0.0,
                "leverage": 0.0,
                "exposure_percentage": 0.0,
                "risk_percentage": 0.0,
                "largest_position": None,
                "daily_pnl": 0.0,
                "weekly_pnl": 0.0,
                "monthly_pnl": 0.0
            }
            
            # Aggregate account information across exchanges
            for exchange_id, account_info in self.account_info.items():
                metrics["total_equity"] += float(account_info.get("total_equity", 0))
                metrics["total_available_balance"] += float(account_info.get("available_balance", 0))
                metrics["total_margin_balance"] += float(account_info.get("margin_balance", 0))
                metrics["total_unrealized_pnl"] += float(account_info.get("unrealized_pnl", 0))
                
                # Exchange-specific metrics
                metrics["exchanges"][exchange_id] = {
                    "equity": float(account_info.get("total_equity", 0)),
                    "available_balance": float(account_info.get("available_balance", 0)),
                    "margin_balance": float(account_info.get("margin_balance", 0)),
                    "unrealized_pnl": float(account_info.get("unrealized_pnl", 0)),
                    "position_count": 0,
                    "position_value": 0.0,
                    "exposure_percentage": 0.0
                }
            
            # Process positions
            largest_position_value = 0.0
            for exchange_id, exchange_positions in self.positions.items():
                for symbol, position in exchange_positions.items():
                    # Add to total position count
                    metrics["position_count"] += 1
                    metrics["exchanges"][exchange_id]["position_count"] += 1
                    
                    # Get position details
                    position_size = float(position.get("quantity", 0))
                    position_value = float(position.get("notional_value", 0))
                    
                    # Add to total position size and value
                    metrics["total_position_size"] += abs(position_size)
                    metrics["total_position_value"] += position_value
                    metrics["exchanges"][exchange_id]["position_value"] += position_value
                    
                    # Add position to list
                    metrics["positions"].append({
                        "exchange": exchange_id,
                        "symbol": symbol,
                        "side": position.get("side", ""),
                        "quantity": position_size,
                        "notional_value": position_value,
                        "entry_price": float(position.get("entry_price", 0)),
                        "liquidation_price": float(position.get("liquidation_price", 0)),
                        "unrealized_pnl": float(position.get("unrealized_pnl", 0)),
                        "leverage": float(position.get("leverage", 1)),
                        "margin_type": position.get("margin_type", ""),
                    })
                    
                    # Check if this is the largest position
                    if position_value > largest_position_value:
                        largest_position_value = position_value
                        metrics["largest_position"] = {
                            "exchange": exchange_id,
                            "symbol": symbol,
                            "value": position_value,
                            "percentage_of_equity": position_value / metrics["total_equity"] * 100 if metrics["total_equity"] > 0 else 0
                        }
            
            # Calculate exposure percentage
            if metrics["total_equity"] > 0:
                metrics["exposure_percentage"] = metrics["total_position_value"] / metrics["total_equity"] * 100
                
                # Calculate exchange-specific exposure
                for exchange_id in metrics["exchanges"]:
                    if "equity" in metrics["exchanges"][exchange_id] and metrics["exchanges"][exchange_id]["equity"] > 0:
                        metrics["exchanges"][exchange_id]["exposure_percentage"] = (
                            metrics["exchanges"][exchange_id]["position_value"] / 
                            metrics["exchanges"][exchange_id]["equity"] * 100
                        )
            
            # Calculate leverage
            if metrics["total_margin_balance"] > 0:
                metrics["leverage"] = metrics["total_position_value"] / metrics["total_margin_balance"]
            
            # Calculate drawdown
            if self.max_equity > 0:
                current_equity = Decimal(str(metrics["total_equity"]))
                drawdown_amount = self.max_equity - current_equity
                metrics["max_drawdown"] = float(drawdown_amount)
                metrics["current_drawdown"] = float(drawdown_amount / self.max_equity * 100) if drawdown_amount > 0 else 0
            
            # Calculate PnL for different time periods
            now = datetime.utcnow()
            
            # Daily PnL (24 hours)
            day_ago = now - timedelta(days=1)
            day_ago_equity = self._get_equity_at_time(day_ago)
            if day_ago_equity is not None and metrics["total_equity"] > 0:
                metrics["daily_pnl"] = metrics["total_equity"] - day_ago_equity
                metrics["daily_pnl_percentage"] = (metrics["daily_pnl"] / day_ago_equity) * 100 if day_ago_equity > 0 else 0
            
            # Weekly PnL
            week_ago = now - timedelta(days=7)
            week_ago_equity = self._get_equity_at_time(week_ago)
            if week_ago_equity is not None and metrics["total_equity"] > 0:
                metrics["weekly_pnl"] = metrics["total_equity"] - week_ago_equity
                metrics["weekly_pnl_percentage"] = (metrics["weekly_pnl"] / week_ago_equity) * 100 if week_ago_equity > 0 else 0
            
            # Monthly PnL
            month_ago = now - timedelta(days=30)
            month_ago_equity = self._get_equity_at_time(month_ago)
            if month_ago_equity is not None and metrics["total_equity"] > 0:
                metrics["monthly_pnl"] = metrics["total_equity"] - month_ago_equity
                metrics["monthly_pnl_percentage"] = (metrics["monthly_pnl"] / month_ago_equity) * 100 if month_ago_equity > 0 else 0
            
            # Calculate risk percentage based on largest position
            if metrics["total_equity"] > 0 and metrics["largest_position"]:
                metrics["risk_percentage"] = metrics["largest_position"]["value"] / metrics["total_equity"] * 100
            
            # Notify risk update callbacks
            for callback in self.on_risk_update_callbacks:
                try:
                    callback(metrics)
                except Exception as e:
                    log_event(
                        self.logger,
                        "RISK_UPDATE_CALLBACK_ERROR",
                        f"Error in risk update callback: {str(e)}",
                        level="ERROR"
                    )
            
            return metrics
            
        except Exception as e:
            log_event(
                self.logger,
                "RISK_METRICS_CALCULATION_ERROR",
                f"Error calculating risk metrics: {str(e)}",
                level="ERROR",
                context={"account_id": self.account_id, "error": str(e)}
            )
            raise
    
    async def _check_circuit_breakers(self) -> None:
        """Check if any circuit breakers should be triggered."""
        try:
            # Get active circuit breakers for the account
            circuit_breakers = await self.circuit_breaker_repository.get_by_account_id(
                self.account_id, enabled=True
            )
            
            if not circuit_breakers:
                return
            
            # Get current risk metrics
            risk_metrics = await self._calculate_risk_metrics()
            
            # Check each circuit breaker
            for breaker in circuit_breakers:
                try:
                    should_trigger, trigger_values = self._evaluate_circuit_breaker(breaker, risk_metrics)
                    
                    if should_trigger:
                        await self._trigger_circuit_breaker(breaker, trigger_values, risk_metrics)
                except Exception as e:
                    log_event(
                        self.logger,
                        "CIRCUIT_BREAKER_EVALUATION_ERROR",
                        f"Error evaluating circuit breaker {breaker.name}: {str(e)}",
                        level="ERROR",
                        context={
                            "account_id": self.account_id,
                            "circuit_breaker_id": breaker.id,
                            "name": breaker.name,
                            "error": str(e)
                        }
                    )
        except Exception as e:
            log_event(
                self.logger,
                "CIRCUIT_BREAKERS_CHECK_ERROR",
                f"Error checking circuit breakers: {str(e)}",
                level="ERROR",
                context={"account_id": self.account_id, "error": str(e)}
            )
    
    def _evaluate_circuit_breaker(
        self, breaker: CircuitBreaker, risk_metrics: Dict[str, Any]
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Evaluate a circuit breaker against current risk metrics.
        
        Args:
            breaker: The circuit breaker to evaluate
            risk_metrics: The current risk metrics
            
        Returns:
            Tuple of (should_trigger, trigger_values)
        """
        # Extract condition and parameters
        condition = breaker.condition
        parameters = breaker.parameters
        
        # Initialize trigger values
        trigger_values = {}
        
        # Check specific conditions
        if condition == "max_drawdown":
            threshold = parameters.get("threshold", 10.0)  # Default 10%
            current_value = risk_metrics.get("current_drawdown", 0.0)
            
            trigger_values = {
                "threshold": threshold,
                "current_value": current_value
            }
            
            return current_value >= threshold, trigger_values
            
        elif condition == "max_position_size":
            threshold = parameters.get("threshold", 25.0)  # Default 25%
            
            # Check if we have a largest position
            if not risk_metrics.get("largest_position"):
                return False, trigger_values
                
            current_value = risk_metrics["largest_position"].get("percentage_of_equity", 0.0)
            
            trigger_values = {
                "threshold": threshold,
                "current_value": current_value,
                "position": risk_metrics["largest_position"]
            }
            
            return current_value >= threshold, trigger_values
            
        elif condition == "max_leverage":
            threshold = parameters.get("threshold", 5.0)  # Default 5x
            current_value = risk_metrics.get("leverage", 0.0)
            
            trigger_values = {
                "threshold": threshold,
                "current_value": current_value
            }
            
            return current_value >= threshold, trigger_values
            
        elif condition == "max_exposure":
            threshold = parameters.get("threshold", 80.0)  # Default 80%
            current_value = risk_metrics.get("exposure_percentage", 0.0)
            
            trigger_values = {
                "threshold": threshold,
                "current_value": current_value
            }
            
            return current_value >= threshold, trigger_values
            
        elif condition == "daily_loss":
            threshold = parameters.get("threshold", -5.0)  # Default -5%
            
            if "daily_pnl_percentage" not in risk_metrics:
                return False, trigger_values
                
            current_value = risk_metrics["daily_pnl_percentage"]
            
            trigger_values = {
                "threshold": threshold,
                "current_value": current_value
            }
            
            return current_value <= threshold, trigger_values
        
        # Unknown condition
        return False, {}
    
    async def _trigger_circuit_breaker(
        self, breaker: CircuitBreaker, trigger_values: Dict[str, Any], risk_metrics: Dict[str, Any]
    ) -> None:
        """
        Trigger a circuit breaker action.
        
        Args:
            breaker: The circuit breaker to trigger
            trigger_values: The values that triggered the circuit breaker
            risk_metrics: The current risk metrics
        """
        action = breaker.action
        parameters = breaker.parameters
        action_result = {}
        positions_affected = {}
        
        try:
            # Record the event
            await self.circuit_breaker_repository.create_event(
                breaker.id,
                trigger_values=trigger_values,
                action_taken=action,
                action_result=action_result,
                positions_affected=positions_affected
            )
            
            # Log the event
            log_event(
                self.logger,
                "CIRCUIT_BREAKER_TRIGGERED",
                f"Circuit breaker {breaker.name} triggered: {action}",
                level="WARNING",
                context={
                    "account_id": self.account_id,
                    "circuit_breaker_id": breaker.id,
                    "name": breaker.name,
                    "action": action,
                    "trigger_values": trigger_values
                }
            )
            
            # Execute the action
            if action == "notify":
                # Just notification, no actual action
                pass
                
            elif action == "reduce_position":
                # Reduce the largest position by a percentage
                reduction_percentage = parameters.get("reduction_percentage", 50.0)  # Default 50%
                
                # Find the largest position
                if not risk_metrics.get("largest_position"):
                    return
                    
                exchange_id = risk_metrics["largest_position"]["exchange"]
                symbol = risk_metrics["largest_position"]["symbol"]
                
                # Get the client for this exchange
                if exchange_id not in self.exchange_clients:
                    log_event(
                        self.logger,
                        "CIRCUIT_BREAKER_ACTION_ERROR",
                        f"No client for exchange {exchange_id}",
                        level="ERROR"
                    )
                    return
                    
                client = self.exchange_clients[exchange_id]
                
                # Get the current position
                position = await client.get_position(symbol)
                if not position:
                    return
                    
                # Calculate the amount to reduce
                current_quantity = Decimal(str(position.get("quantity", 0)))
                reduce_quantity = abs(current_quantity) * Decimal(str(reduction_percentage)) / Decimal("100")
                
                # Reduce the position
                result = await client.update_position(
                    symbol=symbol,
                    reduce_quantity=reduce_quantity
                )
                
                action_result = result
                positions_affected = {symbol: position}
                
            elif action == "close_position":
                # Close the largest position or specific positions
                symbols = parameters.get("symbols", [])
                close_all = parameters.get("close_all", False)
                
                positions_closed = {}
                
                if close_all:
                    # Close all positions across all exchanges
                    for exchange_id, exchange_positions in self.positions.items():
                        if exchange_id not in self.exchange_clients:
                            continue
                            
                        client = self.exchange_clients[exchange_id]
                        
                        for symbol in exchange_positions:
                            try:
                                result = await client.close_position(symbol)
                                positions_closed[f"{exchange_id}:{symbol}"] = result
                            except Exception as e:
                                log_event(
                                    self.logger,
                                    "POSITION_CLOSE_ERROR",
                                    f"Error closing position {symbol} on {exchange_id}: {str(e)}",
                                    level="ERROR"
                                )
                                
                elif symbols:
                    # Close specific symbols
                    for symbol_spec in symbols:
                        # Symbol spec can be "exchange_id:symbol" or just "symbol"
                        parts = symbol_spec.split(":")
                        if len(parts) > 1:
                            exchange_id, symbol = parts
                        else:
                            # If exchange not specified, use the exchange with the largest position
                            symbol = parts[0]
                            exchange_id = None
                            
                            # Find the exchange with this symbol
                            for exc_id, exchange_positions in self.positions.items():
                                if symbol in exchange_positions:
                                    exchange_id = exc_id
                                    break
                        
                        if not exchange_id or exchange_id not in self.exchange_clients:
                            continue
                            
                        client = self.exchange_clients[exchange_id]
                        
                        try:
                            result = await client.close_position(symbol)
                            positions_closed[f"{exchange_id}:{symbol}"] = result
                        except Exception as e:
                            log_event(
                                self.logger,
                                "POSITION_CLOSE_ERROR",
                                f"Error closing position {symbol} on {exchange_id}: {str(e)}",
                                level="ERROR"
                            )
                else:
                    # Close the largest position
                    if not risk_metrics.get("largest_position"):
                        return
                        
                    exchange_id = risk_metrics["largest_position"]["exchange"]
                    symbol = risk_metrics["largest_position"]["symbol"]
                    
                    if exchange_id not in self.exchange_clients:
                        return
                        
                    client = self.exchange_clients[exchange_id]
                    
                    try:
                        result = await client.close_position(symbol)
                        positions_closed[f"{exchange_id}:{symbol}"] = result
                    except Exception as e:
                        log_event(
                            self.logger,
                            "POSITION_CLOSE_ERROR",
                            f"Error closing position {symbol} on {exchange_id}: {str(e)}",
                            level="ERROR"
                        )
                
                action_result = {"positions_closed": positions_closed}
                positions_affected = positions_closed
                
            elif action == "pause_trading":
                # Set a flag to pause trading
                # This would need to be integrated with a trading strategy manager
                pass
            
            # Notify callbacks
            for callback in self.on_circuit_breaker_callbacks:
                try:
                    callback(breaker, {
                        "trigger_values": trigger_values,
                        "action_result": action_result,
                        "positions_affected": positions_affected
                    })
                except Exception as e:
                    log_event(
                        self.logger,
                        "CIRCUIT_BREAKER_CALLBACK_ERROR",
                        f"Error in circuit breaker callback: {str(e)}",
                        level="ERROR"
                    )
            
            # Update the event with the action results
            await self.circuit_breaker_repository.update_event(
                breaker.id,
                action_result=action_result,
                positions_affected=positions_affected
            )
            
        except Exception as e:
            log_event(
                self.logger,
                "CIRCUIT_BREAKER_ACTION_ERROR",
                f"Error executing circuit breaker action: {str(e)}",
                level="ERROR",
                context={
                    "account_id": self.account_id,
                    "circuit_breaker_id": breaker.id,
                    "name": breaker.name,
                    "action": action,
                    "error": str(e)
                }
            )
    
    def _get_equity_at_time(self, target_time: datetime) -> Optional[float]:
        """
        Get the total equity at a specific time from the balance history.
        
        Args:
            target_time: The target time to get the equity for
            
        Returns:
            The equity at the target time, or None if not available
        """
        if not self.balance_history:
            return None
        
        # Find the closest entry before or at the target time
        closest_entry = None
        min_time_diff = None
        
        for entry in self.balance_history:
            entry_time = entry["timestamp"]
            if entry_time <= target_time:
                time_diff = (target_time - entry_time).total_seconds()
                if min_time_diff is None or time_diff < min_time_diff:
                    min_time_diff = time_diff
                    closest_entry = entry
        
        if closest_entry:
            return closest_entry["equity"]
        
        # If no entry found before the target time, use the earliest available
        return self.balance_history[0]["equity"] if self.balance_history else None
    
    def register_risk_update_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register a callback for risk metric updates.
        
        Args:
            callback: Function to call with risk metrics
        """
        self.on_risk_update_callbacks.append(callback)
    
    def register_circuit_breaker_callback(
        self, callback: Callable[[CircuitBreaker, Dict[str, Any]], None]
    ) -> None:
        """
        Register a callback for circuit breaker events.
        
        Args:
            callback: Function to call when a circuit breaker is triggered
        """
        self.on_circuit_breaker_callbacks.append(callback)
    
    def register_position_update_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register a callback for position updates.
        
        Args:
            callback: Function to call with position updates
        """
        self.on_position_update_callbacks.append(callback) 