# Exchange Client Integration

This document outlines the exchange client integration in the Enhanced Trading Risk Management System (ETRMS), including the implementation details for Binance Futures and Hyperliquid exchanges.

## Overview

The ETRMS integrates with multiple cryptocurrency exchanges through a common interface, allowing the risk management system to monitor and manage positions across different platforms in a uniform way. 

The exchange integration consists of:

1. A common abstract interface (`ExchangeInterface`)
2. Exchange-specific implementations (Binance Futures, Hyperliquid)
3. WebSocket integration for real-time data
4. Position and order management functionality

## Exchange Interface

All exchange clients implement the common `ExchangeInterface` abstract base class, which defines the required methods for interacting with exchanges. This ensures consistent behavior across different exchange implementations.

Key methods in the interface include:

- Account and position information retrieval
- Order creation and management
- Market data access
- WebSocket integration for real-time updates

## Binance Futures Client

The `BinanceFuturesClient` provides integration with the Binance Futures exchange.

### Features

- **REST API Integration**: Full implementation of the Binance Futures REST API
- **WebSocket Support**: Real-time data streaming for account, position, and market updates
- **Position Management**: High-level methods for opening, closing, and managing positions
- **Error Handling**: Robust error handling with retry logic for transient errors
- **Rate Limiting**: Compliance with Binance API rate limits

### Example Usage

```python
from exchange.binance.binance_futures_client import BinanceFuturesClient

# Initialize client
client = BinanceFuturesClient(api_key="YOUR_API_KEY", api_secret="YOUR_API_SECRET")
await client.initialize()

# Account information
account_info = await client.get_account_info()
print(f"Total equity: {account_info['total_equity']}")

# Open a position
position = await client.open_position(
    symbol="BTCUSDT",
    side="buy",
    quantity=Decimal("0.01"),
    leverage=5,
    stop_loss=Decimal("19000"),
    take_profit=Decimal("21000")
)

# Market data
ticker = await client.get_ticker(symbol="BTCUSDT")
orderbook = await client.get_orderbook(symbol="BTCUSDT", depth=10)

# Real-time data with callbacks
def position_update_callback(message):
    print(f"Position update: {message}")

client.add_position_update_callback(position_update_callback)
await client.start_user_socket()

# Close resources when done
await client.close()
```

## Hyperliquid Client

The `HyperliquidClient` provides integration with the Hyperliquid exchange.

### Features

- **REST API Integration**: Implementation of the Hyperliquid REST API
- **WebSocket Support**: Real-time data streaming for account, position, and market updates
- **Position Management**: High-level methods for opening, closing, and managing positions
- **Error Handling**: Robust error handling for API requests

### Example Usage

```python
from exchange.hyperliquid.hyperliquid_client import HyperliquidClient

# Initialize client
client = HyperliquidClient(api_key="YOUR_API_KEY", api_secret="YOUR_API_SECRET")
await client.initialize()

# Account information
account_info = await client.get_account_info()
print(f"Total equity: {account_info['total_equity']}")

# Open a position
position = await client.open_position(
    symbol="BTC-PERP",
    side="buy",
    quantity=Decimal("0.01"),
    leverage=5,
    stop_loss=Decimal("19000"),
    take_profit=Decimal("21000")
)

# Market data
ticker = await client.get_ticker(symbol="BTC-PERP")
orderbook = await client.get_orderbook(symbol="BTC-PERP", depth=10)

# Real-time data with callbacks
def position_update_callback(message):
    print(f"Position update: {message}")

client.add_position_update_callback(position_update_callback)
await client.start_user_socket()

# Close resources when done
await client.close()
```

## WebSocket Integration

Both exchange clients implement WebSocket support for real-time data, which is crucial for effective risk monitoring.

### Types of WebSocket Data

1. **User Data**:
   - Account updates (balance changes)
   - Position updates (entry, exit, liquidation)
   - Order updates (creation, execution, cancellation)

2. **Market Data**:
   - Ticker updates (price, volume)
   - Orderbook updates (bid/ask changes)

### Callback System

The WebSocket integration uses a callback system to notify other components of updates:

```python
# Register a callback for position updates
client.add_position_update_callback(async_callback_function)

# Register a callback for market updates for a specific symbol
client.add_market_update_callback("BTCUSDT", async_callback_function)
```

## Position Management

Both exchange clients provide high-level methods for position management:

### Opening Positions

```python
position = await client.open_position(
    symbol="BTCUSDT",
    side="buy",
    quantity=Decimal("0.01"),
    leverage=5,
    order_type="MARKET",
    stop_loss=Decimal("19000"),
    take_profit=Decimal("21000")
)
```

This creates the main position order and also sets up stop loss and take profit orders in a single operation.

### Closing Positions

```python
result = await client.close_position(
    symbol="BTCUSDT",
    order_type="MARKET"
)
```

This closes the position with a market order and cancels any related orders (stop loss, take profit).

### Updating Stop Loss/Take Profit

```python
result = await client.update_position_sl_tp(
    symbol="BTCUSDT",
    stop_loss=Decimal("19500"),
    take_profit=Decimal("21500")
)
```

This updates or creates stop loss and take profit orders for an existing position.

## Error Handling

The exchange clients implement robust error handling with:

1. **Retry Logic**: Automatic retries for transient errors (network issues, rate limits)
2. **Error Categorization**: Different handling for different types of errors
3. **Logging**: Comprehensive logging of all errors with context information

## Adding a New Exchange

To add support for a new exchange:

1. Create a new class that implements the `ExchangeInterface` abstract base class
2. Implement all required methods, adapting the exchange's API to match the interface
3. Add WebSocket support for real-time data
4. Implement high-level position management methods
5. Add proper error handling and logging
6. Update the factory method to create instances of the new exchange client

## Conclusion

The exchange client integration provides a unified interface for interacting with different cryptocurrency exchanges, allowing the ETRMS to monitor and manage positions across platforms with consistent behavior. The implementation includes REST API integration, WebSocket support for real-time data, position management functionality, and robust error handling. 