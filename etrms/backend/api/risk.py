"""
Enhanced Trading Risk Management System Risk API

This module provides endpoints for managing risk settings and circuit breakers.
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, Request
from datetime import datetime
from sqlalchemy.orm import Session

from config.settings import settings
from exchange import ExchangeClientFactory
from risk import RiskMonitor, CircuitBreaker, CircuitBreakerCondition
from risk.circuit_breaker import (
    max_drawdown_condition, 
    max_position_size_condition, 
    create_pnl_condition,
    close_position_action,
    cancel_all_orders_action,
    trailing_stop_condition,
    consecutive_losses_condition,
    time_based_condition,
    volatility_condition,
    reduce_position_size_action
)
from api.accounts import get_risk_monitor
from data.database import get_db

# Create a router instance
router = APIRouter()

# Create a circuit breaker instance
circuit_breaker = CircuitBreaker()


async def get_circuit_breaker():
    """
    Dependency to get the circuit breaker instance.
    
    Returns:
        The circuit breaker instance.
    """
    return circuit_breaker


@router.get("/circuit-breakers", summary="Get all circuit breaker conditions")
async def get_circuit_breakers(
    breaker: CircuitBreaker = Depends(get_circuit_breaker)
) -> Dict[str, Any]:
    """
    Get all circuit breaker conditions.
    
    Returns:
        Dict containing circuit breaker conditions.
    """
    return {
        "conditions": breaker.get_conditions()
    }


@router.post("/circuit-breakers", summary="Add a circuit breaker condition")
async def add_circuit_breaker(
    name: str = Body(..., description="Unique name for the condition"),
    description: str = Body(..., description="Description of the condition"),
    condition_type: str = Body(..., description="Type of condition (max_drawdown, max_position_size, pnl, trailing_stop, consecutive_losses, time_based, volatility)"),
    threshold: float = Body(..., description="Threshold value"),
    action: str = Body(..., description="Action to take (close_position, cancel_all_orders, reduce_position_size)"),
    symbols: Optional[List[str]] = Body(None, description="Symbols this condition applies to (None for all)"),
    exchanges: Optional[List[str]] = Body(None, description="Exchanges this condition applies to (None for all)"),
    enabled: bool = Body(True, description="Whether the condition is enabled"),
    additional_params: Optional[Dict[str, Any]] = Body(None, description="Additional parameters for specific condition types"),
    breaker: CircuitBreaker = Depends(get_circuit_breaker)
) -> Dict[str, Any]:
    """
    Add a new circuit breaker condition.
    
    Args:
        name: Unique name for the condition.
        description: Description of the condition.
        condition_type: Type of condition.
        threshold: Threshold value.
        action: Action to take when the condition is met.
        symbols: Symbols this condition applies to (None for all).
        exchanges: Exchanges this condition applies to (None for all).
        enabled: Whether the condition is enabled.
        additional_params: Additional parameters for specific condition types.
        
    Returns:
        Dict containing status information.
    """
    # Check if a condition with this name already exists
    existing_conditions = breaker.get_conditions()
    for condition in existing_conditions:
        if condition["name"] == name:
            return {
                "status": "error",
                "message": f"A condition with name '{name}' already exists"
            }
    
    # Create the evaluation function based on condition type
    evaluation_fn = None
    if condition_type == "max_drawdown":
        evaluation_fn = max_drawdown_condition(threshold)
    elif condition_type == "max_position_size":
        evaluation_fn = max_position_size_condition(threshold)
    elif condition_type == "pnl":
        is_percentage = additional_params.get("is_percentage", True) if additional_params else True
        is_unrealized = additional_params.get("is_unrealized", True) if additional_params else True
        evaluation_fn = create_pnl_condition(threshold, is_unrealized, is_percentage)
    elif condition_type == "trailing_stop":
        # Need additional parameters for trailing stop
        if not additional_params or "initial_price" not in additional_params or "side" not in additional_params:
            return {
                "status": "error",
                "message": "Trailing stop requires 'initial_price' and 'side' in additional_params"
            }
        initial_price = additional_params["initial_price"]
        side = additional_params["side"]
        evaluation_fn = trailing_stop_condition(initial_price, threshold, side)
    elif condition_type == "consecutive_losses":
        evaluation_fn = consecutive_losses_condition(int(threshold))
    elif condition_type == "time_based":
        evaluation_fn = time_based_condition(threshold)  # threshold is max hours
    elif condition_type == "volatility":
        lookback_periods = additional_params.get("lookback_periods", 14) if additional_params else 14
        evaluation_fn = volatility_condition(threshold, lookback_periods)
    else:
        return {
            "status": "error",
            "message": f"Unknown condition type: {condition_type}"
        }
    
    # Create the action function
    action_fn = None
    if action == "close_position":
        action_fn = close_position_action
    elif action == "cancel_all_orders":
        action_fn = cancel_all_orders_action
    elif action == "reduce_position_size":
        action_fn = reduce_position_size_action
    else:
        return {
            "status": "error",
            "message": f"Unknown action type: {action}"
        }
    
    # Create the condition
    condition = CircuitBreakerCondition(
        name=name,
        description=description,
        evaluation_fn=evaluation_fn,
        action_fn=action_fn,
        symbols=symbols,
        exchanges=exchanges,
        enabled=enabled
    )
    
    # Add the condition to the circuit breaker
    breaker.add_condition(condition)
    
    return {
        "status": "success",
        "message": f"Added circuit breaker condition: {name}",
        "condition": {
            "name": name,
            "description": description,
            "condition_type": condition_type,
            "threshold": threshold,
            "action": action,
            "symbols": symbols,
            "exchanges": exchanges,
            "enabled": enabled
        }
    }


@router.delete("/circuit-breakers/{name}", summary="Remove a circuit breaker condition")
async def remove_circuit_breaker(
    name: str = Path(..., description="Name of the condition to remove"),
    breaker: CircuitBreaker = Depends(get_circuit_breaker)
) -> Dict[str, Any]:
    """
    Remove a circuit breaker condition.
    
    Args:
        name: Name of the condition to remove.
        
    Returns:
        Dict containing the result of the operation.
    """
    result = breaker.remove_condition(name)
    
    if result:
        return {
            "status": "condition_removed",
            "name": name
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=f"No condition found with the name '{name}'."
        )


@router.put("/circuit-breakers/{name}/enable", summary="Enable a circuit breaker condition")
async def enable_circuit_breaker(
    name: str = Path(..., description="Name of the condition to enable"),
    breaker: CircuitBreaker = Depends(get_circuit_breaker)
) -> Dict[str, Any]:
    """
    Enable a circuit breaker condition.
    
    Args:
        name: Name of the condition to enable.
        
    Returns:
        Dict containing the result of the operation.
    """
    result = breaker.enable_condition(name)
    
    if result:
        return {
            "status": "condition_enabled",
            "name": name
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=f"No condition found with the name '{name}'."
        )


@router.put("/circuit-breakers/{name}/disable", summary="Disable a circuit breaker condition")
async def disable_circuit_breaker(
    name: str = Path(..., description="Name of the condition to disable"),
    breaker: CircuitBreaker = Depends(get_circuit_breaker)
) -> Dict[str, Any]:
    """
    Disable a circuit breaker condition.
    
    Args:
        name: Name of the condition to disable.
        
    Returns:
        Dict containing the result of the operation.
    """
    result = breaker.disable_condition(name)
    
    if result:
        return {
            "status": "condition_disabled",
            "name": name
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=f"No condition found with the name '{name}'."
        )


@router.post("/evaluate", summary="Manually evaluate circuit breaker conditions")
async def evaluate_circuit_breakers(
    breaker: CircuitBreaker = Depends(get_circuit_breaker),
    monitor: RiskMonitor = Depends(get_risk_monitor)
) -> Dict[str, Any]:
    """
    Manually evaluate all circuit breaker conditions against current data.
    
    Returns:
        Dict containing evaluation results.
    """
    # Check if monitoring is active
    if not monitor.is_monitoring:
        return {
            "status": "error",
            "message": "Position monitoring is not active. Start monitoring first."
        }
    
    # Get all exchanges
    exchanges = monitor.exchanges
    
    # Get all positions
    all_positions = await monitor.get_all_positions()
    
    # Get risk metrics
    risk_metrics = await monitor.calculate_risk_metrics()
    
    # Track triggered conditions
    triggered_conditions = []
    
    # Evaluate each position
    for position in all_positions:
        # Prepare context for evaluation
        exchange_name = position["exchange"]
        symbol = position["symbol"]
        
        context = {
            "exchange": exchange_name,
            "symbol": symbol,
            "position": position,
            "risk_metrics": risk_metrics,
            "current_price": position.get("mark_price", 0),
            "position_size": position.get("position_amt", 0),
            "leverage": position.get("leverage", 1),
            "unrealized_pnl": position.get("unrealized_pnl", 0),
            "unrealized_pnl_percentage": position.get("unrealized_pnl_percentage", 0),
            "drawdown": {
                "daily": risk_metrics.get("drawdown", {}).get("daily", 0),
                "weekly": risk_metrics.get("drawdown", {}).get("weekly", 0),
                "monthly": risk_metrics.get("drawdown", {}).get("monthly", 0)
            }
        }
        
        # Evaluate circuit breakers
        try:
            exchange = exchanges.get(exchange_name)
            if exchange:
                results = await breaker.evaluate_all(
                    exchanges={exchange_name: exchange},
                    context=context
                )
                
                # Add to triggered conditions
                for condition, result in results:
                    triggered_conditions.append({
                        "condition_name": condition.name,
                        "description": condition.description,
                        "exchange": exchange_name,
                        "symbol": symbol,
                        "result": result
                    })
        except Exception as e:
            # Log error but continue with other positions
            pass
    
    # Also evaluate account-wide conditions
    for exchange_name, exchange in exchanges.items():
        account_info = monitor.account_info.get(exchange_name, {})
        
        # Prepare context for evaluation
        context = {
            "exchange": exchange_name,
            "account_info": account_info,
            "risk_metrics": risk_metrics,
            "drawdown": {
                "daily": risk_metrics.get("drawdown", {}).get("daily", 0),
                "weekly": risk_metrics.get("drawdown", {}).get("weekly", 0),
                "monthly": risk_metrics.get("drawdown", {}).get("monthly", 0)
            },
            "exposure_percentage": risk_metrics.get("exposure_percentage", 0)
        }
        
        # Evaluate circuit breakers
        try:
            results = await breaker.evaluate_all(
                exchanges={exchange_name: exchange},
                context=context
            )
            
            # Add to triggered conditions
            for condition, result in results:
                triggered_conditions.append({
                    "condition_name": condition.name,
                    "description": condition.description,
                    "exchange": exchange_name,
                    "result": result
                })
        except Exception as e:
            # Log error but continue with other exchanges
            pass
    
    return {
        "status": "success",
        "triggered_conditions": triggered_conditions,
        "total_conditions": len(breaker.conditions),
        "total_triggered": len(triggered_conditions)
    }


@router.get("/metrics")
async def get_risk_metrics(request: Request):
    """Get current risk metrics for all monitored accounts and positions.
    
    Returns risk metrics for all monitored positions across exchanges, including 
    drawdown, exposure percentages, and other key risk indicators.
    """
    try:
        monitor = request.app.state.risk_monitor
        if not monitor or not monitor.is_monitoring:
            return {
                "status": "error",
                "message": "Risk monitoring is not active"
            }
        
        # Calculate risk metrics from the monitor
        risk_metrics = await monitor.calculate_risk_metrics()
        
        # Broadcast the metrics through WebSocket if they've changed
        try:
            prev_metrics = getattr(request.app.state, 'previous_risk_metrics', None)
            if not prev_metrics or has_metrics_changed(prev_metrics, risk_metrics):
                await broadcast_risk_metrics_update(risk_metrics)
                request.app.state.previous_risk_metrics = risk_metrics
        except Exception as e:
            logger.error(f"Failed to broadcast risk metrics: {str(e)}")
        
        return {
            "status": "success",
            "data": risk_metrics
        }
    except Exception as e:
        logger.error(f"Error in get_risk_metrics: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to get risk metrics: {str(e)}"
        }

def has_metrics_changed(prev_metrics, current_metrics, threshold=0.01):
    """Check if risk metrics have changed significantly.
    
    Args:
        prev_metrics: Previous metrics
        current_metrics: Current metrics
        threshold: Change threshold (percentage as decimal)
        
    Returns:
        bool: True if metrics have changed significantly
    """
    if not prev_metrics:
        return True
    
    # Check for changes in key metrics
    key_numeric_fields = [
        'total_equity', 'total_position_value', 'total_unrealized_pnl', 
        'exposure_percentage', 'position_count'
    ]
    
    for field in key_numeric_fields:
        if field in prev_metrics and field in current_metrics:
            prev_value = prev_metrics[field]
            current_value = current_metrics[field]
            
            # Skip if either value is None or zero
            if prev_value is None or current_value is None:
                continue
                
            if prev_value == 0:
                if current_value != 0:
                    return True
            else:
                # Calculate percentage change
                pct_change = abs((current_value - prev_value) / prev_value)
                if pct_change > threshold:
                    return True
    
    # Check nested structures like drawdown
    if 'drawdown' in prev_metrics and 'drawdown' in current_metrics:
        for period in ['daily', 'weekly', 'monthly']:
            if period in prev_metrics['drawdown'] and period in current_metrics['drawdown']:
                prev_value = prev_metrics['drawdown'][period]
                current_value = current_metrics['drawdown'][period]
                
                if prev_value is None or current_value is None:
                    continue
                    
                if abs(current_value - prev_value) > threshold * 100:  # Drawdown is in percent
                    return True
    
    # Check for changes in positions by exchange
    if 'positions_by_exchange' in prev_metrics and 'positions_by_exchange' in current_metrics:
        # Check if exchanges have changed
        prev_exchanges = set(prev_metrics['positions_by_exchange'].keys())
        current_exchanges = set(current_metrics['positions_by_exchange'].keys())
        
        if prev_exchanges != current_exchanges:
            return True
            
        # Check each exchange's metrics
        for exchange in prev_exchanges.intersection(current_exchanges):
            prev_exchange_data = prev_metrics['positions_by_exchange'].get(exchange, {})
            current_exchange_data = current_metrics['positions_by_exchange'].get(exchange, {})
            
            # Check position count
            if prev_exchange_data.get('position_count') != current_exchange_data.get('position_count'):
                return True
                
            # Check position value
            prev_value = prev_exchange_data.get('position_value')
            current_value = current_exchange_data.get('position_value')
            
            if prev_value and current_value and prev_value > 0:
                pct_change = abs((current_value - prev_value) / prev_value)
                if pct_change > threshold:
                    return True
    
    return False

async def broadcast_risk_metrics_update(risk_metrics):
    """Broadcast risk metrics update to all connected WebSocket clients.
    
    Args:
        risk_metrics: The risk metrics data to broadcast
    """
    try:
        # Import the broadcast function dynamically
        from .websocket import broadcast_risk_metrics
        
        # Broadcast the update
        await broadcast_risk_metrics({
            "type": "risk_metrics_update",
            "timestamp": datetime.now().isoformat(),
            "risk_metrics": risk_metrics
        })
        
        logger.info("Broadcasted risk metrics update")
    except ImportError:
        logger.error("Failed to import broadcast_risk_metrics function")
    except Exception as e:
        logger.error(f"Error broadcasting risk metrics: {str(e)}")


@router.get("/advanced-metrics", summary="Get advanced risk metrics")
async def get_advanced_risk_metrics(
    monitor: RiskMonitor = Depends(get_risk_monitor)
) -> Dict[str, Any]:
    """
    Get advanced risk metrics including Value at Risk (VaR), 
    correlation matrix, stress test results, and more.
    
    Returns:
        Dict containing advanced risk metrics.
    """
    try:
        metrics = await monitor.calculate_advanced_risk_metrics()
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": str(e)
        }


@router.get("/position-sizing/{symbol}", summary="Calculate optimal position size")
async def calculate_position_size(
    symbol: str = Path(..., description="Trading symbol (e.g., BTCUSDT)"),
    risk_per_trade: float = Query(0.01, description="Risk per trade as a decimal (e.g., 0.01 for 1%)"),
    win_rate: float = Query(0.5, description="Estimated win rate as a decimal (e.g., 0.5 for 50%)"),
    reward_risk_ratio: float = Query(2.0, description="Reward to risk ratio (e.g., 2.0)"),
    monitor: RiskMonitor = Depends(get_risk_monitor)
) -> Dict[str, Any]:
    """
    Calculate the optimal position size for a trade using various sizing algorithms,
    including Kelly Criterion and risk-based sizing.
    
    Parameters:
        symbol: The symbol to trade (e.g., BTCUSDT)
        risk_per_trade: Risk per trade as a decimal (e.g., 0.01 for 1%)
        win_rate: Estimated win rate as a decimal (e.g., 0.5 for 50%)
        reward_risk_ratio: Reward to risk ratio (e.g., 2.0)
    
    Returns:
        Dict containing position sizing recommendations.
    """
    try:
        sizing_data = await monitor.calculate_optimal_position_size(
            symbol=symbol,
            risk_per_trade=risk_per_trade,
            win_rate=win_rate,
            reward_risk_ratio=reward_risk_ratio
        )
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "position_sizing": sizing_data
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": str(e)
        }


@router.post("/configurations", summary="Save risk configuration")
async def save_risk_configuration(
    config_id: str = Body(..., description="Configuration ID"),
    account_id: str = Body(..., description="Account ID"),
    monitor: RiskMonitor = Depends(get_risk_monitor),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Save the current risk configuration with circuit breaker settings.
    
    Parameters:
        config_id: Configuration ID to save under
        account_id: Account ID to associate with the configuration
    
    Returns:
        Dict containing the saved configuration.
    """
    try:
        config = await monitor.save_risk_configuration(config_id, account_id, db)
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "configuration": config
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": str(e)
        }


