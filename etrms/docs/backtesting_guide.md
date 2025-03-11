# ETRMS Backtesting System Guide

## Overview

The Enhanced Trading Risk Management System (ETRMS) Backtesting System provides powerful tools for testing and evaluating trading strategies, risk management techniques, and position sizing methods using historical market data. This guide explains how to use the backtesting system effectively.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Historical Data Management](#historical-data-management)
3. [Creating and Using Strategies](#creating-and-using-strategies)
4. [Running Backtests](#running-backtests)
5. [Analyzing Results](#analyzing-results)
6. [Advanced Features](#advanced-features)
7. [API Reference](#api-reference)
8. [Best Practices](#best-practices)

## Getting Started

### Prerequisites

Before using the backtesting system, ensure that:

- You have ETRMS installed and configured properly
- You have API keys for the exchanges you want to use (for downloading historical data)
- You have sufficient disk space for historical data storage

### Components Overview

The backtesting system consists of several key components:

- **Historical Data Downloader**: Downloads and manages historical market data
- **Backtesting Client**: Simulates exchange functionality using historical data
- **Backtesting Engine**: Orchestrates the backtesting process
- **Strategy Factory**: Manages trading strategies
- **Performance Analyzer**: Evaluates and reports backtest results

## Historical Data Management

### Downloading Historical Data

You can download historical data through either the API endpoint or the command-line interface:

#### Using the API

```bash
curl -X POST "http://localhost:8000/api/backtesting/download-data" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "exchange": "binance",
    "symbols": ["BTCUSDT", "ETHUSDT"],
    "timeframes": ["1h", "4h", "1d"],
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "download_orderbooks": false
  }'
```

#### Using the CLI

```bash
python -m exchange.backtesting.historical_data_downloader \
  --exchange binance \
  --symbols BTCUSDT ETHUSDT \
  --timeframes 1h 4h 1d \
  --start_date 2023-01-01 \
  --end_date 2023-12-31
```

### Data Storage Structure

Historical data is stored in the `data/historical` directory by default, with the following structure:

```
data/historical/
├── BTCUSDT_1h.json
├── BTCUSDT_4h.json
├── BTCUSDT_1d.json
├── BTCUSDT_orderbook.json
├── ETHUSDT_1h.json
├── ETHUSDT_4h.json
├── ETHUSDT_1d.json
└── ETHUSDT_orderbook.json
```

### Supported Timeframes

The backtesting system supports the following timeframes:

| Code | Description |
|------|-------------|
| 1m   | 1 minute    |
| 3m   | 3 minutes   |
| 5m   | 5 minutes   |
| 15m  | 15 minutes  |
| 30m  | 30 minutes  |
| 1h   | 1 hour      |
| 2h   | 2 hours     |
| 4h   | 4 hours     |
| 6h   | 6 hours     |
| 8h   | 8 hours     |
| 12h  | 12 hours    |
| 1d   | 1 day       |
| 3d   | 3 days      |
| 1w   | 1 week      |

## Creating and Using Strategies

### Pre-built Strategies

The ETRMS backtesting system comes with several pre-built strategies:

1. **SMA Crossover**: Trades based on the crossing of simple moving averages
2. **RSI Mean Reversion**: Trades based on oversold/overbought conditions using RSI

To use these strategies, simply specify their name when running a backtest.

### Creating Custom Strategies

You can create custom strategies by implementing functions that follow the strategy interface:

```python
async def custom_strategy(
    client: BacktestingClient,
    risk_monitor: RiskMonitor,
    current_time: datetime,
    **kwargs
) -> None:
    """
    Your custom strategy implementation.
    
    Args:
        client: The backtesting client for market data and order execution
        risk_monitor: The risk monitor for risk management
        current_time: The current simulation time
        **kwargs: Additional strategy-specific parameters
    """
    # Your strategy logic here
    pass
```

To register your custom strategy with the strategy factory:

```python
from exchange.backtesting.strategy_factory import StrategyFactory

# Register your strategy
StrategyFactory.register_strategy(
    "my_custom_strategy",
    custom_strategy,
    {
        "name": "My Custom Strategy",
        "description": "This is my custom trading strategy",
        "parameters": {
            "parameter1": {"type": "int", "default": 10, "description": "First parameter"},
            "parameter2": {"type": "float", "default": 0.5, "description": "Second parameter"}
        }
    }
)
```

## Running Backtests

### Using the API

To run a backtest via the API:

```bash
curl -X POST "http://localhost:8000/api/backtesting/run" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "strategy_name": "sma_crossover",
    "symbols": ["BTCUSDT"],
    "timeframe": "1h",
    "initial_balance": 10000.0,
    "fee_rate": 0.0004,
    "slippage": 0.0001,
    "risk_per_trade": 0.01,
    "strategy_params": {
      "fast_period": 20,
      "slow_period": 50
    },
    "save_results": true,
    "generate_report": true
  }'
```

### Using Python Code

You can also run backtests directly from Python code:

```python
import asyncio
from exchange.backtesting.backtesting_engine import run_backtest
from exchange.backtesting.strategy_factory import StrategyFactory

async def main():
    # Get a strategy
    strategy = StrategyFactory.get_strategy(
        "sma_crossover",
        fast_period=20,
        slow_period=50
    )
    
    # Run backtest
    results = await run_backtest(
        start_date="2023-01-01",
        end_date="2023-12-31",
        symbols=["BTCUSDT"],
        timeframe="1h",
        initial_balance=10000.0,
        fee_rate=0.0004,
        slippage=0.0001,
        risk_per_trade=0.01,
        strategy=strategy,
        save_results=True,
        generate_report=True
    )
    
    print(f"Total return: {results['performance_metrics']['total_return_percentage']}%")

asyncio.run(main())
```

### Configuring Risk Parameters

When running backtests, you can configure various risk parameters:

- **initial_balance**: Starting account balance
- **risk_per_trade**: Risk per trade as a percentage of account balance
- **fee_rate**: Trading fee rate
- **slippage**: Simulated slippage
- **RiskMonitor settings**: Circuit breakers and other risk controls

## Analyzing Results

### Performance Metrics

The backtesting system calculates a comprehensive set of performance metrics:

- **Total Return**: Overall profit/loss in both absolute and percentage terms
- **Sharpe Ratio**: Risk-adjusted return metric
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit divided by gross loss
- **Average Trade**: Average profit/loss per trade
- **Recovery Factor**: Total return divided by maximum drawdown
- **Calmar Ratio**: Annualized return divided by maximum drawdown
- **Volatility**: Standard deviation of returns

### Viewing Results

Backtest results can be viewed in several ways:

1. **JSON Results**: Raw results in JSON format
2. **HTML Reports**: Comprehensive visual reports with charts and tables
3. **API Endpoints**: Retrieving results via the API

#### Example HTML Report Content

- Equity curve
- Drawdown chart
- Trade history table
- Monthly returns heatmap
- Performance metrics summary
- Order execution summary
- Position sizing analysis

## Advanced Features

### Optimizing Strategies

You can optimize strategy parameters by running multiple backtests with different parameters:

```python
import asyncio
from itertools import product
from exchange.backtesting.backtesting_engine import run_backtest
from exchange.backtesting.strategy_factory import StrategyFactory

async def optimize_strategy():
    # Define parameter ranges
    fast_periods = range(10, 31, 5)  # 10, 15, 20, 25, 30
    slow_periods = range(30, 101, 10)  # 30, 40, 50, 60, 70, 80, 90, 100
    
    results = []
    
    # Test all combinations
    for fast_period, slow_period in product(fast_periods, slow_periods):
        if fast_period >= slow_period:
            continue
            
        strategy = StrategyFactory.get_strategy(
            "sma_crossover",
            fast_period=fast_period,
            slow_period=slow_period
        )
        
        backtest_result = await run_backtest(
            start_date="2023-01-01",
            end_date="2023-12-31",
            symbols=["BTCUSDT"],
            timeframe="1h",
            strategy=strategy,
            save_results=False,
            generate_report=False
        )
        
        results.append({
            "fast_period": fast_period,
            "slow_period": slow_period,
            "total_return": backtest_result["performance_metrics"]["total_return_percentage"],
            "sharpe_ratio": backtest_result["performance_metrics"]["sharpe_ratio"],
            "max_drawdown": backtest_result["performance_metrics"]["max_drawdown_percentage"]
        })
    
    # Sort by Sharpe ratio (or any other metric)
    results.sort(key=lambda x: x["sharpe_ratio"], reverse=True)
    
    return results

asyncio.run(optimize_strategy())
```

### Walk-Forward Analysis

You can perform walk-forward analysis to test strategy robustness:

1. Divide your historical data into multiple segments
2. Optimize strategy parameters on one segment (in-sample)
3. Test the optimized strategy on the next segment (out-of-sample)
4. Repeat for all segments
5. Analyze the consistency of performance across out-of-sample periods

### Monte Carlo Simulation

You can run Monte Carlo simulations to better understand the range of possible outcomes:

1. Run a backtest to get a list of trade results
2. Randomly resample the trades with replacement
3. Generate multiple equity curves with different trade sequences
4. Analyze the distribution of performance metrics

## API Reference

### Historical Data Endpoints

- `POST /api/backtesting/download-data`: Download historical data
- `GET /api/backtesting/available-data`: List available historical data

### Strategy Endpoints

- `GET /api/backtesting/available-strategies`: List available strategies
- `GET /api/backtesting/strategy/{strategy_name}`: Get strategy details

### Backtest Endpoints

- `POST /api/backtesting/run`: Run a backtest
- `GET /api/backtesting/results/{task_id}`: Get backtest results
- `GET /api/backtesting/reports`: List backtest reports
- `DELETE /api/backtesting/results/{task_id}`: Delete backtest results
- `GET /api/backtesting/comparison`: Compare multiple backtests

## Best Practices

### Avoiding Common Pitfalls

1. **Look-Ahead Bias**: Ensure your strategy does not use future data
2. **Overfitting**: Avoid excessive optimization on a specific time period
3. **Survivorship Bias**: Be aware that some symbols may have been delisted
4. **Transaction Costs**: Always include realistic fees and slippage
5. **Data Quality**: Verify the quality of your historical data

### Performance Optimization

1. **Data Management**: Pre-download and cache historical data
2. **Selective Testing**: Start with shorter periods and fewer symbols for initial tests
3. **Parallel Processing**: For parameter optimization, use multiple processes
4. **Memory Management**: Clear large data structures when no longer needed

### Testing Strategy Robustness

1. **Test across different market conditions**: Bull, bear, and sideways markets
2. **Test across multiple symbols**: Verify strategy works on different instruments
3. **Test across different timeframes**: Confirm strategy effectiveness at different scales
4. **Stress testing**: Test with extreme market conditions
5. **Parameter sensitivity**: Small changes in parameters should not drastically change results

## Conclusion

The ETRMS Backtesting System provides a comprehensive framework for developing, testing, and optimizing trading strategies with robust risk management. By following the guidelines in this documentation, you can make the most of this powerful tool to enhance your trading strategies and overall risk management approach.

## Additional Documentation Resources

For more detailed information about specific backtesting features, please refer to the following resources:

### Feature Documentation

- [Basic Backtesting](features/basic_backtesting.md): Detailed guide to running standard backtests
- [Monte Carlo Simulation](features/monte_carlo_simulation.md): In-depth explanation of Monte Carlo analysis
- [Parameter Optimization](features/parameter_optimization.md): Comprehensive guide to optimizing strategy parameters
- [Walk-Forward Analysis](features/walk_forward_analysis.md): Detailed explanation of walk-forward testing methodology

### API Documentation

- [Backtesting API Reference](api/backtesting_api.md): Complete API documentation with request/response examples

### Module Overview

- [Backtesting Module README](backtesting/README.md): High-level overview of the entire backtesting system

These resources provide comprehensive details about each feature's purpose, methodology, usage instructions, and result interpretation. They are designed for both new users looking to understand the basics and experienced users seeking to leverage advanced features. 