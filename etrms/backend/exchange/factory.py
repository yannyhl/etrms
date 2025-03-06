"""
Enhanced Trading Risk Management System Exchange Factory

This module provides a factory for creating exchange client instances.
"""
from typing import Dict, Optional, Type

from exchange.common import ExchangeInterface
from exchange.binance import BinanceFuturesClient
from exchange.hyperliquid import HyperliquidClient
from utils.logger import get_logger, log_event


class ExchangeClientFactory:
    """
    Factory class for creating exchange client instances.
    
    This factory provides a centralized way to create and manage
    exchange client instances.
    """
    
    # Map of exchange names to client classes
    _EXCHANGE_CLIENTS: Dict[str, Type[ExchangeInterface]] = {
        "binance": BinanceFuturesClient,
        "hyperliquid": HyperliquidClient
    }
    
    @classmethod
    def get_client(
        cls, 
        exchange_name: str, 
        api_key: Optional[str] = None, 
        api_secret: Optional[str] = None
    ) -> ExchangeInterface:
        """
        Get an exchange client instance.
        
        Args:
            exchange_name: The name of the exchange (e.g., 'binance', 'hyperliquid').
            api_key: Optional API key. If not provided, will use the one from settings.
            api_secret: Optional API secret. If not provided, will use the one from settings.
            
        Returns:
            An instance of the appropriate exchange client.
            
        Raises:
            ValueError: If the exchange is not supported.
        """
        logger = get_logger(__name__)
        
        # Convert to lowercase for case-insensitive comparison
        exchange_name = exchange_name.lower()
        
        if exchange_name not in cls._EXCHANGE_CLIENTS:
            log_event(
                logger,
                "EXCHANGE_FACTORY_ERROR",
                f"Unsupported exchange: {exchange_name}",
                level="ERROR",
                context={"supported_exchanges": list(cls._EXCHANGE_CLIENTS.keys())}
            )
            raise ValueError(
                f"Unsupported exchange: {exchange_name}. "
                f"Supported exchanges: {', '.join(cls._EXCHANGE_CLIENTS.keys())}"
            )
        
        # Create and return the client instance
        client_class = cls._EXCHANGE_CLIENTS[exchange_name]
        client = client_class(api_key=api_key, api_secret=api_secret)
        
        log_event(
            logger,
            "EXCHANGE_CLIENT_CREATED",
            f"Created {exchange_name} client",
            context={"exchange": exchange_name}
        )
        
        return client
    
    @classmethod
    def get_supported_exchanges(cls) -> list[str]:
        """
        Get a list of supported exchanges.
        
        Returns:
            A list of supported exchange names.
        """
        return list(cls._EXCHANGE_CLIENTS.keys()) 