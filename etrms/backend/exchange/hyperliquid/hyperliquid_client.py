"""
Enhanced Trading Risk Management System Hyperliquid Client
"""
import asyncio
import base64
import hashlib
import hmac
import json
import time
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple, Callable

import aiohttp
import websockets

from config.settings import settings
from exchange.common.exchange_interface import ExchangeInterface
from utils.logger import get_logger, log_event


class HyperliquidClient(ExchangeInterface):
    """
    Implementation of the Exchange Interface for Hyperliquid.
    """
    
    BASE_URL = "https://api.hyperliquid.xyz"
    WS_URL = "wss://api.hyperliquid.xyz/ws"
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Initialize the Hyperliquid client.
        
        Args:
            api_key: The API key for authentication.
            api_secret: The API secret for authentication.
        """
        self.api_key = api_key or settings.HYPERLIQUID_API_KEY
        self.api_secret = api_secret or settings.HYPERLIQUID_API_SECRET
        self.session = None
        self.logger = get_logger(__name__)
        
        # WebSocket related attributes
        self.ws = None
        self.ws_connected = False
        self.user_ws = None
        self.user_ws_connected = False
        self.market_ws = {}
        self.callbacks = {
            'account_update': [],
            'position_update': [],
            'order_update': [],
            'market_update': {},
            'book_update': {}
        }
        
        log_event(
            self.logger, 
            "HYPERLIQUID_CLIENT_INIT", 
            "Initializing Hyperliquid client"
        )
    
    async def initialize(self) -> None:
        """
        Initialize the Hyperliquid client.
        """
        try:
            self.session = aiohttp.ClientSession()
            log_event(
                self.logger,
                "HYPERLIQUID_CLIENT_INITIALIZED",
                "Hyperliquid client initialized successfully"
            )
        except Exception as e:
            log_event(
                self.logger,
                "HYPERLIQUID_CLIENT_INIT_ERROR",
                f"Failed to initialize Hyperliquid client: {str(e)}",
                level="ERROR"
            )
            raise
    
    async def close(self) -> None:
        """
        Close the Hyperliquid client.
        """
        if self.session:
            await self.session.close()
            log_event(
                self.logger,
                "HYPERLIQUID_CLIENT_CLOSED",
                "Hyperliquid client closed"
            )
    
    async def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information including balance, positions, etc.
        
        Returns:
            Dict containing account information.
        """
        try:
            response = await self._request("GET", "/api/v1/user/accountSummary")
            
            # Format the response to match our expected format
            formatted_account = {
                "total_equity": float(response.get("totalCollateralValue", 0)),
                "available_balance": float(response.get("availableMargin", 0)),
                "margin_balance": float(response.get("maintenanceMargin", 0)),
                "unrealized_pnl": float(response.get("unrealizedPnl", 0)),
                "positions": [self._format_position(p) for p in response.get("positions", [])]
            }
            
            return formatted_account
        except Exception as e:
            log_event(
                self.logger,
                "HYPERLIQUID_API_ERROR",
                f"Error getting account info: {str(e)}",
                level="ERROR"
            )
            raise
    
    async def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific position.
        
        Args:
            symbol: The trading pair symbol.
            
        Returns:
            Dict containing position information or None if no position exists.
        """
        try:
            response = await self._request("GET", f"/api/v1/user/position?asset={symbol}")
            
            if not response or "position" not in response or not response["position"]:
                return None
                
            return self._format_position(response["position"])
        except Exception as e:
            log_event(
                self.logger,
                "HYPERLIQUID_API_ERROR",
                f"Error getting position for {symbol}: {str(e)}",
                level="ERROR",
                context={"symbol": symbol}
            )
            raise
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get all open positions.
        
        Returns:
            List of dicts containing position information.
        """
        try:
            response = await self._request("GET", "/api/v1/user/positions")
            
            # Filter out positions with zero size
            active_positions = [p for p in response.get("positions", []) if float(p.get("size", 0)) != 0]
            
            return [self._format_position(p) for p in active_positions]
        except Exception as e:
            log_event(
                self.logger,
                "HYPERLIQUID_API_ERROR",
                f"Error getting positions: {str(e)}",
                level="ERROR"
            )
            raise
    
    async def get_order(self, order_id: str, symbol: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific order.
        
        Args:
            order_id: The ID of the order.
            symbol: The trading pair symbol (optional).
            
        Returns:
            Dict containing order information or None if the order doesn't exist.
        """
        try:
            response = await self._request("GET", f"/api/v1/user/order?orderId={order_id}")
            
            if not response or "order" not in response:
                return None
                
            return self._format_order(response["order"])
        except Exception as e:
            log_event(
                self.logger,
                "HYPERLIQUID_API_ERROR",
                f"Error getting order {order_id}: {str(e)}",
                level="ERROR",
                context={"order_id": order_id}
            )
            raise
    
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
                response = await self._request("GET", f"/api/v1/user/orders?asset={symbol}")
            else:
                response = await self._request("GET", "/api/v1/user/orders")
                
            orders = response.get("orders", [])
            
            return [self._format_order(order) for order in orders]
        except Exception as e:
            log_event(
                self.logger,
                "HYPERLIQUID_API_ERROR",
                f"Error getting orders: {str(e)}",
                level="ERROR",
                context={"symbol": symbol}
            )
            raise
    
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
                "asset": symbol,
                "side": "B" if side.lower() == "buy" else "A",
                "size": str(quantity),
                "reduceOnly": reduce_only
            }
            
            # Add additional parameters based on order type
            if order_type.lower() in ["limit", "stop_limit"]:
                if not price:
                    raise ValueError("Price is required for limit orders")
                params["orderType"] = "LIMIT"
                params["limitPrice"] = str(price)
                params["timeInForce"] = time_in_force
            elif order_type.lower() in ["market"]:
                params["orderType"] = "MARKET"
            elif order_type.lower() in ["stop", "stop_market"]:
                if not stop_price:
                    raise ValueError("Stop price is required for stop orders")
                params["orderType"] = "STOP_MARKET"
                params["triggerPrice"] = str(stop_price)
            elif order_type.lower() in ["stop_limit"]:
                if not price or not stop_price:
                    raise ValueError("Price and stop price are required for stop limit orders")
                params["orderType"] = "STOP_LIMIT"
                params["limitPrice"] = str(price)
                params["triggerPrice"] = str(stop_price)
                params["timeInForce"] = time_in_force
            
            # Create the order
            response = await self._request("POST", "/api/v1/order", data=params)
            
            if "orderId" not in response:
                raise ValueError(f"Failed to create order: {response}")
            
            # Get the created order
            created_order = await self.get_order(response["orderId"])
            
            log_event(
                self.logger,
                "ORDER_CREATED",
                f"Created {order_type} order for {symbol}",
                context={"symbol": symbol, "order_id": response["orderId"], "side": side, "quantity": float(quantity)}
            )
            
            return created_order
        except Exception as e:
            log_event(
                self.logger,
                "HYPERLIQUID_API_ERROR",
                f"Error creating order for {symbol}: {str(e)}",
                level="ERROR",
                context={
                    "symbol": symbol, 
                    "side": side, 
                    "order_type": order_type, 
                    "quantity": float(quantity)
                }
            )
            raise
    
    async def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel an existing order.
        
        Args:
            order_id: The ID of the order.
            symbol: The trading pair symbol (not required for Hyperliquid).
            
        Returns:
            Dict containing order information.
        """
        try:
            params = {
                "orderId": order_id
            }
            
            response = await self._request("POST", "/api/v1/cancel", data=params)
            
            if "success" not in response or not response["success"]:
                raise ValueError(f"Failed to cancel order: {response}")
            
            log_event(
                self.logger,
                "ORDER_CANCELED",
                f"Canceled order {order_id}",
                context={"order_id": order_id}
            )
            
            # Get the order after cancellation
            canceled_order = await self.get_order(order_id)
            if not canceled_order:
                # If order not found, create a minimal response
                canceled_order = {
                    "order_id": order_id,
                    "status": "canceled",
                    "symbol": symbol or "UNKNOWN"
                }
            
            return canceled_order
        except Exception as e:
            log_event(
                self.logger,
                "HYPERLIQUID_API_ERROR",
                f"Error canceling order {order_id}: {str(e)}",
                level="ERROR",
                context={"order_id": order_id}
            )
            raise
    
    async def cancel_all_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Cancel all open orders, optionally filtered by symbol.
        
        Args:
            symbol: The trading pair symbol (optional).
            
        Returns:
            List of dicts containing order information.
        """
        try:
            params = {}
            if symbol:
                params["asset"] = symbol
                
            response = await self._request("POST", "/api/v1/cancelAll", data=params)
            
            if "success" not in response or not response["success"]:
                raise ValueError(f"Failed to cancel all orders: {response}")
            
            log_event(
                self.logger,
                "ALL_ORDERS_CANCELED",
                f"Canceled all orders{' for ' + symbol if symbol else ''}",
                context={"symbol": symbol}
            )
            
            # Get orders after cancellation
            return await self.get_orders(symbol)
        except Exception as e:
            log_event(
                self.logger,
                "HYPERLIQUID_API_ERROR",
                f"Error canceling all orders: {str(e)}",
                level="ERROR",
                context={"symbol": symbol}
            )
            raise
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get the current ticker for a symbol.
        
        Args:
            symbol: The trading pair symbol.
            
        Returns:
            Dict containing ticker information.
        """
        try:
            response = await self._request("GET", f"/api/v1/ticker?asset={symbol}")
            
            return {
                "symbol": symbol,
                "price": float(response.get("markPrice", 0)),
                "time": int(time.time() * 1000)
            }
        except Exception as e:
            log_event(
                self.logger,
                "HYPERLIQUID_API_ERROR",
                f"Error getting ticker for {symbol}: {str(e)}",
                level="ERROR",
                context={"symbol": symbol}
            )
            raise
    
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
            response = await self._request("GET", f"/api/v1/orderbook?asset={symbol}&depth={depth}")
            
            return {
                "symbol": symbol,
                "bids": [[float(item[0]), float(item[1])] for item in response.get("bids", [])],
                "asks": [[float(item[0]), float(item[1])] for item in response.get("asks", [])],
                "timestamp": int(time.time() * 1000)
            }
        except Exception as e:
            log_event(
                self.logger,
                "HYPERLIQUID_API_ERROR",
                f"Error getting orderbook for {symbol}: {str(e)}",
                level="ERROR",
                context={"symbol": symbol, "depth": depth}
            )
            raise
    
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
            # Map our interval format to Hyperliquid's
            interval_map = {
                "1m": "1min",
                "5m": "5min",
                "15m": "15min",
                "30m": "30min",
                "1h": "1hour",
                "4h": "4hour",
                "1d": "1day"
            }
            
            hl_interval = interval_map.get(interval, "1hour")
            
            params = {
                "asset": symbol,
                "resolution": hl_interval,
                "limit": limit
            }
            
            if start_time:
                params["startTime"] = start_time
            if end_time:
                params["endTime"] = end_time
                
            response = await self._request("GET", "/api/v1/klines", params=params)
            
            # Format the klines
            formatted_klines = []
            for k in response:
                formatted_klines.append({
                    "open_time": k["time"],
                    "open": float(k["open"]),
                    "high": float(k["high"]),
                    "low": float(k["low"]),
                    "close": float(k["close"]),
                    "volume": float(k["volume"]),
                    "close_time": k["time"] + self._get_interval_ms(interval),
                    "quote_volume": 0,  # Not provided by Hyperliquid
                    "count": 0,  # Not provided by Hyperliquid
                    "taker_buy_volume": 0,  # Not provided by Hyperliquid
                    "taker_buy_quote_volume": 0  # Not provided by Hyperliquid
                })
            
            return formatted_klines
        except Exception as e:
            log_event(
                self.logger,
                "HYPERLIQUID_API_ERROR",
                f"Error getting klines for {symbol}: {str(e)}",
                level="ERROR",
                context={
                    "symbol": symbol,
                    "interval": interval,
                    "limit": limit
                }
            )
            raise
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to the Hyperliquid API.
        
        Args:
            method: The HTTP method.
            endpoint: The API endpoint.
            params: Query parameters.
            data: Request body data.
            
        Returns:
            API response.
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add authentication for private endpoints
        if endpoint.startswith("/api/v1/user") or endpoint.startswith("/api/v1/order") or endpoint.startswith("/api/v1/cancel"):
            timestamp = int(time.time() * 1000)
            headers["HL-API-KEY"] = self.api_key
            headers["HL-SIGNATURE"] = self._generate_signature(endpoint, timestamp, data)
            headers["HL-TIMESTAMP"] = str(timestamp)
        
        # Prepare request
        kwargs = {}
        if params:
            kwargs["params"] = params
        if data:
            kwargs["json"] = data
            
        async with self.session.request(method, url, headers=headers, **kwargs) as response:
            if response.status != 200:
                error_text = await response.text()
                log_event(
                    self.logger,
                    "HYPERLIQUID_API_ERROR",
                    f"API error: {response.status} - {error_text}",
                    level="ERROR",
                    context={"status_code": response.status, "endpoint": endpoint}
                )
                raise ValueError(f"API error: {response.status} - {error_text}")
                
            return await response.json()
    
    def _generate_signature(self, endpoint: str, timestamp: int, data: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a signature for the API request.
        
        Args:
            endpoint: The API endpoint.
            timestamp: The request timestamp.
            data: Request body data.
            
        Returns:
            The signature.
        """
        message = f"{endpoint}{timestamp}"
        if data:
            message += json.dumps(data, separators=(',', ':'))
            
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _format_position(self, position: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a position from the Hyperliquid API to match our expected format.
        
        Args:
            position: The position from the Hyperliquid API.
            
        Returns:
            Dict containing formatted position information.
        """
        size = float(position.get("size", 0))
        entry_price = float(position.get("entryPrice", 0))
        mark_price = float(position.get("markPrice", 0))
        
        # Determine side
        side = "long" if size > 0 else "short"
        
        # Calculate PnL
        unrealized_pnl = float(position.get("unrealizedPnl", 0))
        leverage = float(position.get("leverage", 1))
        
        return {
            "symbol": position.get("asset", "UNKNOWN"),
            "side": side,
            "entry_price": entry_price,
            "mark_price": mark_price,
            "position_amt": abs(size),
            "leverage": leverage,
            "unrealized_pnl": unrealized_pnl,
            "margin_type": position.get("marginType", "cross").lower(),
            "isolate_margin": float(position.get("isolatedMargin", 0)) if position.get("marginType") == "isolated" else None,
            "liquidation_price": float(position.get("liquidationPrice", 0)) if "liquidationPrice" in position else None,
            "position_value": abs(size) * mark_price
        }
    
    def _format_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format an order from the Hyperliquid API to match our expected format.
        
        Args:
            order: The order from the Hyperliquid API.
            
        Returns:
            Dict containing formatted order information.
        """
        return {
            "order_id": order.get("orderId", "UNKNOWN"),
            "client_order_id": order.get("clientOrderId", ""),
            "symbol": order.get("asset", "UNKNOWN"),
            "status": order.get("status", "unknown").lower(),
            "side": "buy" if order.get("side") == "B" else "sell",
            "order_type": self._map_order_type_reverse(order.get("orderType", "LIMIT")),
            "time_in_force": order.get("timeInForce", "GTC"),
            "quantity": float(order.get("size", 0)),
            "price": float(order.get("limitPrice", 0)) if "limitPrice" in order and float(order.get("limitPrice", 0)) > 0 else None,
            "stop_price": float(order.get("triggerPrice", 0)) if "triggerPrice" in order and float(order.get("triggerPrice", 0)) > 0 else None,
            "executed_qty": float(order.get("filledSize", 0)),
            "reduce_only": order.get("reduceOnly", False),
            "created_time": order.get("createdAt", 0),
            "updated_time": order.get("updatedAt", 0)
        }
    
    def _map_order_type_reverse(self, order_type: str) -> str:
        """
        Map Hyperliquid's order types to our standardized order types.
        
        Args:
            order_type: Hyperliquid's order type.
            
        Returns:
            Our standardized order type.
        """
        mapping = {
            "LIMIT": "limit",
            "MARKET": "market",
            "STOP_MARKET": "stop_market",
            "STOP_LIMIT": "stop_limit",
            "TAKE_PROFIT_MARKET": "take_profit_market",
            "TAKE_PROFIT_LIMIT": "take_profit_limit"
        }
        
        return mapping.get(order_type, "limit")
    
    def _get_interval_ms(self, interval: str) -> int:
        """
        Convert interval string to milliseconds.
        
        Args:
            interval: Interval string (e.g., '1m', '5m', '1h').
            
        Returns:
            Interval in milliseconds.
        """
        unit = interval[-1]
        value = int(interval[:-1])
        
        if unit == 'm':
            return value * 60 * 1000
        elif unit == 'h':
            return value * 60 * 60 * 1000
        elif unit == 'd':
            return value * 24 * 60 * 60 * 1000
        else:
            return 60 * 60 * 1000  # Default to 1 hour 
    
    async def start_user_socket(self) -> None:
        """
        Start a WebSocket connection for user data (account, positions, orders).
        """
        if self.user_ws_connected:
            return
            
        try:
            self.user_ws = await websockets.connect(self.WS_URL)
            
            # Subscribe to user updates
            subscription_message = {
                "type": "subscribe",
                "channel": "user",
                "token": self._generate_auth_token()
            }
            
            await self.user_ws.send(json.dumps(subscription_message))
            
            # Start listener task
            asyncio.create_task(self._user_socket_listener())
            
            self.user_ws_connected = True
            
            log_event(
                self.logger,
                "HYPERLIQUID_USER_SOCKET_STARTED",
                "Started user data WebSocket"
            )
        except Exception as e:
            log_event(
                self.logger,
                "HYPERLIQUID_USER_SOCKET_ERROR",
                f"Error starting user WebSocket: {str(e)}",
                level="ERROR"
            )
            self.user_ws_connected = False
            raise
    
    async def _user_socket_listener(self) -> None:
        """
        Listener for user socket messages.
        """
        try:
            while True:
                if not self.user_ws:
                    break
                    
                message = await self.user_ws.recv()
                data = json.loads(message)
                
                await self._process_user_socket_message(data)
        except websockets.exceptions.ConnectionClosed:
            log_event(
                self.logger,
                "HYPERLIQUID_USER_SOCKET_CLOSED",
                "User WebSocket connection closed",
                level="WARNING"
            )
        except Exception as e:
            log_event(
                self.logger,
                "HYPERLIQUID_USER_SOCKET_ERROR",
                f"Error in user WebSocket listener: {str(e)}",
                level="ERROR"
            )
        finally:
            self.user_ws_connected = False
            # Try to reconnect after a delay
            await asyncio.sleep(5)
            asyncio.create_task(self.start_user_socket())
    
    async def _process_user_socket_message(self, data: Dict[str, Any]) -> None:
        """
        Process a message from the user socket.
        
        Args:
            data: The WebSocket message.
        """
        try:
            if "type" not in data:
                return
                
            if data["type"] == "account":
                # Account update
                account_data = data.get("data", {})
                
                # Create account update event
                account_event = {
                    "type": "account_update",
                    "timestamp": int(time.time() * 1000),
                    "data": account_data
                }
                
                # Notify callbacks
                for callback in self.callbacks["account_update"]:
                    await callback(account_event)
                    
            elif data["type"] == "position":
                # Position update
                position_data = data.get("data", {})
                
                # Create position update event
                position_event = {
                    "type": "position_update",
                    "timestamp": int(time.time() * 1000),
                    "data": position_data
                }
                
                # Notify callbacks
                for callback in self.callbacks["position_update"]:
                    await callback(position_event)
                    
            elif data["type"] == "order":
                # Order update
                order_data = data.get("data", {})
                
                # Create order update event
                order_event = {
                    "type": "order_update",
                    "timestamp": int(time.time() * 1000),
                    "data": order_data
                }
                
                # Notify callbacks
                for callback in self.callbacks["order_update"]:
                    await callback(order_event)
                    
            else:
                log_event(
                    self.logger,
                    "HYPERLIQUID_UNKNOWN_MESSAGE",
                    f"Unknown message type: {data['type']}",
                    level="WARNING",
                    context={"message": data}
                )
        except Exception as e:
            log_event(
                self.logger,
                "HYPERLIQUID_MESSAGE_PROCESSING_ERROR",
                f"Error processing WebSocket message: {str(e)}",
                level="ERROR",
                context={"message": data}
            )
    
    async def start_market_socket(self, symbol: str) -> None:
        """
        Start a WebSocket connection for market data.
        
        Args:
            symbol: The trading pair symbol.
        """
        if symbol in self.market_ws and self.market_ws[symbol] is not None:
            return
            
        try:
            ws = await websockets.connect(self.WS_URL)
            
            # Subscribe to market data
            subscription_message = {
                "type": "subscribe",
                "channel": "market",
                "asset": symbol
            }
            
            await ws.send(json.dumps(subscription_message))
            
            # Store the WebSocket connection
            self.market_ws[symbol] = ws
            
            # Start listener task
            asyncio.create_task(self._market_socket_listener(symbol))
            
            log_event(
                self.logger,
                "HYPERLIQUID_MARKET_SOCKET_STARTED",
                f"Started market data WebSocket for {symbol}"
            )
        except Exception as e:
            log_event(
                self.logger,
                "HYPERLIQUID_MARKET_SOCKET_ERROR",
                f"Error starting market WebSocket for {symbol}: {str(e)}",
                level="ERROR",
                context={"symbol": symbol}
            )
            raise
    
    async def _market_socket_listener(self, symbol: str) -> None:
        """
        Listener for market socket messages.
        
        Args:
            symbol: The trading pair symbol.
        """
        try:
            ws = self.market_ws[symbol]
            
            while True:
                if ws is None:
                    break
                    
                message = await ws.recv()
                data = json.loads(message)
                
                await self._process_market_socket_message(symbol, data)
        except websockets.exceptions.ConnectionClosed:
            log_event(
                self.logger,
                "HYPERLIQUID_MARKET_SOCKET_CLOSED",
                f"Market WebSocket connection closed for {symbol}",
                level="WARNING",
                context={"symbol": symbol}
            )
        except Exception as e:
            log_event(
                self.logger,
                "HYPERLIQUID_MARKET_SOCKET_ERROR",
                f"Error in market WebSocket listener for {symbol}: {str(e)}",
                level="ERROR",
                context={"symbol": symbol}
            )
        finally:
            self.market_ws[symbol] = None
            # Try to reconnect after a delay
            await asyncio.sleep(5)
            asyncio.create_task(self.start_market_socket(symbol))
    
    async def _process_market_socket_message(self, symbol: str, data: Dict[str, Any]) -> None:
        """
        Process a message from the market socket.
        
        Args:
            symbol: The trading pair symbol.
            data: The WebSocket message.
        """
        try:
            if "type" not in data:
                return
                
            if data["type"] == "ticker":
                # Ticker update
                ticker_data = data.get("data", {})
                
                # Create ticker update event
                ticker_event = {
                    "type": "ticker",
                    "symbol": symbol,
                    "timestamp": int(time.time() * 1000),
                    "data": ticker_data
                }
                
                # Notify callbacks
                if symbol in self.callbacks["market_update"]:
                    for callback in self.callbacks["market_update"][symbol]:
                        await callback(ticker_event)
                        
            elif data["type"] == "orderbook":
                # Orderbook update
                orderbook_data = data.get("data", {})
                
                # Create orderbook update event
                orderbook_event = {
                    "type": "orderbook",
                    "symbol": symbol,
                    "timestamp": int(time.time() * 1000),
                    "data": orderbook_data
                }
                
                # Notify callbacks
                if symbol in self.callbacks["book_update"]:
                    for callback in self.callbacks["book_update"][symbol]:
                        await callback(orderbook_event)
                        
            else:
                log_event(
                    self.logger,
                    "HYPERLIQUID_UNKNOWN_MARKET_MESSAGE",
                    f"Unknown market message type: {data['type']}",
                    level="WARNING",
                    context={"symbol": symbol, "message": data}
                )
        except Exception as e:
            log_event(
                self.logger,
                "HYPERLIQUID_MARKET_MESSAGE_PROCESSING_ERROR",
                f"Error processing market WebSocket message: {str(e)}",
                level="ERROR",
                context={"symbol": symbol, "message": data}
            )
    
    def add_account_update_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Add a callback for account updates.
        
        Args:
            callback: The callback function.
        """
        self.callbacks["account_update"].append(callback)
    
    def add_position_update_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Add a callback for position updates.
        
        Args:
            callback: The callback function.
        """
        self.callbacks["position_update"].append(callback)
    
    def add_order_update_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Add a callback for order updates.
        
        Args:
            callback: The callback function.
        """
        self.callbacks["order_update"].append(callback)
    
    def add_market_update_callback(self, symbol: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Add a callback for market updates.
        
        Args:
            symbol: The trading pair symbol.
            callback: The callback function.
        """
        if symbol not in self.callbacks["market_update"]:
            self.callbacks["market_update"][symbol] = []
            
        self.callbacks["market_update"][symbol].append(callback)
    
    def add_book_update_callback(self, symbol: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Add a callback for orderbook updates.
        
        Args:
            symbol: The trading pair symbol.
            callback: The callback function.
        """
        if symbol not in self.callbacks["book_update"]:
            self.callbacks["book_update"][symbol] = []
            
        self.callbacks["book_update"][symbol].append(callback)
    
    def _generate_auth_token(self) -> str:
        """
        Generate an authentication token for WebSocket connections.
        
        Returns:
            The authentication token.
        """
        timestamp = str(int(time.time() * 1000))
        message = f"{timestamp}{self.api_key}"
        
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        token = base64.b64encode(f"{self.api_key}:{timestamp}:{signature}".encode('utf-8')).decode('utf-8')
        
        return token 

    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """
        Set the leverage for a symbol.
        
        Args:
            symbol: The trading pair symbol.
            leverage: The leverage value.
            
        Returns:
            Dict containing leverage information.
        """
        try:
            # Hyperliquid leverage is set per position when creating the order
            # This is just a stub to maintain interface compatibility
            
            return {
                "status": "success",
                "symbol": symbol,
                "leverage": leverage,
                "message": "Leverage will be applied when opening the position"
            }
        except Exception as e:
            log_event(
                self.logger,
                "HYPERLIQUID_API_ERROR",
                f"Error setting leverage for {symbol}: {str(e)}",
                level="ERROR",
                context={"symbol": symbol, "leverage": leverage}
            )
            raise
    
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
        try:
            # Create the entry order with leverage
            entry_order = await self.create_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                leverage=leverage
            )
            
            # Get the position after order execution
            position = await self.get_position(symbol)
            
            # Create stop loss order if requested
            sl_order = None
            if stop_loss:
                sl_side = "sell" if side.lower() == "buy" else "buy"
                sl_order = await self.create_order(
                    symbol=symbol,
                    side=sl_side,
                    order_type="STOP",
                    quantity=quantity,
                    price=stop_loss,
                    reduce_only=True
                )
            
            # Create take profit order if requested
            tp_order = None
            if take_profit:
                tp_side = "sell" if side.lower() == "buy" else "buy"
                tp_order = await self.create_order(
                    symbol=symbol,
                    side=tp_side,
                    order_type="LIMIT",
                    quantity=quantity,
                    price=take_profit,
                    reduce_only=True
                )
            
            sl_tp_orders = {
                "stop_loss": sl_order,
                "take_profit": tp_order
            }
            
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
        try:
            # Get current position
            position = await self.get_position(symbol)
            
            if not position or float(position["size"]) == 0:
                return {
                    "status": "error",
                    "message": f"No open position for {symbol}"
                }
            
            # Determine side and quantity
            position_size = float(position["size"])
            side = "sell" if position_size > 0 else "buy"
            quantity = abs(position_size)
            
            # Create the close order
            close_order = await self.create_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=Decimal(str(quantity)),
                price=price,
                reduce_only=True
            )
            
            # Cancel all related orders (SL/TP)
            await self.cancel_all_orders(symbol)
            
            result = {
                "status": "success",
                "close_order": close_order
            }
            
            log_event(
                self.logger,
                "POSITION_CLOSED",
                f"Closed position for {symbol}",
                context={
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "order_type": order_type,
                    "price": float(price) if price else None
                }
            )
            
            return result
        except Exception as e:
            log_event(
                self.logger,
                "POSITION_CLOSE_ERROR",
                f"Error closing position for {symbol}: {str(e)}",
                level="ERROR",
                context={
                    "symbol": symbol,
                    "order_type": order_type,
                    "price": float(price) if price else None
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
        Update stop loss and take profit for an existing position.
        
        Args:
            symbol: The trading pair symbol.
            stop_loss: New stop loss price.
            take_profit: New take profit price.
            
        Returns:
            Dict containing order information.
        """
        try:
            # Get current position
            position = await self.get_position(symbol)
            
            if not position or float(position["size"]) == 0:
                return {
                    "status": "error",
                    "message": f"No open position for {symbol}"
                }
            
            # Determine position side and quantity
            position_size = float(position["size"])
            position_side = "buy" if position_size > 0 else "sell"
            quantity = abs(position_size)
            
            # Cancel existing SL/TP orders
            await self.cancel_all_orders(symbol)
            
            sl_order = None
            tp_order = None
            
            # Create new stop loss order if requested
            if stop_loss:
                sl_side = "sell" if position_side == "buy" else "buy"
                sl_order = await self.create_order(
                    symbol=symbol,
                    side=sl_side,
                    order_type="STOP",
                    quantity=Decimal(str(quantity)),
                    price=stop_loss,
                    reduce_only=True
                )
            
            # Create new take profit order if requested
            if take_profit:
                tp_side = "sell" if position_side == "buy" else "buy"
                tp_order = await self.create_order(
                    symbol=symbol,
                    side=tp_side,
                    order_type="LIMIT",
                    quantity=Decimal(str(quantity)),
                    price=take_profit,
                    reduce_only=True
                )
            
            result = {
                "status": "success",
                "stop_loss_order": sl_order,
                "take_profit_order": tp_order
            }
            
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
            
            return result
        except Exception as e:
            log_event(
                self.logger,
                "POSITION_SL_TP_UPDATE_ERROR",
                f"Error updating SL/TP for {symbol}: {str(e)}",
                level="ERROR",
                context={
                    "symbol": symbol,
                    "stop_loss": float(stop_loss) if stop_loss else None,
                    "take_profit": float(take_profit) if take_profit else None
                }
            )
            raise 