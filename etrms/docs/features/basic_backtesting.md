# Basic Backtesting

## Overview

Basic Backtesting is the foundation of the ETRMS strategy evaluation framework, allowing traders to test trading strategies against historical market data. This feature simulates the execution of a trading strategy over a specified time period, recording trades, calculating performance metrics, and visualizing results to help users understand how a strategy would have performed in the past.

## Purpose

The primary purposes of Basic Backtesting are:

1. **Performance Assessment**: Evaluate how a trading strategy would have performed historically
2. **Strategy Validation**: Verify that a strategy's logic works as intended
3. **Risk Analysis**: Understand potential drawdowns and risk exposure
4. **Metric Generation**: Calculate various performance indicators (win rate, profit factor, etc.)
5. **Trade Log Creation**: Generate detailed logs of all trades for further analysis
6. **Hypothesis Testing**: Test trading ideas before risking real capital

## How Basic Backtesting Works

The ETRMS Basic Backtesting engine follows these steps:

1. **Data Preparation**: Historical market data is retrieved and prepared for the selected symbols and timeframe
2. **Strategy Initialization**: The selected trading strategy is initialized with the specified parameters
3. **Market Simulation**: Historical data is fed to the strategy one candle at a time, simulating the passage of time
4. **Trade Execution**: When the strategy generates buy/sell signals, the system simulates trade execution
5. **Account Tracking**: The system tracks account balance, position size, and equity throughout the simulation
6. **Performance Calculation**: After simulation, comprehensive performance metrics are calculated
7. **Result Visualization**: Results are displayed through charts, tables, and downloadable reports

## Using Basic Backtesting

### Prerequisites

Before running a backtest, you need:
- A defined trading strategy to test
- Access to historical market data for relevant trading pairs
- A basic understanding of backtest configuration parameters

### Running a Backtest

1. Navigate to the "Backtesting" section in the ETRMS interface
2. Select the "Basic Backtest" tab
3. Configure the backtest settings:
   - Select a trading strategy
   - Choose trading symbols
   - Set date range and timeframe
   - Configure initial balance, fees, and slippage
   - Set strategy-specific parameters
4. Click "Run Backtest" to start the simulation

### Backtest Parameters

- **Strategy Name**: The trading strategy to test
- **Symbols**: Trading pairs to include in the backtest (e.g., BTC/USDT, ETH/USDT)
- **Start Date and End Date**: The historical period to analyze
- **Timeframe**: The candle interval (1m, 5m, 15m, 1h, 4h, 1d, etc.)
- **Initial Balance**: Starting account balance for the simulation
- **Fee Rate**: Trading fee percentage applied to each trade
- **Slippage**: Simulated execution slippage percentage
- **Risk Per Trade**: Maximum percentage of account to risk per trade (if applicable)
- **Strategy Parameters**: Specific parameters required by the selected strategy

## Interpreting Results

The Basic Backtesting results are presented in several sections:

### Summary Metrics

Key performance indicators including:
- Total Return (percentage and absolute)
- Number of Trades (total, winning, losing)
- Win Rate
- Average Win and Loss
- Maximum Drawdown
- Profit Factor
- Sharpe Ratio
- Sortino Ratio
- Average Holding Time

### Equity Curve

A line chart showing:
- Account equity over time
- Drawdown periods highlighted
- Benchmark comparison (optional)
- Trade entry and exit points

### Drawdown Analysis

Details about equity retracements:
- Maximum drawdown (largest peak-to-trough decline)
- Drawdown duration
- Recovery time
- Drawdown distribution

### Trade List

Detailed table of all executed trades:
- Entry and exit dates/times
- Entry and exit prices
- Position size
- Profit/loss (absolute and percentage)
- Duration
- Trade notes

### Monthly/Yearly Breakdown

Performance aggregated by time periods:
- Monthly returns table and heatmap
- Yearly summary
- Day-of-week analysis
- Hour-of-day analysis (for intraday strategies)

### Trade Distribution

Charts showing the distribution of:
- Trade profits and losses
- Trade durations
- Winning and losing streaks

## Common Use Cases

### Strategy Development

During strategy development:
- Test initial strategy ideas quickly
- Identify potential issues or edge cases
- Refine entry and exit conditions

### Performance Comparison

To compare different approaches:
- Test multiple strategies under identical conditions
- Compare strategy variants with different parameters
- Benchmark against market indices or alternative strategies

### Risk Assessment

To understand risk profile:
- Analyze maximum drawdown and recovery periods
- Examine worst-case scenarios
- Assess risk-adjusted returns

## Best Practices

1. **Avoid Overfitting**: Be cautious of strategies that work perfectly on historical data but may fail in the future
2. **Use Realistic Settings**: Configure fees, slippage, and execution delays that match real-world conditions
3. **Test Different Market Conditions**: Evaluate performance across bull markets, bear markets, and sideways markets
4. **Start with Low Complexity**: Begin with simple strategies before adding complexity
5. **Consider Sample Size**: Ensure your backtest includes enough trades for statistical significance
6. **Verify Data Quality**: Check for data gaps, errors, or biases in your historical data
7. **Account for Survivorship Bias**: Be aware that delisted or failed assets may not appear in historical data

## Advanced Features

### Custom Indicators

Create and use custom technical indicators in your backtest:
- Import external indicators
- Develop proprietary indicators
- Combine multiple indicators

### Position Sizing Options

Configure different position sizing methods:
- Fixed size
- Percentage of equity
- Risk-based sizing (fixed percentage risk)
- Kelly criterion
- Custom sizing functions

### Filter Conditions

Apply additional filters to strategy signals:
- Time-based filters (time of day, day of week)
- Volatility filters
- Volume filters
- Market regime filters

## Limitations

Be aware of these limitations:

1. **Past Performance**: Historical performance does not guarantee future results
2. **Market Impact**: Backtests typically don't account for market impact of large orders
3. **Look-Ahead Bias**: Care must be taken to avoid using future information in strategy logic
4. **Perfect Execution**: Basic backtests may assume perfect execution of orders
5. **Data Limitations**: Historical data may have gaps or inaccuracies

## Next Steps

After running basic backtests, consider these advanced analyses:

1. **Monte Carlo Simulation**: Randomize trade sequence to understand result variability
2. **Parameter Optimization**: Find optimal strategy parameters through systematic testing
3. **Walk-Forward Analysis**: Test strategy robustness using out-of-sample data
4. **Multi-market Testing**: Verify strategy performance across different markets

## Additional Resources

- [Backtesting Best Practices](https://www.investopedia.com/articles/trading/05/030205.asp)
- [Understanding Backtest Statistics](https://www.investopedia.com/terms/s/sharperatio.asp)
- [Common Backtesting Mistakes to Avoid](https://www.tradingview.com/script/SFrMfKLM-The-7-Deadly-Sins-of-Backtesting/) 