@router.get("/configurations/{config_id}", summary="Load risk configuration")
async def load_risk_configuration(
    config_id: str = Path(..., description="Configuration ID to load"),
    account_id: str = Query(..., description="Account ID associated with the configuration"),
    monitor: RiskMonitor = Depends(get_risk_monitor),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Load a saved risk configuration with circuit breaker settings.
    
    Parameters:
        config_id: Configuration ID to load
        account_id: Account ID associated with the configuration
    
    Returns:
        Dict containing the loaded configuration.
    """
    try:
        config = await monitor.load_risk_configuration(config_id, account_id, db)
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "configuration": config
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": str(e)
        }


@router.post("/setup-default-circuit-breakers", summary="Set up default circuit breakers")
async def setup_default_circuit_breakers(
    monitor: RiskMonitor = Depends(get_risk_monitor)
) -> Dict[str, Any]:
    """
    Set up default circuit breaker conditions.
    
    Returns:
        Dict containing status information.
    """
    try:
        await monitor.setup_default_circuit_breakers()
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "message": "Default circuit breakers set up successfully",
            "conditions": monitor.circuit_breaker.get_conditions()
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": str(e)
        }


@router.get("/configurations", summary="Get all risk configurations")
async def get_all_risk_configurations(
    account_id: str = Query(..., description="Account ID"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get all risk configurations for an account.
    
    Parameters:
        account_id: Account ID
    
    Returns:
        Dict containing the list of configurations.
    """
    try:
        from data.repositories import RiskConfigurationRepository
        
        risk_repo = RiskConfigurationRepository()
        configs = risk_repo.get_all_for_account(db, account_id)
        
        config_list = [risk_repo.to_dict(config) for config in configs]
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "configurations": config_list
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": str(e)
        }

