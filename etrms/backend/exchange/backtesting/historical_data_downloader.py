"""
Enhanced Trading Risk Management System Historical Data Downloader

This module provides functionality to download historical data from exchanges
for use in backtesting.
"""
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

import aiohttp
from tqdm import tqdm

from exchange.binance.client import BinanceClient
from exchange.hyperliquid.client import HyperliquidClient
from utils.logger import get_logger, log_event


class HistoricalDataDownloader:
    """
    Downloads and prepares historical data for backtesting purposes.
    
    This class handles:
    - Downloading kline (candlestick) data from various exchanges
    - Downloading order book snapshots
    - Converting and saving data in a format suitable for backtesting
    - Managing timeframes and date ranges
    """
    
    def __init__(
        self,
        data_path: str = "data/historical",
        binance_api_key: Optional[str] = None,
        binance_api_secret: Optional[str] = None,
        hyperliquid_api_key: Optional[str] = None,
        hyperliquid_api_secret: Optional[str] = None,
    ):
        """
        Initialize the historical data downloader.
        
        Args:
            data_path: Path to save downloaded data
            binance_api_key: Binance API key (optional)
            binance_api_secret: Binance API secret (optional)
            hyperliquid_api_key: Hyperliquid API key (optional)
            hyperliquid_api_secret: Hyperliquid API secret (optional)
        """
        self.logger = get_logger(__name__)
        self.data_path = data_path
        
        # Ensure data directory exists
        os.makedirs(data_path, exist_ok=True)
        
        # API credentials
        self.binance_api_key = binance_api_key
        self.binance_api_secret = binance_api_secret
        self.hyperliquid_api_key = hyperliquid_api_key
        self.hyperliquid_api_secret = hyperliquid_api_secret
        
        # Exchange clients
        self.binance_client = None
        self.hyperliquid_client = None
        
        log_event(
            self.logger,
            "HISTORICAL_DATA_DOWNLOADER_INIT",
            "Initializing historical data downloader",
            context={"data_path": data_path}
        )
    
    async def initialize(self) -> None:
        """
        Initialize exchange clients.
        """
        # Initialize Binance client if credentials provided
        if self.binance_api_key and self.binance_api_secret:
            self.binance_client = BinanceClient(
                api_key=self.binance_api_key,
                api_secret=self.binance_api_secret
            )
            await self.binance_client.initialize()
            
            log_event(
                self.logger,
                "BINANCE_CLIENT_INITIALIZED",
                "Binance client initialized for historical data download"
            )
        
        # Initialize Hyperliquid client if credentials provided
        if self.hyperliquid_api_key and self.hyperliquid_api_secret:
            self.hyperliquid_client = HyperliquidClient(
                api_key=self.hyperliquid_api_key,
                api_secret=self.hyperliquid_api_secret
            )
            await self.hyperliquid_client.initialize()
            
            log_event(
                self.logger,
                "HYPERLIQUID_CLIENT_INITIALIZED",
                "Hyperliquid client initialized for historical data download"
            )
    
    async def close(self) -> None:
        """
        Close exchange clients.
        """
        if self.binance_client:
            await self.binance_client.close()
        
        if self.hyperliquid_client:
            await self.hyperliquid_client.close()
            
        log_event(
            self.logger,
            "HISTORICAL_DATA_DOWNLOADER_CLOSED",
            "Historical data downloader closed"
        )
    
    async def download_klines(
        self,
        exchange: str,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        progress_bar: bool = True
    ) -> bool:
        """
        Download kline (candlestick) data for a symbol.
        
        Args:
            exchange: Exchange name ('binance' or 'hyperliquid')
            symbol: Trading pair symbol
            timeframe: Timeframe of the data (e.g., '1m', '5m', '1h', '1d')
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            progress_bar: Whether to show a progress bar
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert dates to datetime objects
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            # Ensure data directory exists
            os.makedirs(f"{self.data_path}", exist_ok=True)
            
            # Select the appropriate client based on exchange
            if exchange.lower() == "binance":
                if not self.binance_client:
                    raise ValueError("Binance client not initialized")
                client = self.binance_client
                result = await self._download_binance_klines(client, symbol, timeframe, start_dt, end_dt, progress_bar)
            elif exchange.lower() == "hyperliquid":
                if not self.hyperliquid_client:
                    raise ValueError("Hyperliquid client not initialized")
                client = self.hyperliquid_client
                result = await self._download_hyperliquid_klines(client, symbol, timeframe, start_dt, end_dt, progress_bar)
            else:
                raise ValueError(f"Unsupported exchange: {exchange}")
                
            return result
        except Exception as e:
            log_event(
                self.logger,
                "KLINES_DOWNLOAD_ERROR",
                f"Error downloading klines: {str(e)}",
                level="ERROR",
                context={
                    "exchange": exchange,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "start_date": start_date,
                    "end_date": end_date,
                    "error": str(e)
                }
            )
            return False
    
    async def download_orderbook_snapshots(
        self,
        exchange: str,
        symbol: str,
        start_date: str,
        end_date: str,
        interval_minutes: int = 60,
        depth: int = 100,
        progress_bar: bool = True
    ) -> bool:
        """
        Download order book snapshots for a symbol.
        
        Args:
            exchange: Exchange name ('binance' or 'hyperliquid')
            symbol: Trading pair symbol
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            interval_minutes: Interval between snapshots in minutes
            depth: Depth of the order book
            progress_bar: Whether to show a progress bar
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert dates to datetime objects
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            # Ensure data directory exists
            os.makedirs(f"{self.data_path}", exist_ok=True)
            
            # Select the appropriate client based on exchange
            if exchange.lower() == "binance":
                if not self.binance_client:
                    raise ValueError("Binance client not initialized")
                client = self.binance_client
                result = await self._download_binance_orderbooks(
                    client, symbol, start_dt, end_dt, interval_minutes, depth, progress_bar
                )
            elif exchange.lower() == "hyperliquid":
                if not self.hyperliquid_client:
                    raise ValueError("Hyperliquid client not initialized")
                client = self.hyperliquid_client
                result = await self._download_hyperliquid_orderbooks(
                    client, symbol, start_dt, end_dt, interval_minutes, depth, progress_bar
                )
            else:
                raise ValueError(f"Unsupported exchange: {exchange}")
                
            return result
        except Exception as e:
            log_event(
                self.logger,
                "ORDERBOOK_DOWNLOAD_ERROR",
                f"Error downloading orderbooks: {str(e)}",
                level="ERROR",
                context={
                    "exchange": exchange,
                    "symbol": symbol,
                    "start_date": start_date,
                    "end_date": end_date,
                    "interval_minutes": interval_minutes,
                    "error": str(e)
                }
            )
            return False
    
    async def _download_binance_klines(
        self,
        client: BinanceClient,
        symbol: str,
        timeframe: str,
        start_dt: datetime,
        end_dt: datetime,
        progress_bar: bool = True
    ) -> bool:
        """
        Download kline data from Binance.
        
        Args:
            client: Binance client
            symbol: Trading pair symbol
            timeframe: Timeframe of the data
            start_dt: Start datetime
            end_dt: End datetime
            progress_bar: Whether to show a progress bar
            
        Returns:
            True if successful, False otherwise
        """
        # Map timeframe to milliseconds for chunking requests
        timeframe_ms = {
            "1m": 60 * 1000,
            "3m": 3 * 60 * 1000,
            "5m": 5 * 60 * 1000,
            "15m": 15 * 60 * 1000,
            "30m": 30 * 60 * 1000,
            "1h": 60 * 60 * 1000,
            "2h": 2 * 60 * 60 * 1000,
            "4h": 4 * 60 * 60 * 1000,
            "6h": 6 * 60 * 60 * 1000,
            "8h": 8 * 60 * 60 * 1000,
            "12h": 12 * 60 * 60 * 1000,
            "1d": 24 * 60 * 60 * 1000,
            "3d": 3 * 24 * 60 * 60 * 1000,
            "1w": 7 * 24 * 60 * 60 * 1000,
        }.get(timeframe, 60 * 60 * 1000)  # Default to 1h
        
        # Binance limit is 1000 candles per request
        # We need to calculate how many candles we can get in a single request
        # based on the timeframe
        chunk_size = 1000 * timeframe_ms
        
        # Convert datetime to milliseconds timestamp
        start_ms = int(start_dt.timestamp() * 1000)
        end_ms = int(end_dt.timestamp() * 1000)
        
        # Calculate total chunks
        total_duration = end_ms - start_ms
        chunks = (total_duration // chunk_size) + 1
        
        all_klines = []
        
        # Create progress bar if requested
        pbar = tqdm(total=chunks, desc=f"Downloading {symbol} {timeframe} from Binance") if progress_bar else None
        
        # Download data in chunks
        for i in range(chunks):
            chunk_start = start_ms + (i * chunk_size)
            chunk_end = min(chunk_start + chunk_size, end_ms)
            
            try:
                klines = await client.get_klines(
                    symbol=symbol,
                    interval=timeframe,
                    start_time=chunk_start,
                    end_time=chunk_end,
                    limit=1000
                )
                
                # Process and append data
                for k in klines:
                    kline_data = [
                        k["open_time"],
                        k["open"],
                        k["high"],
                        k["low"],
                        k["close"],
                        k["volume"],
                        k["close_time"],
                        k["quote_volume"],
                        k["trades"],
                        k["taker_buy_base_volume"],
                        k["taker_buy_quote_volume"]
                    ]
                    all_klines.append(kline_data)
                
                # Update progress bar
                if pbar:
                    pbar.update(1)
                
                # Respect API rate limits
                await asyncio.sleep(0.1)
            except Exception as e:
                log_event(
                    self.logger,
                    "BINANCE_KLINES_CHUNK_ERROR",
                    f"Error downloading kline chunk: {str(e)}",
                    level="ERROR",
                    context={
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "chunk_start": chunk_start,
                        "chunk_end": chunk_end,
                        "error": str(e)
                    }
                )
                # Continue with the next chunk
                if pbar:
                    pbar.update(1)
                continue
        
        # Close progress bar
        if pbar:
            pbar.close()
        
        # Check if we got any data
        if not all_klines:
            log_event(
                self.logger,
                "BINANCE_KLINES_NO_DATA",
                f"No kline data returned for {symbol} ({timeframe})",
                level="WARNING",
                context={"symbol": symbol, "timeframe": timeframe}
            )
            return False
        
        # Sort by timestamp to ensure order
        all_klines.sort(key=lambda x: x[0])
        
        # Write to file
        filename = f"{self.data_path}/{symbol}_{timeframe}.json"
        with open(filename, "w") as f:
            json.dump(all_klines, f)
        
        log_event(
            self.logger,
            "BINANCE_KLINES_DOWNLOADED",
            f"Downloaded {len(all_klines)} klines for {symbol} ({timeframe})",
            context={
                "symbol": symbol,
                "timeframe": timeframe,
                "kline_count": len(all_klines),
                "filename": filename
            }
        )
        
        return True
    
    async def _download_hyperliquid_klines(
        self,
        client: HyperliquidClient,
        symbol: str,
        timeframe: str,
        start_dt: datetime,
        end_dt: datetime,
        progress_bar: bool = True
    ) -> bool:
        """
        Download kline data from Hyperliquid.
        
        Args:
            client: Hyperliquid client
            symbol: Trading pair symbol
            timeframe: Timeframe of the data
            start_dt: Start datetime
            end_dt: End datetime
            progress_bar: Whether to show a progress bar
            
        Returns:
            True if successful, False otherwise
        """
        # Similar implementation as Binance but adjusted for Hyperliquid API
        # Map timeframe to minutes for chunking requests
        timeframe_min = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "4h": 240,
            "1d": 1440,
        }.get(timeframe, 60)  # Default to 1h
        
        # Hyperliquid typically has different limits, let's say 300 candles per request
        max_candles_per_request = 300
        
        # Calculate chunk size in minutes
        chunk_size_min = timeframe_min * max_candles_per_request
        chunk_size_ms = chunk_size_min * 60 * 1000
        
        # Convert datetime to milliseconds timestamp
        start_ms = int(start_dt.timestamp() * 1000)
        end_ms = int(end_dt.timestamp() * 1000)
        
        # Calculate total chunks
        total_duration = end_ms - start_ms
        chunks = (total_duration // chunk_size_ms) + 1
        
        all_klines = []
        
        # Create progress bar if requested
        pbar = tqdm(total=chunks, desc=f"Downloading {symbol} {timeframe} from Hyperliquid") if progress_bar else None
        
        # Download data in chunks
        for i in range(chunks):
            chunk_start = start_ms + (i * chunk_size_ms)
            chunk_end = min(chunk_start + chunk_size_ms, end_ms)
            
            try:
                klines = await client.get_klines(
                    symbol=symbol,
                    interval=timeframe,
                    start_time=chunk_start,
                    end_time=chunk_end,
                    limit=max_candles_per_request
                )
                
                # Process and append data - format to match Binance for consistency
                for k in klines:
                    # Convert Hyperliquid specific data format to our standard format
                    kline_data = [
                        k["open_time"],
                        k["open"],
                        k["high"],
                        k["low"],
                        k["close"],
                        k["volume"],
                        k["close_time"],
                        k.get("quote_volume", 0),  # May not be available in Hyperliquid
                        k.get("trades", 0),  # May not be available in Hyperliquid
                        k.get("taker_buy_base_volume", 0),  # May not be available in Hyperliquid
                        k.get("taker_buy_quote_volume", 0)  # May not be available in Hyperliquid
                    ]
                    all_klines.append(kline_data)
                
                # Update progress bar
                if pbar:
                    pbar.update(1)
                
                # Respect API rate limits
                await asyncio.sleep(0.2)  # Hyperliquid might have different rate limits
            except Exception as e:
                log_event(
                    self.logger,
                    "HYPERLIQUID_KLINES_CHUNK_ERROR",
                    f"Error downloading kline chunk: {str(e)}",
                    level="ERROR",
                    context={
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "chunk_start": chunk_start,
                        "chunk_end": chunk_end,
                        "error": str(e)
                    }
                )
                # Continue with the next chunk
                if pbar:
                    pbar.update(1)
                continue
        
        # Close progress bar
        if pbar:
            pbar.close()
        
        # Check if we got any data
        if not all_klines:
            log_event(
                self.logger,
                "HYPERLIQUID_KLINES_NO_DATA",
                f"No kline data returned for {symbol} ({timeframe})",
                level="WARNING",
                context={"symbol": symbol, "timeframe": timeframe}
            )
            return False
        
        # Sort by timestamp to ensure order
        all_klines.sort(key=lambda x: x[0])
        
        # Write to file
        filename = f"{self.data_path}/{symbol}_{timeframe}.json"
        with open(filename, "w") as f:
            json.dump(all_klines, f)
        
        log_event(
            self.logger,
            "HYPERLIQUID_KLINES_DOWNLOADED",
            f"Downloaded {len(all_klines)} klines for {symbol} ({timeframe})",
            context={
                "symbol": symbol,
                "timeframe": timeframe,
                "kline_count": len(all_klines),
                "filename": filename
            }
        )
        
        return True
    
    async def _download_binance_orderbooks(
        self,
        client: BinanceClient,
        symbol: str,
        start_dt: datetime,
        end_dt: datetime,
        interval_minutes: int = 60,
        depth: int = 100,
        progress_bar: bool = True
    ) -> bool:
        """
        Download order book snapshots from Binance.
        
        In a real implementation, historical order book data would likely
        be downloaded from a premium data provider, as exchanges typically
        don't provide historical order book data via their APIs. Here, we're
        simulating the process.
        
        Args:
            client: Binance client
            symbol: Trading pair symbol
            start_dt: Start datetime
            end_dt: End datetime
            interval_minutes: Interval between snapshots in minutes
            depth: Depth of the order book
            progress_bar: Whether to show a progress bar
            
        Returns:
            True if successful, False otherwise
        """
        # For the purposes of this implementation, we'll create synthetic orderbook data
        # In a real implementation, you would need to source this data from a professional data provider
        current_dt = start_dt
        interval = timedelta(minutes=interval_minutes)
        
        orderbook_snapshots = []
        total_steps = int((end_dt - start_dt).total_seconds() / interval.total_seconds()) + 1
        
        # Create progress bar if requested
        pbar = tqdm(total=total_steps, desc=f"Generating synthetic orderbook data for {symbol}") if progress_bar else None
        
        while current_dt <= end_dt:
            try:
                # Get current orderbook as a sample
                # In a real implementation, this would come from historical data
                orderbook = await client.get_orderbook(symbol=symbol, depth=depth)
                
                # Add timestamp
                timestamp_ms = int(current_dt.timestamp() * 1000)
                orderbook_snapshot = {
                    "timestamp": timestamp_ms,
                    "bids": orderbook["bids"],
                    "asks": orderbook["asks"]
                }
                
                orderbook_snapshots.append(orderbook_snapshot)
                
                # Move to next interval
                current_dt += interval
                
                # Update progress bar
                if pbar:
                    pbar.update(1)
                
                # Respect API rate limits
                await asyncio.sleep(0.5)
            except Exception as e:
                log_event(
                    self.logger,
                    "BINANCE_ORDERBOOK_ERROR",
                    f"Error generating orderbook snapshot: {str(e)}",
                    level="ERROR",
                    context={
                        "symbol": symbol,
                        "timestamp": current_dt.isoformat(),
                        "error": str(e)
                    }
                )
                # Move to next interval
                current_dt += interval
                
                # Update progress bar
                if pbar:
                    pbar.update(1)
                continue
        
        # Close progress bar
        if pbar:
            pbar.close()
        
        # Check if we got any data
        if not orderbook_snapshots:
            log_event(
                self.logger,
                "BINANCE_ORDERBOOK_NO_DATA",
                f"No orderbook snapshots generated for {symbol}",
                level="WARNING",
                context={"symbol": symbol}
            )
            return False
        
        # Write to file
        filename = f"{self.data_path}/{symbol}_orderbook.json"
        with open(filename, "w") as f:
            json.dump(orderbook_snapshots, f)
        
        log_event(
            self.logger,
            "BINANCE_ORDERBOOK_GENERATED",
            f"Generated {len(orderbook_snapshots)} orderbook snapshots for {symbol}",
            context={
                "symbol": symbol,
                "snapshot_count": len(orderbook_snapshots),
                "filename": filename
            }
        )
        
        return True
    
    async def _download_hyperliquid_orderbooks(
        self,
        client: HyperliquidClient,
        symbol: str,
        start_dt: datetime,
        end_dt: datetime,
        interval_minutes: int = 60,
        depth: int = 100,
        progress_bar: bool = True
    ) -> bool:
        """
        Download order book snapshots from Hyperliquid.
        
        Similar to Binance, this is a simulation as historical orderbook
        data is typically not available via exchange APIs.
        
        Args:
            client: Hyperliquid client
            symbol: Trading pair symbol
            start_dt: Start datetime
            end_dt: End datetime
            interval_minutes: Interval between snapshots in minutes
            depth: Depth of the order book
            progress_bar: Whether to show a progress bar
            
        Returns:
            True if successful, False otherwise
        """
        # Similar implementation as Binance but adjusted for Hyperliquid specifics
        current_dt = start_dt
        interval = timedelta(minutes=interval_minutes)
        
        orderbook_snapshots = []
        total_steps = int((end_dt - start_dt).total_seconds() / interval.total_seconds()) + 1
        
        # Create progress bar if requested
        pbar = tqdm(total=total_steps, desc=f"Generating synthetic orderbook data for {symbol}") if progress_bar else None
        
        while current_dt <= end_dt:
            try:
                # Get current orderbook as a sample
                orderbook = await client.get_orderbook(symbol=symbol, depth=depth)
                
                # Add timestamp
                timestamp_ms = int(current_dt.timestamp() * 1000)
                orderbook_snapshot = {
                    "timestamp": timestamp_ms,
                    "bids": orderbook["bids"],
                    "asks": orderbook["asks"]
                }
                
                orderbook_snapshots.append(orderbook_snapshot)
                
                # Move to next interval
                current_dt += interval
                
                # Update progress bar
                if pbar:
                    pbar.update(1)
                
                # Respect API rate limits
                await asyncio.sleep(0.5)
            except Exception as e:
                log_event(
                    self.logger,
                    "HYPERLIQUID_ORDERBOOK_ERROR",
                    f"Error generating orderbook snapshot: {str(e)}",
                    level="ERROR",
                    context={
                        "symbol": symbol,
                        "timestamp": current_dt.isoformat(),
                        "error": str(e)
                    }
                )
                # Move to next interval
                current_dt += interval
                
                # Update progress bar
                if pbar:
                    pbar.update(1)
                continue
        
        # Close progress bar
        if pbar:
            pbar.close()
        
        # Check if we got any data
        if not orderbook_snapshots:
            log_event(
                self.logger,
                "HYPERLIQUID_ORDERBOOK_NO_DATA",
                f"No orderbook snapshots generated for {symbol}",
                level="WARNING",
                context={"symbol": symbol}
            )
            return False
        
        # Write to file
        filename = f"{self.data_path}/{symbol}_orderbook.json"
        with open(filename, "w") as f:
            json.dump(orderbook_snapshots, f)
        
        log_event(
            self.logger,
            "HYPERLIQUID_ORDERBOOK_GENERATED",
            f"Generated {len(orderbook_snapshots)} orderbook snapshots for {symbol}",
            context={
                "symbol": symbol,
                "snapshot_count": len(orderbook_snapshots),
                "filename": filename
            }
        )
        
        return True
    
    @staticmethod
    def get_available_timeframes() -> Dict[str, str]:
        """
        Get available timeframes and their descriptions.
        
        Returns:
            Dict mapping timeframe codes to descriptions
        """
        return {
            "1m": "1 minute",
            "3m": "3 minutes",
            "5m": "5 minutes",
            "15m": "15 minutes",
            "30m": "30 minutes",
            "1h": "1 hour",
            "2h": "2 hours",
            "4h": "4 hours",
            "6h": "6 hours",
            "8h": "8 hours",
            "12h": "12 hours",
            "1d": "1 day",
            "3d": "3 days",
            "1w": "1 week"
        }


async def download_historical_data(
    exchange: str,
    symbols: List[str],
    timeframes: List[str],
    start_date: str,
    end_date: str,
    data_path: str = "data/historical",
    download_orderbooks: bool = False,
    orderbook_interval_minutes: int = 60,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None
) -> bool:
    """
    Helper function to download historical data for multiple symbols and timeframes.
    
    Args:
        exchange: Exchange name ('binance' or 'hyperliquid')
        symbols: List of trading pair symbols
        timeframes: List of timeframes (e.g., ['1h', '4h', '1d'])
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        data_path: Path to save downloaded data
        download_orderbooks: Whether to download orderbook snapshots
        orderbook_interval_minutes: Interval between orderbook snapshots
        api_key: API key for the exchange
        api_secret: API secret for the exchange
        
    Returns:
        True if all downloads were successful, False otherwise
    """
    # Create downloader
    downloader = HistoricalDataDownloader(
        data_path=data_path,
        binance_api_key=api_key if exchange.lower() == "binance" else None,
        binance_api_secret=api_secret if exchange.lower() == "binance" else None,
        hyperliquid_api_key=api_key if exchange.lower() == "hyperliquid" else None,
        hyperliquid_api_secret=api_secret if exchange.lower() == "hyperliquid" else None,
    )
    
    try:
        # Initialize downloader
        await downloader.initialize()
        
        all_successful = True
        
        # Download klines for each symbol and timeframe
        for symbol in symbols:
            for timeframe in timeframes:
                success = await downloader.download_klines(
                    exchange=exchange,
                    symbol=symbol,
                    timeframe=timeframe,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if not success:
                    all_successful = False
            
            # Download orderbook snapshots if requested
            if download_orderbooks:
                success = await downloader.download_orderbook_snapshots(
                    exchange=exchange,
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    interval_minutes=orderbook_interval_minutes
                )
                
                if not success:
                    all_successful = False
        
        return all_successful
    except Exception as e:
        logger = get_logger("download_historical_data")
        log_event(
            logger,
            "HISTORICAL_DATA_DOWNLOAD_ERROR",
            f"Error downloading historical data: {str(e)}",
            level="ERROR",
            context={
                "exchange": exchange,
                "symbols": symbols,
                "timeframes": timeframes,
                "start_date": start_date,
                "end_date": end_date,
                "error": str(e)
            }
        )
        return False
    finally:
        # Close downloader
        await downloader.close()


if __name__ == "__main__":
    # Example usage
    import argparse
    import sys
    
    async def main():
        parser = argparse.ArgumentParser(description='Download historical data for backtesting')
        parser.add_argument('--exchange', type=str, required=True, choices=['binance', 'hyperliquid'],
                           help='Exchange to download data from')
        parser.add_argument('--symbols', type=str, required=True, nargs='+',
                           help='List of symbols (e.g., BTCUSDT ETHUSDT)')
        parser.add_argument('--timeframes', type=str, required=True, nargs='+',
                           help='List of timeframes (e.g., 1h 4h 1d)')
        parser.add_argument('--start_date', type=str, required=True, 
                           help='Start date in YYYY-MM-DD format')
        parser.add_argument('--end_date', type=str, required=True,
                           help='End date in YYYY-MM-DD format')
        parser.add_argument('--data_path', type=str, default='data/historical',
                           help='Path to save downloaded data')
        parser.add_argument('--download_orderbooks', action='store_true',
                           help='Whether to download orderbook snapshots')
        parser.add_argument('--orderbook_interval', type=int, default=60,
                           help='Interval between orderbook snapshots in minutes')
        parser.add_argument('--api_key', type=str, help='API key for the exchange')
        parser.add_argument('--api_secret', type=str, help='API secret for the exchange')
        
        args = parser.parse_args()
        
        success = await download_historical_data(
            exchange=args.exchange,
            symbols=args.symbols,
            timeframes=args.timeframes,
            start_date=args.start_date,
            end_date=args.end_date,
            data_path=args.data_path,
            download_orderbooks=args.download_orderbooks,
            orderbook_interval_minutes=args.orderbook_interval,
            api_key=args.api_key,
            api_secret=args.api_secret
        )
        
        if success:
            print("Historical data download completed successfully.")
            return 0
        else:
            print("Some errors occurred during historical data download. Check logs for details.")
            return 1
    
    if sys.version_info[0] == 3 and sys.version_info[1] >= 7:
        asyncio.run(main())
    else:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(main())
        sys.exit(result) 