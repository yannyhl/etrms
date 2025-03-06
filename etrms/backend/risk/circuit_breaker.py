"""
Enhanced Trading Risk Management System Circuit Breaker

This module provides circuit breaker functionality to automatically 
take risk mitigation actions when predefined conditions are met.
"""
import asyncio
import importlib
from typing import Dict, List, Any, Optional, Callable, Awaitable, Tuple
import time

from exchange import ExchangeInterface
from utils.logger import get_logger, log_event


# Get risk monitor for alert broadcasting (import dynamically to avoid circular imports)
def _get_risk_monitor():
    """Dynamically import the RiskMonitor to avoid circular imports"""
    try:
        from risk.monitor import RiskMonitor
        # Get the singleton instance if possible
        module = importlib.import_module("api.accounts")
        get_risk_monitor = getattr(module, "get_risk_monitor", None)
        if get_risk_monitor:
            return get_risk_monitor()
        return None
    except (ImportError, AttributeError) as e:
        logger = get_logger(__name__)
        logger.warning(f"Unable to get RiskMonitor for alerts: {e}")
        return None


class CircuitBreakerCondition:
    """
    Defines a condition that, when met, triggers a circuit breaker action.
    """
    
    def __init__(
        self, 
        name: str,
        description: str,
        evaluation_fn: Callable[[Dict[str, Any]], bool],
        action_fn: Callable[[ExchangeInterface, Dict[str, Any]], Awaitable[None]],
        symbols: Optional[List[str]] = None,
        exchanges: Optional[List[str]] = None,
        enabled: bool = True
    ):
        """
        Initialize a circuit breaker condition.
        
        Args:
            name: A unique name for the condition.
            description: A description of what the condition checks.
            evaluation_fn: Function that evaluates if the condition is met.
            action_fn: Async function that executes when the condition is met.
            symbols: List of symbols this condition applies to (None for all).
            exchanges: List of exchanges this condition applies to (None for all).
            enabled: Whether this condition is enabled.
        """
        self.name = name
        self.description = description
        self.evaluation_fn = evaluation_fn
        self.action_fn = action_fn
        self.symbols = symbols
        self.exchanges = exchanges
        self.enabled = enabled
    
    def matches_context(self, exchange: str, symbol: Optional[str] = None) -> bool:
        """
        Check if this condition applies to the given exchange and symbol.
        
        Args:
            exchange: The exchange name.
            symbol: The symbol (optional).
            
        Returns:
            True if the condition applies, False otherwise.
        """
        # Check if the exchange matches
        if self.exchanges is not None and exchange not in self.exchanges:
            return False
        
        # Check if the symbol matches (if a symbol is provided)
        if symbol is not None and self.symbols is not None and symbol not in self.symbols:
            return False
            
        return True
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate if the condition is met.
        
        Args:
            context: Context data to evaluate against.
            
        Returns:
            True if the condition is met, False otherwise.
        """
        if not self.enabled:
            return False
            
        return self.evaluation_fn(context)


class CircuitBreaker:
    """
    Circuit Breaker component that monitors for conditions and executes
    risk mitigation actions when necessary.
    """
    
    def __init__(self):
        """
        Initialize the circuit breaker.
        """
        self.logger = get_logger(__name__)
        self.conditions: List[CircuitBreakerCondition] = []
        
        log_event(
            self.logger,
            "CIRCUIT_BREAKER_INIT",
            "Circuit breaker initialized"
        )
    
    def add_condition(self, condition: CircuitBreakerCondition) -> None:
        """
        Add a condition to the circuit breaker.
        
        Args:
            condition: The condition to add.
        """
        self.conditions.append(condition)
        
        log_event(
            self.logger,
            "CONDITION_ADDED",
            f"Added condition: {condition.name}",
            context={
                "condition_name": condition.name,
                "description": condition.description,
                "symbols": condition.symbols,
                "exchanges": condition.exchanges,
                "enabled": condition.enabled
            }
        )
    
    def remove_condition(self, condition_name: str) -> bool:
        """
        Remove a condition from the circuit breaker.
        
        Args:
            condition_name: The name of the condition to remove.
            
        Returns:
            True if the condition was removed, False if it wasn't found.
        """
        for i, condition in enumerate(self.conditions):
            if condition.name == condition_name:
                self.conditions.pop(i)
                
                log_event(
                    self.logger,
                    "CONDITION_REMOVED",
                    f"Removed condition: {condition_name}",
                    context={"condition_name": condition_name}
                )
                
                return True
                
        return False
    
    def enable_condition(self, condition_name: str) -> bool:
        """
        Enable a condition.
        
        Args:
            condition_name: The name of the condition to enable.
            
        Returns:
            True if the condition was enabled, False if it wasn't found.
        """
        for condition in self.conditions:
            if condition.name == condition_name:
                condition.enabled = True
                
                log_event(
                    self.logger,
                    "CONDITION_ENABLED",
                    f"Enabled condition: {condition_name}",
                    context={"condition_name": condition_name}
                )
                
                return True
                
        return False
    
    def disable_condition(self, condition_name: str) -> bool:
        """
        Disable a condition.
        
        Args:
            condition_name: The name of the condition to disable.
            
        Returns:
            True if the condition was disabled, False if it wasn't found.
        """
        for condition in self.conditions:
            if condition.name == condition_name:
                condition.enabled = False
                
                log_event(
                    self.logger,
                    "CONDITION_DISABLED",
                    f"Disabled condition: {condition_name}",
                    context={"condition_name": condition_name}
                )
                
                return True
                
        return False
    
    def get_conditions(self) -> List[Dict[str, Any]]:
        """
        Get all conditions.
        
        Returns:
            List of condition details.
        """
        return [
            {
                "name": condition.name,
                "description": condition.description,
                "symbols": condition.symbols,
                "exchanges": condition.exchanges,
                "enabled": condition.enabled
            }
            for condition in self.conditions
        ]
    
    async def evaluate_all(
        self, 
        exchanges: Dict[str, ExchangeInterface], 
        context: Dict[str, Any]
    ) -> List[Tuple[CircuitBreakerCondition, Any]]:
        """
        Evaluate all conditions and execute actions for triggered conditions.
        
        Args:
            exchanges: Dict mapping exchange names to exchange interfaces.
            context: Context data for evaluating conditions.
            
        Returns:
            List of tuples containing triggered conditions and action results.
        """
        if not self.conditions:
            return []
            
        triggered_conditions = []
        
        for condition in self.conditions:
            # Skip disabled conditions
            if not condition.enabled:
                continue
                
            # Check if condition applies to the context
            exchange_name = context.get("exchange", None)
            symbol = context.get("symbol", None)
            
            if exchange_name and not condition.matches_context(exchange_name, symbol):
                continue
                
            # Evaluate condition
            try:
                condition_met = condition.evaluation_fn(context)
                
                if condition_met:
                    log_event(
                        self.logger,
                        "CIRCUIT_BREAKER_TRIGGERED",
                        f"Circuit breaker condition '{condition.name}' triggered",
                        context={
                            "condition": condition.name,
                            "description": condition.description,
                            "exchange": exchange_name,
                            "symbol": symbol,
                            "metrics": {k: v for k, v in context.items() if k not in ["exchange", "symbol"]}
                        }
                    )
                    
                    # Execute action if the exchange exists
                    action_result = None
                    if exchange_name in exchanges:
                        try:
                            action_result = await condition.action_fn(exchanges[exchange_name], context)
                        except Exception as e:
                            log_event(
                                self.logger,
                                "CIRCUIT_BREAKER_ACTION_ERROR",
                                f"Error executing action for condition '{condition.name}': {str(e)}",
                                level="ERROR"
                            )
                    
                    # Record the triggered condition
                    triggered_conditions.append((condition, action_result))
                    
                    # Broadcast alert
                    await self._broadcast_alert({
                        "type": "circuit_breaker",
                        "condition_name": condition.name,
                        "description": condition.description,
                        "exchange": exchange_name,
                        "symbol": symbol,
                        "triggered_at": time.time(),
                        "context": {k: v for k, v in context.items() 
                                  if k not in ["exchange", "symbol"] and not callable(v)},
                        "action_result": str(action_result) if action_result else None
                    })
            except Exception as e:
                log_event(
                    self.logger,
                    "CIRCUIT_BREAKER_EVALUATION_ERROR",
                    f"Error evaluating condition '{condition.name}': {str(e)}",
                    level="ERROR"
                )
        
        return triggered_conditions
    
    async def _broadcast_alert(self, alert_data: Dict[str, Any]) -> None:
        """
        Broadcast an alert via the RiskMonitor.
        
        Args:
            alert_data: Alert information to broadcast.
        """
        # Get RiskMonitor instance dynamically
        risk_monitor = _get_risk_monitor()
        
        if risk_monitor:
            try:
                await risk_monitor.broadcast_alert(alert_data)
            except Exception as e:
                self.logger.error(f"Error broadcasting circuit breaker alert: {e}")
        else:
            self.logger.warning("Unable to broadcast circuit breaker alert: RiskMonitor not available")


# Common circuit breaker conditions and actions

async def cancel_all_orders_action(exchange: ExchangeInterface, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cancel all orders on the exchange.
    
    Args:
        exchange: The exchange client.
        context: Context data.
        
    Returns:
        Dict with information about the canceled orders.
    """
    symbol = context.get("symbol")
    canceled_orders = await exchange.cancel_all_orders(symbol)
    
    return {
        "action": "cancel_all_orders",
        "symbol": symbol,
        "canceled_count": len(canceled_orders)
    }


