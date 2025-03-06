"""
Enhanced Trading Risk Management System Backtesting Engine

This module provides the main backtesting engine for running and managing backtests
of the ETRMS.
"""
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Coroutine

from exchange.backtesting.backtesting_client import BacktestingClient
from risk.monitor import RiskMonitor
from utils.logger import get_logger, log_event


class BacktestingEngine:
    """
    Backtesting engine for the ETRMS.
    
    This class manages the process of running backtests, including:
    - Setting up the backtesting environment
    - Loading historical data
    - Running simulations
    - Collecting and analyzing results
    - Generating performance reports
    """
    
    def __init__(
        self,
        start_date: str,
        end_date: str,
        initial_balance: float = 10000.0,
        data_path: str = "data/historical",
        symbols: List[str] = ["BTCUSDT", "ETHUSDT"],
        timeframe: str = "1h",
        fee_rate: float = 0.0004,
        slippage: float = 0.0001,
        risk_per_trade: float = 0.01,
        strategy: Optional[Callable[[BacktestingClient, RiskMonitor, datetime], Coroutine[Any, Any, None]]] = None
    ):
        """
        Initialize the backtesting engine.
        
        Args:
            start_date: Start date for the backtest in 'YYYY-MM-DD' format
            end_date: End date for the backtest in 'YYYY-MM-DD' format
            initial_balance: Initial account balance
            data_path: Path to historical data directory
            symbols: List of symbols to include in the backtest
            timeframe: Timeframe for historical data ('1m', '5m', '1h', '1d', etc.)
            fee_rate: Trading fee rate
            slippage: Simulated slippage
            risk_per_trade: Risk per trade as a percentage of account balance
            strategy: Optional strategy function to run on each time step
        """
        self.logger = get_logger(__name__)
        
        # Backtesting parameters
        self.start_date = start_date
        self.end_date = end_date
        self.initial_balance = initial_balance
        self.data_path = data_path
        self.symbols = symbols
        self.timeframe = timeframe
        self.fee_rate = fee_rate
        self.slippage = slippage
        self.risk_per_trade = risk_per_trade
        self.strategy = strategy
        
        # Backtesting components
        self.client = None
        self.risk_monitor = None
        
        # Results
        self.results = {}
        
        log_event(
            self.logger,
            "BACKTEST_ENGINE_INIT",
            "Initializing backtesting engine",
            context={
                "start_date": start_date,
                "end_date": end_date,
                "initial_balance": initial_balance,
                "symbols": symbols,
                "timeframe": timeframe
            }
        )
    
    async def setup(self) -> None:
        """
        Set up the backtesting environment.
        """
        # Create backtesting client
        self.client = BacktestingClient(
            initial_balance=self.initial_balance,
            start_date=self.start_date,
            end_date=self.end_date,
            data_path=self.data_path,
            fee_rate=self.fee_rate,
            slippage=self.slippage
        )
        
        # Initialize the client
        await self.client.initialize()
        
        # Load historical data for all symbols
        for symbol in self.symbols:
            success = await self.client.load_historical_data(symbol, self.timeframe)
            if not success:
                log_event(
                    self.logger,
                    "BACKTEST_DATA_LOAD_ERROR",
                    f"Failed to load historical data for {symbol}",
                    level="ERROR",
                    context={"symbol": symbol, "timeframe": self.timeframe}
                )
                raise ValueError(f"Failed to load historical data for {symbol}")
                
            # Try to load orderbook data if available
            await self.client.load_orderbook_snapshots(symbol)
        
        # Create risk monitor
        self.risk_monitor = RiskMonitor()
        
        # Add the exchange to the risk monitor
        await self.risk_monitor.add_exchange("backtest", client=self.client)
        
        # Add symbols to monitor
        for symbol in self.symbols:
            await self.risk_monitor.add_symbol(symbol)
        
        # Start monitoring
        await self.risk_monitor.start_monitoring()
        
        log_event(
            self.logger,
            "BACKTEST_SETUP_COMPLETE",
            "Backtesting setup complete",
            context={"symbols": self.symbols, "timeframe": self.timeframe}
        )
    
    async def run(self) -> Dict[str, Any]:
        """
        Run the backtest.
        
        Returns:
            Dict containing the results of the backtest.
        """
        if not self.client or not self.risk_monitor:
            await self.setup()
        
        # Parse dates
        start = datetime.strptime(self.start_date, "%Y-%m-%d")
        end = datetime.strptime(self.end_date, "%Y-%m-%d")
        
        # Define time step based on timeframe
        time_step = self._get_time_step(self.timeframe)
        
        # Set current time to start date
        current_time = start
        
        # Run simulation
        while current_time <= end:
            # Process time step in the backtesting client
            self.client.process_time_step(current_time)
            
            # Run strategy if provided
            if self.strategy:
                await self.strategy(self.client, self.risk_monitor, current_time)
            
            # Step to next time point
            current_time += time_step
            
            # Log progress periodically
            if current_time.day != (current_time - time_step).day:
                progress = (current_time - start).days / (end - start).days * 100
                log_event(
                    self.logger,
                    "BACKTEST_PROGRESS",
                    f"Backtesting progress: {progress:.1f}%",
                    context={"current_date": current_time.strftime("%Y-%m-%d"), "progress": progress}
                )
        
        # Calculate performance metrics
        metrics = self.client.calculate_performance_metrics()
        
        # Store results
        self.results = {
            "performance_metrics": metrics,
            "equity_history": [(dt.isoformat(), equity) for dt, equity in self.client.equity_history],
            "trade_history": self.client.trade_history
        }
        
        log_event(
            self.logger,
            "BACKTEST_COMPLETE",
            "Backtesting completed",
            context={
                "total_return": metrics["total_return"],
                "total_trades": metrics["total_trades"],
                "win_rate": metrics["win_rate"],
                "max_drawdown": metrics["max_drawdown"]
            }
        )
        
        return self.results
    
    def save_results(self, filename: str) -> None:
        """
        Save the backtest results to a file.
        
        Args:
            filename: The name of the file to save to.
        """
        if not self.results:
            raise ValueError("No results to save. Run the backtest first.")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Save results to file
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)
        
        log_event(
            self.logger,
            "BACKTEST_RESULTS_SAVED",
            f"Backtest results saved to {filename}",
            context={"filename": filename}
        )
    
    def generate_report(self, filename: str) -> None:
        """
        Generate a detailed HTML report of the backtest results.
        
        Args:
            filename: The name of the file to save the report to.
        """
        if not self.results:
            raise ValueError("No results to generate report from. Run the backtest first.")
        
        # This would generate an HTML report with charts and tables
        # A simple implementation for now, to be enhanced later
        
        metrics = self.results["performance_metrics"]
        
        # Create HTML report
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ETRMS Backtest Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                .metric {{ margin-bottom: 10px; }}
                .metric span {{ font-weight: bold; }}
                .positive {{ color: green; }}
                .negative {{ color: red; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
        </head>
        <body>
            <h1>ETRMS Backtest Report</h1>
            <h2>Backtest Settings</h2>
            <div class="metric">Period: <span>{self.start_date}</span> to <span>{self.end_date}</span></div>
            <div class="metric">Symbols: <span>{', '.join(self.symbols)}</span></div>
            <div class="metric">Timeframe: <span>{self.timeframe}</span></div>
            <div class="metric">Initial Balance: <span>${self.initial_balance:,.2f}</span></div>
            
            <h2>Performance Metrics</h2>
            <div class="metric">Final Equity: <span>${metrics["final_equity"]:,.2f}</span></div>
            <div class="metric">Total Return: <span class="{'positive' if metrics['total_return'] >= 0 else 'negative'}">{metrics["total_return"]:.2f}%</span></div>
            <div class="metric">Total Trades: <span>{metrics["total_trades"]}</span></div>
            <div class="metric">Win Rate: <span>{metrics["win_rate"]:.2f}%</span></div>
            <div class="metric">Profit Factor: <span>{metrics["profit_factor"]:.2f}</span></div>
            <div class="metric">Maximum Drawdown: <span class="negative">{metrics["max_drawdown"]:.2f}%</span></div>
            <div class="metric">Average Profit: <span class="positive">${metrics["avg_profit"]:,.2f}</span></div>
            <div class="metric">Average Loss: <span class="negative">${metrics["avg_loss"]:,.2f}</span></div>
            
            <h2>Trade History</h2>
            <table>
                <tr>
                    <th>Timestamp</th>
                    <th>Symbol</th>
                    <th>Side</th>
                    <th>Quantity</th>
                    <th>Price</th>
                    <th>P&L</th>
                </tr>
        """
        
        # Add trade rows
        for trade in self.results["trade_history"]:
            timestamp = datetime.fromtimestamp(trade["timestamp"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
            pnl_class = "positive" if trade["realized_pnl"] >= 0 else "negative"
            
            html += f"""
                <tr>
                    <td>{timestamp}</td>
                    <td>{trade["symbol"]}</td>
                    <td>{trade["side"]}</td>
                    <td>{trade["quantity"]:.4f}</td>
                    <td>${trade["price"]:.2f}</td>
                    <td class="{pnl_class}">${trade["realized_pnl"]:.2f}</td>
                </tr>
            """
        
        html += """
            </table>
        </body>
        </html>
        """
        
        # Save HTML report
        with open(filename, "w") as f:
            f.write(html)
        
        log_event(
            self.logger,
            "BACKTEST_REPORT_GENERATED",
            f"Backtest report generated at {filename}",
            context={"filename": filename}
        )
    
    def _get_time_step(self, timeframe: str) -> timedelta:
        """
        Get time step based on timeframe.
        
        Args:
            timeframe: The timeframe string (e.g., '1m', '5m', '1h', '1d').
            
        Returns:
            A timedelta representing the time step.
        """
        # Parse timeframe
        if timeframe.endswith('m'):
            minutes = int(timeframe[:-1])
            return timedelta(minutes=minutes)
        elif timeframe.endswith('h'):
            hours = int(timeframe[:-1])
            return timedelta(hours=hours)
        elif timeframe.endswith('d'):
            days = int(timeframe[:-1])
            return timedelta(days=days)
        elif timeframe.endswith('w'):
            weeks = int(timeframe[:-1])
            return timedelta(weeks=weeks)
        else:
            raise ValueError(f"Unsupported timeframe: {timeframe}")


async def run_backtest(
    start_date: str,
    end_date: str,
    initial_balance: float = 10000.0,
    data_path: str = "data/historical",
    symbols: List[str] = ["BTCUSDT", "ETHUSDT"],
    timeframe: str = "1h",
    fee_rate: float = 0.0004,
    slippage: float = 0.0001,
    risk_per_trade: float = 0.01,
    strategy: Optional[Callable[[BacktestingClient, RiskMonitor, datetime], Coroutine[Any, Any, None]]] = None,
    save_results: bool = True,
    generate_report: bool = True
) -> Dict[str, Any]:
    """
    Run a backtest with the specified parameters.
    
    Args:
        start_date: Start date for the backtest in 'YYYY-MM-DD' format
        end_date: End date for the backtest in 'YYYY-MM-DD' format
        initial_balance: Initial account balance
        data_path: Path to historical data directory
        symbols: List of symbols to include in the backtest
        timeframe: Timeframe for historical data ('1m', '5m', '1h', '1d', etc.)
        fee_rate: Trading fee rate
        slippage: Simulated slippage
        risk_per_trade: Risk per trade as a percentage of account balance
        strategy: Optional strategy function to run on each time step
        save_results: Whether to save results to a file
        generate_report: Whether to generate an HTML report
        
    Returns:
        Dict containing the results of the backtest.
    """
    # Create backtesting engine
    engine = BacktestingEngine(
        start_date=start_date,
        end_date=end_date,
        initial_balance=initial_balance,
        data_path=data_path,
        symbols=symbols,
        timeframe=timeframe,
        fee_rate=fee_rate,
        slippage=slippage,
        risk_per_trade=risk_per_trade,
        strategy=strategy
    )
    
    # Run backtest
    results = await engine.run()
    
    # Save results
    if save_results:
        results_dir = "results/backtests"
        os.makedirs(results_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{results_dir}/backtest_{timestamp}.json"
        engine.save_results(filename)
    
    # Generate report
    if generate_report:
        reports_dir = "results/reports"
        os.makedirs(reports_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{reports_dir}/backtest_report_{timestamp}.html"
        engine.generate_report(filename)
    
    return results 