@router.get("/circuit-breakers/all", summary="Get all circuit breakers")
async def get_all_circuit_breakers(
    account_id: str = Query(..., description="Account ID"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get all circuit breakers for an account.
    
    Parameters:
        account_id: Account ID
    
    Returns:
        Dict containing the list of circuit breakers.
    """
    try:
        from data.repositories import CircuitBreakerRepository
        
        breaker_repo = CircuitBreakerRepository()
        breakers = breaker_repo.get_all_for_account(db, account_id)
        
        breaker_list = [breaker_repo.to_dict(breaker) for breaker in breakers]
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "circuit_breakers": breaker_list
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": str(e)
        }

@router.post("/circuit-breakers/db", summary="Create a circuit breaker in the database")
async def create_circuit_breaker_db(
    breaker_data: Dict[str, Any] = Body(..., description="Circuit breaker data"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a new circuit breaker in the database.
    
    Parameters:
        breaker_data: Circuit breaker data
    
    Returns:
        Dict containing the created circuit breaker.
    """
    try:
        from data.repositories import CircuitBreakerRepository
        
        breaker_repo = CircuitBreakerRepository()
        breaker = breaker_repo.create(db, breaker_data)
        
        if not breaker:
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "message": "Failed to create circuit breaker"
            }
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "circuit_breaker": breaker_repo.to_dict(breaker)
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": str(e)
        }

