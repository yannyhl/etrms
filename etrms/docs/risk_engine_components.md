# Risk Engine Components

This document outlines the components of the Risk Engine in the Enhanced Trading Risk Management System (ETRMS), including their purpose, functionality, and API endpoints.

## Overview

The Risk Engine is the core component of the ETRMS responsible for monitoring positions, calculating risk metrics, enforcing risk limits through circuit breakers, and providing position sizing recommendations. It consists of several key components:

1. **RiskMonitor**: Monitors positions and account information across exchanges
2. **CircuitBreaker**: Defines and enforces risk limits through automated actions
3. **Risk Metrics Calculator**: Calculates basic and advanced risk metrics
4. **Position Sizing Engine**: Provides optimal position size recommendations

## RiskMonitor

The `RiskMonitor` class is the central component of the Risk Engine. It connects to exchanges, monitors positions and account information, calculates risk metrics, and evaluates circuit breaker conditions.

### Key Features

- **Multi-Exchange Support**: Monitors positions across multiple exchanges
- **Real-time Monitoring**: Fetches data at configurable intervals
- **Risk Metrics Calculation**: Computes both basic and advanced risk metrics
- **Circuit Breaker Integration**: Evaluates risk conditions and takes automated actions
- **WebSocket Broadcasting**: Sends real-time updates via WebSockets
- **Configuration Management**: Saves and loads risk configurations

### Usage Example

```python
# Initialize a risk monitor
risk_monitor = RiskMonitor(refresh_interval=5)  # Refresh every 5 seconds

# Add exchanges to monitor
await risk_monitor.add_exchange("binance", api_key="YOUR_API_KEY", api_secret="YOUR_API_SECRET")
await risk_monitor.add_exchange("hyperliquid", api_key="YOUR_API_KEY", api_secret="YOUR_API_SECRET")

# Add symbols to monitor
await risk_monitor.add_symbol("BTCUSDT")
await risk_monitor.add_symbol("ETHUSDT")

# Start monitoring
await risk_monitor.start_monitoring()

# Set up default circuit breakers
await risk_monitor.setup_default_circuit_breakers()

# Calculate risk metrics
risk_metrics = await risk_monitor.calculate_risk_metrics()

# Calculate advanced risk metrics
advanced_metrics = await risk_monitor.calculate_advanced_risk_metrics()

# Calculate optimal position size
position_size = await risk_monitor.calculate_optimal_position_size(
    symbol="BTCUSDT",
    risk_per_trade=0.01,
    win_rate=0.55,
    reward_risk_ratio=2.0
)

# Stop monitoring
await risk_monitor.stop_monitoring()
```

## CircuitBreaker

The `CircuitBreaker` class defines and enforces risk limits through automated actions. It evaluates conditions and executes actions when conditions are met.

### Key Features

- **Flexible Condition Definitions**: Supports multiple condition types
- **Automated Actions**: Executes predefined actions when conditions are met
- **Filtering by Symbol and Exchange**: Conditions can be limited to specific symbols or exchanges
- **Enable/Disable Support**: Conditions can be enabled or disabled as needed
- **Alert Broadcasting**: Sends alerts when conditions are triggered

### Condition Types

- **Maximum Drawdown**: Triggers when drawdown exceeds a threshold
- **Maximum Position Size**: Triggers when position size exceeds a threshold
- **PnL-based**: Triggers based on unrealized or realized PnL
- **Trailing Stop**: Implements a trailing stop based on price movement
- **Consecutive Losses**: Triggers after a specified number of consecutive losses
- **Time-based**: Triggers when a position has been open for too long
- **Volatility-based**: Triggers when market volatility exceeds a threshold

### Action Types

- **Close Position**: Closes the position by creating a market order
- **Cancel All Orders**: Cancels all open orders
- **Reduce Position Size**: Reduces the position size by a specified percentage

### Usage Example

