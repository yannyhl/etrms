#!/usr/bin/env python
"""
Script to download historical data for backtesting.

This script downloads historical price data from supported exchanges and
saves it in a format that can be used by the backtesting engine.

Usage:
    python download_historical_data.py --exchange binance --symbols BTCUSDT,ETHUSDT --timeframes 1h,4h,1d --start 2022-01-01 --end 2023-01-01
"""

import argparse
import asyncio
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

from binance import AsyncClient

# Add the project root to the Python path
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from etrms.backend.exchange.binance.binance_futures_client import BinanceFuturesClient
from etrms.backend.exchange.hyperliquid.hyperliquid_client import HyperliquidClient
from etrms.backend.utils.logger import get_logger, log_event


logger = get_logger(__name__)

# Define the data directory
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/historical"))


async def download_binance_data(
    symbols: List[str],
    timeframes: List[str],
    start_date: str,
    end_date: str,
    api_key: str = None,
    api_secret: str = None,
    testnet: bool = True
) -> None:
    """
    Download historical data from Binance.
    
    Args:
        symbols: List of symbols to download data for
        timeframes: List of timeframes to download data for
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        api_key: Binance API key (optional)
        api_secret: Binance API secret (optional)
        testnet: Whether to use the testnet
    """
    # Create the Binance client
    client = await AsyncClient.create(api_key, api_secret, testnet=testnet)
    
    # Parse dates
    start = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp() * 1000)
    end = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp() * 1000)
    
    # Create the data directory if it doesn't exist
    os.makedirs(os.path.join(DATA_DIR, "binance"), exist_ok=True)
    
    # Download data for each symbol and timeframe
    for symbol in symbols:
        for timeframe in timeframes:
            logger.info(f"Downloading {symbol} {timeframe} data from Binance")
            
            # Create the directory for this symbol
            symbol_dir = os.path.join(DATA_DIR, "binance", symbol)
            os.makedirs(symbol_dir, exist_ok=True)
            
            # Download the data
            klines = []
            current_start = start
            
            while current_start < end:
                # Calculate the end time for this batch (max 1000 candles)
                batch_end = min(end, current_start + (1000 * get_timeframe_ms(timeframe)))
                
                # Get the klines
                batch = await client.futures_klines(
                    symbol=symbol,
                    interval=timeframe,
                    startTime=current_start,
                    endTime=batch_end,
                    limit=1000
                )
                
                if not batch:
                    break
                
                # Format the klines
                for k in batch:
                    klines.append({
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
                
                # Update the start time for the next batch
                if batch:
                    current_start = batch[-1][0] + 1
                else:
                    break
                
                # Sleep to avoid rate limits
                await asyncio.sleep(0.5)
            
            # Save the data
            filename = os.path.join(symbol_dir, f"{timeframe}.json")
            with open(filename, "w") as f:
                json.dump(klines, f, indent=2)
            
            logger.info(f"Downloaded {len(klines)} candles for {symbol} {timeframe}")
    
    # Close the client
    await client.close_connection()


async def download_hyperliquid_data(
    symbols: List[str],
    timeframes: List[str],
    start_date: str,
    end_date: str
) -> None:
    """
    Download historical data from Hyperliquid.
    
    Args:
        symbols: List of symbols to download data for
        timeframes: List of timeframes to download data for
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    # Create the Hyperliquid client
    client = HyperliquidClient()
    await client.initialize()
    
    # Parse dates
    start = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    end = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
    
    # Create the data directory if it doesn't exist
    os.makedirs(os.path.join(DATA_DIR, "hyperliquid"), exist_ok=True)
    
    # Download data for each symbol and timeframe
    for symbol in symbols:
        for timeframe in timeframes:
            logger.info(f"Downloading {symbol} {timeframe} data from Hyperliquid")
            
            # Create the directory for this symbol
            symbol_dir = os.path.join(DATA_DIR, "hyperliquid", symbol)
            os.makedirs(symbol_dir, exist_ok=True)
            
            # Download the data
            klines = []
            current_start = start
            
            while current_start < end:
                # Calculate the end time for this batch (max 1000 candles)
                batch_end = min(end, current_start + (1000 * get_timeframe_seconds(timeframe)))
                
                # Get the klines
                batch = await client.get_klines(
                    symbol=symbol,
                    interval=timeframe,
                    start_time=current_start * 1000,
                    end_time=batch_end * 1000,
                    limit=1000
                )
                
                if not batch:
                    break
                
                klines.extend(batch)
                
                # Update the start time for the next batch
                if batch:
                    current_start = int(batch[-1]["open_time"] / 1000) + 1
                else:
                    break
                
                # Sleep to avoid rate limits
                await asyncio.sleep(0.5)
            
            # Save the data
            filename = os.path.join(symbol_dir, f"{timeframe}.json")
            with open(filename, "w") as f:
                json.dump(klines, f, indent=2)
            
            logger.info(f"Downloaded {len(klines)} candles for {symbol} {timeframe}")
    
    # Close the client
    await client.close()


def get_timeframe_ms(timeframe: str) -> int:
    """
    Get the number of milliseconds in a timeframe.
    
    Args:
        timeframe: Timeframe string (e.g., '1m', '1h', '1d')
        
    Returns:
        Number of milliseconds in the timeframe
    """
    if timeframe.endswith('m'):
        return int(timeframe[:-1]) * 60 * 1000
    elif timeframe.endswith('h'):
        return int(timeframe[:-1]) * 60 * 60 * 1000
    elif timeframe.endswith('d'):
        return int(timeframe[:-1]) * 24 * 60 * 60 * 1000
    elif timeframe.endswith('w'):
        return int(timeframe[:-1]) * 7 * 24 * 60 * 60 * 1000
    else:
        raise ValueError(f"Invalid timeframe: {timeframe}")


def get_timeframe_seconds(timeframe: str) -> int:
    """
    Get the number of seconds in a timeframe.
    
    Args:
        timeframe: Timeframe string (e.g., '1m', '1h', '1d')
        
    Returns:
        Number of seconds in the timeframe
    """
    return get_timeframe_ms(timeframe) // 1000


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Download historical data for backtesting")
    parser.add_argument("--exchange", type=str, required=True, choices=["binance", "hyperliquid", "all"],
                        help="Exchange to download data from")
    parser.add_argument("--symbols", type=str, required=True,
                        help="Comma-separated list of symbols to download data for")
    parser.add_argument("--timeframes", type=str, required=True,
                        help="Comma-separated list of timeframes to download data for")
    parser.add_argument("--start", type=str, required=True,
                        help="Start date in YYYY-MM-DD format")
    parser.add_argument("--end", type=str, required=True,
                        help="End date in YYYY-MM-DD format")
    parser.add_argument("--api-key", type=str, help="API key (for Binance)")
    parser.add_argument("--api-secret", type=str, help="API secret (for Binance)")
    parser.add_argument("--testnet", action="store_true", help="Use testnet (for Binance)")
    
    args = parser.parse_args()
    
    # Parse arguments
    exchange = args.exchange
    symbols = args.symbols.split(",")
    timeframes = args.timeframes.split(",")
    start_date = args.start
    end_date = args.end
    api_key = args.api_key
    api_secret = args.api_secret
    testnet = args.testnet
    
    # Create the data directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Download data
    if exchange == "binance" or exchange == "all":
        await download_binance_data(
            symbols=symbols,
            timeframes=timeframes,
            start_date=start_date,
            end_date=end_date,
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet
        )
    
    if exchange == "hyperliquid" or exchange == "all":
        await download_hyperliquid_data(
            symbols=symbols,
            timeframes=timeframes,
            start_date=start_date,
            end_date=end_date
        )


if __name__ == "__main__":
    asyncio.run(main()) 