@router.put("/circuit-breakers/db/{breaker_id}", summary="Update a circuit breaker in the database")
async def update_circuit_breaker_db(
    breaker_id: int = Path(..., description="Circuit breaker ID"),
    breaker_data: Dict[str, Any] = Body(..., description="Circuit breaker data"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update an existing circuit breaker in the database.
    
    Parameters:
        breaker_id: Circuit breaker ID
        breaker_data: Circuit breaker data
    
    Returns:
        Dict containing the updated circuit breaker.
    """
    try:
        from data.repositories import CircuitBreakerRepository
        
        breaker_repo = CircuitBreakerRepository()
        breaker = breaker_repo.update(db, breaker_id, breaker_data)
        
        if not breaker:
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "message": f"Circuit breaker with ID {breaker_id} not found"
            }
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "circuit_breaker": breaker_repo.to_dict(breaker)
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": str(e)
        }

@router.delete("/circuit-breakers/db/{breaker_id}", summary="Delete a circuit breaker from the database")
async def delete_circuit_breaker_db(
    breaker_id: int = Path(..., description="Circuit breaker ID"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Delete a circuit breaker from the database.
    
    Parameters:
        breaker_id: Circuit breaker ID
    
    Returns:
        Dict containing the status of the operation.
    """
    try:
        from data.repositories import CircuitBreakerRepository
        
        breaker_repo = CircuitBreakerRepository()
        success = breaker_repo.delete(db, breaker_id)
        
        if not success:
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "message": f"Circuit breaker with ID {breaker_id} not found"
            }
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "message": f"Circuit breaker with ID {breaker_id} deleted"
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": str(e)
        }