```python
from risk.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerCondition,
    max_drawdown_condition,
    close_position_action
)

# Create a circuit breaker
circuit_breaker = CircuitBreaker()

# Add a condition
circuit_breaker.add_condition(
    CircuitBreakerCondition(
        name="max_drawdown_10_percent",
        description="Maximum drawdown of 10%",
        evaluation_fn=max_drawdown_condition(0.1),
        action_fn=close_position_action,
        symbols=["BTCUSDT", "ETHUSDT"],
        exchanges=["binance"],
        enabled=True
    )
)

# Evaluate conditions
triggered_conditions = await circuit_breaker.evaluate_all(
    exchanges={"binance": binance_client},
    context={
        "positions": positions,
        "risk_metrics": risk_metrics,
        "timestamp": time.time()
    }
)
```

## Risk Metrics Calculator

The Risk Engine calculates a wide range of risk metrics, from basic position values to advanced risk measures.

### Basic Risk Metrics

- **Total Equity**: Total account value across all exchanges
- **Total Position Value**: Value of all open positions
- **Largest Position**: Information about the largest position
- **Highest Leverage**: Information about the position with the highest leverage
- **Total Unrealized PnL**: Total unrealized profit or loss
- **Exposure Percentage**: Position value as a percentage of equity
- **Drawdown**: Daily, weekly, and monthly drawdown metrics

### Advanced Risk Metrics

- **Value at Risk (VaR)**: Potential loss with 95%, 99%, and 99.5% confidence levels
- **Conditional VaR (Expected Shortfall)**: Expected loss beyond VaR
- **Correlation Matrix**: Correlation between different positions
- **Stress Test Results**: Portfolio impact under different market scenarios
- **Kelly Criterion**: Optimal position sizing based on win rate and profit/loss ratio
- **Maximum Drawdown Metrics**: Historical and current drawdown analysis

## Position Sizing Engine

The Position Sizing Engine provides optimal position size recommendations based on various algorithms.

### Sizing Algorithms

- **Risk-Based Sizing**: Based on a percentage of account equity
- **Kelly Criterion**: Optimal position size based on edge and risk
- **Volatility Adjustment**: Adjusts position size based on market volatility
- **Max Leverage Calculation**: Recommends maximum safe leverage

### Usage Example

```python
# Calculate optimal position size
position_size = await risk_monitor.calculate_optimal_position_size(
    symbol="BTCUSDT",
    risk_per_trade=0.01,
    win_rate=0.55,
    reward_risk_ratio=2.0
)

# Access position sizing recommendations
quantity = position_size["quantity"]
kelly_quantity = position_size["kelly_quantity"]
volatility_adjusted_quantity = position_size["volatility_adjusted_quantity"]
max_leverage = position_size["max_recommended_leverage"]
```

## API Endpoints

The Risk Engine exposes several API endpoints for managing risk:

### Risk Metrics

- `GET /api/risk/metrics`: Get basic risk metrics
- `GET /api/risk/advanced-metrics`: Get advanced risk metrics

### Circuit Breakers

- `GET /api/risk/circuit-breakers`: Get all circuit breaker conditions
- `POST /api/risk/circuit-breakers`: Add a circuit breaker condition
- `DELETE /api/risk/circuit-breakers/{name}`: Remove a circuit breaker condition
- `PUT /api/risk/circuit-breakers/{name}/enable`: Enable a circuit breaker condition
- `PUT /api/risk/circuit-breakers/{name}/disable`: Disable a circuit breaker condition
- `POST /api/risk/evaluate`: Manually evaluate circuit breaker conditions
- `POST /api/risk/setup-default-circuit-breakers`: Set up default circuit breakers

### Position Sizing

- `GET /api/risk/position-sizing/{symbol}`: Calculate optimal position size

### Configuration Management

- `POST /api/risk/configurations`: Save risk configuration
- `GET /api/risk/configurations/{config_id}`: Load risk configuration

## Conclusion

The Risk Engine provides a comprehensive solution for monitoring and managing trading risk. By using the RiskMonitor, CircuitBreaker, and position sizing functionality, traders can implement robust risk management practices and automate risk mitigation actions. 