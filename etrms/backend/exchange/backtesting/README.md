# ETRMS Backtesting Module

This module provides a comprehensive backtesting framework for the Enhanced Trading Risk Management System (ETRMS). It allows users to test trading strategies, risk management configurations, and circuit breaker settings using historical data.

## Components

The backtesting module consists of the following key components:

1. **BacktestingClient**: Implements the `ExchangeInterface` for backtesting purposes, simulating exchange behavior with historical data.
2. **BacktestingEngine**: Orchestrates the backtesting process, managing the environment setup, running simulations, and generating reports.
3. **Integration with Risk Management**: Full integration with the `RiskMonitor` and `CircuitBreaker` systems.

## Getting Started

### 1. Download Historical Data

Before running backtests, you need to download historical data. Use the provided script:

```bash
python -m etrms.backend.scripts.download_historical_data \
    --exchange binance \
    --symbols BTCUSDT,ETHUSDT \
    --timeframes 1h,4h,1d \
    --start 2022-01-01 \
    --end 2023-01-01
```

Options:
- `--exchange`: Exchange to download data from (`binance`, `hyperliquid`, or `all`)
- `--symbols`: Comma-separated list of symbols
- `--timeframes`: Comma-separated list of timeframes
- `--start`: Start date in YYYY-MM-DD format
- `--end`: End date in YYYY-MM-DD format
- `--api-key`: API key (for Binance)
- `--api-secret`: API secret (for Binance)
- `--testnet`: Use testnet (for Binance)

### 2. Create a Backtest Configuration

You can create a backtest configuration through the API or UI. The configuration includes:

- Symbols and exchanges to include
- Date range for the backtest
- Initial capital and leverage settings
- Circuit breaker configurations
- Additional parameters specific to the backtest type

Example API request:

```json
POST /api/v1/backtest
{
  "name": "BTC Trend Following",
  "description": "Testing a simple trend following strategy on BTC",
  "type": "standard",
  "start_date": "2022-01-01T00:00:00Z",
  "end_date": "2022-12-31T23:59:59Z",
  "exchanges": ["binance"],
  "symbols": ["BTCUSDT"],
  "timeframe": "1h",
  "initial_capital": 10000.0,
  "circuit_breakers": [
    {
      "type": "MAX_DRAWDOWN",
      "threshold": 0.1,
      "action": "CLOSE_POSITIONS",
      "enabled": true
    }
  ],
  "parameters": {
    "risk_per_trade": 0.02,
    "leverage": 3
  }
}
```

### 3. Run the Backtest

Backtests are run asynchronously through the `BacktestService`. You can start a backtest through the API:

```
POST /api/v1/backtest/{backtest_id}/run
```

### 4. View Results

Once the backtest is complete, you can view the results through the API or UI:

```
GET /api/v1/backtest/{backtest_id}
```

The results include:
- Performance metrics (total return, max drawdown, Sharpe ratio, etc.)
- Trade history
- Circuit breaker events
- Equity curve data

## Advanced Usage

### Custom Strategies

You can implement custom strategies by creating a strategy function that takes the following parameters:

```python
async def my_strategy(
    client: BacktestingClient,
    risk_monitor: RiskMonitor,
    current_time: datetime
) -> None:
    # Implement your strategy logic here
    pass
```

Then pass this function to the `BacktestingEngine`:

```python
engine = BacktestingEngine(
    start_date="2022-01-01",
    end_date="2022-12-31",
    initial_balance=10000.0,
    symbols=["BTCUSDT"],
    timeframe="1h",
    strategy=my_strategy
)
```

### Parameter Optimization

For parameter optimization backtests, specify the parameters to optimize and their ranges:

