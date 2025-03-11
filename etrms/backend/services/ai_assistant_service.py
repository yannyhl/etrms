"""
AI Trading Assistant service for the ETRMS.

This service integrates the AI Trading Assistant components to provide
setup detection, strategy recommendations, performance analysis, and decision support.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
from datetime import datetime, timedelta
import asyncio
import json

from ..utils.logger import get_logger
from ..exchange.factory import ExchangeClientFactory
from ..analysis.regime import MarketRegime, RegimeChangeDetector
from ..ai.detection import SetupDetector, SetupType
from ..ai.recommendation import StrategyRecommender, StrategyType
from ..ai.analytics import PerformanceAnalyzer
from ..ai.decision import DecisionSupport

logger = get_logger(__name__)


class AIAssistantService:
    """
    Service that integrates AI Trading Assistant components.
    
    This service provides a unified interface for the AI Trading Assistant,
    coordinating setup detection, strategy recommendations, performance analysis,
    and decision support.
    """
    
    def __init__(
        self,
        exchange_factory: ExchangeClientFactory,
        update_interval: int = 60,  # seconds
        lookback_periods: int = 100,
        min_setup_quality: float = 0.6,
        default_risk_percent: float = 1.0,
        use_market_regime: bool = True
    ):
        """
        Initialize the AIAssistantService.
        
        Args:
            exchange_factory: Factory for creating exchange clients
            update_interval: Interval for updating data and detecting setups (seconds)
            lookback_periods: Number of periods to look back for analysis
            min_setup_quality: Minimum setup quality to consider valid
            default_risk_percent: Default risk percentage per trade
            use_market_regime: Whether to use market regime information
        """
        self.exchange_factory = exchange_factory
        self.update_interval = update_interval
        self.lookback_periods = lookback_periods
        self.min_setup_quality = min_setup_quality
        self.default_risk_percent = default_risk_percent
        self.use_market_regime = use_market_regime
        
        # Initialize components
        self.setup_detector = SetupDetector(
            lookback_periods=lookback_periods,
            min_setup_quality=min_setup_quality,
            use_market_regime=use_market_regime
        )
        
        self.strategy_recommender = StrategyRecommender(
            default_risk_percent=default_risk_percent,
            min_risk_percent=0.5,
            max_risk_percent=2.0,
            use_market_regime=use_market_regime
        )
        
        self.performance_analyzer = PerformanceAnalyzer(
            min_trades_for_analysis=20,
            lookback_periods=lookback_periods,
            use_market_regime_analysis=use_market_regime
        )
        
        self.decision_support = DecisionSupport(
            default_risk_percent=default_risk_percent,
            min_setup_quality=min_setup_quality,
            use_market_regime=use_market_regime
        )
        
        # State variables
        self.exchange_clients = {}
        self.market_data = {}
        self.detected_setups = {}
        self.recommendations = {}
        self.running = False
        self.setup_callbacks = []
        self.recommendation_callbacks = []
        self.logger = logger
        
        self.logger.info(
            f"Initialized AIAssistantService with update_interval={update_interval}, "
            f"lookback_periods={lookback_periods}, min_setup_quality={min_setup_quality}, "
            f"default_risk_percent={default_risk_percent}, use_market_regime={use_market_regime}"
        )
    
    async def start(self, symbols: List[str], exchanges: List[str]) -> None:
        """
        Start the AI Trading Assistant service.
        
        Args:
            symbols: List of symbols to monitor
            exchanges: List of exchanges to monitor
        """
        if self.running:
            self.logger.warning("AI Trading Assistant service is already running")
            return
        
        self.running = True
        self.symbols = symbols
        self.exchanges = exchanges
        
        self.logger.info(
            f"Starting AI Trading Assistant service for symbols: {symbols} "
            f"on exchanges: {exchanges}"
        )
        
        # Initialize exchange clients
        await self._initialize_exchange_clients()
        
        # Start the main loop
        asyncio.create_task(self._assistant_loop())
    
    async def stop(self) -> None:
        """Stop the AI Trading Assistant service."""
        if not self.running:
            self.logger.warning("AI Trading Assistant service is not running")
            return
        
        self.running = False
        self.logger.info("Stopping AI Trading Assistant service")
        
        # Close exchange clients
        for exchange, client in self.exchange_clients.items():
            try:
                await client.close()
                self.logger.info(f"Closed {exchange} client")
            except Exception as e:
                self.logger.error(f"Error closing {exchange} client: {e}")
    
    async def _initialize_exchange_clients(self) -> None:
        """Initialize exchange clients for all specified exchanges."""
        self.logger.info(f"Initializing exchange clients for: {self.exchanges}")
        
        for exchange in self.exchanges:
            try:
                client = self.exchange_factory.create_client(exchange)
                await client.connect()
                self.exchange_clients[exchange] = client
                self.logger.info(f"Initialized {exchange} client")
            except Exception as e:
                self.logger.error(f"Error initializing {exchange} client: {e}")
    
    async def _assistant_loop(self) -> None:
        """Main loop for the AI Trading Assistant service."""
        self.logger.info("Starting AI Trading Assistant main loop")
        
        while self.running:
            try:
                # Update market data
                await self._update_market_data()
                
                # Detect setups
                await self._detect_setups()
                
                # Generate recommendations for new setups
                await self._generate_recommendations()
                
                # Wait for the next update
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                self.logger.error(f"Error in AI Trading Assistant loop: {e}")
                await asyncio.sleep(10)  # Wait a bit before retrying
    
    async def _update_market_data(self) -> None:
        """Update market data for all exchanges and symbols."""
        self.logger.debug("Updating market data")
        
        for exchange, client in self.exchange_clients.items():
            for symbol in self.symbols:
                try:
                    # Get OHLCV data
                    timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"]
                    
                    for timeframe in timeframes:
                        ohlcv = await client.get_candles(
                            symbol=symbol,
                            timeframe=timeframe,
                            limit=self.lookback_periods
                        )
                        
                        # Convert to DataFrame
                        df = pd.DataFrame(
                            ohlcv,
                            columns=["timestamp", "open", "high", "low", "close", "volume"]
                        )
                        
                        # Store in market data
                        if exchange not in self.market_data:
                            self.market_data[exchange] = {}
                        
                        if symbol not in self.market_data[exchange]:
                            self.market_data[exchange][symbol] = {}
                        
                        self.market_data[exchange][symbol][timeframe] = df
                    
                    # Get order book
                    orderbook = await client.get_orderbook(symbol=symbol, limit=20)
                    
                    # Store in market data
                    self.market_data[exchange][symbol]["orderbook"] = orderbook
                    
                    self.logger.debug(f"Updated market data for {symbol} on {exchange}")
                except Exception as e:
                    self.logger.error(f"Error updating market data for {symbol} on {exchange}: {e}")
    
    async def _detect_setups(self) -> None:
        """Detect trading setups for all exchanges and symbols."""
        self.logger.debug("Detecting trading setups")
        
        new_setups = {}
        
        for exchange, exchange_data in self.market_data.items():
            if exchange not in new_setups:
                new_setups[exchange] = {}
            
            for symbol, symbol_data in exchange_data.items():
                if symbol not in new_setups[exchange]:
                    new_setups[exchange][symbol] = {}
                
                for timeframe in ["1h", "4h", "1d"]:  # Focus on higher timeframes
                    if timeframe in symbol_data:
                        try:
                            # Get price data
                            price_data = symbol_data[timeframe]
                            
                            # Get volume data
                            volume_data = price_data[["timestamp", "volume"]]
                            
                            # Get market regime if available
                            market_regime = None  # In a real implementation, this would come from market analysis
                            
                            # Detect setups
                            setups = self.setup_detector.detect_setups(
                                price_data=price_data,
                                volume_data=volume_data,
                                market_regime=market_regime,
                                timeframe=timeframe,
                                exchange=exchange,
                                symbol=symbol
                            )
                            
                            if setups:
                                new_setups[exchange][symbol][timeframe] = setups
                                self.logger.info(
                                    f"Detected {len(setups)} setups for {symbol} "
                                    f"on {exchange} ({timeframe})"
                                )
                                
                                # Notify callbacks
                                for callback in self.setup_callbacks:
                                    try:
                                        callback(exchange, symbol, timeframe, setups)
                                    except Exception as e:
                                        self.logger.error(f"Error in setup callback: {e}")
                        except Exception as e:
                            self.logger.error(
                                f"Error detecting setups for {symbol} on {exchange} ({timeframe}): {e}"
                            )
        
        # Update detected setups
        self.detected_setups = new_setups
    
    async def _generate_recommendations(self) -> None:
        """Generate strategy recommendations for detected setups."""
        self.logger.debug("Generating strategy recommendations")
        
        new_recommendations = {}
        
        for exchange, exchange_setups in self.detected_setups.items():
            if exchange not in new_recommendations:
                new_recommendations[exchange] = {}
            
            for symbol, symbol_setups in exchange_setups.items():
                if symbol not in new_recommendations[exchange]:
                    new_recommendations[exchange][symbol] = {}
                
                for timeframe, setups in symbol_setups.items():
                    if timeframe not in new_recommendations[exchange][symbol]:
                        new_recommendations[exchange][symbol][timeframe] = []
                    
                    for setup in setups:
                        try:
                            # Get market conditions if available
                            market_regime = None  # In a real implementation, this would come from market analysis
                            volatility_regime = None
                            liquidity_regime = None
                            
                            # Generate recommendation
                            recommendation = self.strategy_recommender.recommend_strategy(
                                setup=setup,
                                market_regime=market_regime,
                                volatility_regime=volatility_regime,
                                liquidity_regime=liquidity_regime
                            )
                            
                            # Add to recommendations
                            new_recommendations[exchange][symbol][timeframe].append({
                                "setup": setup,
                                "recommendation": recommendation,
                                "timestamp": datetime.now().isoformat()
                            })
                            
                            self.logger.info(
                                f"Generated {recommendation.get('strategy_type')} recommendation "
                                f"for {setup.get('type')} setup on {symbol} ({exchange}, {timeframe})"
                            )
                            
                            # Notify callbacks
                            for callback in self.recommendation_callbacks:
                                try:
                                    callback(exchange, symbol, timeframe, setup, recommendation)
                                except Exception as e:
                                    self.logger.error(f"Error in recommendation callback: {e}")
                        except Exception as e:
                            self.logger.error(
                                f"Error generating recommendation for setup on {symbol} "
                                f"({exchange}, {timeframe}): {e}"
                            )
        
        # Update recommendations
        self.recommendations = new_recommendations
    
    def get_setups(
        self,
        exchange: Optional[str] = None,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        min_quality: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Get detected setups with optional filtering.
        
        Args:
            exchange: Filter by exchange
            symbol: Filter by symbol
            timeframe: Filter by timeframe
            min_quality: Filter by minimum setup quality
            
        Returns:
            List of detected setups
        """
        filtered_setups = []
        
        for ex, exchange_setups in self.detected_setups.items():
            if exchange and ex != exchange:
                continue
            
            for sym, symbol_setups in exchange_setups.items():
                if symbol and sym != symbol:
                    continue
                
                for tf, setups in symbol_setups.items():
                    if timeframe and tf != timeframe:
                        continue
                    
                    for setup in setups:
                        if min_quality and setup.get("quality", 0) < min_quality:
                            continue
                        
                        filtered_setups.append(setup)
        
        return filtered_setups
    
    def get_recommendations(
        self,
        exchange: Optional[str] = None,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        strategy_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get strategy recommendations with optional filtering.
        
        Args:
            exchange: Filter by exchange
            symbol: Filter by symbol
            timeframe: Filter by timeframe
            strategy_type: Filter by strategy type
            
        Returns:
            List of strategy recommendations
        """
        filtered_recommendations = []
        
        for ex, exchange_recommendations in self.recommendations.items():
            if exchange and ex != exchange:
                continue
            
            for sym, symbol_recommendations in exchange_recommendations.items():
                if symbol and sym != symbol:
                    continue
                
                for tf, recommendations in symbol_recommendations.items():
                    if timeframe and tf != timeframe:
                        continue
                    
                    for recommendation_data in recommendations:
                        recommendation = recommendation_data.get("recommendation", {})
                        if strategy_type and recommendation.get("strategy_type") != strategy_type:
                            continue
                        
                        filtered_recommendations.append(recommendation_data)
        
        return filtered_recommendations
    
    def assess_trade_risk(
        self,
        setup_id: str,
        recommendation_id: Optional[str] = None,
        portfolio_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Assess the risk of a potential trade.
        
        Args:
            setup_id: ID of the detected setup
            recommendation_id: ID of the strategy recommendation (optional)
            portfolio_state: Current portfolio state (optional)
            
        Returns:
            Dict with risk assessment results
        """
        # Find the setup
        setup = None
        recommendation = None
        
        for exchange, exchange_setups in self.detected_setups.items():
            for symbol, symbol_setups in exchange_setups.items():
                for timeframe, setups in symbol_setups.items():
                    for s in setups:
                        if s.get("id") == setup_id:
                            setup = s
                            
                            # Find the recommendation if ID is provided
                            if recommendation_id and exchange in self.recommendations:
                                if symbol in self.recommendations[exchange]:
                                    if timeframe in self.recommendations[exchange][symbol]:
                                        for r in self.recommendations[exchange][symbol][timeframe]:
                                            if r.get("recommendation", {}).get("id") == recommendation_id:
                                                recommendation = r.get("recommendation")
                                                break
                            
                            # If no recommendation ID provided or not found, use the first one for this setup
                            if not recommendation and exchange in self.recommendations:
                                if symbol in self.recommendations[exchange]:
                                    if timeframe in self.recommendations[exchange][symbol]:
                                        for r in self.recommendations[exchange][symbol][timeframe]:
                                            if r.get("setup", {}).get("id") == setup_id:
                                                recommendation = r.get("recommendation")
                                                break
                            
                            break
        
        if not setup:
            self.logger.error(f"Setup with ID {setup_id} not found")
            return {"error": "Setup not found"}
        
        if not recommendation:
            self.logger.warning(f"No recommendation found for setup {setup_id}, generating default")
            recommendation = self.strategy_recommender.recommend_strategy(setup=setup)
        
        # Get market conditions if available
        market_regime = None  # In a real implementation, this would come from market analysis
        volatility_regime = None
        liquidity_regime = None
        
        # Assess risk
        risk_assessment = self.decision_support.assess_trade_risk(
            setup=setup,
            recommendation=recommendation,
            portfolio_state=portfolio_state,
            market_regime=market_regime,
            volatility_regime=volatility_regime,
            liquidity_regime=liquidity_regime
        )
        
        return risk_assessment
    
    def generate_trade_checklist(
        self,
        setup_id: str,
        recommendation_id: Optional[str] = None,
        risk_assessment: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate a checklist for validating a trade before execution.
        
        Args:
            setup_id: ID of the detected setup
            recommendation_id: ID of the strategy recommendation (optional)
            risk_assessment: Risk assessment results (optional)
            
        Returns:
            List of checklist items
        """
        # Find the setup and recommendation (similar to assess_trade_risk)
        setup = None
        recommendation = None
        
        for exchange, exchange_setups in self.detected_setups.items():
            for symbol, symbol_setups in exchange_setups.items():
                for timeframe, setups in symbol_setups.items():
                    for s in setups:
                        if s.get("id") == setup_id:
                            setup = s
                            
                            # Find the recommendation if ID is provided
                            if recommendation_id and exchange in self.recommendations:
                                if symbol in self.recommendations[exchange]:
                                    if timeframe in self.recommendations[exchange][symbol]:
                                        for r in self.recommendations[exchange][symbol][timeframe]:
                                            if r.get("recommendation", {}).get("id") == recommendation_id:
                                                recommendation = r.get("recommendation")
                                                break
                            
                            # If no recommendation ID provided or not found, use the first one for this setup
                            if not recommendation and exchange in self.recommendations:
                                if symbol in self.recommendations[exchange]:
                                    if timeframe in self.recommendations[exchange][symbol]:
                                        for r in self.recommendations[exchange][symbol][timeframe]:
                                            if r.get("setup", {}).get("id") == setup_id:
                                                recommendation = r.get("recommendation")
                                                break
                            
                            break
        
        if not setup:
            self.logger.error(f"Setup with ID {setup_id} not found")
            return []
        
        if not recommendation:
            self.logger.warning(f"No recommendation found for setup {setup_id}, generating default")
            recommendation = self.strategy_recommender.recommend_strategy(setup=setup)
        
        # If risk assessment not provided, generate it
        if not risk_assessment:
            risk_assessment = self.assess_trade_risk(setup_id, recommendation_id)
        
        # Get market conditions if available
        market_regime = None  # In a real implementation, this would come from market analysis
        
        # Generate checklist
        checklist = self.decision_support.generate_trade_checklist(
            setup=setup,
            recommendation=recommendation,
            risk_assessment=risk_assessment,
            market_regime=market_regime
        )
        
        return checklist
    
    def model_scenarios(
        self,
        setup_id: str,
        recommendation_id: Optional[str] = None,
        current_price: Optional[float] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Model different scenarios for a potential trade.
        
        Args:
            setup_id: ID of the detected setup
            recommendation_id: ID of the strategy recommendation (optional)
            current_price: Current price of the asset (optional)
            
        Returns:
            Dict with modeled scenarios
        """
        # Find the setup and recommendation (similar to previous methods)
        setup = None
        recommendation = None
        
        for exchange, exchange_setups in self.detected_setups.items():
            for symbol, symbol_setups in exchange_setups.items():
                for timeframe, setups in symbol_setups.items():
                    for s in setups:
                        if s.get("id") == setup_id:
                            setup = s
                            
                            # Get current price if not provided
                            if not current_price and exchange in self.market_data:
                                if symbol in self.market_data[exchange]:
                                    if "1m" in self.market_data[exchange][symbol]:
                                        df = self.market_data[exchange][symbol]["1m"]
                                        if not df.empty:
                                            current_price = df.iloc[-1]["close"]
                            
                            # Find the recommendation if ID is provided
                            if recommendation_id and exchange in self.recommendations:
                                if symbol in self.recommendations[exchange]:
                                    if timeframe in self.recommendations[exchange][symbol]:
                                        for r in self.recommendations[exchange][symbol][timeframe]:
                                            if r.get("recommendation", {}).get("id") == recommendation_id:
                                                recommendation = r.get("recommendation")
                                                break
                            
                            # If no recommendation ID provided or not found, use the first one for this setup
                            if not recommendation and exchange in self.recommendations:
                                if symbol in self.recommendations[exchange]:
                                    if timeframe in self.recommendations[exchange][symbol]:
                                        for r in self.recommendations[exchange][symbol][timeframe]:
                                            if r.get("setup", {}).get("id") == setup_id:
                                                recommendation = r.get("recommendation")
                                                break
                            
                            break
        
        if not setup:
            self.logger.error(f"Setup with ID {setup_id} not found")
            return {}
        
        if not recommendation:
            self.logger.warning(f"No recommendation found for setup {setup_id}, generating default")
            recommendation = self.strategy_recommender.recommend_strategy(setup=setup)
        
        if not current_price:
            self.logger.warning(f"No current price available for setup {setup_id}, using placeholder")
            current_price = 100.0  # Placeholder
        
        # Model scenarios
        scenarios = self.decision_support.model_scenarios(
            setup=setup,
            recommendation=recommendation,
            current_price=current_price
        )
        
        return scenarios
    
    def analyze_performance(
        self,
        trades: List[Dict[str, Any]],
        market_regimes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze trading performance and generate comprehensive metrics.
        
        Args:
            trades: List of completed trades
            market_regimes: Market regime data for the trade periods
            
        Returns:
            Dict with performance analysis
        """
        # Convert trades to DataFrame
        if not trades:
            return {"error": "No trades provided for analysis"}
        
        try:
            trades_df = pd.DataFrame(trades)
            
            # Convert market regimes to DataFrame if provided
            market_regimes_df = None
            if market_regimes:
                market_regimes_df = pd.DataFrame(market_regimes)
            
            # Analyze performance
            analysis = self.performance_analyzer.analyze_performance(
                trades=trades_df,
                market_regimes=market_regimes_df
            )
            
            return analysis
        except Exception as e:
            self.logger.error(f"Error analyzing performance: {e}")
            return {"error": f"Error analyzing performance: {str(e)}"}
    
    def register_setup_callback(
        self,
        callback: callable
    ) -> None:
        """
        Register a callback for new setup detections.
        
        Args:
            callback: Function to call when new setups are detected
        """
        self.setup_callbacks.append(callback)
        self.logger.info(f"Registered setup callback: {callback.__name__}")
    
    def register_recommendation_callback(
        self,
        callback: callable
    ) -> None:
        """
        Register a callback for new strategy recommendations.
        
        Args:
            callback: Function to call when new recommendations are generated
        """
        self.recommendation_callbacks.append(callback)
        self.logger.info(f"Registered recommendation callback: {callback.__name__}")
    
    def create_trade_journal_entry(
        self,
        setup_id: str,
        recommendation_id: Optional[str] = None,
        execution_details: Dict[str, Any] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a structured trade journal entry for a trade.
        
        Args:
            setup_id: ID of the detected setup
            recommendation_id: ID of the strategy recommendation (optional)
            execution_details: Details of trade execution
            notes: Additional notes from the trader
            
        Returns:
            Dict with structured trade journal entry
        """
        # Find the setup and recommendation (similar to previous methods)
        setup = None
        recommendation = None
        
        for exchange, exchange_setups in self.detected_setups.items():
            for symbol, symbol_setups in exchange_setups.items():
                for timeframe, setups in symbol_setups.items():
                    for s in setups:
                        if s.get("id") == setup_id:
                            setup = s
                            
                            # Find the recommendation if ID is provided
                            if recommendation_id and exchange in self.recommendations:
                                if symbol in self.recommendations[exchange]:
                                    if timeframe in self.recommendations[exchange][symbol]:
                                        for r in self.recommendations[exchange][symbol][timeframe]:
                                            if r.get("recommendation", {}).get("id") == recommendation_id:
                                                recommendation = r.get("recommendation")
                                                break
                            
                            # If no recommendation ID provided or not found, use the first one for this setup
                            if not recommendation and exchange in self.recommendations:
                                if symbol in self.recommendations[exchange]:
                                    if timeframe in self.recommendations[exchange][symbol]:
                                        for r in self.recommendations[exchange][symbol][timeframe]:
                                            if r.get("setup", {}).get("id") == setup_id:
                                                recommendation = r.get("recommendation")
                                                break
                            
                            break
        
        if not setup:
            self.logger.error(f"Setup with ID {setup_id} not found")
            return {"error": "Setup not found"}
        
        if not recommendation:
            self.logger.warning(f"No recommendation found for setup {setup_id}, generating default")
            recommendation = self.strategy_recommender.recommend_strategy(setup=setup)
        
        # Assess risk
        risk_assessment = self.assess_trade_risk(setup_id, recommendation_id)
        
        # Get market conditions if available
        market_conditions = {
            "market_regime": risk_assessment.get("market_regime", "unknown"),
            "volatility_regime": risk_assessment.get("volatility_regime", "unknown"),
            "liquidity_regime": risk_assessment.get("liquidity_regime", "unknown")
        }
        
        # Create journal entry
        journal_entry = self.decision_support.create_trade_journal_entry(
            setup=setup,
            recommendation=recommendation,
            risk_assessment=risk_assessment,
            execution_details=execution_details or {},
            market_conditions=market_conditions,
            notes=notes
        )
        
        return journal_entry 