async def close_position_action(exchange: ExchangeInterface, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Close a position by creating a market order in the opposite direction.
    
    Args:
        exchange: The exchange client.
        context: Context data.
        
    Returns:
        Dict with information about the closed position.
    """
    position = context.get("position")
    if not position:
        return {"action": "close_position", "status": "no_position"}
    
    symbol = position.get("symbol")
    side = "sell" if position.get("side") == "long" else "buy"
    quantity = position.get("position_amt")
    
    # Cancel existing orders first
    await exchange.cancel_all_orders(symbol)
    
    # Create market order to close position
    order = await exchange.create_order(
        symbol=symbol,
        side=side,
        order_type="market",
        quantity=quantity,
        reduce_only=True
    )
    
    return {
        "action": "close_position",
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "order_id": order.get("order_id")
    }


def max_drawdown_condition(threshold: float) -> Callable[[Dict[str, Any]], bool]:
    """
    Create a condition that triggers when a position's drawdown exceeds a threshold.
    
    Args:
        threshold: The maximum acceptable drawdown as a decimal (e.g., 0.1 for 10%).
        
    Returns:
        Function that evaluates the condition.
    """
    def evaluate(context: Dict[str, Any]) -> bool:
        position = context.get("position")
        if not position:
            return False
        
        entry_price = position.get("entry_price", 0)
        if entry_price == 0:
            return False
            
        mark_price = position.get("mark_price", 0)
        side = position.get("side", "")
        
        if side == "long":
            drawdown = (entry_price - mark_price) / entry_price
        else:  # short
            drawdown = (mark_price - entry_price) / entry_price
            
        return drawdown > threshold
        
    return evaluate


def max_position_size_condition(max_size: float) -> Callable[[Dict[str, Any]], bool]:
    """
    Create a condition that triggers when a position size exceeds a threshold.
    
    Args:
        max_size: The maximum acceptable position size.
        
    Returns:
        Function that evaluates the condition.
    """
    def evaluate(context: Dict[str, Any]) -> bool:
        position = context.get("position")
        if not position:
            return False
            
        position_amt = position.get("position_amt", 0)
        return position_amt > max_size
        
    return evaluate


def create_pnl_condition(
    threshold: float, 
    is_unrealized: bool = True, 
    is_percentage: bool = True
) -> Callable[[Dict[str, Any]], bool]:
    """
    Create a condition that triggers based on PnL.
    
    Args:
        threshold: The threshold value (percentage or absolute).
        is_unrealized: Whether to check unrealized PnL (True) or realized PnL (False).
        is_percentage: Whether threshold is a percentage (True) or absolute value (False).
        
    Returns:
        Function that evaluates the condition.
    """
    def evaluate(context: Dict[str, Any]) -> bool:
        position = context.get("position")
        if not position:
            return False
            
        if is_unrealized:
            pnl = position.get("unrealized_pnl", 0)
        else:
            pnl = position.get("realized_pnl", 0)
            
        if is_percentage:
            # Calculate PnL as a percentage of position value
            position_value = position.get("position_value", 0)
            if position_value == 0:
                return False
                
            pnl_percentage = pnl / position_value
            return pnl_percentage <= threshold
        else:
            # Compare absolute PnL
            return pnl <= threshold
            
    return evaluate 


# Add some additional condition creator functions

def trailing_stop_condition(initial_price: float, trail_percent: float, side: str = "long") -> Callable[[Dict[str, Any]], bool]:
    """
    Create a condition that triggers when price moves against position by trail_percent from the highest/lowest price.
    
    Args:
        initial_price: The initial price when the trailing stop is set.
        trail_percent: The trailing percentage (e.g., 2.0 for 2%).
        side: The position side ('long' or 'short').
        
    Returns:
        A function that evaluates if the trailing stop is triggered.
    """
    trail_factor = trail_percent / 100.0
    best_price = initial_price  # Track the best price seen (highest for long, lowest for short)
    
    def evaluate(context: Dict[str, Any]) -> bool:
        nonlocal best_price
        current_price = context.get("current_price", None)
        
        if current_price is None:
            return False
            
        # Update best price
        if side.lower() == "long" and current_price > best_price:
            best_price = current_price
        elif side.lower() == "short" and current_price < best_price:
            best_price = current_price
            
        # Check if the trailing stop is triggered
        if side.lower() == "long":
            stop_price = best_price * (1 - trail_factor)
            return current_price <= stop_price
        else:  # short
            stop_price = best_price * (1 + trail_factor)
            return current_price >= stop_price
            
    return evaluate


def consecutive_losses_condition(threshold: int) -> Callable[[Dict[str, Any]], bool]:
    """
    Create a condition that triggers when the number of consecutive losses exceeds the threshold.
    
    Args:
        threshold: The maximum number of consecutive losses allowed.
        
    Returns:
        A function that evaluates if the consecutive losses threshold is exceeded.
    """
    def evaluate(context: Dict[str, Any]) -> bool:
        consecutive_losses = context.get("consecutive_losses", 0)
        return consecutive_losses >= threshold
            
    return evaluate


def time_based_condition(max_duration_hours: float) -> Callable[[Dict[str, Any]], bool]:
    """
    Create a condition that triggers when a position has been open for longer than the specified duration.
    
    Args:
        max_duration_hours: The maximum time in hours a position should be held.
        
    Returns:
        A function that evaluates if the position duration exceeds the threshold.
    """
    def evaluate(context: Dict[str, Any]) -> bool:
        position_open_time = context.get("position_open_time", None)
        
        if position_open_time is None:
            return False
            
        # Calculate position duration in hours
        current_time = time.time()
        duration_hours = (current_time - position_open_time) / 3600.0
        
        return duration_hours >= max_duration_hours
            
    return evaluate


def volatility_condition(threshold: float, lookback_periods: int = 14) -> Callable[[Dict[str, Any]], bool]:
    """
    Create a condition that triggers when market volatility exceeds the threshold.
    
    Args:
        threshold: The volatility threshold.
        lookback_periods: The number of periods to calculate volatility over.
        
    Returns:
        A function that evaluates if the market volatility exceeds the threshold.
    """
    def evaluate(context: Dict[str, Any]) -> bool:
        # Get price data from context
        price_data = context.get("price_data", None)
        
        if not price_data or len(price_data) < lookback_periods:
            return False
            
        # Calculate price returns
        returns = []
        for i in range(1, min(lookback_periods + 1, len(price_data))):
            previous_close = float(price_data[i-1]["close"])
            current_close = float(price_data[i]["close"])
            
            if previous_close > 0:
                returns.append((current_close - previous_close) / previous_close)
        
        if not returns:
            return False
            
        # Calculate volatility as standard deviation of returns
        mean_return = sum(returns) / len(returns)
        squared_diffs = [(r - mean_return) ** 2 for r in returns]
        variance = sum(squared_diffs) / len(squared_diffs)
        volatility = variance ** 0.5
        
        # Annualize volatility (assuming daily data)
        annualized_volatility = volatility * (252 ** 0.5)
        
        return annualized_volatility >= threshold
            
    return evaluate


async def reduce_position_size_action(exchange: ExchangeInterface, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Action to reduce position size by a percentage.
    
    Args:
        exchange: The exchange client.
        context: Context data including position information.
        
    Returns:
        Dict containing action result information.
    """
    symbol = context.get("symbol", None)
    reduction_factor = context.get("reduction_factor", 0.5)  # Default to 50% reduction
    
    if not symbol:
        return {"status": "error", "message": "Symbol not provided in context"}
    
    try:
        # Get the current position
        position = await exchange.get_position(symbol)
        
        if not position or float(position.get("position_amt", 0)) == 0:
            return {"status": "warning", "message": f"No open position found for {symbol}"}
        
        # Calculate the amount to reduce
        position_size = float(position.get("position_amt", 0))
        reduction_amount = position_size * reduction_factor
        
        # Determine the side (opposite of position side)
        position_side = position.get("side", "long")
        order_side = "sell" if position_side == "long" else "buy"
        
        # Create the reduction order
        order = await exchange.create_order(
            symbol=symbol,
            side=order_side,
            order_type="MARKET",
            quantity=reduction_amount,
            reduce_only=True
        )
        
        return {
            "status": "success",
            "message": f"Reduced position size for {symbol} by {reduction_factor * 100:.1f}%",
            "order": order
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error reducing position size for {symbol}: {str(e)}"
        } 