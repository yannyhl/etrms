"""
Integration tests for the circuit breaker component of the risk engine.
"""
import pytest
import time
from unittest.mock import AsyncMock, patch

from risk.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerCondition,
    max_drawdown_condition,
    max_position_size_condition,
    trailing_stop_condition,
    consecutive_losses_condition,
    time_based_condition,
    volatility_condition,
    close_position_action,
    cancel_all_orders_action,
    reduce_position_size_action
)
from exchange import ExchangeInterface


@pytest.fixture
def mock_exchange():
    """Create a mock exchange for testing."""
    exchange = AsyncMock(spec=ExchangeInterface)
    
    # Mock close_position method
    exchange.close_position = AsyncMock(return_value={"status": "success", "message": "Position closed"})
    
    # Mock cancel_all_orders method
    exchange.cancel_all_orders = AsyncMock(return_value={"status": "success", "message": "Orders canceled"})
    
    # Mock create_order method for reducing position size
    exchange.create_order = AsyncMock(return_value={"status": "success", "message": "Order created"})
    
    return exchange


@pytest.fixture
def circuit_breaker():
    """Create a circuit breaker instance for testing."""
    return CircuitBreaker()


@pytest.mark.asyncio
async def test_max_drawdown_condition():
    """Test the max_drawdown_condition factory function."""
    # Create a condition that triggers at 10% drawdown
    condition_fn = max_drawdown_condition(10.0)
    
    # Test with a position below the threshold
    context = {
        "entry_price": 50000.0,
        "current_price": 48000.0,
        "side": "long",
        "leverage": 1.0
    }
    assert not condition_fn(context)  # 4% drawdown, shouldn't trigger
    
    # Test with a position above the threshold
    context = {
        "entry_price": 50000.0,
        "current_price": 45000.0,
        "side": "long",
        "leverage": 1.0
    }
    assert condition_fn(context)  # 10% drawdown, should trigger
    
    # Test with a short position
    context = {
        "entry_price": 50000.0,
        "current_price": 55000.0,
        "side": "short",
        "leverage": 1.0
    }
    assert condition_fn(context)  # 10% drawdown for short, should trigger
    
    # Test with leverage
    context = {
        "entry_price": 50000.0,
        "current_price": 47500.0,
        "side": "long",
        "leverage": 2.0
    }
    assert condition_fn(context)  # 5% * 2x leverage = 10% drawdown, should trigger


@pytest.mark.asyncio
async def test_max_position_size_condition():
    """Test the max_position_size_condition factory function."""
    # Create a condition that triggers when position value exceeds 100,000
    condition_fn = max_position_size_condition(100000.0)
    
    # Test with a position below the threshold
    context = {
        "position_value": 50000.0
    }
    assert not condition_fn(context)  # Below threshold, shouldn't trigger
    
    # Test with a position at the threshold
    context = {
        "position_value": 100000.0
    }
    assert condition_fn(context)  # At threshold, should trigger
    
    # Test with a position above the threshold
    context = {
        "position_value": 150000.0
    }
    assert condition_fn(context)  # Above threshold, should trigger


@pytest.mark.asyncio
async def test_trailing_stop_condition():
    """Test the trailing_stop_condition factory function."""
    # Create a condition for a long position with 5% trailing stop from initial price of 50,000
    condition_fn = trailing_stop_condition(50000.0, 5.0, "long")
    
    # Test with price still above trailing stop
    context = {
        "current_price": 48000.0  # 4% below initial, shouldn't trigger
    }
    assert not condition_fn(context)
    
    # Test with price below trailing stop
    context = {
        "current_price": 47000.0  # 6% below initial, should trigger
    }
    assert condition_fn(context)
    
    # Test with a short position
    condition_fn = trailing_stop_condition(50000.0, 5.0, "short")
    
    # Test with price still below trailing stop for short
    context = {
        "current_price": 52000.0  # 4% above initial, shouldn't trigger
    }
    assert not condition_fn(context)
    
    # Test with price above trailing stop for short
    context = {
        "current_price": 53000.0  # 6% above initial, should trigger
    }
    assert condition_fn(context)


@pytest.mark.asyncio
async def test_time_based_condition():
    """Test the time_based_condition factory function."""
    # Create a condition that triggers after 2 hours
    condition_fn = time_based_condition(2.0)
    
    now = time.time()
    one_hour_ago = now - 3600
    three_hours_ago = now - 10800
    
    # Test with a position opened less than 2 hours ago
    context = {
        "open_time": one_hour_ago
    }
    assert not condition_fn(context)  # Less than 2 hours, shouldn't trigger
    
    # Test with a position opened more than 2 hours ago
    context = {
        "open_time": three_hours_ago
    }
    assert condition_fn(context)  # More than 2 hours, should trigger


@pytest.mark.asyncio
async def test_circuit_breaker_add_condition():
    """Test adding conditions to a circuit breaker."""
    # Create a circuit breaker
    breaker = CircuitBreaker()
    
    # Create a condition
    condition = CircuitBreakerCondition(
        name="test_condition",
        description="Test condition",
        evaluation_fn=lambda context: True,
        action_fn=lambda exchange, context: {"status": "success"},
        symbols=["BTCUSDT"],
        exchanges=["binance"],
        enabled=True
    )
    
    # Add the condition
    breaker.add_condition(condition)
    
    # Check that the condition was added
    assert len(breaker.conditions) == 1
    assert breaker.conditions[0] == condition