@router.put("/circuit-breakers/db/{breaker_id}/enable", summary="Enable a circuit breaker")
async def enable_circuit_breaker_db(
    breaker_id: int = Path(..., description="Circuit breaker ID"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Enable a circuit breaker.
    
    Parameters:
        breaker_id: Circuit breaker ID
    
    Returns:
        Dict containing the updated circuit breaker.
    """
    try:
        from data.repositories import CircuitBreakerRepository
        
        breaker_repo = CircuitBreakerRepository()
        breaker = breaker_repo.enable(db, breaker_id)
        
        if not breaker:
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "message": f"Circuit breaker with ID {breaker_id} not found"
            }
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "circuit_breaker": breaker_repo.to_dict(breaker)
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": str(e)
        }

@router.put("/circuit-breakers/db/{breaker_id}/disable", summary="Disable a circuit breaker")
async def disable_circuit_breaker_db(
    breaker_id: int = Path(..., description="Circuit breaker ID"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Disable a circuit breaker.
    
    Parameters:
        breaker_id: Circuit breaker ID
    
    Returns:
        Dict containing the updated circuit breaker.
    """
    try:
        from data.repositories import CircuitBreakerRepository
        
        breaker_repo = CircuitBreakerRepository()
        breaker = breaker_repo.disable(db, breaker_id)
        
        if not breaker:
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "message": f"Circuit breaker with ID {breaker_id} not found"
            }
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "circuit_breaker": breaker_repo.to_dict(breaker)
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": str(e)
        }

@router.get("/circuit-breakers/db/{breaker_id}/events", summary="Get circuit breaker events")
async def get_circuit_breaker_events(
    breaker_id: int = Path(..., description="Circuit breaker ID"),
    limit: int = Query(100, description="Maximum number of events to return"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get events for a circuit breaker.
    
    Parameters:
        breaker_id: Circuit breaker ID
        limit: Maximum number of events to return
    
    Returns:
        Dict containing the list of events.
    """
    try:
        from data.repositories import CircuitBreakerRepository
        
        breaker_repo = CircuitBreakerRepository()
        events = breaker_repo.get_events(db, breaker_id, limit)
        
        event_list = [breaker_repo.event_to_dict(event) for event in events]
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "events": event_list
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": str(e)
        } 