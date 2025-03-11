"""
Enhanced Trading Risk Management System - Market Analysis Service

This service integrates the market analysis components with the risk management system,
providing real-time market condition analysis to inform trading decisions.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd

from analysis.regime import MarketRegimeDetector, RegimeChangeDetector, MarketRegime
from analysis.volatility import VolatilityAnalyzer, VolatilityRegimeDetector
from analysis.correlation import CorrelationAnalyzer, CorrelationRegimeDetector
from analysis.liquidity import LiquidityAnalyzer, LiquidityRegimeDetector
from exchange.factory import ExchangeClientFactory
from utils.logger import get_logger, log_event


class MarketAnalysisService:
    """
    Service for analyzing market conditions and providing insights to the risk management system.
    
    This service:
    - Monitors market regimes across multiple exchanges and symbols
    - Tracks volatility, correlation, and liquidity conditions
    - Provides recommendations for position sizing and risk parameters
    - Integrates with the risk management system to adjust risk thresholds
    """
    
    def __init__(
        self,
        exchange_factory: ExchangeClientFactory,
        update_interval: int = 60,  # seconds
        lookback_periods: int = 100,
        symbols: Optional[List[str]] = None,
        exchanges: Optional[List[str]] = None
    ):
        """
        Initialize the MarketAnalysisService.
        
        Args:
            exchange_factory: Factory for creating exchange clients
            update_interval: Interval for updating market analysis (in seconds)
            lookback_periods: Number of periods to look back for analysis
            symbols: List of symbols to analyze (defaults to all active symbols)
            exchanges: List of exchanges to analyze (defaults to all configured exchanges)
        """
        self.exchange_factory = exchange_factory
        self.update_interval = update_interval
        self.lookback_periods = lookback_periods
        self.symbols = symbols
        self.exchanges = exchanges
        self.logger = get_logger(__name__)
        
        # Initialize analysis components
        self.market_regime_detector = MarketRegimeDetector(lookback_periods=lookback_periods)
        self.volatility_analyzer = VolatilityAnalyzer(lookback_periods=lookback_periods)
        self.correlation_analyzer = CorrelationAnalyzer(lookback_periods=lookback_periods)
        self.liquidity_analyzer = LiquidityAnalyzer(lookback_periods=lookback_periods)
        
        # Initialize regime detectors
        self.regime_change_detector = RegimeChangeDetector(self.market_regime_detector)
        self.volatility_regime_detector = VolatilityRegimeDetector(self.volatility_analyzer)
        self.correlation_regime_detector = CorrelationRegimeDetector(self.correlation_analyzer)
        self.liquidity_regime_detector = LiquidityRegimeDetector(self.liquidity_analyzer)
        
        # State variables
        self.running = False
        self.analysis_task = None
        self.exchange_clients = {}
        self.historical_data = {}
        self.orderbook_data = {}
        self.market_analysis = {}
        self.last_update_time = None
        
        # Callbacks
        self.on_regime_change_callbacks = []
        self.on_analysis_update_callbacks = []
        
        log_event(
            self.logger,
            "MARKET_ANALYSIS_SERVICE_INIT",
            "Market analysis service initialized",
            context={
                "update_interval": update_interval,
                "lookback_periods": lookback_periods,
                "symbols": symbols,
                "exchanges": exchanges
            }
        )
    
    async def start(self) -> None:
        """Start the market analysis service."""
        if self.running:
            log_event(
                self.logger,
                "MARKET_ANALYSIS_SERVICE_ALREADY_RUNNING",
                "Market analysis service already running"
            )
            return
        
        self.running = True
        
        try:
            # Initialize exchange clients
            await self._initialize_exchange_clients()
            
            # Start the analysis task
            self.analysis_task = asyncio.create_task(self._analysis_loop())
            
            log_event(
                self.logger,
                "MARKET_ANALYSIS_SERVICE_STARTED",
                "Market analysis service started"
            )
        except Exception as e:
            self.running = False
            log_event(
                self.logger,
                "MARKET_ANALYSIS_SERVICE_START_ERROR",
                f"Error starting market analysis service: {str(e)}",
                context={"error": str(e)}
            )
            raise
    
    async def stop(self) -> None:
        """Stop the market analysis service."""
        if not self.running:
            return
        
        self.running = False
        
        if self.analysis_task:
            self.analysis_task.cancel()
            try:
                await self.analysis_task
            except asyncio.CancelledError:
                pass
            self.analysis_task = None
        
        # Close exchange clients
        for client in self.exchange_clients.values():
            await client.close()
        
        self.exchange_clients = {}
        
        log_event(
            self.logger,
            "MARKET_ANALYSIS_SERVICE_STOPPED",
            "Market analysis service stopped"
        )
    
    async def _initialize_exchange_clients(self) -> None:
        """Initialize exchange clients."""
        # Get exchanges to analyze
        exchanges = self.exchanges
        if not exchanges:
            # Get all configured exchanges
            exchanges = self.exchange_factory.get_available_exchanges()
        
        # Initialize clients
        for exchange_name in exchanges:
            try:
                client = self.exchange_factory.create_client(exchange_name)
                await client.initialize()
                self.exchange_clients[exchange_name] = client
                
                log_event(
                    self.logger,
                    "EXCHANGE_CLIENT_INITIALIZED",
                    f"Initialized exchange client for {exchange_name}"
                )
            except Exception as e:
                log_event(
                    self.logger,
                    "EXCHANGE_CLIENT_INIT_ERROR",
                    f"Error initializing exchange client for {exchange_name}: {str(e)}",
                    context={"exchange": exchange_name, "error": str(e)}
                )
    
    async def _analysis_loop(self) -> None:
        """Main analysis loop."""
        while self.running:
            try:
                # Update market data
                await self._update_market_data()
                
                # Perform market analysis
                await self._analyze_market_conditions()
                
                # Update last update time
                self.last_update_time = datetime.utcnow()
                
                # Wait for next update
                await asyncio.sleep(self.update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log_event(
                    self.logger,
                    "MARKET_ANALYSIS_ERROR",
                    f"Error in market analysis loop: {str(e)}",
                    context={"error": str(e)}
                )
                await asyncio.sleep(5)  # Short delay before retrying
    
    async def _update_market_data(self) -> None:
        """Update market data for all exchanges and symbols."""
        # Get symbols to analyze
        symbols = self.symbols
        
        for exchange_name, client in self.exchange_clients.items():
            try:
                # If no symbols specified, get all active symbols
                if not symbols:
                    # This is exchange-specific, might need to be adapted
                    exchange_info = await client.get_exchange_info()
                    active_symbols = [
                        symbol['symbol'] for symbol in exchange_info.get('symbols', [])
                        if symbol.get('status') == 'TRADING'
                    ]
                else:
                    active_symbols = symbols
                
                # Initialize data structures if needed
                if exchange_name not in self.historical_data:
                    self.historical_data[exchange_name] = {}
                
                if exchange_name not in self.orderbook_data:
                    self.orderbook_data[exchange_name] = {}
                
                # Update data for each symbol
                for symbol in active_symbols:
                    # Get historical klines
                    klines = await client.get_klines(
                        symbol=symbol,
                        interval='1h',
                        limit=self.lookback_periods
                    )
                    
                    # Convert to DataFrame
                    df = pd.DataFrame(klines)
                    if not df.empty:
                        # Rename columns for consistency
                        df = df.rename(columns={
                            'open_time': 'timestamp',
                            'open': 'open',
                            'high': 'high',
                            'low': 'low',
                            'close': 'close',
                            'volume': 'volume'
                        })
                        
                        # Store historical data
                        self.historical_data[exchange_name][symbol] = df
                    
                    # Get orderbook data
                    orderbook = await client.get_orderbook(symbol=symbol, depth=20)
                    if orderbook:
                        self.orderbook_data[exchange_name][symbol] = orderbook
                    
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.1)
            
            except Exception as e:
                log_event(
                    self.logger,
                    "MARKET_DATA_UPDATE_ERROR",
                    f"Error updating market data for {exchange_name}: {str(e)}",
                    context={"exchange": exchange_name, "error": str(e)}
                )
    
    async def _analyze_market_conditions(self) -> None:
        """Analyze market conditions for all exchanges and symbols."""
        for exchange_name in self.historical_data:
            for symbol in self.historical_data[exchange_name]:
                try:
                    # Get data
                    price_data = self.historical_data[exchange_name][symbol]
                    orderbook_data = self.orderbook_data.get(exchange_name, {}).get(symbol)
                    
                    if price_data.empty or not orderbook_data:
                        continue
                    
                    # Initialize analysis for this symbol if needed
                    if exchange_name not in self.market_analysis:
                        self.market_analysis[exchange_name] = {}
                    
                    if symbol not in self.market_analysis[exchange_name]:
                        self.market_analysis[exchange_name][symbol] = {}
                    
                    # Analyze market regime
                    market_regime, regime_changed = self.regime_change_detector.update(
                        price_data=price_data,
                        timestamp=datetime.utcnow()
                    )
                    
                    # Analyze volatility
                    volatility = self.volatility_analyzer.calculate_historical_volatility(price_data)
                    volatility_regime, volatility_regime_changed = self.volatility_regime_detector.update(
                        price_data=price_data,
                        timestamp=datetime.utcnow()
                    )
                    
                    # Analyze liquidity
                    liquidity_metrics = self.liquidity_analyzer.calculate_liquidity_score(
                        orderbook_data=orderbook_data,
                        price_data=price_data,
                        volume_data=price_data  # Using price data for volume as well
                    )
                    liquidity_regime, liquidity_regime_changed = self.liquidity_regime_detector.update(
                        orderbook_data=orderbook_data,
                        price_data=price_data,
                        volume_data=price_data,
                        timestamp=datetime.utcnow()
                    )
                    
                    # Store analysis results
                    self.market_analysis[exchange_name][symbol] = {
                        'timestamp': datetime.utcnow(),
                        'market_regime': market_regime,
                        'volatility': volatility,
                        'volatility_regime': volatility_regime,
                        'liquidity_metrics': liquidity_metrics,
                        'liquidity_regime': liquidity_regime,
                        'trading_recommendations': self._generate_trading_recommendations(
                            market_regime, volatility_regime, liquidity_regime
                        )
                    }
                    
                    # Notify callbacks if regime changed
                    if regime_changed or volatility_regime_changed or liquidity_regime_changed:
                        self._notify_regime_change(
                            exchange=exchange_name,
                            symbol=symbol,
                            market_regime=market_regime,
                            volatility_regime=volatility_regime,
                            liquidity_regime=liquidity_regime
                        )
                
                except Exception as e:
                    log_event(
                        self.logger,
                        "MARKET_ANALYSIS_ERROR",
                        f"Error analyzing market conditions for {exchange_name}/{symbol}: {str(e)}",
                        context={
                            "exchange": exchange_name,
                            "symbol": symbol,
                            "error": str(e)
                        }
                    )
        
        # Analyze correlations (requires data from multiple symbols)
        try:
            self._analyze_correlations()
        except Exception as e:
            log_event(
                self.logger,
                "CORRELATION_ANALYSIS_ERROR",
                f"Error analyzing correlations: {str(e)}",
                context={"error": str(e)}
            )
        
        # Notify analysis update callbacks
        self._notify_analysis_update()
    
    def _analyze_correlations(self) -> None:
        """Analyze correlations between symbols."""
        for exchange_name in self.historical_data:
            # Skip if there are less than 2 symbols
            if len(self.historical_data[exchange_name]) < 2:
                continue
            
            # Prepare price data for correlation analysis
            price_data = {}
            for symbol in self.historical_data[exchange_name]:
                price_data[symbol] = self.historical_data[exchange_name][symbol]
            
            # Calculate correlation matrix
            correlation_matrix = self.correlation_analyzer.calculate_correlation_matrix(price_data)
            
            # Detect correlation regime
            correlation_regime, regime_changed = self.correlation_regime_detector.update(
                price_data=price_data,
                timestamp=datetime.utcnow()
            )
            
            # Calculate diversification score
            diversification_score = self.correlation_analyzer.calculate_diversification_score(correlation_matrix)
            
            # Store correlation analysis
            if 'correlation' not in self.market_analysis[exchange_name]:
                self.market_analysis[exchange_name]['correlation'] = {}
            
            self.market_analysis[exchange_name]['correlation'] = {
                'timestamp': datetime.utcnow(),
                'correlation_matrix': correlation_matrix.to_dict(),
                'correlation_regime': correlation_regime,
                'diversification_score': diversification_score
            }
    
    def _generate_trading_recommendations(
        self,
        market_regime: MarketRegime,
        volatility_regime: str,
        liquidity_regime: str
    ) -> Dict[str, Any]:
        """
        Generate trading recommendations based on market conditions.
        
        Args:
            market_regime: Current market regime
            volatility_regime: Current volatility regime
            liquidity_regime: Current liquidity regime
            
        Returns:
            Dictionary with trading recommendations
        """
        recommendations = {
            'position_sizing': 'normal',
            'risk_adjustment': 1.0,
            'strategy_type': 'neutral',
            'notes': []
        }
        
        # Adjust based on market regime
        if market_regime == MarketRegime.TRENDING_UP:
            recommendations['strategy_type'] = 'trend_following'
            recommendations['notes'].append('Market is in an uptrend - trend following strategies preferred')
        
        elif market_regime == MarketRegime.TRENDING_DOWN:
            recommendations['strategy_type'] = 'trend_following'
            recommendations['notes'].append('Market is in a downtrend - trend following strategies preferred')
        
        elif market_regime == MarketRegime.RANGING:
            recommendations['strategy_type'] = 'mean_reversion'
            recommendations['notes'].append('Market is ranging - mean reversion strategies preferred')
        
        elif market_regime == MarketRegime.VOLATILE:
            recommendations['position_sizing'] = 'reduced'
            recommendations['risk_adjustment'] = 0.7
            recommendations['notes'].append('Market is volatile - reduce position sizes and tighten risk controls')
        
        elif market_regime == MarketRegime.BREAKOUT:
            recommendations['strategy_type'] = 'breakout'
            recommendations['notes'].append('Market is breaking out - breakout strategies preferred')
        
        elif market_regime == MarketRegime.REVERSAL:
            recommendations['strategy_type'] = 'reversal'
            recommendations['notes'].append('Market is showing reversal signals - counter-trend strategies preferred')
        
        # Adjust based on volatility regime
        if volatility_regime == 'high':
            recommendations['position_sizing'] = 'reduced'
            recommendations['risk_adjustment'] = min(recommendations['risk_adjustment'], 0.7)
            recommendations['notes'].append('High volatility detected - reduce position sizes')
        
        elif volatility_regime == 'low':
            if recommendations['position_sizing'] == 'normal':
                recommendations['position_sizing'] = 'increased'
                recommendations['risk_adjustment'] = 1.2
                recommendations['notes'].append('Low volatility detected - consider increasing position sizes')
        
        # Adjust based on liquidity regime
        if liquidity_regime == 'low':
            recommendations['position_sizing'] = 'reduced'
            recommendations['risk_adjustment'] = min(recommendations['risk_adjustment'], 0.8)
            recommendations['notes'].append('Low liquidity detected - reduce position sizes to minimize market impact')
        
        return recommendations
    
    def _notify_regime_change(
        self,
        exchange: str,
        symbol: str,
        market_regime: MarketRegime,
        volatility_regime: str,
        liquidity_regime: str
    ) -> None:
        """
        Notify callbacks about regime changes.
        
        Args:
            exchange: Exchange name
            symbol: Symbol
            market_regime: Current market regime
            volatility_regime: Current volatility regime
            liquidity_regime: Current liquidity regime
        """
        for callback in self.on_regime_change_callbacks:
            try:
                callback(
                    exchange=exchange,
                    symbol=symbol,
                    market_regime=market_regime,
                    volatility_regime=volatility_regime,
                    liquidity_regime=liquidity_regime
                )
            except Exception as e:
                log_event(
                    self.logger,
                    "CALLBACK_ERROR",
                    f"Error in regime change callback: {str(e)}",
                    context={"error": str(e)}
                )
    
    def _notify_analysis_update(self) -> None:
        """Notify callbacks about analysis updates."""
        for callback in self.on_analysis_update_callbacks:
            try:
                callback(analysis=self.market_analysis)
            except Exception as e:
                log_event(
                    self.logger,
                    "CALLBACK_ERROR",
                    f"Error in analysis update callback: {str(e)}",
                    context={"error": str(e)}
                )
    
    def register_regime_change_callback(
        self,
        callback: Callable[[str, str, MarketRegime, str, str], None]
    ) -> None:
        """
        Register a callback for regime changes.
        
        Args:
            callback: Function to call when a regime changes
        """
        self.on_regime_change_callbacks.append(callback)
    
    def register_analysis_update_callback(
        self,
        callback: Callable[[Dict[str, Dict[str, Any]]], None]
    ) -> None:
        """
        Register a callback for analysis updates.
        
        Args:
            callback: Function to call when analysis is updated
        """
        self.on_analysis_update_callbacks.append(callback)
    
    def get_market_analysis(
        self,
        exchange: Optional[str] = None,
        symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get the current market analysis.
        
        Args:
            exchange: Optional exchange name to filter by
            symbol: Optional symbol to filter by
            
        Returns:
            Dictionary with market analysis
        """
        if exchange and symbol:
            return self.market_analysis.get(exchange, {}).get(symbol, {})
        elif exchange:
            return self.market_analysis.get(exchange, {})
        else:
            return self.market_analysis
    
    def get_trading_recommendations(
        self,
        exchange: str,
        symbol: str
    ) -> Dict[str, Any]:
        """
        Get trading recommendations for a specific symbol.
        
        Args:
            exchange: Exchange name
            symbol: Symbol
            
        Returns:
            Dictionary with trading recommendations
        """
        analysis = self.get_market_analysis(exchange, symbol)
        return analysis.get('trading_recommendations', {})
    
    def adjust_risk_parameters(
        self,
        base_parameters: Dict[str, Any],
        exchange: str,
        symbol: str
    ) -> Dict[str, Any]:
        """
        Adjust risk parameters based on market conditions.
        
        Args:
            base_parameters: Base risk parameters
            exchange: Exchange name
            symbol: Symbol
            
        Returns:
            Adjusted risk parameters
        """
        analysis = self.get_market_analysis(exchange, symbol)
        if not analysis:
            return base_parameters
        
        recommendations = analysis.get('trading_recommendations', {})
        risk_adjustment = recommendations.get('risk_adjustment', 1.0)
        
        # Adjust parameters
        adjusted_parameters = base_parameters.copy()
        
        # Adjust position size limit
        if 'position_size_limit' in adjusted_parameters:
            adjusted_parameters['position_size_limit'] *= risk_adjustment
        
        # Adjust stop loss distance
        if 'stop_loss_percent' in adjusted_parameters:
            # In high volatility, we might want wider stops
            volatility_regime = analysis.get('volatility_regime', 'normal')
            if volatility_regime == 'high':
                adjusted_parameters['stop_loss_percent'] *= 1.2
            elif volatility_regime == 'low':
                adjusted_parameters['stop_loss_percent'] *= 0.8
        
        # Adjust max drawdown threshold
        if 'max_drawdown_threshold' in adjusted_parameters:
            market_regime = analysis.get('market_regime', MarketRegime.UNKNOWN)
            if market_regime in [MarketRegime.VOLATILE, MarketRegime.BREAKOUT]:
                # More conservative in volatile or breakout markets
                adjusted_parameters['max_drawdown_threshold'] *= 0.8
        
        return adjusted_parameters 