@pytest.mark.asyncio
async def test_circuit_breaker_remove_condition():
    """Test removing conditions from a circuit breaker."""
    # Create a circuit breaker
    breaker = CircuitBreaker()
    
    # Create and add a condition
    condition = CircuitBreakerCondition(
        name="test_condition",
        description="Test condition",
        evaluation_fn=lambda context: True,
        action_fn=lambda exchange, context: {"status": "success"},
        symbols=["BTCUSDT"],
        exchanges=["binance"],
        enabled=True
    )
    breaker.add_condition(condition)
    
    # Check that the condition was added
    assert len(breaker.conditions) == 1
    
    # Remove the condition
    result = breaker.remove_condition("test_condition")
    
    # Check that the condition was removed
    assert result is True
    assert len(breaker.conditions) == 0
    
    # Try to remove a non-existent condition
    result = breaker.remove_condition("non_existent_condition")
    
    # Check that the removal failed
    assert result is False


@pytest.mark.asyncio
async def test_circuit_breaker_enable_disable_condition():
    """Test enabling and disabling conditions in a circuit breaker."""
    # Create a circuit breaker
    breaker = CircuitBreaker()
    
    # Create and add a condition
    condition = CircuitBreakerCondition(
        name="test_condition",
        description="Test condition",
        evaluation_fn=lambda context: True,
        action_fn=lambda exchange, context: {"status": "success"},
        symbols=["BTCUSDT"],
        exchanges=["binance"],
        enabled=True
    )
    breaker.add_condition(condition)
    
    # Check that the condition is enabled
    assert breaker.conditions[0].enabled is True
    
    # Disable the condition
    result = breaker.disable_condition("test_condition")
    
    # Check that the condition was disabled
    assert result is True
    assert breaker.conditions[0].enabled is False
    
    # Enable the condition
    result = breaker.enable_condition("test_condition")
    
    # Check that the condition was enabled
    assert result is True
    assert breaker.conditions[0].enabled is True


@pytest.mark.asyncio
async def test_circuit_breaker_evaluate_all(mock_exchange):
    """Test evaluating all conditions in a circuit breaker."""
    # Create a circuit breaker
    breaker = CircuitBreaker()
    
    # Create evaluation and action functions
    def always_true(context):
        return True
    
    async def mock_action(exchange, context):
        return {"status": "success", "message": "Action executed"}
    
    # Create and add conditions
    condition1 = CircuitBreakerCondition(
        name="condition1",
        description="Condition 1",
        evaluation_fn=always_true,
        action_fn=mock_action,
        symbols=["BTCUSDT"],
        exchanges=["binance"],
        enabled=True
    )
    breaker.add_condition(condition1)
    
    condition2 = CircuitBreakerCondition(
        name="condition2",
        description="Condition 2",
        evaluation_fn=lambda context: False,  # This condition won't trigger
        action_fn=mock_action,
        symbols=["ETHUSDT"],
        exchanges=["binance"],
        enabled=True
    )
    breaker.add_condition(condition2)
    
    # Create context
    context = {
        "exchange": "binance",
        "symbol": "BTCUSDT",
        "position_value": 100000.0,
        "entry_price": 50000.0,
        "current_price": 45000.0,
        "side": "long"
    }
    
    # Create exchanges dictionary
    exchanges = {"binance": mock_exchange}
    
    # Mock the _broadcast_alert method
    with patch.object(breaker, '_broadcast_alert', new_callable=AsyncMock) as mock_broadcast:
        # Evaluate all conditions
        triggered = await breaker.evaluate_all(exchanges, context)
        
        # Check that one condition was triggered
        assert len(triggered) == 1
        assert triggered[0][0] == condition1
        
        # Check that the action was executed
        assert triggered[0][1]["status"] == "success"
        
        # Check that _broadcast_alert was called
        mock_broadcast.assert_called_once()


@pytest.mark.asyncio
async def test_close_position_action(mock_exchange):
    """Test the close_position_action function."""
    # Create context
    context = {
        "symbol": "BTCUSDT",
        "exchange": "binance"
    }
    
    # Call the action
    result = await close_position_action(mock_exchange, context)
    
    # Check that the exchange.close_position method was called with the correct symbol
    mock_exchange.close_position.assert_called_once_with("BTCUSDT")
    
    # Check that the action returned a success message
    assert result["status"] == "success"
    assert "Position closed" in result["message"]


@pytest.mark.asyncio
async def test_cancel_all_orders_action(mock_exchange):
    """Test the cancel_all_orders_action function."""
    # Create context
    context = {
        "symbol": "BTCUSDT",
        "exchange": "binance"
    }
    
    # Call the action
    result = await cancel_all_orders_action(mock_exchange, context)
    
    # Check that the exchange.cancel_all_orders method was called with the correct symbol
    mock_exchange.cancel_all_orders.assert_called_once_with("BTCUSDT")
    
    # Check that the action returned a success message
    assert result["status"] == "success"
    assert "Orders canceled" in result["message"]


@pytest.mark.asyncio
async def test_reduce_position_size_action(mock_exchange):
    """Test the reduce_position_size_action function."""
    # Create context
    context = {
        "symbol": "BTCUSDT",
        "exchange": "binance",
        "side": "long",
        "size": 1.0,
        "current_price": 50000.0
    }
    
    # Call the action
    result = await reduce_position_size_action(mock_exchange, context)
    
    # Check that the exchange.create_order method was called with the correct parameters
    mock_exchange.create_order.assert_called_once()
    args = mock_exchange.create_order.call_args[0]
    kwargs = mock_exchange.create_order.call_args[1]
    
    # Check symbol and side
    assert "BTCUSDT" in args or kwargs.get("symbol") == "BTCUSDT"
    assert "sell" in args or kwargs.get("side") == "sell"  # Opposite side for long position
    
    # Check that the action returned a success message
    assert result["status"] == "success"
    assert "Position size reduced" in result["message"] 