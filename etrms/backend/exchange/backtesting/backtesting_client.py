"""
Enhanced Trading Risk Management System Backtesting Client

This module provides a client for backtesting trading strategies using historical data.
"""
import asyncio
import json
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Callable, Coroutine, Tuple

from exchange.common.exchange_interface import ExchangeInterface
from utils.logger import get_logger, log_event


class BacktestingClient(ExchangeInterface):
    """
    Implementation of the Exchange Interface for backtesting with historical data.
    
    This client simulates exchange behavior for backtesting purposes:
    - Loads historical price data
    - Simulates order execution
    - Tracks positions and balances
    - Provides performance metrics
    
    It maintains the same interface as real exchange clients, allowing the
    risk management system to work seamlessly in both live and backtest modes.
    """
    
    def __init__(
        self,
        initial_balance: float = 10000.0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        data_path: str = "data/historical",
        fee_rate: float = 0.0004,  # 0.04% fee rate (maker + taker / 2)
        slippage: float = 0.0001,  # 0.01% slippage
        latency_ms: int = 0,  # Simulated latency in milliseconds
    ):
        """
        Initialize the backtesting client.
        
        Args:
            initial_balance: Initial account balance in USD
            start_date: Backtest start date in 'YYYY-MM-DD' format
            end_date: Backtest end date in 'YYYY-MM-DD' format 
            data_path: Path to historical data directory
            fee_rate: Trading fee rate (as a decimal)
            slippage: Simulated slippage (as a decimal)
            latency_ms: Simulated latency in milliseconds
        """
        self.logger = get_logger(__name__)
        
        # Backtesting parameters
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.fee_rate = fee_rate
        self.slippage = slippage
        self.latency_ms = latency_ms
        
        # Date handling
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
        self.current_time = self.start_date if self.start_date else datetime.now()
        
        # Data path
        self.data_path = data_path
        
        # State tracking
        self.positions = {}  # symbol -> position
        self.orders = {}  # order_id -> order
        self.order_id_counter = 1
        self.historical_data = {}  # symbol -> candles
        self.order_book_data = {}  # symbol -> order book snapshots
        
        # Performance tracking
        self.equity_history = []  # [(timestamp, equity)]
        self.trade_history = []  # [trade_details]
        self.performance_metrics = {}
        
        # WebSocket simulation
        self.callbacks = {
            'account_update': [],
            'position_update': [],
            'order_update': [],
            'market_update': {},
            'book_update': {}
        }
        
        # Simulated asset prices (latest known price for each symbol)
        self.current_prices = {}
        
        log_event(
            self.logger,
            "BACKTEST_CLIENT_INIT",
            "Initializing backtesting client",
            context={
                "initial_balance": initial_balance,
                "start_date": start_date,
                "end_date": end_date,
                "fee_rate": fee_rate,
                "slippage": slippage
            }
        )
    
    async def initialize(self) -> None:
        """
        Initialize the backtesting client.
        """
        try:
            # Here we would load historical data, but we'll implement that separately
            log_event(
                self.logger,
                "BACKTEST_CLIENT_INITIALIZED",
                "Backtesting client initialized"
            )
        except Exception as e:
            log_event(
                self.logger,
                "BACKTEST_CLIENT_INIT_ERROR",
                f"Error initializing backtesting client: {str(e)}",
                level="ERROR"
            )
            raise
    
    async def close(self) -> None:
        """
        Close the backtesting client.
        """
        # Nothing to close, but implemented to maintain interface compatibility
        log_event(
            self.logger,
            "BACKTEST_CLIENT_CLOSED",
            "Backtesting client closed"
        )
    
    # Additional methods will be implemented in subsequent edits
    
    async def load_historical_data(self, symbol: str, timeframe: str = "1h") -> bool:
        """
        Load historical price data for a symbol from disk.
        
        Args:
            symbol: The trading pair symbol.
            timeframe: Timeframe of the data (e.g., '1m', '5m', '1h', '1d').
            
        Returns:
            True if data was loaded successfully, False otherwise.
        """
        try:
            # Construct filename based on symbol and timeframe
            filename = f"{self.data_path}/{symbol}_{timeframe}.json"
            
            # Load data from file
            with open(filename, "r") as f:
                data = json.load(f)
            
            # Store data in memory
            self.historical_data[symbol] = data
            
            # Set current price
            if data and len(data) > 0:
                # Use the close price of the first candle within our date range
                for candle in data:
                    candle_time = datetime.fromtimestamp(candle[0] / 1000)  # Convert ms to seconds
                    if self.start_date is None or candle_time >= self.start_date:
                        self.current_prices[symbol] = float(candle[4])  # Close price
                        break
            
            log_event(
                self.logger,
                "HISTORICAL_DATA_LOADED",
                f"Loaded historical data for {symbol} ({timeframe})",
                context={"symbol": symbol, "timeframe": timeframe, "candle_count": len(data)}
            )
            
            return True
        except FileNotFoundError:
            log_event(
                self.logger,
                "HISTORICAL_DATA_NOT_FOUND",
                f"Historical data file not found for {symbol} ({timeframe})",
                level="WARNING",
                context={"symbol": symbol, "timeframe": timeframe, "path": f"{self.data_path}/{symbol}_{timeframe}.json"}
            )
            return False
        except Exception as e:
            log_event(
                self.logger,
                "HISTORICAL_DATA_LOAD_ERROR",
                f"Error loading historical data for {symbol}: {str(e)}",
                level="ERROR",
                context={"symbol": symbol, "timeframe": timeframe, "error": str(e)}
            )
            return False
    
    async def load_orderbook_snapshots(self, symbol: str) -> bool:
        """
        Load order book snapshots for a symbol from disk.
        
        Args:
            symbol: The trading pair symbol.
            
        Returns:
            True if data was loaded successfully, False otherwise.
        """
        try:
            # Construct filename based on symbol
            filename = f"{self.data_path}/{symbol}_orderbook.json"
            
            # Load data from file
            with open(filename, "r") as f:
                data = json.load(f)
            
            # Store data in memory
            self.order_book_data[symbol] = data
            
            log_event(
                self.logger,
                "ORDERBOOK_DATA_LOADED",
                f"Loaded order book snapshots for {symbol}",
                context={"symbol": symbol, "snapshot_count": len(data)}
            )
            
            return True
        except FileNotFoundError:
            log_event(
                self.logger,
                "ORDERBOOK_DATA_NOT_FOUND",
                f"Order book data file not found for {symbol}",
                level="WARNING",
                context={"symbol": symbol, "path": f"{self.data_path}/{symbol}_orderbook.json"}
            )
            return False
        except Exception as e:
            log_event(
                self.logger,
                "ORDERBOOK_DATA_LOAD_ERROR",
                f"Error loading order book data for {symbol}: {str(e)}",
                level="ERROR",
                context={"symbol": symbol, "error": str(e)}
            )
            return False
    
    def get_price_at_time(self, symbol: str, timestamp: datetime) -> Optional[float]:
        """
        Get the price of a symbol at a specific time.
        
        Args:
            symbol: The trading pair symbol.
            timestamp: The timestamp to get the price for.
            
        Returns:
            The price at the specified time, or None if not available.
        """
        if symbol not in self.historical_data:
            return None
        
        # Convert timestamp to milliseconds
        timestamp_ms = int(timestamp.timestamp() * 1000)
        
        # Find the appropriate candle
        # Assuming candles are sorted by time in ascending order
        candles = self.historical_data[symbol]
        
        for i, candle in enumerate(candles):
            candle_time = candle[0]  # Open time in milliseconds
            
            if i == len(candles) - 1 or candles[i + 1][0] > timestamp_ms:
                # This is the candle that contains our timestamp
                # Use the close price as an approximation
                return float(candle[4])
        
        return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get the current price of a symbol.
        
        Args:
            symbol: The trading pair symbol.
            
        Returns:
            The current price, or None if not available.
        """
        return self.current_prices.get(symbol)
    
    def update_time(self, new_time: datetime) -> None:
        """
        Update the current simulation time.
        
        This is called during backtesting to advance the simulation time.
        It updates prices and processes any pending orders that should
        be filled at the new time.
        
        Args:
            new_time: The new simulation time.
        """
        self.current_time = new_time
        
        # Update current prices based on the new time
        for symbol in self.historical_data:
            price = self.get_price_at_time(symbol, new_time)
            if price is not None:
                self.current_prices[symbol] = price
        
        # Process any orders that should be filled at this time
        # (This will be implemented in the order execution methods)
    
    def simulate_order_execution(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate the execution of an order based on current prices.
        
        Args:
            order: The order to simulate.
            
        Returns:
            The executed order with fill information.
        """
        symbol = order["symbol"]
        side = order["side"]
        order_type = order["type"]
        quantity = float(order["quantity"])
        
        # Get current price
        price = self.get_current_price(symbol)
        if price is None:
            order["status"] = "REJECTED"
            order["reason"] = "No price data available"
            return order
        
        # Apply slippage
        if side.lower() == "buy":
            execution_price = price * (1 + self.slippage)
        else:
            execution_price = price * (1 - self.slippage)
        
        # Calculate fill amount and fees
        fill_qty = quantity
        fill_price = execution_price
        fee = fill_qty * fill_price * self.fee_rate
        
        # Update order with fill information
        filled_order = order.copy()
        filled_order["status"] = "FILLED"
        filled_order["executed_quantity"] = fill_qty
        filled_order["executed_price"] = fill_price
        filled_order["fee"] = fee
        filled_order["filled_time"] = self.current_time.timestamp() * 1000  # Milliseconds
        
        # Add some simulated execution delay if configured
        if self.latency_ms > 0:
            time.sleep(self.latency_ms / 1000)
        
        return filled_order
    
    # Exchange interface methods will be implemented in subsequent edits
    
    async def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information including balance, positions, etc.
        
        Returns:
            Dict containing account information.
        """
        # Calculate unrealized P&L for all positions
        unrealized_pnl = 0.0
        for symbol, position in self.positions.items():
            if position["size"] != 0:
                current_price = self.get_current_price(symbol)
                if current_price is not None:
                    if position["side"] == "buy":
                        unrealized_pnl += position["size"] * (current_price - position["entry_price"])
                    else:
                        unrealized_pnl += position["size"] * (position["entry_price"] - current_price)
        
        # Calculate total equity and available balance
        total_equity = self.current_balance + unrealized_pnl
        
        # Calculate margin used by open positions
        margin_used = 0.0
        for symbol, position in self.positions.items():
            if position["size"] != 0:
                margin_used += position["margin"]
        
        available_balance = self.current_balance - margin_used
        
        # Format account info to match the expected format
        account_info = {
            "total_equity": total_equity,
            "available_balance": available_balance,
            "margin_balance": self.current_balance,
            "unrealized_pnl": unrealized_pnl,
            "positions": list(self.positions.values())
        }
        
        return account_info
    
    async def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific position.
        
        Args:
            symbol: The trading pair symbol.
            
        Returns:
            Dict containing position information or None if no position exists.
        """
        position = self.positions.get(symbol)
        
        # If no position exists or size is 0, return None
        if position is None or position["size"] == 0:
            return None
        
        # Get current price to calculate unrealized P&L
        current_price = self.get_current_price(symbol)
        if current_price is not None:
            # Update unrealized P&L
            if position["side"] == "buy":
                position["unrealized_pnl"] = position["size"] * (current_price - position["entry_price"])
                # Update unrealized P&L percentage
                if position["entry_price"] > 0:
                    position["unrealized_pnl_percentage"] = (current_price / position["entry_price"] - 1) * 100 * position["leverage"]
            else:
                position["unrealized_pnl"] = position["size"] * (position["entry_price"] - current_price)
                # Update unrealized P&L percentage
                if position["entry_price"] > 0:
                    position["unrealized_pnl_percentage"] = (position["entry_price"] / current_price - 1) * 100 * position["leverage"]
        
        return position
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get all open positions.
        
        Returns:
            List of dicts containing position information.
        """
        # Get positions with updated P&L for each
        positions = []
        for symbol in self.positions:
            position = await self.get_position(symbol)
            if position is not None:
                positions.append(position)
        
        return positions
    
    def _format_position(self, position: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a position dictionary to match the expected format.
        
        Args:
            position: The position to format.
            
        Returns:
            Formatted position.
        """
        symbol = position["symbol"]
        side = position["side"]
        size = position["size"]
        entry_price = position["entry_price"]
        leverage = position["leverage"]
        
        # Calculate position value
        position_value = abs(size) * entry_price
        
        # Get current price to calculate unrealized P&L
        current_price = self.get_current_price(symbol)
        unrealized_pnl = 0.0
        unrealized_pnl_percentage = 0.0
        
        if current_price is not None:
            # Calculate unrealized P&L
            if side == "buy":
                unrealized_pnl = size * (current_price - entry_price)
                if entry_price > 0:
                    unrealized_pnl_percentage = (current_price / entry_price - 1) * 100 * leverage
            else:
                unrealized_pnl = size * (entry_price - current_price)
                if entry_price > 0:
                    unrealized_pnl_percentage = (entry_price / current_price - 1) * 100 * leverage
        
        # Calculate margin
        margin = position_value / leverage
        
        # Format position to match expected format
        formatted_position = {
            "symbol": symbol,
            "side": side,
            "size": size,
            "entry_price": entry_price,
            "mark_price": current_price,
            "leverage": leverage,
            "margin": margin,
            "liquidation_price": position.get("liquidation_price", 0.0),
            "position_value": position_value,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_percentage": unrealized_pnl_percentage,
            "timestamp": int(self.current_time.timestamp() * 1000)  # Milliseconds
        }
        
        return formatted_position
    
    def _update_position(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a position based on an executed order.
        
        Args:
            order: The executed order.
            
        Returns:
            The updated position.
        """
        symbol = order["symbol"]
        side = order["side"]
        quantity = float(order["executed_quantity"])
        price = float(order["executed_price"])
        reduce_only = order.get("reduce_only", False)
        leverage = order.get("leverage", 1)
        
        # Get existing position or create a new one
        position = self.positions.get(symbol)
        if position is None:
            position = {
                "symbol": symbol,
                "side": "buy" if side.lower() == "buy" else "sell",
                "size": 0.0,
                "entry_price": 0.0,
                "mark_price": price,
                "leverage": leverage,
                "margin": 0.0,
                "liquidation_price": 0.0,
                "position_value": 0.0,
                "unrealized_pnl": 0.0,
                "unrealized_pnl_percentage": 0.0,
                "timestamp": int(self.current_time.timestamp() * 1000)  # Milliseconds
            }
            self.positions[symbol] = position
        
        # If no existing position, create a new one
        if position["size"] == 0:
            position["side"] = "buy" if side.lower() == "buy" else "sell"
            position["size"] = quantity if side.lower() == "buy" else -quantity
            position["entry_price"] = price
            position["leverage"] = leverage
            position["timestamp"] = int(self.current_time.timestamp() * 1000)
        else:
            # Existing position exists, update it
            current_size = position["size"]
            current_side = position["side"]
            
            # If order is reduce_only, ensure it only reduces the position
            if reduce_only:
                # If trying to increase position size with reduce_only, reject
                if (current_side == "buy" and side.lower() == "buy") or (current_side == "sell" and side.lower() == "sell"):
                    return position
                
                # Limit quantity to not flip the position
                quantity = min(quantity, abs(current_size))
            
            # Calculate order impact
            order_impact = quantity if side.lower() == "buy" else -quantity
            
            # Check if order flips position
            new_size = current_size + order_impact
            
            if (current_size > 0 and new_size < 0) or (current_size < 0 and new_size > 0):
                # Position is being flipped
                position["side"] = "buy" if new_size > 0 else "sell"
                position["size"] = new_size
                position["entry_price"] = price
                position["timestamp"] = int(self.current_time.timestamp() * 1000)
            elif new_size == 0:
                # Position is being closed
                position["side"] = "buy"  # Default side
                position["size"] = 0
                position["entry_price"] = 0
                position["timestamp"] = int(self.current_time.timestamp() * 1000)
            else:
                # Position is being adjusted, recalculate entry price
                old_value = abs(current_size) * position["entry_price"]
                new_value = quantity * price
                
                if abs(new_size) > 0:
                    position["entry_price"] = (old_value + new_value) / abs(new_size)
                    position["size"] = new_size
                    position["timestamp"] = int(self.current_time.timestamp() * 1000)
        
        # Calculate position value
        position_value = abs(position["size"]) * position["entry_price"]
        position["position_value"] = position_value
        
        # Calculate margin
        margin = position_value / position["leverage"]
        position["margin"] = margin
        
        # Calculate liquidation price (simplified estimate)
        # In a real implementation, this would use a more sophisticated formula based on 
        # maintenance margin requirements and other factors
        if position["size"] != 0:
            margin_requirement = 1 / position["leverage"]
            liquidation_threshold = 0.8  # Example: maintenance margin is 80% of initial margin
            buffer = margin_requirement * liquidation_threshold
            
            if position["side"] == "buy":
                position["liquidation_price"] = position["entry_price"] * (1 - buffer)
            else:
                position["liquidation_price"] = position["entry_price"] * (1 + buffer)
        else:
            position["liquidation_price"] = 0.0
        
        # Update position in the dictionary
        self.positions[symbol] = position
        
        # Return formatted position
        return self._format_position(position)
    
    # Order management methods will be implemented in subsequent edits
    
    async def get_order(self, order_id: str, symbol: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific order.
        
        Args:
            order_id: The ID of the order.
            symbol: The trading pair symbol (optional for some exchanges).
            
        Returns:
            Dict containing order information or None if the order doesn't exist.
        """
        order = self.orders.get(order_id)
        return order
    
    async def get_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all open orders, optionally filtered by symbol.
        
        Args:
            symbol: The trading pair symbol (optional).
            
        Returns:
            List of dicts containing order information.
        """
        orders = []
        
        for order_id, order in self.orders.items():
            # Filter by symbol if provided
            if symbol is not None and order["symbol"] != symbol:
                continue
            
            # Only include open orders
            if order["status"] == "NEW" or order["status"] == "PARTIALLY_FILLED":
                orders.append(order)
        
        return orders
    
    async def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        time_in_force: str = "GTC",
        reduce_only: bool = False,
        leverage: int = 1
    ) -> Dict[str, Any]:
        """
        Create a new order.
        
        Args:
            symbol: The trading pair symbol.
            side: Order side ('buy' or 'sell').
            order_type: Order type ('limit', 'market', 'stop', etc.).
            quantity: Order quantity.
            price: Order price (required for limit orders).
            stop_price: Stop price (required for stop orders).
            time_in_force: Time in force ('GTC', 'IOC', 'FOK').
            reduce_only: Whether the order should only reduce the position.
            leverage: Leverage to use for the position.
            
        Returns:
            Dict containing order information.
        """
        # Validate inputs
        if order_type.lower() in ["limit", "stop_limit"] and price is None:
            return {
                "status": "REJECTED",
                "reason": "Price is required for limit orders",
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": float(quantity)
            }
            
        if order_type.lower() in ["stop", "stop_market", "stop_limit"] and stop_price is None:
            return {
                "status": "REJECTED",
                "reason": "Stop price is required for stop orders",
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": float(quantity)
            }
        
        # Generate a unique order ID
        order_id = str(self.order_id_counter)
        self.order_id_counter += 1
        
        # Format order type for consistency
        mapped_order_type = self._map_order_type(order_type)
        
        # Create the order object
        order = {
            "order_id": order_id,
            "symbol": symbol,
            "side": side.lower(),
            "type": mapped_order_type,
            "quantity": float(quantity),
            "price": float(price) if price is not None else None,
            "stop_price": float(stop_price) if stop_price is not None else None,
            "time_in_force": time_in_force,
            "reduce_only": reduce_only,
            "leverage": leverage,
            "status": "NEW",
            "executed_quantity": 0.0,
            "executed_price": 0.0,
            "fee": 0.0,
            "created_time": int(self.current_time.timestamp() * 1000),  # Milliseconds
            "updated_time": int(self.current_time.timestamp() * 1000)   # Milliseconds
        }
        
        # For market orders, execute immediately
        if mapped_order_type == "MARKET":
            # Execute the order
            executed_order = self.simulate_order_execution(order)
            
            # Update account balance
            self._update_account_balance(executed_order)
            
            # Update position
            self._update_position(executed_order)
            
            # Store the executed order
            self.orders[order_id] = executed_order
            
            # Add to trade history
            self._add_to_trade_history(executed_order)
            
            # Notify callbacks
            asyncio.create_task(self._notify_order_update(executed_order))
            
            return executed_order
        
        # For other order types, just store the order for now
        # In a real implementation, these would be processed when the price conditions are met
        self.orders[order_id] = order
        
        # Notify callbacks
        asyncio.create_task(self._notify_order_update(order))
        
        return order
    
    async def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel an existing order.
        
        Args:
            order_id: The ID of the order.
            symbol: The trading pair symbol (required for some exchanges).
            
        Returns:
            Dict containing order information.
        """
        # Find the order
        order = self.orders.get(order_id)
        
        if order is None:
            return {
                "status": "REJECTED",
                "reason": f"Order {order_id} not found",
                "order_id": order_id
            }
        
        # Check if order can be canceled
        if order["status"] not in ["NEW", "PARTIALLY_FILLED"]:
            return {
                "status": "REJECTED",
                "reason": f"Order {order_id} is already {order['status']}",
                "order_id": order_id
            }
        
        # Update order status
        order["status"] = "CANCELED"
        order["updated_time"] = int(self.current_time.timestamp() * 1000)
        
        # Store the updated order
        self.orders[order_id] = order
        
        # Notify callbacks
        asyncio.create_task(self._notify_order_update(order))
        
        return order
    
    async def cancel_all_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Cancel all open orders, optionally filtered by symbol.
        
        Args:
            symbol: The trading pair symbol (optional).
            
        Returns:
            List of dicts containing order information.
        """
        canceled_orders = []
        
        for order_id, order in list(self.orders.items()):
            # Filter by symbol if provided
            if symbol is not None and order["symbol"] != symbol:
                continue
            
            # Skip orders that can't be canceled
            if order["status"] not in ["NEW", "PARTIALLY_FILLED"]:
                continue
            
            # Cancel the order
            canceled_order = await self.cancel_order(order_id)
            canceled_orders.append(canceled_order)
        
        return canceled_orders
    
    def _map_order_type(self, order_type: str) -> str:
        """
        Map order types to standardized values.
        
        Args:
            order_type: The order type to map.
            
        Returns:
            Standardized order type.
        """
        order_type_lower = order_type.lower()
        
        if order_type_lower == "market":
            return "MARKET"
        elif order_type_lower == "limit":
            return "LIMIT"
        elif order_type_lower in ["stop", "stop_market"]:
            return "STOP_MARKET"
        elif order_type_lower == "stop_limit":
            return "STOP_LIMIT"
        else:
            return order_type.upper()
    
    def _update_account_balance(self, order: Dict[str, Any]) -> None:
        """
        Update account balance based on an executed order.
        
        Args:
            order: The executed order.
        """
        # Only process filled orders
        if order["status"] != "FILLED":
            return
        
        # Extract order details
        symbol = order["symbol"]
        side = order["side"]
        quantity = float(order["executed_quantity"])
        price = float(order["executed_price"])
        fee = float(order["fee"])
        
        # Get position
        position = self.positions.get(symbol)
        
        # Calculate PnL if closing or reducing a position
        realized_pnl = 0.0
        
        if position and position["size"] != 0:
            # Determine if this is a closing or reducing order
            is_closing = False
            
            if (position["side"] == "buy" and side == "sell") or (position["side"] == "sell" and side == "buy"):
                # Calculate PnL for the closed portion
                closed_quantity = min(quantity, abs(position["size"]))
                
                if position["side"] == "buy":
                    realized_pnl = closed_quantity * (price - position["entry_price"])
                else:
                    realized_pnl = closed_quantity * (position["entry_price"] - price)
                
                is_closing = True
        
        # Calculate cost of the order
        if not position or position["size"] == 0 or not is_closing:
            # Opening or increasing a position
            cost = quantity * price / order["leverage"]
            self.current_balance -= cost
        else:
            # Closing or reducing a position
            # Cost is already accounted for when position was opened
            # Just add the realized P&L
            self.current_balance += realized_pnl
        
        # Subtract fees
        self.current_balance -= fee
        
        # Add to equity history
        self.equity_history.append((self.current_time, self.current_balance))
    
    def _add_to_trade_history(self, order: Dict[str, Any]) -> None:
        """
        Add a trade to the trade history.
        
        Args:
            order: The executed order.
        """
        # Only add filled orders
        if order["status"] != "FILLED":
            return
        
        # Extract order details
        symbol = order["symbol"]
        side = order["side"]
        quantity = float(order["executed_quantity"])
        price = float(order["executed_price"])
        fee = float(order["fee"])
        
        # Get position
        position = self.positions.get(symbol)
        
        # Determine if this is opening, closing, or adjusting a position
        position_effect = "open"
        
        if position and position["size"] != 0:
            if (position["side"] == "buy" and side == "sell") or (position["side"] == "sell" and side == "buy"):
                # Reducing or closing position
                if position["size"] == quantity:
                    position_effect = "close"
                else:
                    position_effect = "reduce"
            else:
                # Increasing position
                position_effect = "increase"
        
        # Calculate P&L
        realized_pnl = 0.0
        
        if position_effect in ["close", "reduce"]:
            # Calculate P&L for the closed portion
            closed_quantity = min(quantity, abs(position["size"]))
            
            if position["side"] == "buy":
                realized_pnl = closed_quantity * (price - position["entry_price"])
            else:
                realized_pnl = closed_quantity * (position["entry_price"] - price)
        
        # Create trade record
        trade = {
            "timestamp": int(self.current_time.timestamp() * 1000),  # Milliseconds
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "fee": fee,
            "order_id": order["order_id"],
            "order_type": order["type"],
            "position_effect": position_effect,
            "realized_pnl": realized_pnl,
            "account_balance": self.current_balance
        }
        
        # Add to trade history
        self.trade_history.append(trade)
    
    async def _notify_order_update(self, order: Dict[str, Any]) -> None:
        """
        Notify callbacks about an order update.
        
        Args:
            order: The updated order.
        """
        # Format the order update message
        order_update = {
            "type": "order_update",
            "timestamp": int(self.current_time.timestamp() * 1000),  # Milliseconds
            "data": order
        }
        
        # Notify order update callbacks
        for callback in self.callbacks["order_update"]:
            try:
                await callback(order_update)
            except Exception as e:
                log_event(
                    self.logger,
                    "CALLBACK_ERROR",
                    f"Error in order update callback: {str(e)}",
                    level="ERROR",
                    context={"error": str(e)}
                )
    
    # Market data methods will be implemented in subsequent edits
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get the current ticker for a symbol.
        
        Args:
            symbol: The trading pair symbol.
            
        Returns:
            Dict containing ticker information.
        """
        # Get current price
        price = self.get_current_price(symbol)
        
        if price is None:
            raise ValueError(f"No price data available for {symbol}")
        
        # Create a simplified ticker
        ticker = {
            "symbol": symbol,
            "price": price,
            "bid": price * 0.9999,  # Simulated bid (slightly lower)
            "ask": price * 1.0001,  # Simulated ask (slightly higher)
            "volume": 1000.0,  # Dummy volume
            "timestamp": int(self.current_time.timestamp() * 1000)  # Milliseconds
        }
        
        return ticker
    
    async def get_orderbook(self, symbol: str, depth: int = 10) -> Dict[str, Any]:
        """
        Get the order book for a symbol.
        
        Args:
            symbol: The trading pair symbol.
            depth: The depth of the order book to retrieve.
            
        Returns:
            Dict containing order book information.
        """
        # Get current price
        price = self.get_current_price(symbol)
        
        if price is None:
            raise ValueError(f"No price data available for {symbol}")
        
        # Check if we have orderbook snapshots
        if symbol in self.order_book_data:
            # Find the closest orderbook snapshot
            snapshot = None
            min_time_diff = float('inf')
            
            timestamp_ms = int(self.current_time.timestamp() * 1000)
            
            for ob_snapshot in self.order_book_data[symbol]:
                time_diff = abs(ob_snapshot.get("timestamp", 0) - timestamp_ms)
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    snapshot = ob_snapshot
            
            if snapshot:
                return {
                    "symbol": symbol,
                    "bids": snapshot.get("bids", [])[:depth],
                    "asks": snapshot.get("asks", [])[:depth],
                    "timestamp": snapshot.get("timestamp", timestamp_ms)
                }
        
        # If no orderbook data or no suitable snapshot found, generate a synthetic one
        # This is a simplified orderbook for backtesting purposes
        bids = [[price * (1 - 0.0001 * i), 1.0 / (i + 1)] for i in range(depth)]
        asks = [[price * (1 + 0.0001 * i), 1.0 / (i + 1)] for i in range(depth)]
        
        return {
            "symbol": symbol,
            "bids": bids,
            "asks": asks,
            "timestamp": int(self.current_time.timestamp() * 1000)  # Milliseconds
        }
    
    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get kline/candlestick data for a symbol.
        
        Args:
            symbol: The trading pair symbol.
            interval: The interval of the klines (e.g., '1m', '5m', '1h').
            limit: The maximum number of klines to retrieve.
            start_time: The start time in milliseconds.
            end_time: The end time in milliseconds.
            
        Returns:
            List of dicts containing kline information.
        """
        if symbol not in self.historical_data:
            raise ValueError(f"No historical data loaded for {symbol}")
        
        # Get historical candles
        candles = self.historical_data[symbol]
        
        # Filter by time range if specified
        filtered_candles = []
        
        for candle in candles:
            candle_time = candle[0]  # Open time in milliseconds
            
            # Filter by start_time
            if start_time is not None and candle_time < start_time:
                continue
                
            # Filter by end_time
            if end_time is not None and candle_time > end_time:
                continue
                
            filtered_candles.append(candle)
        
        # Apply limit
        filtered_candles = filtered_candles[-limit:]
        
        # Format candles to match the expected format
        formatted_candles = []
        
        for candle in filtered_candles:
            formatted_candle = {
                "open_time": candle[0],
                "open": float(candle[1]),
                "high": float(candle[2]),
                "low": float(candle[3]),
                "close": float(candle[4]),
                "volume": float(candle[5]),
                "close_time": candle[6],
                "quote_volume": float(candle[7]) if len(candle) > 7 else 0.0,
                "trades": int(candle[8]) if len(candle) > 8 else 0,
                "taker_buy_base_volume": float(candle[9]) if len(candle) > 9 else 0.0,
                "taker_buy_quote_volume": float(candle[10]) if len(candle) > 10 else 0.0,
            }
            
            formatted_candles.append(formatted_candle)
        
        return formatted_candles
    
    # High-level trading functionality
    
    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """
        Set the leverage for a symbol.
        
        Args:
            symbol: The trading pair symbol.
            leverage: The leverage value.
            
        Returns:
            Dict containing leverage information.
        """
        # In a backtesting environment, we just store the leverage
        # and apply it to future positions
        return {
            "symbol": symbol,
            "leverage": leverage,
            "status": "success"
        }
    
    async def open_position(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        leverage: int = 1,
        order_type: str = "MARKET",
        price: Optional[Decimal] = None,
        stop_loss: Optional[Decimal] = None,
        take_profit: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Open a new position with optional stop loss and take profit orders.
        
        Args:
            symbol: The trading pair symbol.
            side: Order side ('buy' or 'sell').
            quantity: Order quantity.
            leverage: The leverage to use.
            order_type: Order type ('MARKET', 'LIMIT', etc.).
            price: Order price (required for limit orders).
            stop_loss: Optional stop loss price.
            take_profit: Optional take profit price.
            
        Returns:
            Dict containing position and order information.
        """
        # Create the entry order
        entry_order = await self.create_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            leverage=leverage
        )
        
        # If entry order was rejected, return error
        if entry_order["status"] == "REJECTED":
            return {
                "status": "error",
                "message": entry_order["reason"],
                "symbol": symbol,
                "side": side,
                "quantity": float(quantity)
            }
        
        # Get the position after order execution
        position = await self.get_position(symbol)
        
        # Create stop loss and take profit orders
        sl_tp_orders = {}
        
        if position and stop_loss is not None:
            # Create stop loss order
            sl_side = "sell" if side == "buy" else "buy"
            sl_order = await self.create_order(
                symbol=symbol,
                side=sl_side,
                order_type="STOP_MARKET",
                quantity=quantity,
                stop_price=stop_loss,
                reduce_only=True
            )
            sl_tp_orders["stop_loss"] = sl_order
        
        if position and take_profit is not None:
            # Create take profit order
            tp_side = "sell" if side == "buy" else "buy"
            tp_order = await self.create_order(
                symbol=symbol,
                side=tp_side,
                order_type="LIMIT",
                quantity=quantity,
                price=take_profit,
                reduce_only=True
            )
            sl_tp_orders["take_profit"] = tp_order
        
        return {
            "status": "success",
            "position": position,
            "entry_order": entry_order,
            "sl_tp_orders": sl_tp_orders
        }
    
    async def close_position(
        self,
        symbol: str,
        order_type: str = "MARKET",
        price: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Close an existing position.
        
        Args:
            symbol: The trading pair symbol.
            order_type: Order type ('MARKET', 'LIMIT').
            price: Order price (required for limit orders).
            
        Returns:
            Dict containing order information.
        """
        # Get current position
        position = await self.get_position(symbol)
        
        if not position:
            return {
                "status": "error",
                "message": f"No open position for {symbol}",
                "symbol": symbol
            }
        
        # Determine side and quantity
        side = "sell" if position["side"] == "buy" else "buy"
        quantity = abs(position["size"])
        
        # Create close order
        close_order = await self.create_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=Decimal(str(quantity)),
            price=price,
            reduce_only=True
        )
        
        # Cancel all other orders for this symbol
        await self.cancel_all_orders(symbol)
        
        return {
            "status": "success",
            "close_order": close_order
        }
    
    # Backtesting engine functions
    
    def process_time_step(self, new_time: datetime) -> None:
        """
        Process a single time step in the backtesting simulation.
        
        Args:
            new_time: The new simulation time.
        """
        # Update current time
        self.update_time(new_time)
        
        # Process pending orders
        self._process_pending_orders()
        
        # Calculate and record portfolio value
        self._record_portfolio_value()
    
    def _process_pending_orders(self) -> None:
        """
        Process any pending orders that should be filled at the current time.
        """
        for order_id, order in list(self.orders.items()):
            # Skip orders that are not pending
            if order["status"] != "NEW":
                continue
            
            # Check if order conditions are met
            if self._should_fill_order(order):
                # Execute the order
                executed_order = self.simulate_order_execution(order)
                
                # Update account balance
                self._update_account_balance(executed_order)
                
                # Update position
                self._update_position(executed_order)
                
                # Store the executed order
                self.orders[order_id] = executed_order
                
                # Add to trade history
                self._add_to_trade_history(executed_order)
                
                # Notify callbacks
                asyncio.create_task(self._notify_order_update(executed_order))
    
    def _should_fill_order(self, order: Dict[str, Any]) -> bool:
        """
        Check if an order should be filled at the current time.
        
        Args:
            order: The order to check.
            
        Returns:
            True if the order should be filled, False otherwise.
        """
        # Order type
        order_type = order["type"]
        
        # Symbol and side
        symbol = order["symbol"]
        side = order["side"]
        
        # Get current price
        current_price = self.get_current_price(symbol)
        
        if current_price is None:
            return False
        
        # Check each order type
        if order_type == "LIMIT":
            # Check if limit price is reached
            price = order["price"]
            
            if side == "buy" and current_price <= price:
                return True
                
            if side == "sell" and current_price >= price:
                return True
                
        elif order_type == "STOP_MARKET":
            # Check if stop price is reached
            stop_price = order["stop_price"]
            
            if side == "buy" and current_price >= stop_price:
                return True
                
            if side == "sell" and current_price <= stop_price:
                return True
                
        elif order_type == "STOP_LIMIT":
            # Check if stop price is reached
            stop_price = order["stop_price"]
            
            if side == "buy" and current_price >= stop_price:
                return True
                
            if side == "sell" and current_price <= stop_price:
                return True
        
        return False
    
    def _record_portfolio_value(self) -> None:
        """
        Calculate and record the current portfolio value.
        """
        # Calculate unrealized P&L
        unrealized_pnl = 0.0
        
        for symbol, position in self.positions.items():
            if position["size"] != 0:
                current_price = self.get_current_price(symbol)
                
                if current_price is not None:
                    if position["side"] == "buy":
                        unrealized_pnl += position["size"] * (current_price - position["entry_price"])
                    else:
                        unrealized_pnl += position["size"] * (position["entry_price"] - current_price)
        
        # Calculate total equity
        total_equity = self.current_balance + unrealized_pnl
        
        # Record the current equity value
        self.equity_history.append((self.current_time, total_equity))
    
    def calculate_performance_metrics(self) -> Dict[str, Any]:
        """
        Calculate performance metrics for the backtest.
        
        Returns:
            Dict containing performance metrics.
        """
        # Calculate basic metrics
        initial_equity = self.initial_balance
        final_equity = self.equity_history[-1][1] if self.equity_history else self.initial_balance
        
        total_return = (final_equity / initial_equity - 1) * 100
        total_trades = len(self.trade_history)
        
        # Calculate win rate
        winning_trades = sum(1 for trade in self.trade_history if trade["realized_pnl"] > 0)
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # Calculate average profit and loss
        avg_profit = sum(trade["realized_pnl"] for trade in self.trade_history if trade["realized_pnl"] > 0) / winning_trades if winning_trades > 0 else 0
        avg_loss = sum(trade["realized_pnl"] for trade in self.trade_history if trade["realized_pnl"] < 0) / (total_trades - winning_trades) if total_trades > winning_trades else 0
        
        # Calculate profit factor
        gross_profit = sum(trade["realized_pnl"] for trade in self.trade_history if trade["realized_pnl"] > 0)
        gross_loss = abs(sum(trade["realized_pnl"] for trade in self.trade_history if trade["realized_pnl"] < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Calculate drawdown
        max_drawdown = 0.0
        max_equity = initial_equity
        
        for _, equity in self.equity_history:
            max_equity = max(max_equity, equity)
            drawdown = (max_equity - equity) / max_equity * 100
            max_drawdown = max(max_drawdown, drawdown)
        
        # Store and return the metrics
        metrics = {
            "initial_equity": initial_equity,
            "final_equity": final_equity,
            "total_return": total_return,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "win_rate": win_rate,
            "avg_profit": avg_profit,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.current_time.isoformat()
        }
        
        self.performance_metrics = metrics
        return metrics 