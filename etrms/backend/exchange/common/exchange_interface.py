"""
Enhanced Trading Risk Management System Exchange Interface
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, List, Optional, Any


class ExchangeInterface(ABC):
    """
    Abstract base class defining the common interface for all exchange implementations.
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the exchange client and establish connections.
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """
        Close connections and clean up resources.
        """
        pass
    
    @abstractmethod
    async def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information including balance, positions, etc.
        
        Returns:
            Dict containing account information.
        """
        pass
    
    @abstractmethod
    async def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific position.
        
        Args:
            symbol: The trading pair symbol.
            
        Returns:
            Dict containing position information or None if no position exists.
        """
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get all open positions.
        
        Returns:
            List of dicts containing position information.
        """
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str, symbol: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific order.
        
        Args:
            order_id: The ID of the order.
            symbol: The trading pair symbol (optional for some exchanges).
            
        Returns:
            Dict containing order information or None if the order doesn't exist.
        """
        pass
    
    @abstractmethod
    async def get_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all open orders, optionally filtered by symbol.
        
        Args:
            symbol: The trading pair symbol (optional).
            
        Returns:
            List of dicts containing order information.
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel an existing order.
        
        Args:
            order_id: The ID of the order.
            symbol: The trading pair symbol (required for some exchanges).
            
        Returns:
            Dict containing order information.
        """
        pass
    
    @abstractmethod
    async def cancel_all_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Cancel all open orders, optionally filtered by symbol.
        
        Args:
            symbol: The trading pair symbol (optional).
            
        Returns:
            List of dicts containing order information.
        """
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get the current ticker for a symbol.
        
        Args:
            symbol: The trading pair symbol.
            
        Returns:
            Dict containing ticker information.
        """
        pass
    
    @abstractmethod
    async def get_orderbook(self, symbol: str, depth: int = 10) -> Dict[str, Any]:
        """
        Get the order book for a symbol.
        
        Args:
            symbol: The trading pair symbol.
            depth: The depth of the order book to retrieve.
            
        Returns:
            Dict containing order book information.
        """
        pass
    
    @abstractmethod
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
        pass 