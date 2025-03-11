"""
Integration tests for the Hyperliquid API client.

These tests require valid API keys with testnet access.
To run these tests:
1. Set the HYPERLIQUID_API_KEY and HYPERLIQUID_API_SECRET environment variables
2. Run pytest with the integration marker: pytest -m integration

Note: These tests interact with the Hyperliquid testnet and may create/cancel orders.
"""

import os
import pytest
import asyncio
from decimal import Decimal

from etrms.backend.exchange.factory import ExchangeClientFactory
from etrms.backend.exchange.hyperliquid.hyperliquid_client import HyperliquidClient

# Test configuration
TEST_SYMBOL = "BTC-USDC"  # Use a symbol available on Hyperliquid testnet
TEST_QUANTITY = 0.001     # Small quantity for testing
TEST_LEVERAGE = 5         # Leverage for testing

# Skip all tests if API keys are not available
pytestmark = pytest.mark.skipif(
    not os.environ.get("HYPERLIQUID_API_KEY") or not os.environ.get("HYPERLIQUID_API_SECRET"),
    reason="Hyperliquid API keys not available"
)

@pytest.fixture
async def client():
    """Create and initialize a Hyperliquid client for testing."""
    factory = ExchangeClientFactory()
    client = factory.get_client(
        "hyperliquid",
        api_key=os.environ.get("HYPERLIQUID_API_KEY"),
        api_secret=os.environ.get("HYPERLIQUID_API_SECRET"),
        testnet=True
    )
    
    # Initialize the client
    await client.initialize()
    
    # Set leverage for testing
    try:
        await client.set_leverage(TEST_SYMBOL, TEST_LEVERAGE)
    except Exception as e:
        print(f"Warning: Could not set leverage: {e}")
    
    yield client
    
    # Close the client after tests
    await client.close()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_account_info(client):
    """Test retrieving account information."""
    account_info = await client.get_account_info()
    
    # Verify the structure of the account info
    assert isinstance(account_info, dict)
    assert "totalEquity" in account_info
    assert "availableBalance" in account_info
    assert isinstance(account_info["totalEquity"], (float, Decimal))
    assert isinstance(account_info["availableBalance"], (float, Decimal))

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_ticker(client):
    """Test retrieving ticker data."""
    ticker = await client.get_ticker(TEST_SYMBOL)
    
    # Verify the structure of the ticker
    assert isinstance(ticker, dict)
    assert "symbol" in ticker
    assert "lastPrice" in ticker
    assert ticker["symbol"] == TEST_SYMBOL
    assert isinstance(ticker["lastPrice"], (float, Decimal))

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_orderbook(client):
    """Test retrieving orderbook data."""
    orderbook = await client.get_orderbook(TEST_SYMBOL)
    
    # Verify the structure of the orderbook
    assert isinstance(orderbook, dict)
    assert "symbol" in orderbook
    assert "bids" in orderbook
    assert "asks" in orderbook
    assert isinstance(orderbook["bids"], list)
    assert isinstance(orderbook["asks"], list)
    
    # Verify there are bids and asks
    if orderbook["bids"]:
        assert isinstance(orderbook["bids"][0], list)
        assert len(orderbook["bids"][0]) >= 2  # Price and quantity
    
    if orderbook["asks"]:
        assert isinstance(orderbook["asks"][0], list)
        assert len(orderbook["asks"][0]) >= 2  # Price and quantity

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_klines(client):
    """Test retrieving kline (candlestick) data."""
    klines = await client.get_klines(TEST_SYMBOL, interval="1h", limit=10)
    
    # Verify the structure of the klines
    assert isinstance(klines, list)
    assert len(klines) <= 10  # Should be at most the requested limit
    
    if klines:
        # Check the structure of a single kline
        kline = klines[0]
        assert isinstance(kline, list)
        assert len(kline) >= 6  # Open time, open, high, low, close, volume

@pytest.mark.integration
@pytest.mark.asyncio
async def test_order_lifecycle(client):
    """Test the full lifecycle of an order: create, get, cancel."""
    # Get the current market price
    ticker = await client.get_ticker(TEST_SYMBOL)
    price = float(ticker["lastPrice"])
    
    # Create a limit order slightly away from the market price
    buy_price = price * 0.95  # 5% below current price
    
    try:
        # Create a buy limit order
        order = await client.create_order(
            symbol=TEST_SYMBOL,
            side="BUY",
            order_type="LIMIT",
            quantity=TEST_QUANTITY,
            price=buy_price,
            time_in_force="GTC"
        )
        
        # Verify the order was created
        assert isinstance(order, dict)
        assert "orderId" in order
        assert "symbol" in order
        assert order["symbol"] == TEST_SYMBOL
        assert order["side"] == "BUY"
        assert float(order["quantity"]) == TEST_QUANTITY
        
        order_id = order["orderId"]
        
        # Get the order details
        retrieved_order = await client.get_order(TEST_SYMBOL, order_id)
        assert retrieved_order["orderId"] == order_id
        
        # Get all open orders
        open_orders = await client.get_orders(TEST_SYMBOL)
        assert isinstance(open_orders, list)
        
        # Cancel the order
        cancel_result = await client.cancel_order(TEST_SYMBOL, order_id)
        assert cancel_result["success"] is True
        
    except Exception as e:
        # If any test fails, make sure to cancel all orders
        await client.cancel_all_orders(TEST_SYMBOL)
        raise e

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_positions(client):
    """Test retrieving positions."""
    positions = await client.get_positions()
    
    # Verify the structure of the positions
    assert isinstance(positions, list)
    
    for position in positions:
        assert isinstance(position, dict)
        assert "symbol" in position
        assert "positionAmt" in position
        assert "entryPrice" in position
        assert "unrealizedProfit" in position

@pytest.mark.integration
@pytest.mark.asyncio
async def test_cancel_all_orders(client):
    """Test canceling all orders."""
    # Create a test order first
    ticker = await client.get_ticker(TEST_SYMBOL)
    price = float(ticker["lastPrice"])
    buy_price = price * 0.95  # 5% below current price
    
    try:
        # Create a buy limit order
        await client.create_order(
            symbol=TEST_SYMBOL,
            side="BUY",
            order_type="LIMIT",
            quantity=TEST_QUANTITY,
            price=buy_price,
            time_in_force="GTC"
        )
        
        # Cancel all orders
        result = await client.cancel_all_orders(TEST_SYMBOL)
        
        # Verify the result
        assert isinstance(result, dict)
        assert "success" in result
        assert result["success"] is True
        
        # Verify there are no open orders
        open_orders = await client.get_orders(TEST_SYMBOL)
        assert len(open_orders) == 0
        
    except Exception as e:
        # If any test fails, make sure to cancel all orders
        await client.cancel_all_orders(TEST_SYMBOL)
        raise e 