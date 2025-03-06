"""
Integration tests for the Binance Futures client.

These tests require valid API keys with testnet access.
Set the environment variables:
- BINANCE_TESTNET_API_KEY
- BINANCE_TESTNET_API_SECRET

To run these tests:
pytest -xvs etrms/backend/tests/integration/exchange/test_binance_futures_client.py
"""
import asyncio
import os
import pytest
from decimal import Decimal

from etrms.backend.exchange.binance.binance_futures_client import BinanceFuturesClient
from etrms.backend.config.settings import Settings

# Skip all tests if no API keys are provided
pytestmark = pytest.mark.skipif(
    not os.environ.get("BINANCE_TESTNET_API_KEY") or not os.environ.get("BINANCE_TESTNET_API_SECRET"),
    reason="Binance testnet API keys not provided"
)

# Test configuration
TEST_SYMBOL = "BTCUSDT"
TEST_QUANTITY = Decimal("0.001")  # Small quantity for testing
TEST_LEVERAGE = 5


@pytest.fixture
async def client():
    """Create and initialize a Binance Futures client for testing."""
    settings = Settings()
    settings.BINANCE_API_KEY = os.environ.get("BINANCE_TESTNET_API_KEY")
    settings.BINANCE_API_SECRET = os.environ.get("BINANCE_TESTNET_API_SECRET")
    settings.BINANCE_TESTNET = True
    
    client = BinanceFuturesClient(
        api_key=settings.BINANCE_API_KEY,
        api_secret=settings.BINANCE_API_SECRET,
        testnet=True
    )
    
    await client.initialize()
    
    try:
        yield client
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_get_account_info(client):
    """Test fetching account information."""
    account_info = await client.get_account_info()
    
    # Verify structure
    assert "total_equity" in account_info
    assert "available_balance" in account_info
    assert "margin_balance" in account_info
    assert "unrealized_pnl" in account_info
    assert "positions" in account_info
    
    # Values should be numeric
    assert isinstance(account_info["total_equity"], float)
    assert isinstance(account_info["available_balance"], float)


@pytest.mark.asyncio
async def test_get_ticker(client):
    """Test fetching ticker data."""
    ticker = await client.get_ticker(TEST_SYMBOL)
    
    # Verify structure
    assert "symbol" in ticker
    assert "price" in ticker
    assert "price_change" in ticker
    assert "price_change_percent" in ticker
    
    # Symbol should match
    assert ticker["symbol"] == TEST_SYMBOL
    
    # Price should be a positive number
    assert float(ticker["price"]) > 0


@pytest.mark.asyncio
async def test_get_orderbook(client):
    """Test fetching orderbook data."""
    orderbook = await client.get_orderbook(TEST_SYMBOL)
    
    # Verify structure
    assert "symbol" in orderbook
    assert "bids" in orderbook
    assert "asks" in orderbook
    
    # Symbol should match
    assert orderbook["symbol"] == TEST_SYMBOL
    
    # Should have bids and asks
    assert len(orderbook["bids"]) > 0
    assert len(orderbook["asks"]) > 0
    
    # First bid should be a price/quantity pair
    assert len(orderbook["bids"][0]) == 2
    assert float(orderbook["bids"][0][0]) > 0  # Price
    assert float(orderbook["bids"][0][1]) > 0  # Quantity


@pytest.mark.asyncio
async def test_get_klines(client):
    """Test fetching kline/candlestick data."""
    klines = await client.get_klines(TEST_SYMBOL, interval="1h", limit=10)
    
    # Should have requested number of klines
    assert len(klines) <= 10
    
    # Each kline should have expected structure
    for kline in klines:
        assert "open_time" in kline
        assert "open" in kline
        assert "high" in kline
        assert "low" in kline
        assert "close" in kline
        assert "volume" in kline


@pytest.mark.asyncio
async def test_order_lifecycle(client):
    """Test the complete lifecycle of an order: create, query, cancel."""
    # Set leverage first
    await client.set_leverage(TEST_SYMBOL, TEST_LEVERAGE)
    
    # Get current market price
    ticker = await client.get_ticker(TEST_SYMBOL)
    current_price = float(ticker["price"])
    
    # Create a limit order slightly below market price
    limit_price = Decimal(str(current_price * 0.95))
    
    try:
        # 1. Create order
        order = await client.create_order(
            symbol=TEST_SYMBOL,
            side="buy",
            order_type="limit",
            quantity=TEST_QUANTITY,
            price=limit_price,
            time_in_force="GTC"
        )
        
        # Verify order creation
        assert order["symbol"] == TEST_SYMBOL
        assert order["side"] == "buy"
        assert order["type"] == "limit"
        assert float(order["quantity"]) == float(TEST_QUANTITY)
        assert float(order["price"]) == float(limit_price)
        
        order_id = order["id"]
        
        # 2. Get specific order
        fetched_order = await client.get_order(order_id, TEST_SYMBOL)
        assert fetched_order["id"] == order_id
        
        # 3. Get all orders
        all_orders = await client.get_orders(TEST_SYMBOL)
        assert any(o["id"] == order_id for o in all_orders)
        
        # 4. Cancel order
        cancelled_order = await client.cancel_order(order_id, TEST_SYMBOL)
        assert cancelled_order["id"] == order_id
        assert cancelled_order["status"] in ["canceled", "cancelled"]
        
    except Exception as e:
        # If any step fails, make sure to cancel the order to clean up
        try:
            await client.cancel_all_orders(TEST_SYMBOL)
        except:
            pass
        raise e


@pytest.mark.asyncio
async def test_open_and_close_position(client):
    """Test opening and closing a small position."""
    # This test is optional and will create actual trades on testnet
    
    # Set leverage first
    await client.set_leverage(TEST_SYMBOL, TEST_LEVERAGE)
    
    try:
        # 1. Open a small long position
        position_result = await client.open_position(
            symbol=TEST_SYMBOL,
            side="buy",
            quantity=TEST_QUANTITY,
            leverage=TEST_LEVERAGE,
            order_type="MARKET"
        )
        
        # Wait a moment for position to be established
        await asyncio.sleep(2)
        
        # 2. Check position
        position = await client.get_position(TEST_SYMBOL)
        
        # Position should exist and be long
        assert position is not None
        assert position["symbol"] == TEST_SYMBOL
        assert position["side"] == "long" or float(position["quantity"]) > 0
        
        # 3. Close position
        close_result = await client.close_position(
            symbol=TEST_SYMBOL,
            close_type="MARKET"
        )
        
        # Wait a moment for position to be closed
        await asyncio.sleep(2)
        
        # 4. Check position is closed
        position = await client.get_position(TEST_SYMBOL)
        
        # Position might be null or have zero quantity
        if position is not None:
            assert float(position["quantity"]) == 0
        
    except Exception as e:
        # If any step fails, make sure to close the position to clean up
        try:
            await client.close_position(TEST_SYMBOL, "MARKET")
        except:
            pass
        raise e 