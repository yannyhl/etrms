"""
Enhanced Trading Risk Management System Binance Futures Client
"""
import asyncio
import json
import time
from decimal import Decimal
from functools import wraps
from typing import Dict, List, Optional, Any, Tuple, Callable, Coroutine

from binance import AsyncClient
from binance.exceptions import BinanceAPIException
from binance.streams import BinanceSocketManager

from config.settings import settings
from exchange.common.exchange_interface import ExchangeInterface
from utils.logger import get_logger, log_event


def retry_async(max_retries=3, retry_delay=1, backoff_factor=2, retry_exceptions=(BinanceAPIException,)):
    """
    Retry decorator for async methods that may encounter temporary failures.
    
    Args:
        max_retries: Maximum number of retry attempts.
        retry_delay: Initial delay between retries in seconds.
        backoff_factor: Multiplier for the delay after each retry.
        retry_exceptions: Tuple of exceptions that should trigger a retry.
        
    Returns:
        Decorated function with retry logic.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            self = args[0]  # Extract the class instance
            last_exception = None
            delay = retry_delay
            
            for retry in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retry_exceptions as e:
                    last_exception = e
                    
                    # Don't retry on certain error codes
                    if isinstance(e, BinanceAPIException):
                        # Don't retry on certain error codes (e.g., invalid API keys, parameter errors)
                        if e.code in (-2014, -2015, -1021, -1100, -1106):
                            log_event(
                                self.logger,
                                "BINANCE_API_ERROR_NO_RETRY",
                                f"Error in {func.__name__}, not retrying: {str(e)}",
                                level="ERROR",
                                context={"error_code": e.code, "error_message": e.message}
                            )
                            raise
                    
                    if retry < max_retries:
                        log_event(
                            self.logger,
                            "BINANCE_API_RETRY",
                            f"Retrying {func.__name__} after error: {str(e)} (Attempt {retry+1}/{max_retries})",
                            level="WARNING"
                        )
                        await asyncio.sleep(delay)
                        delay *= backoff_factor
                    else:
                        log_event(
                            self.logger,
                            "BINANCE_API_MAX_RETRIES",
                            f"Max retries reached for {func.__name__}: {str(e)}",
                            level="ERROR"
                        )
                        raise last_exception
            
            return None  # Should never reach here
        return wrapper
    return decorator


class BinanceFuturesClient(ExchangeInterface):
    """
    Implementation of the Exchange Interface for Binance Futures.
    """
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, testnet: bool = False):
        """
        Initialize the Binance Futures client.
        
        Args:
            api_key: The API key for authentication.
            api_secret: The API secret for authentication.
            testnet: Whether to use the testnet.
        """
        self.api_key = api_key or settings.BINANCE_API_KEY
        self.api_secret = api_secret or settings.BINANCE_API_SECRET
        self.testnet = testnet or settings.BINANCE_TESTNET
        self.client = None
        self.logger = get_logger(__name__)
        
        # WebSocket related attributes
        self.bsm = None
        self.user_socket = None
        self.market_sockets = {}
        self.book_sockets = {}
        self.callbacks = {
            'account_update': [],
            'position_update': [],
            'order_update': [],
            'market_update': {},
            'book_update': {}
        }
        
        log_event(
            self.logger, 
            "BINANCE_CLIENT_INIT", 
            f"Initializing Binance Futures client (testnet: {self.testnet})"
        )
    
    async def initialize(self) -> None:
        """
        Initialize the Binance Futures client.
        """
        try:
            self.client = await AsyncClient.create(
                api_key=self.api_key,
                api_secret=self.api_secret,
                testnet=self.testnet
            )
            
            # Initialize the WebSocket manager
            self.bsm = BinanceSocketManager(self.client)
            
            log_event(
                self.logger,
                "BINANCE_CLIENT_INITIALIZED",
                "Binance Futures client initialized successfully"
            )
        except Exception as e:
            log_event(
                self.logger,
                "BINANCE_CLIENT_INIT_ERROR",
                f"Failed to initialize Binance Futures client: {str(e)}",
                level="ERROR"
            )
            raise
    
    async def close(self) -> None:
        """
        Close the Binance Futures client.
        """
        try:
            # Close WebSocket connections
            if self.user_socket:
                await self.user_socket.close()
                self.user_socket = None
                
            for symbol, socket in self.market_sockets.items():
                await socket.close()
            self.market_sockets = {}
            
            for symbol, socket in self.book_sockets.items():
                await socket.close()
            self.book_sockets = {}
                
            # Close REST API client
            if self.client:
                await self.client.close_connection()
                
            log_event(
                self.logger,
                "BINANCE_CLIENT_CLOSED",
                "Binance Futures client closed"
            )
        except Exception as e:
            log_event(
                self.logger,
                "BINANCE_CLIENT_CLOSE_ERROR",
                f"Error closing Binance Futures client: {str(e)}",
                level="ERROR"
            )
    
    @retry_async()
    async def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information including balance, positions, etc.
        
        Returns:
            Dict containing account information.
        """
        try:
            account = await self.client.futures_account()
            
            # Format the response to match our expected format
            formatted_account = {
                "total_equity": float(account["totalWalletBalance"]),
                "available_balance": float(account["availableBalance"]),
                "margin_balance": float(account["totalMarginBalance"]),
                "unrealized_pnl": float(account["totalUnrealizedProfit"]),
                "positions": [
                    self._format_position(p) for p in account["positions"]
                    if float(p["positionAmt"]) != 0
                ]
            }
            
            return formatted_account
        except BinanceAPIException as e:
            log_event(
                self.logger,
                "BINANCE_API_ERROR",
                f"Error getting account info: {str(e)}",
                level="ERROR",
                context={"error_code": e.code, "error_message": e.message}
            )
            raise
    
    @retry_async()
    async def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific position.
        
        Args:
            symbol: The trading pair symbol.
            
        Returns:
            Dict containing position information or None if no position exists.
        """
        try:
            positions = await self.client.futures_position_information(symbol=symbol)
            if not positions:
                return None
                
            position = positions[0]
            if float(position["positionAmt"]) == 0:
                return None
                
            return self._format_position(position)
        except BinanceAPIException as e:
            log_event(
                self.logger,
                "BINANCE_API_ERROR",
                f"Error getting position for {symbol}: {str(e)}",
                level="ERROR",
                context={"symbol": symbol, "error_code": e.code, "error_message": e.message}
            )
            raise
    
    @retry_async()
    async def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get all open positions.
        
        Returns:
            List of dicts containing position information.
        """
        try:
            positions = await self.client.futures_position_information()
            # Filter out positions with zero amount
            active_positions = [p for p in positions if float(p["positionAmt"]) != 0]
            
            return [self._format_position(p) for p in active_positions]
        except BinanceAPIException as e:
            log_event(
                self.logger,
                "BINANCE_API_ERROR",
                f"Error getting positions: {str(e)}",
                level="ERROR",
                context={"error_code": e.code, "error_message": e.message}
            )
            raise
    
    @retry_async()
    async def get_order(self, order_id: str, symbol: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific order.
        
        Args:
            order_id: The ID of the order.
            symbol: The trading pair symbol (required for Binance).
            
        Returns:
            Dict containing order information or None if the order doesn't exist.
        """
        if not symbol:
            raise ValueError("Symbol is required for Binance Futures API")
            
        try:
            order = await self.client.futures_get_order(
                symbol=symbol,
                orderId=order_id
            )
            
            return self._format_order(order)
        except BinanceAPIException as e:
            if e.code == -2013:  # Order does not exist
                return None
                
            log_event(
                self.logger,
                "BINANCE_API_ERROR",
                f"Error getting order {order_id} for {symbol}: {str(e)}",
                level="ERROR",
                context={"order_id": order_id, "symbol": symbol, "error_code": e.code, "error_message": e.message}
            )
            raise
    
    @retry_async()
    async def get_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all open orders, optionally filtered by symbol.
        
        Args:
            symbol: The trading pair symbol (optional).
            
        Returns:
            List of dicts containing order information.
        """
        try:
            if symbol:
                orders = await self.client.futures_get_open_orders(symbol=symbol)
            else:
                orders = await self.client.futures_get_open_orders()
                
            return [self._format_order(order) for order in orders]
        except BinanceAPIException as e:
            log_event(
                self.logger,
                "BINANCE_API_ERROR",
                f"Error getting orders: {str(e)}",
                level="ERROR",
                context={"symbol": symbol, "error_code": e.code, "error_message": e.message}
            )
            raise
    
    @retry_async()
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
            
        Returns:
            Dict containing order information.
        """
        try:
            # Prepare parameters
            params = {
                "symbol": symbol,
                "side": side.upper(),
                "type": self._map_order_type(order_type),
                "quantity": float(quantity),
                "reduceOnly": reduce_only
            }
            
            # Add additional parameters based on order type
            if order_type.lower() in ["limit", "stop_limit"]:
                if not price:
                    raise ValueError("Price is required for limit orders")
                params["timeInForce"] = time_in_force
                params["price"] = float(price)
                
            if order_type.lower() in ["stop", "stop_market", "stop_limit"]:
                if not stop_price:
                    raise ValueError("Stop price is required for stop orders")
                params["stopPrice"] = float(stop_price)
            
            # Create the order
            response = await self.client.futures_create_order(**params)
            
            # Get the created order
            created_order = await self.get_order(str(response["orderId"]), symbol)
            
            log_event(
                self.logger,
                "ORDER_CREATED",
                f"Created {order_type} order for {symbol}",
                context={"symbol": symbol, "order_id": response["orderId"], "side": side, "quantity": float(quantity)}
            )
            
            return created_order
        except BinanceAPIException as e:
            log_event(
                self.logger,
                "BINANCE_API_ERROR",
                f"Error creating order for {symbol}: {str(e)}",
                level="ERROR",
                context={
                    "symbol": symbol, 
                    "side": side, 
                    "order_type": order_type, 
                    "quantity": float(quantity),
                    "error_code": e.code, 
                    "error_message": e.message
                }
            )
            raise
    
    @retry_async()
    async def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel an existing order.
        
        Args:
            order_id: The ID of the order.
            symbol: The trading pair symbol (required for Binance).
            
        Returns:
            Dict containing order information.
        """
        if not symbol:
            raise ValueError("Symbol is required for Binance Futures API")
            
        try:
            response = await self.client.futures_cancel_order(
                symbol=symbol,
                orderId=order_id
            )
            
            log_event(
                self.logger,
                "ORDER_CANCELED",
                f"Canceled order {order_id} for {symbol}",
                context={"symbol": symbol, "order_id": order_id}
            )
            
            return self._format_order(response)
        except BinanceAPIException as e:
            log_event(
                self.logger,
                "BINANCE_API_ERROR",
                f"Error canceling order {order_id} for {symbol}: {str(e)}",
                level="ERROR",
                context={"order_id": order_id, "symbol": symbol, "error_code": e.code, "error_message": e.message}
            )
            raise
    
    @retry_async()
    async def cancel_all_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Cancel all open orders, optionally filtered by symbol.
        
        Args:
            symbol: The trading pair symbol (optional).
            
        Returns:
            List of dicts containing order information.
        """
        try:
            if symbol:
                response = await self.client.futures_cancel_all_open_orders(symbol=symbol)
                canceled_orders = await self.get_orders(symbol=symbol)
                
                log_event(
                    self.logger,
                    "ALL_ORDERS_CANCELED",
                    f"Canceled all orders for {symbol}",
                    context={"symbol": symbol}
                )
                
                return canceled_orders
            else:
                # Get all symbols with open orders
                all_orders = await self.get_orders()
                symbols = set(order["symbol"] for order in all_orders)
                
                # Cancel orders for each symbol
                canceled_orders = []
                for sym in symbols:
                    await self.client.futures_cancel_all_open_orders(symbol=sym)
                
                log_event(
                    self.logger,
                    "ALL_ORDERS_CANCELED",
                    "Canceled all orders across all symbols",
                    context={"symbol_count": len(symbols)}
                )
                
                return canceled_orders
        except BinanceAPIException as e:
            log_event(
                self.logger,
                "BINANCE_API_ERROR",
                f"Error canceling all orders: {str(e)}",
                level="ERROR",
                context={"symbol": symbol, "error_code": e.code, "error_message": e.message}
            )
            raise
    
    @retry_async()
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get the current ticker for a symbol.
        
        Args:
            symbol: The trading pair symbol.
            
        Returns:
            Dict containing ticker information.
        """
        try:
            ticker = await self.client.futures_symbol_ticker(symbol=symbol)
            
            return {
                "symbol": ticker["symbol"],
                "price": float(ticker["price"]),
                "time": ticker["time"]
            }
        except BinanceAPIException as e:
            log_event(
                self.logger,
                "BINANCE_API_ERROR",
                f"Error getting ticker for {symbol}: {str(e)}",
                level="ERROR",
                context={"symbol": symbol, "error_code": e.code, "error_message": e.message}
            )
            raise
    
    @retry_async()
    async def get_orderbook(self, symbol: str, depth: int = 10) -> Dict[str, Any]:
        """
        Get the order book for a symbol.
        
        Args:
            symbol: The trading pair symbol.
            depth: The depth of the order book to retrieve.
            
        Returns:
            Dict containing order book information.
        """
        try:
            orderbook = await self.client.futures_order_book(symbol=symbol, limit=depth)
            
            return {
                "symbol": orderbook["symbol"] if "symbol" in orderbook else symbol,
                "bids": [[float(price), float(qty)] for price, qty in orderbook["bids"]],
                "asks": [[float(price), float(qty)] for price, qty in orderbook["asks"]],
                "timestamp": orderbook["time"] if "time" in orderbook else None
            }
        except BinanceAPIException as e:
            log_event(
                self.logger,
                "BINANCE_API_ERROR",
                f"Error getting orderbook for {symbol}: {str(e)}",
                level="ERROR",
                context={"symbol": symbol, "depth": depth, "error_code": e.code, "error_message": e.message}
            )
            raise
    
    @retry_async()
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
        try:
            klines = await self.client.futures_klines(
                symbol=symbol,
                interval=interval,
                limit=limit,
                startTime=start_time,
                endTime=end_time
            )
            
            # Format the klines
            formatted_klines = []
            for k in klines:
                formatted_klines.append({
                    "open_time": k[0],
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5]),
                    "close_time": k[6],
                    "quote_volume": float(k[7]),
                    "count": k[8],
                    "taker_buy_volume": float(k[9]),
                    "taker_buy_quote_volume": float(k[10])
                })
            
            return formatted_klines
        except BinanceAPIException as e:
            log_event(
                self.logger,
                "BINANCE_API_ERROR",
                f"Error getting klines for {symbol}: {str(e)}",
                level="ERROR",
                context={
                    "symbol": symbol,
                    "interval": interval,
                    "limit": limit,
                    "error_code": e.code,
                    "error_message": e.message
                }
            )
            raise
    
    async def start_user_socket(self) -> None:
        """
        Start the user data stream WebSocket connection.
        This includes account updates, position updates, and order updates.
        """
        if self.user_socket:
            await self.user_socket.close()
            
        self.user_socket = await self.bsm.futures_user_socket()
        asyncio.create_task(self._user_socket_listener())
        
        log_event(
            self.logger,
            "BINANCE_USER_SOCKET_STARTED",
            "Started user data stream WebSocket"
        )
    
    async def _user_socket_listener(self) -> None:
        """
        Listener for user data stream WebSocket messages.
        """
        try:
            async with self.user_socket as stream:
                while True:
                    msg = await stream.recv()
                    await self._process_user_socket_message(msg)
        except Exception as e:
            log_event(
                self.logger,
                "BINANCE_USER_SOCKET_ERROR",
                f"Error in user data stream: {str(e)}",
                level="ERROR"
            )
            # Try to reconnect
            await asyncio.sleep(5)
            asyncio.create_task(self.start_user_socket())
    
    async def _process_user_socket_message(self, msg: Dict[str, Any]) -> None:
        """
        Process a message from the user data stream.
        
        Args:
            msg: The WebSocket message.
        """
        try:
            if 'e' not in msg:
                return
                
            event_type = msg['e']
            
            if event_type == 'ACCOUNT_UPDATE':
                # Process account update
                for callback in self.callbacks['account_update']:
                    await callback(msg)
                
                # Also process positions in the account update
                if 'a' in msg and 'P' in msg['a']:
                    positions = msg['a']['P']
                    for position in positions:
                        pos_event = {
                            'e': 'POSITION_UPDATE',
                            'E': msg['E'],
                            'position': position
                        }
                        for callback in self.callbacks['position_update']:
                            await callback(pos_event)
            
            elif event_type == 'ORDER_TRADE_UPDATE':
                # Process order update
                for callback in self.callbacks['order_update']:
                    await callback(msg)
            
            else:
                # Unknown event type
                log_event(
                    self.logger,
                    "BINANCE_UNKNOWN_EVENT",
                    f"Unknown event type: {event_type}",
                    level="WARNING",
                    context={"event": event_type, "message": msg}
                )
        except Exception as e:
            log_event(
                self.logger,
                "BINANCE_MESSAGE_PROCESSING_ERROR",
                f"Error processing WebSocket message: {str(e)}",
                level="ERROR",
                context={"message": msg}
            )
    
    async def start_market_socket(self, symbol: str) -> None:
        """
        Start a market data WebSocket connection for a symbol.
        
        Args:
            symbol: The trading pair symbol.
        """
        if symbol in self.market_sockets:
            await self.market_sockets[symbol].close()
            
        self.market_sockets[symbol] = await self.bsm.futures_symbol_ticker_socket(symbol.lower())
        asyncio.create_task(self._market_socket_listener(symbol))
        
        log_event(
            self.logger,
            "BINANCE_MARKET_SOCKET_STARTED",
            f"Started market data WebSocket for {symbol}",
            context={"symbol": symbol}
        )
    
    async def _market_socket_listener(self, symbol: str) -> None:
        """
        Listener for market data WebSocket messages.
        
        Args:
            symbol: The trading pair symbol.
        """
        try:
            async with self.market_sockets[symbol] as stream:
                while True:
                    msg = await stream.recv()
                    
                    # Check if callbacks exist for this symbol
                    if symbol in self.callbacks['market_update']:
                        for callback in self.callbacks['market_update'][symbol]:
                            await callback(msg)
        except Exception as e:
            log_event(
                self.logger,
                "BINANCE_MARKET_SOCKET_ERROR",
                f"Error in market data stream for {symbol}: {str(e)}",
                level="ERROR",
                context={"symbol": symbol}
            )
            # Try to reconnect
            await asyncio.sleep(5)
            asyncio.create_task(self.start_market_socket(symbol))
    
    async def start_orderbook_socket(self, symbol: str, depth: int = 20) -> None:
        """
        Start an order book WebSocket connection for a symbol.
        
        Args:
            symbol: The trading pair symbol.
            depth: The depth of the order book to retrieve.
        """
        if symbol in self.book_sockets:
            await self.book_sockets[symbol].close()
            
        self.book_sockets[symbol] = await self.bsm.futures_depth_socket(symbol.lower(), depth=depth)
        asyncio.create_task(self._orderbook_socket_listener(symbol))
        
        log_event(
            self.logger,
            "BINANCE_ORDERBOOK_SOCKET_STARTED",
            f"Started order book WebSocket for {symbol}",
            context={"symbol": symbol, "depth": depth}
        )
    
    async def _orderbook_socket_listener(self, symbol: str) -> None:
        """
        Listener for order book WebSocket messages.
        
        Args:
            symbol: The trading pair symbol.
        """
        try:
            async with self.book_sockets[symbol] as stream:
                while True:
                    msg = await stream.recv()
                    
                    # Check if callbacks exist for this symbol
                    if symbol in self.callbacks['book_update']:
                        for callback in self.callbacks['book_update'][symbol]:
                            await callback(msg)
        except Exception as e:
            log_event(
                self.logger,
                "BINANCE_ORDERBOOK_SOCKET_ERROR",
                f"Error in order book stream for {symbol}: {str(e)}",
                level="ERROR",
                context={"symbol": symbol}
            )
            # Try to reconnect
            await asyncio.sleep(5)
            asyncio.create_task(self.start_orderbook_socket(symbol))
    
    def register_account_callback(self, callback: Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]) -> None:
        """
        Register a callback for account updates.
        
        Args:
            callback: The callback function.
        """
        self.callbacks['account_update'].append(callback)
    
    def register_position_callback(self, callback: Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]) -> None:
        """
        Register a callback for position updates.
        
        Args:
            callback: The callback function.
        """
        self.callbacks['position_update'].append(callback)
    
    def register_order_callback(self, callback: Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]) -> None:
        """
        Register a callback for order updates.
        
        Args:
            callback: The callback function.
        """
        self.callbacks['order_update'].append(callback)
    
    def register_market_callback(self, symbol: str, callback: Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]) -> None:
        """
        Register a callback for market data updates.
        
        Args:
            symbol: The trading pair symbol.
            callback: The callback function.
        """
        if symbol not in self.callbacks['market_update']:
            self.callbacks['market_update'][symbol] = []
        self.callbacks['market_update'][symbol].append(callback)
    
    def register_orderbook_callback(self, symbol: str, callback: Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]) -> None:
        """
        Register a callback for order book updates.
        
        Args:
            symbol: The trading pair symbol.
            callback: The callback function.
        """
        if symbol not in self.callbacks['book_update']:
            self.callbacks['book_update'][symbol] = []
        self.callbacks['book_update'][symbol].append(callback)
    
    @retry_async()
    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """
        Set the leverage for a symbol.
        
        Args:
            symbol: The trading pair symbol.
            leverage: The leverage to set (1-125).
            
        Returns:
            Dict containing response information.
        """
        try:
            response = await self.client.futures_change_leverage(
                symbol=symbol,
                leverage=leverage
            )
            
            log_event(
                self.logger,
                "LEVERAGE_UPDATED",
                f"Updated leverage for {symbol} to {leverage}x",
                context={"symbol": symbol, "leverage": leverage}
            )
            
            return response
        except BinanceAPIException as e:
            log_event(
                self.logger,
                "BINANCE_API_ERROR",
                f"Error setting leverage for {symbol}: {str(e)}",
                level="ERROR",
                context={"symbol": symbol, "leverage": leverage, "error_code": e.code, "error_message": e.message}
            )
            raise
    
    @retry_async()
    async def set_margin_type(self, symbol: str, margin_type: str) -> Dict[str, Any]:
        """
        Set the margin type for a symbol.
        
        Args:
            symbol: The trading pair symbol.
            margin_type: The margin type to set ('ISOLATED' or 'CROSSED').
            
        Returns:
            Dict containing response information.
        """
        try:
            response = await self.client.futures_change_margin_type(
                symbol=symbol,
                marginType=margin_type.upper()
            )
            
            log_event(
                self.logger,
                "MARGIN_TYPE_UPDATED",
                f"Updated margin type for {symbol} to {margin_type}",
                context={"symbol": symbol, "margin_type": margin_type}
            )
            
            return response
        except BinanceAPIException as e:
            # Ignore error if margin type is already what we're trying to set
            if e.code == -4046:  # "No need to change margin type."
                return {"msg": "Margin type already set.", "success": True}
                
            log_event(
                self.logger,
                "BINANCE_API_ERROR",
                f"Error setting margin type for {symbol}: {str(e)}",
                level="ERROR",
                context={"symbol": symbol, "margin_type": margin_type, "error_code": e.code, "error_message": e.message}
            )
            raise
    
    async def create_stop_loss_order(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        stop_price: Decimal,
        close_position: bool = True
    ) -> Dict[str, Any]:
        """
        Create a stop loss order.
        
        Args:
            symbol: The trading pair symbol.
            side: Order side ('buy' or 'sell').
            quantity: Order quantity. If close_position is True, this is ignored.
            stop_price: Stop price.
            close_position: Whether to close the entire position.
            
        Returns:
            Dict containing order information.
        """
        try:
            params = {
                "symbol": symbol,
                "side": side.upper(),
                "type": "STOP_MARKET",
                "stopPrice": float(stop_price),
                "reduceOnly": True
            }
            
            if close_position:
                params["closePosition"] = True
            else:
                params["quantity"] = float(quantity)
            
            response = await self.client.futures_create_order(**params)
            
            log_event(
                self.logger,
                "STOP_LOSS_CREATED",
                f"Created stop loss order for {symbol} at {stop_price}",
                context={"symbol": symbol, "stop_price": float(stop_price), "side": side, "close_position": close_position}
            )
            
            return self._format_order(response)
        except BinanceAPIException as e:
            log_event(
                self.logger,
                "BINANCE_API_ERROR",
                f"Error creating stop loss order for {symbol}: {str(e)}",
                level="ERROR",
                context={
                    "symbol": symbol, 
                    "side": side, 
                    "stop_price": float(stop_price),
                    "error_code": e.code, 
                    "error_message": e.message
                }
            )
            raise
    
    async def create_take_profit_order(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        take_profit_price: Decimal,
        close_position: bool = True
    ) -> Dict[str, Any]:
        """
        Create a take profit order.
        
        Args:
            symbol: The trading pair symbol.
            side: Order side ('buy' or 'sell').
            quantity: Order quantity. If close_position is True, this is ignored.
            take_profit_price: Take profit price.
            close_position: Whether to close the entire position.
            
        Returns:
            Dict containing order information.
        """
        try:
            params = {
                "symbol": symbol,
                "side": side.upper(),
                "type": "TAKE_PROFIT_MARKET",
                "stopPrice": float(take_profit_price),
                "reduceOnly": True
            }
            
            if close_position:
                params["closePosition"] = True
            else:
                params["quantity"] = float(quantity)
            
            response = await self.client.futures_create_order(**params)
            
            log_event(
                self.logger,
                "TAKE_PROFIT_CREATED",
                f"Created take profit order for {symbol} at {take_profit_price}",
                context={"symbol": symbol, "take_profit_price": float(take_profit_price), "side": side, "close_position": close_position}
            )
            
            return self._format_order(response)
        except BinanceAPIException as e:
            log_event(
                self.logger,
                "BINANCE_API_ERROR",
                f"Error creating take profit order for {symbol}: {str(e)}",
                level="ERROR",
                context={
                    "symbol": symbol, 
                    "side": side, 
                    "take_profit_price": float(take_profit_price),
                    "error_code": e.code, 
                    "error_message": e.message
                }
            )
            raise
    
    async def update_position_sl_tp(
        self,
        symbol: str,
        stop_loss: Optional[Decimal] = None,
        take_profit: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Update the stop loss and take profit for an existing position.
        
        Args:
            symbol: The trading pair symbol.
            stop_loss: The new stop loss price.
            take_profit: The new take profit price.
            
        Returns:
            Dict containing status and orders information.
        """
        try:
            # Get the current position
            position = await self.get_position(symbol)
            if not position:
                raise ValueError(f"No open position for {symbol}")
            
            # Cancel any existing SL/TP orders
            current_orders = await self.get_orders(symbol=symbol)
            for order in current_orders:
                if order["type"] in ["STOP_MARKET", "TAKE_PROFIT_MARKET"]:
                    await self.cancel_order(order["order_id"], symbol)
            
            # Determine the side for SL/TP orders (opposite of position side)
            position_side = position["side"]
            sl_tp_side = "sell" if position_side == "long" else "buy"
            
            # Create new orders
            results = {
                "status": "success",
                "position": position,
                "stop_loss_order": None,
                "take_profit_order": None
            }
            
            if stop_loss:
                sl_order = await self.create_stop_loss_order(
                    symbol=symbol,
                    side=sl_tp_side,
                    quantity=position["position_amt"],
                    stop_price=stop_loss,
                    close_position=True
                )
                results["stop_loss_order"] = sl_order
            
            if take_profit:
                tp_order = await self.create_take_profit_order(
                    symbol=symbol,
                    side=sl_tp_side,
                    quantity=position["position_amt"],
                    take_profit_price=take_profit,
                    close_position=True
                )
                results["take_profit_order"] = tp_order
            
            log_event(
                self.logger,
                "POSITION_SL_TP_UPDATED",
                f"Updated SL/TP for {symbol} position",
                context={
                    "symbol": symbol,
                    "stop_loss": float(stop_loss) if stop_loss else None,
                    "take_profit": float(take_profit) if take_profit else None
                }
            )
            
            return results
        except Exception as e:
            log_event(
                self.logger,
                "POSITION_SL_TP_UPDATE_ERROR",
                f"Error updating SL/TP for {symbol} position: {str(e)}",
                level="ERROR",
                context={
                    "symbol": symbol,
                    "stop_loss": float(stop_loss) if stop_loss else None,
                    "take_profit": float(take_profit) if take_profit else None
                }
            )
            raise
    
    def _format_position(self, position: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a position from the Binance API to match our expected format.
        
        Args:
            position: The position from the Binance API.
            
        Returns:
            Dict containing formatted position information.
        """
        position_amt = float(position["positionAmt"])
        entry_price = float(position["entryPrice"])
        
        # Determine side
        side = "long" if position_amt > 0 else "short"
        
        # Calculate PnL
        unrealized_pnl = float(position["unrealizedProfit"])
        leverage = float(position["leverage"])
        
        return {
            "symbol": position["symbol"],
            "side": side,
            "entry_price": entry_price,
            "mark_price": float(position["markPrice"]),
            "position_amt": abs(position_amt),
            "leverage": leverage,
            "unrealized_pnl": unrealized_pnl,
            "margin_type": position["marginType"].lower(),
            "isolate_margin": float(position["isolatedMargin"]) if position["marginType"] == "ISOLATED" else None,
            "liquidation_price": float(position["liquidationPrice"]) if float(position["liquidationPrice"]) > 0 else None,
            "position_value": abs(position_amt) * float(position["markPrice"])
        }
    
    def _format_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format an order from the Binance API to match our expected format.
        
        Args:
            order: The order from the Binance API.
            
        Returns:
            Dict containing formatted order information.
        """
        return {
            "order_id": str(order["orderId"]),
            "client_order_id": order["clientOrderId"],
            "symbol": order["symbol"],
            "status": order["status"].lower(),
            "side": order["side"].lower(),
            "order_type": self._map_order_type_reverse(order["type"]),
            "time_in_force": order["timeInForce"] if "timeInForce" in order else None,
            "quantity": float(order["origQty"]),
            "price": float(order["price"]) if float(order["price"]) > 0 else None,
            "stop_price": float(order["stopPrice"]) if "stopPrice" in order and float(order["stopPrice"]) > 0 else None,
            "executed_qty": float(order["executedQty"]),
            "reduce_only": order["reduceOnly"] if "reduceOnly" in order else False,
            "created_time": order["time"] if "time" in order else None,
            "updated_time": order["updateTime"] if "updateTime" in order else None
        }
    
    def _map_order_type(self, order_type: str) -> str:
        """
        Map our standardized order types to Binance's order types.
        
        Args:
            order_type: Our standardized order type.
            
        Returns:
            Binance's order type.
        """
        mapping = {
            "limit": "LIMIT",
            "market": "MARKET",
            "stop": "STOP_MARKET",
            "stop_market": "STOP_MARKET",
            "stop_limit": "STOP",
            "take_profit": "TAKE_PROFIT_MARKET",
            "take_profit_market": "TAKE_PROFIT_MARKET",
            "take_profit_limit": "TAKE_PROFIT"
        }
        
        return mapping.get(order_type.lower(), "LIMIT")
    
    def _map_order_type_reverse(self, order_type: str) -> str:
        """
        Map Binance's order types to our standardized order types.
        
        Args:
            order_type: Binance's order type.
            
        Returns:
            Our standardized order type.
        """
        mapping = {
            "LIMIT": "limit",
            "MARKET": "market",
            "STOP_MARKET": "stop_market",
            "STOP": "stop_limit",
            "TAKE_PROFIT_MARKET": "take_profit_market",
            "TAKE_PROFIT": "take_profit_limit"
        }
        
        return mapping.get(order_type, "limit")
    
    async def open_position(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        leverage: int = 1,
        margin_type: str = "ISOLATED",
        order_type: str = "MARKET",
        price: Optional[Decimal] = None,
        stop_loss: Optional[Decimal] = None,
        take_profit: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Open a new position with optional stop loss and take profit orders.
        
        This is a high-level method that:
        1. Sets the leverage
        2. Sets the margin type
        3. Creates the order
        4. Sets up stop loss and take profit orders if requested
        
        Args:
            symbol: The trading pair symbol.
            side: Order side ('buy' or 'sell').
            quantity: Order quantity.
            leverage: The leverage to use.
            margin_type: The margin type ('ISOLATED' or 'CROSSED').
            order_type: Order type ('MARKET', 'LIMIT', etc.).
            price: Order price (required for limit orders).
            stop_loss: Optional stop loss price.
            take_profit: Optional take profit price.
            
        Returns:
            Dict containing position and order information.
        """
        try:
            # Set leverage
            await self.set_leverage(symbol, leverage)
            
            # Set margin type
            await self.set_margin_type(symbol, margin_type)
            
            # Create the order
            entry_order = await self.create_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                reduce_only=False
            )
            
            # Get the position after order execution
            position = await self.get_position(symbol)
            
            # Set up stop loss and take profit if requested
            sl_tp_orders = None
            if position and (stop_loss or take_profit):
                sl_tp_orders = await self.update_position_sl_tp(
                    symbol=symbol,
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
            
            result = {
                "status": "success",
                "position": position,
                "entry_order": entry_order,
                "sl_tp_orders": sl_tp_orders
            }
            
            log_event(
                self.logger,
                "POSITION_OPENED",
                f"Opened {side} position for {symbol} with {leverage}x leverage",
                context={
                    "symbol": symbol,
                    "side": side,
                    "quantity": float(quantity),
                    "leverage": leverage,
                    "order_type": order_type,
                    "price": float(price) if price else None,
                    "stop_loss": float(stop_loss) if stop_loss else None,
                    "take_profit": float(take_profit) if take_profit else None
                }
            )
            
            return result
        except Exception as e:
            log_event(
                self.logger,
                "POSITION_OPEN_ERROR",
                f"Error opening position for {symbol}: {str(e)}",
                level="ERROR",
                context={
                    "symbol": symbol,
                    "side": side,
                    "quantity": float(quantity),
                    "leverage": leverage,
                    "order_type": order_type,
                    "price": float(price) if price else None
                }
            )
            raise
    
    async def close_position(
        self,
        symbol: str,
        close_type: str = "MARKET",
        price: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Close an existing position.
        
        Args:
            symbol: The trading pair symbol.
            close_type: The order type to use for closing ('MARKET' or 'LIMIT').
            price: The price for limit orders (required if close_type is 'LIMIT').
            
        Returns:
            Dict containing order information.
        """
        try:
            # Get the current position
            position = await self.get_position(symbol)
            if not position:
                raise ValueError(f"No open position for {symbol}")
            
            # Determine the close side (opposite of position side)
            close_side = "sell" if position["side"] == "long" else "buy"
            
            # Cancel any existing SL/TP orders
            current_orders = await self.get_orders(symbol=symbol)
            for order in current_orders:
                if order["type"] in ["STOP_MARKET", "TAKE_PROFIT_MARKET"]:
                    await self.cancel_order(order["order_id"], symbol)
            
            # Create the close order
            close_order = await self.create_order(
                symbol=symbol,
                side=close_side,
                order_type=close_type,
                quantity=position["position_amt"],
                price=price,
                reduce_only=True
            )
            
            log_event(
                self.logger,
                "POSITION_CLOSED",
                f"Closed {position['side']} position for {symbol}",
                context={
                    "symbol": symbol,
                    "side": position["side"],
                    "quantity": position["position_amt"],
                    "close_type": close_type,
                    "price": float(price) if price else None
                }
            )
            
            return close_order
        except Exception as e:
            log_event(
                self.logger,
                "POSITION_CLOSE_ERROR",
                f"Error closing position for {symbol}: {str(e)}",
                level="ERROR",
                context={
                    "symbol": symbol,
                    "close_type": close_type,
                    "price": float(price) if price else None
                }
            )
            raise
    
    async def update_position(
        self,
        symbol: str,
        add_quantity: Optional[Decimal] = None,
        reduce_quantity: Optional[Decimal] = None,
        stop_loss: Optional[Decimal] = None,
        take_profit: Optional[Decimal] = None,
        order_type: str = "MARKET",
        price: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Update an existing position by adding to it, reducing it, or updating SL/TP.
        
        Args:
            symbol: The trading pair symbol.
            add_quantity: The quantity to add to the position.
            reduce_quantity: The quantity to reduce from the position.
            stop_loss: The new stop loss price.
            take_profit: The new take profit price.
            order_type: The order type for adding/reducing ('MARKET' or 'LIMIT').
            price: The price for limit orders.
            
        Returns:
            Dict containing order and position information.
        """
        try:
            # Get the current position
            position = await self.get_position(symbol)
            if not position:
                raise ValueError(f"No open position for {symbol}")
            
            result = {
                "status": "success",
                "position": position,
                "orders": []
            }
            
            # Handle quantity modifications
            if add_quantity:
                # Add to position
                add_order = await self.create_order(
                    symbol=symbol,
                    side=position["side"],
                    order_type=order_type,
                    quantity=add_quantity,
                    price=price,
                    reduce_only=False
                )
                result["orders"].append(add_order)
                
                # Get updated position
                position = await self.get_position(symbol)
                result["position"] = position
            
            if reduce_quantity:
                # Reduce position
                reduce_side = "sell" if position["side"] == "long" else "buy"
                reduce_order = await self.create_order(
                    symbol=symbol,
                    side=reduce_side,
                    order_type=order_type,
                    quantity=reduce_quantity,
                    price=price,
                    reduce_only=True
                )
                result["orders"].append(reduce_order)
                
                # Get updated position
                position = await self.get_position(symbol)
                result["position"] = position
            
            # Update SL/TP if requested
            if stop_loss or take_profit:
                sl_tp_result = await self.update_position_sl_tp(
                    symbol=symbol,
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
                result["sl_tp_orders"] = sl_tp_result
            
            log_event(
                self.logger,
                "POSITION_UPDATED",
                f"Updated {position['side']} position for {symbol}",
                context={
                    "symbol": symbol,
                    "add_quantity": float(add_quantity) if add_quantity else None,
                    "reduce_quantity": float(reduce_quantity) if reduce_quantity else None,
                    "stop_loss": float(stop_loss) if stop_loss else None,
                    "take_profit": float(take_profit) if take_profit else None
                }
            )
            
            return result
        except Exception as e:
            log_event(
                self.logger,
                "POSITION_UPDATE_ERROR",
                f"Error updating position for {symbol}: {str(e)}",
                level="ERROR",
                context={
                    "symbol": symbol,
                    "add_quantity": float(add_quantity) if add_quantity else None,
                    "reduce_quantity": float(reduce_quantity) if reduce_quantity else None,
                    "stop_loss": float(stop_loss) if stop_loss else None,
                    "take_profit": float(take_profit) if take_profit else None
                }
            )
            raise 