"""
Enhanced Trading Risk Management System Risk Monitor Tests

This module contains unit tests for the RiskMonitor class.
"""
import unittest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from decimal import Decimal
import json

from risk.monitor import RiskMonitor
from data.models.circuit_breakers import CircuitBreaker


class TestRiskMonitor(unittest.TestCase):
    """Test cases for the RiskMonitor class."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create mocks
        self.account_repo_mock = AsyncMock()
        self.circuit_breaker_repo_mock = AsyncMock()
        
        # Set up account data
        self.test_account_id = "test-account-123"
        self.test_account = MagicMock()
        self.test_account.id = self.test_account_id
        self.test_account.exchanges = [
            {
                "exchange_id": "binance",
                "api_key": "test-api-key",
                "api_secret": "test-api-secret"
            },
            {
                "exchange_id": "hyperliquid",
                "api_key": "test-api-key-2",
                "api_secret": "test-api-secret-2"
            }
        ]
        
        # Mock account repository
        self.account_repo_mock.get_by_id.return_value = self.test_account
        
        # Mock circuit breaker repository
        self.circuit_breaker_test_data = [
            {
                "id": "cb-1",
                "name": "Max Drawdown Circuit Breaker",
                "description": "Triggers when drawdown exceeds 10%",
                "account_id": self.test_account_id,
                "condition": "max_drawdown",
                "action": "notify",
                "parameters": {"threshold": 10.0},
                "enabled": True
            },
            {
                "id": "cb-2",
                "name": "Max Position Size Circuit Breaker",
                "description": "Triggers when position exceeds 25% of equity",
                "account_id": self.test_account_id,
                "condition": "max_position_size",
                "action": "reduce_position",
                "parameters": {"threshold": 25.0, "reduction_percentage": 50.0},
                "enabled": True
            }
        ]
        
        # Create CircuitBreaker instances
        self.circuit_breakers = []
        for cb_data in self.circuit_breaker_test_data:
            cb = CircuitBreaker()
            for key, value in cb_data.items():
                setattr(cb, key, value)
            self.circuit_breakers.append(cb)
            
        self.circuit_breaker_repo_mock.get_by_account_id.return_value = self.circuit_breakers
        self.circuit_breaker_repo_mock.create_event.return_value = MagicMock()
        
        # Create exchange client mocks
        self.binance_client_mock = AsyncMock()
        self.hyperliquid_client_mock = AsyncMock()
        
        # Set up exchange client return values
        self.binance_client_mock.get_account_info.return_value = {
            "total_equity": 10000.0,
            "available_balance": 8000.0,
            "margin_balance": 9000.0,
            "unrealized_pnl": 1000.0
        }
        
        self.hyperliquid_client_mock.get_account_info.return_value = {
            "total_equity": 5000.0,
            "available_balance": 4000.0,
            "margin_balance": 4500.0,
            "unrealized_pnl": 500.0
        }
        
        self.binance_positions = [
            {
                "symbol": "BTCUSDT",
                "side": "long",
                "quantity": 0.5,
                "notional_value": 2500.0,
                "entry_price": 50000.0,
                "liquidation_price": 45000.0,
                "unrealized_pnl": 500.0,
                "leverage": 2,
                "margin_type": "isolated"
            },
            {
                "symbol": "ETHUSDT",
                "side": "short",
                "quantity": -10.0,
                "notional_value": 2000.0,
                "entry_price": 2000.0,
                "liquidation_price": 2200.0,
                "unrealized_pnl": 200.0,
                "leverage": 3,
                "margin_type": "cross"
            }
        ]
        
        self.hyperliquid_positions = [
            {
                "symbol": "BTC-PERP",
                "side": "long",
                "quantity": 0.2,
                "notional_value": 1000.0,
                "entry_price": 50000.0,
                "liquidation_price": 45000.0,
                "unrealized_pnl": 100.0,
                "leverage": 5,
                "margin_type": "cross"
            }
        ]
        
        self.binance_client_mock.get_positions.return_value = self.binance_positions
        self.hyperliquid_client_mock.get_positions.return_value = self.hyperliquid_positions
        
        # Patch the ExchangeClientFactory
        self.factory_patch = patch('risk.monitor.ExchangeClientFactory')
        self.factory_mock = self.factory_patch.start()
        
        # Configure factory to return our mock clients
        self.factory_mock.get_client.side_effect = lambda exchange_name, **kwargs: {
            'binance': self.binance_client_mock,
            'hyperliquid': self.hyperliquid_client_mock
        }.get(exchange_name)
        
        # Create RiskMonitor instance
        self.risk_monitor = RiskMonitor(
            account_id=self.test_account_id,
            account_repository=self.account_repo_mock,
            circuit_breaker_repository=self.circuit_breaker_repo_mock,
            polling_interval=1  # Short polling interval for tests
        )
        
    def tearDown(self):
        """Clean up after each test."""
        self.factory_patch.stop()
    
    def asyncSetUp(self):
        """Async setup for tests."""
        return asyncio.run(self._async_setup())
        
    async def _async_setup(self):
        """Async setup logic."""
        await self.risk_monitor.start()
    
    def asyncTearDown(self):
        """Async teardown for tests."""
        return asyncio.run(self._async_teardown())
        
    async def _async_teardown(self):
        """Async teardown logic."""
        await self.risk_monitor.stop()
    
    def test_initialization(self):
        """Test that RiskMonitor initializes correctly."""
        self.assertEqual(self.risk_monitor.account_id, self.test_account_id)
        self.assertFalse(self.risk_monitor.running)
        self.assertIsNone(self.risk_monitor.monitoring_task)
        self.assertEqual(len(self.risk_monitor.exchange_clients), 0)
        self.assertEqual(len(self.risk_monitor.account_info), 0)
        self.assertEqual(len(self.risk_monitor.positions), 0)
        self.assertEqual(len(self.risk_monitor.balance_history), 0)
        self.assertEqual(self.risk_monitor.max_equity, Decimal('0'))
    
    def test_exchange_client_initialization(self):
        """Test that exchange clients initialize correctly."""
        # Run the test
        asyncio.run(self.risk_monitor._initialize_exchange_clients())
        
        # Check that clients were initialized
        self.assertEqual(len(self.risk_monitor.exchange_clients), 2)
        self.assertIn("binance", self.risk_monitor.exchange_clients)
        self.assertIn("hyperliquid", self.risk_monitor.exchange_clients)
        
        # Verify calls
        self.account_repo_mock.get_by_id.assert_called_once_with(self.test_account_id)
        self.factory_mock.get_client.assert_any_call(
            exchange_name="binance",
            api_key="test-api-key",
            api_secret="test-api-secret"
        )
        self.factory_mock.get_client.assert_any_call(
            exchange_name="hyperliquid",
            api_key="test-api-key-2",
            api_secret="test-api-secret-2"
        )
        self.binance_client_mock.initialize.assert_called_once()
        self.hyperliquid_client_mock.initialize.assert_called_once()
    
    def test_update_account_information(self):
        """Test updating account information."""
        # Set up
        asyncio.run(self.risk_monitor._initialize_exchange_clients())
        
        # Run the test
        asyncio.run(self.risk_monitor._update_account_information())
        
        # Check results
        self.assertEqual(len(self.risk_monitor.account_info), 2)
        self.assertIn("binance", self.risk_monitor.account_info)
        self.assertIn("hyperliquid", self.risk_monitor.account_info)
        self.assertEqual(self.risk_monitor.account_info["binance"]["total_equity"], 10000.0)
        self.assertEqual(self.risk_monitor.account_info["hyperliquid"]["total_equity"], 5000.0)
        
        # Check that max equity was updated
        self.assertEqual(self.risk_monitor.max_equity, Decimal('15000.0'))
        
        # Check that balance history was updated
        self.assertEqual(len(self.risk_monitor.balance_history), 2)
        self.assertEqual(self.risk_monitor.balance_history[0]["exchange"], "binance")
        self.assertEqual(self.risk_monitor.balance_history[0]["equity"], 10000.0)
        self.assertEqual(self.risk_monitor.balance_history[1]["exchange"], "hyperliquid")
        self.assertEqual(self.risk_monitor.balance_history[1]["equity"], 5000.0)
    
    def test_update_positions(self):
        """Test updating position information."""
        # Set up
        asyncio.run(self.risk_monitor._initialize_exchange_clients())
        
        # Run the test
        asyncio.run(self.risk_monitor._update_positions())
        
        # Check results
        self.assertEqual(len(self.risk_monitor.positions), 2)
        self.assertIn("binance", self.risk_monitor.positions)
        self.assertIn("hyperliquid", self.risk_monitor.positions)
        self.assertEqual(len(self.risk_monitor.positions["binance"]), 2)
        self.assertEqual(len(self.risk_monitor.positions["hyperliquid"]), 1)
        self.assertIn("BTCUSDT", self.risk_monitor.positions["binance"])
        self.assertIn("ETHUSDT", self.risk_monitor.positions["binance"])
        self.assertIn("BTC-PERP", self.risk_monitor.positions["hyperliquid"])
    
    def test_calculate_risk_metrics(self):
        """Test calculation of risk metrics."""
        # Set up
        asyncio.run(self.risk_monitor._initialize_exchange_clients())
        asyncio.run(self.risk_monitor._update_account_information())
        asyncio.run(self.risk_monitor._update_positions())
        
        # Run the test
        metrics = asyncio.run(self.risk_monitor._calculate_risk_metrics())
        
        # Check basic metrics
        self.assertEqual(metrics["account_id"], self.test_account_id)
        self.assertEqual(metrics["total_equity"], 15000.0)
        self.assertEqual(metrics["total_available_balance"], 12000.0)
        self.assertEqual(metrics["total_margin_balance"], 13500.0)
        self.assertEqual(metrics["total_unrealized_pnl"], 1500.0)
        
        # Check position metrics
        self.assertEqual(metrics["total_position_size"], 10.7)  # 0.5 + 10 + 0.2
        self.assertEqual(metrics["total_position_value"], 5500.0)  # 2500 + 2000 + 1000
        self.assertEqual(metrics["position_count"], 3)
        
        # Check exchange-specific metrics
        self.assertEqual(metrics["exchanges"]["binance"]["equity"], 10000.0)
        self.assertEqual(metrics["exchanges"]["binance"]["position_count"], 2)
        self.assertEqual(metrics["exchanges"]["binance"]["position_value"], 4500.0)
        self.assertEqual(metrics["exchanges"]["hyperliquid"]["equity"], 5000.0)
        self.assertEqual(metrics["exchanges"]["hyperliquid"]["position_count"], 1)
        self.assertEqual(metrics["exchanges"]["hyperliquid"]["position_value"], 1000.0)
        
        # Check calculated metrics
        self.assertEqual(metrics["leverage"], 5500.0 / 13500.0)
        self.assertEqual(metrics["exposure_percentage"], 5500.0 / 15000.0 * 100)
        
        # Check largest position
        self.assertEqual(metrics["largest_position"]["exchange"], "binance")
        self.assertEqual(metrics["largest_position"]["symbol"], "BTCUSDT")
        self.assertEqual(metrics["largest_position"]["value"], 2500.0)
        self.assertEqual(
            metrics["largest_position"]["percentage_of_equity"], 
            2500.0 / 15000.0 * 100
        )
    
    def test_evaluate_circuit_breaker_max_drawdown(self):
        """Test evaluating a max drawdown circuit breaker."""
        # Create a test circuit breaker
        breaker = CircuitBreaker()
        breaker.id = "test-cb-1"
        breaker.condition = "max_drawdown"
        breaker.parameters = {"threshold": 10.0}
        
        # Create risk metrics with different drawdown values
        risk_metrics_below = {"current_drawdown": 5.0}
        risk_metrics_equal = {"current_drawdown": 10.0}
        risk_metrics_above = {"current_drawdown": 15.0}
        
        # Test below threshold (should not trigger)
        should_trigger, values = self.risk_monitor._evaluate_circuit_breaker(
            breaker, risk_metrics_below
        )
        self.assertFalse(should_trigger)
        self.assertEqual(values["threshold"], 10.0)
        self.assertEqual(values["current_value"], 5.0)
        
        # Test equal to threshold (should trigger)
        should_trigger, values = self.risk_monitor._evaluate_circuit_breaker(
            breaker, risk_metrics_equal
        )
        self.assertTrue(should_trigger)
        self.assertEqual(values["threshold"], 10.0)
        self.assertEqual(values["current_value"], 10.0)
        
        # Test above threshold (should trigger)
        should_trigger, values = self.risk_monitor._evaluate_circuit_breaker(
            breaker, risk_metrics_above
        )
        self.assertTrue(should_trigger)
        self.assertEqual(values["threshold"], 10.0)
        self.assertEqual(values["current_value"], 15.0)
    
    def test_evaluate_circuit_breaker_max_position_size(self):
        """Test evaluating a max position size circuit breaker."""
        # Create a test circuit breaker
        breaker = CircuitBreaker()
        breaker.id = "test-cb-2"
        breaker.condition = "max_position_size"
        breaker.parameters = {"threshold": 20.0}
        
        # Create risk metrics with different position sizes
        largest_position_below = {
            "exchange": "binance",
            "symbol": "BTCUSDT",
            "value": 1000.0,
            "percentage_of_equity": 10.0
        }
        
        largest_position_above = {
            "exchange": "binance",
            "symbol": "BTCUSDT",
            "value": 3000.0,
            "percentage_of_equity": 30.0
        }
        
        risk_metrics_below = {"largest_position": largest_position_below}
        risk_metrics_above = {"largest_position": largest_position_above}
        risk_metrics_no_position = {}
        
        # Test below threshold (should not trigger)
        should_trigger, values = self.risk_monitor._evaluate_circuit_breaker(
            breaker, risk_metrics_below
        )
        self.assertFalse(should_trigger)
        self.assertEqual(values["threshold"], 20.0)
        self.assertEqual(values["current_value"], 10.0)
        
        # Test above threshold (should trigger)
        should_trigger, values = self.risk_monitor._evaluate_circuit_breaker(
            breaker, risk_metrics_above
        )
        self.assertTrue(should_trigger)
        self.assertEqual(values["threshold"], 20.0)
        self.assertEqual(values["current_value"], 30.0)
        
        # Test no position (should not trigger)
        should_trigger, values = self.risk_monitor._evaluate_circuit_breaker(
            breaker, risk_metrics_no_position
        )
        self.assertFalse(should_trigger)
        self.assertEqual(len(values), 0)
    
    @patch('risk.monitor.asyncio.sleep', new_callable=AsyncMock)
    async def test_monitoring_loop(self, mock_sleep):
        """Test the monitoring loop."""
        # Configure the sleep mock to raise an exception after first iteration
        mock_sleep.side_effect = [None, Exception("Stop loop")]
        
        self.risk_monitor._update_account_information = AsyncMock()
        self.risk_monitor._update_positions = AsyncMock()
        self.risk_monitor._calculate_risk_metrics = AsyncMock()
        self.risk_monitor._check_circuit_breakers = AsyncMock()
        
        # Start the monitoring loop
        self.risk_monitor.running = True
        
        # Run the monitoring loop with exception on second iteration
        with self.assertRaises(Exception):
            await self.risk_monitor._monitoring_loop()
        
        # Verify that each method was called once
        self.risk_monitor._update_account_information.assert_called_once()
        self.risk_monitor._update_positions.assert_called_once()
        self.risk_monitor._calculate_risk_metrics.assert_called_once()
        self.risk_monitor._check_circuit_breakers.assert_called_once()
        mock_sleep.assert_called_once_with(1)  # Our polling interval is 1
    
    async def test_check_circuit_breakers(self):
        """Test checking circuit breakers."""
        # Set up
        await self.risk_monitor._initialize_exchange_clients()
        await self.risk_monitor._update_account_information()
        await self.risk_monitor._update_positions()
        
        # Mock calculate_risk_metrics to return metrics that would trigger the max position size breaker
        self.risk_monitor._calculate_risk_metrics = AsyncMock()
        self.risk_monitor._calculate_risk_metrics.return_value = {
            "current_drawdown": 5.0,  # Below threshold for max_drawdown breaker
            "largest_position": {
                "exchange": "binance",
                "symbol": "BTCUSDT",
                "value": 3000.0,
                "percentage_of_equity": 30.0  # Above threshold for max_position_size breaker
            }
        }
        
        # Mock evaluate_circuit_breaker
        original_evaluate = self.risk_monitor._evaluate_circuit_breaker
        self.risk_monitor._evaluate_circuit_breaker = MagicMock()
        self.risk_monitor._evaluate_circuit_breaker.side_effect = lambda breaker, metrics: (
            (True, {"threshold": 25.0, "current_value": 30.0, "position": metrics["largest_position"]})
            if breaker.condition == "max_position_size"
            else (False, {"threshold": 10.0, "current_value": 5.0})
        )
        
        # Mock trigger_circuit_breaker
        self.risk_monitor._trigger_circuit_breaker = AsyncMock()
        
        # Run the test
        await self.risk_monitor._check_circuit_breakers()
        
        # Verify repository called
        self.circuit_breaker_repo_mock.get_by_account_id.assert_called_once_with(
            self.test_account_id, enabled=True
        )
        
        # Verify calculate_risk_metrics called
        self.risk_monitor._calculate_risk_metrics.assert_called_once()
        
        # Verify evaluate_circuit_breaker called twice (once for each breaker)
        self.assertEqual(self.risk_monitor._evaluate_circuit_breaker.call_count, 2)
        
        # Verify trigger_circuit_breaker called once (only for the max_position_size breaker)
        self.assertEqual(self.risk_monitor._trigger_circuit_breaker.call_count, 1)
        
        # Restore original method
        self.risk_monitor._evaluate_circuit_breaker = original_evaluate
    
    def test_get_equity_at_time(self):
        """Test getting equity at a specific time."""
        # Set up balance history
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        two_hours_ago = now - timedelta(hours=2)
        
        self.risk_monitor.balance_history = [
            {
                "timestamp": two_hours_ago,
                "exchange": "binance",
                "equity": 9000.0,
                "available_balance": 7000.0,
                "margin_balance": 8000.0,
                "unrealized_pnl": 1000.0
            },
            {
                "timestamp": one_hour_ago,
                "exchange": "binance",
                "equity": 10000.0,
                "available_balance": 8000.0,
                "margin_balance": 9000.0,
                "unrealized_pnl": 1000.0
            },
            {
                "timestamp": now,
                "exchange": "binance",
                "equity": 11000.0,
                "available_balance": 9000.0,
                "margin_balance": 10000.0,
                "unrealized_pnl": 1000.0
            }
        ]
        
        # Test getting equity at exact times
        self.assertEqual(self.risk_monitor._get_equity_at_time(two_hours_ago), 9000.0)
        self.assertEqual(self.risk_monitor._get_equity_at_time(one_hour_ago), 10000.0)
        self.assertEqual(self.risk_monitor._get_equity_at_time(now), 11000.0)
        
        # Test getting equity at a time between recorded times
        ninety_mins_ago = now - timedelta(minutes=90)
        self.assertEqual(self.risk_monitor._get_equity_at_time(ninety_mins_ago), 9000.0)
        
        # Test getting equity before all recorded times
        three_hours_ago = now - timedelta(hours=3)
        self.assertEqual(self.risk_monitor._get_equity_at_time(three_hours_ago), 9000.0)
        
        # Test getting equity after all recorded times
        one_hour_from_now = now + timedelta(hours=1)
        self.assertEqual(self.risk_monitor._get_equity_at_time(one_hour_from_now), None)
    
    def test_callbacks(self):
        """Test registering and calling callbacks."""
        # Create test callback functions
        risk_update_called = False
        circuit_breaker_called = False
        position_update_called = False
        
        def risk_update_callback(metrics):
            nonlocal risk_update_called
            risk_update_called = True
        
        def circuit_breaker_callback(breaker, data):
            nonlocal circuit_breaker_called
            circuit_breaker_called = True
        
        def position_update_callback(data):
            nonlocal position_update_called
            position_update_called = True
        
        # Register callbacks
        self.risk_monitor.register_risk_update_callback(risk_update_callback)
        self.risk_monitor.register_circuit_breaker_callback(circuit_breaker_callback)
        self.risk_monitor.register_position_update_callback(position_update_callback)
        
        # Verify callbacks were registered
        self.assertEqual(len(self.risk_monitor.on_risk_update_callbacks), 1)
        self.assertEqual(len(self.risk_monitor.on_circuit_breaker_callbacks), 1)
        self.assertEqual(len(self.risk_monitor.on_position_update_callbacks), 1)
        
        # Check callback invocation
        self.risk_monitor.on_risk_update_callbacks[0]({"test": "data"})
        self.risk_monitor.on_circuit_breaker_callbacks[0](MagicMock(), {"test": "data"})
        self.risk_monitor.on_position_update_callbacks[0]({"test": "data"})
        
        # Verify callbacks were called
        self.assertTrue(risk_update_called)
        self.assertTrue(circuit_breaker_called)
        self.assertTrue(position_update_called)


if __name__ == "__main__":
    unittest.main() 