```json
POST /api/v1/backtest
{
  "name": "Parameter Optimization",
  "type": "optimization",
  "start_date": "2022-01-01T00:00:00Z",
  "end_date": "2022-12-31T23:59:59Z",
  "exchanges": ["binance"],
  "symbols": ["BTCUSDT"],
  "timeframe": "1h",
  "initial_capital": 10000.0,
  "parameters": {
    "optimization_target": "sharpe_ratio",
    "parameters_to_optimize": {
      "stop_loss_percent": {
        "start": 0.01,
        "end": 0.05,
        "step": 0.01
      },
      "take_profit_percent": {
        "start": 0.02,
        "end": 0.1,
        "step": 0.02
      }
    }
  }
}
```

### Monte Carlo Simulations

For Monte Carlo simulations, specify the number of simulations and the parameters to randomize:

```json
POST /api/v1/backtest
{
  "name": "Monte Carlo Simulation",
  "type": "monte_carlo",
  "start_date": "2022-01-01T00:00:00Z",
  "end_date": "2022-12-31T23:59:59Z",
  "exchanges": ["binance"],
  "symbols": ["BTCUSDT"],
  "timeframe": "1h",
  "initial_capital": 10000.0,
  "parameters": {
    "num_simulations": 100,
    "randomize_parameters": {
      "slippage": {
        "min": 0.0001,
        "max": 0.001
      },
      "win_rate": {
        "min": 0.4,
        "max": 0.6
      }
    }
  }
}
```

## Circuit Breaker Testing

The backtesting module allows you to test different circuit breaker configurations to find the optimal settings for your trading strategy. You can configure multiple circuit breakers with different conditions and actions.

Example circuit breaker configuration:

```json
{
  "circuit_breakers": [
    {
      "type": "MAX_DRAWDOWN",
      "threshold": 0.1,
      "action": "CLOSE_POSITIONS",
      "enabled": true,
      "symbols": ["BTCUSDT"],
      "exchanges": ["binance"],
      "description": "Close all positions if drawdown exceeds 10%"
    },
    {
      "type": "CONSECUTIVE_LOSSES",
      "threshold": 3,
      "action": "REDUCE_POSITION",
      "enabled": true,
      "description": "Reduce position size after 3 consecutive losses"
    }
  ]
}
```

## Performance Metrics

The backtesting module calculates the following performance metrics:

- **Total Return**: The total percentage return of the strategy
- **Annualized Return**: The annualized percentage return
- **Max Drawdown**: The maximum peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted return (using risk-free rate of 0%)
- **Sortino Ratio**: Downside risk-adjusted return
- **Win Rate**: Percentage of winning trades
- **Profit Factor**: Gross profit divided by gross loss
- **Average Win/Loss**: Average profit of winning trades vs. average loss of losing trades
- **Risk/Reward Ratio**: Average risk per trade vs. average reward
- **Maximum Consecutive Wins/Losses**: Longest streak of winning/losing trades
- **Recovery Factor**: Total return divided by max drawdown
- **Calmar Ratio**: Annualized return divided by max drawdown

## Data Visualization

The backtesting UI provides the following visualizations:

- **Equity Curve**: Chart showing the growth of equity over time
- **Drawdown Chart**: Visualization of drawdowns throughout the backtest
- **Trade Distribution**: Histogram of trade returns
- **Monthly Returns**: Heatmap of monthly returns
- **Circuit Breaker Events**: Timeline of circuit breaker triggers

## Troubleshooting

### Common Issues

1. **Missing Historical Data**: Ensure you've downloaded the required historical data for the symbols and timeframes you want to backtest.
2. **Memory Issues**: For large backtests, you may need to increase the memory allocation for the application.
3. **Slow Performance**: Consider using a smaller date range or fewer symbols for faster results.

### Logging

The backtesting module logs detailed information about the backtest process. Check the logs for any errors or warnings:

```
tail -f logs/backtest.log
```

## Future Enhancements

Planned enhancements for the backtesting module include:

1. **Advanced Strategy Testing**: Support for custom strategy implementations, strategy optimization with genetic algorithms, and multi-asset portfolio backtesting.
2. **Market Condition Analysis**: Regime detection and performance by regime, correlation analysis between assets, and volatility modeling and stress testing.
3. **Machine Learning Integration**: Feature importance analysis, model-based strategy development, and anomaly detection in trading patterns. 