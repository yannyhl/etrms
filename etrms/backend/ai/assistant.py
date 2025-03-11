"""
Enhanced Trading Risk Management System AI Assistant

This module implements the AI-powered trading assistant using Anthropic's Claude API.
"""
import asyncio
import json
import os
import time
from typing import Dict, Any, List, Optional, Tuple

import anthropic
from utils.logger import get_logger, log_event
from config.settings import settings


class Assistant:
    """
    AI-powered trading assistant that provides risk analysis and trading recommendations.
    
    This class uses Anthropic's Claude model to analyze trading positions, provide risk
    assessments, and offer trading recommendations.
    """
    
    # System prompt template
    SYSTEM_PROMPT = """
    You are an expert trading risk management assistant for the Enhanced Trading Risk Management System (ETRMS).
    
    Your purpose is to help traders analyze their positions, evaluate risk, optimize position sizing, and make informed trading decisions.
    You have access to real-time trading data, including account balances, positions, and market conditions.
    
    In your responses, you should:
    1. Analyze the trader's positions and risk exposure
    2. Provide data-driven recommendations
    3. Suggest risk mitigation strategies when appropriate
    4. Present information in a clear, structured format
    5. Use quantitative analysis to support your recommendations
    
    The trader's current portfolio information:
    {portfolio_info}
    
    Current market conditions:
    {market_conditions}
    
    Risk parameters:
    {risk_parameters}
    
    Please provide concise, actionable insights based on this information.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-opus-20240229"):
        """
        Initialize the AI assistant.
        
        Args:
            api_key: Anthropic API key. If not provided, uses settings.ANTHROPIC_API_KEY.
            model: The Claude model to use. Defaults to "claude-3-opus-20240229".
        """
        self.logger = get_logger(__name__)
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        log_event(
            self.logger,
            "AI_ASSISTANT_INIT",
            "AI Assistant initialized",
            context={"model": model}
        )
    
    async def chat(self, message: str, portfolio_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a chat message and return a response.
        
        Args:
            message: The user's message.
            portfolio_info: Optional portfolio information to include in the context.
            
        Returns:
            The assistant's response.
        """
        try:
            # Get portfolio info if not provided
            if portfolio_info is None:
                portfolio_info = self._get_default_portfolio_info()
            
            # Get market conditions
            market_conditions = self._get_market_conditions()
            
            # Get risk parameters
            risk_parameters = self._get_risk_parameters()
            
            # Format the system prompt
            system_prompt = self.SYSTEM_PROMPT.format(
                portfolio_info=json.dumps(portfolio_info, indent=2),
                market_conditions=json.dumps(market_conditions, indent=2),
                risk_parameters=json.dumps(risk_parameters, indent=2)
            )
            
            # Create the chat completion
            response = self.client.messages.create(
                model=self.model,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": message}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            log_event(
                self.logger,
                "AI_ASSISTANT_CHAT",
                "Generated response",
                context={"user_message": message[:100] + "..." if len(message) > 100 else message}
            )
            
            return response.content[0].text
        except Exception as e:
            log_event(
                self.logger,
                "AI_ASSISTANT_ERROR",
                f"Error processing chat message: {str(e)}",
                level="ERROR",
                context={"message": message}
            )
            return f"I apologize, but I'm currently unable to process your request due to an error: {str(e)}"
    
    async def analyze_position(self, symbol: str, exchange: str) -> Dict[str, Any]:
        """
        Analyze a specific trading position.
        
        Args:
            symbol: The trading pair symbol.
            exchange: The exchange name.
            
        Returns:
            Dict containing analysis and recommendations.
        """
        try:
            # Get position information
            position = self._get_position_info(symbol, exchange)
            if not position:
                return {
                    "error": f"No position found for {symbol} on {exchange}",
                    "status": "not_found"
                }
            
            # Create the prompt
            prompt = f"""
            Please analyze the following trading position:
            
            Symbol: {symbol}
            Exchange: {exchange}
            Side: {position.get('side', 'unknown')}
            Entry Price: {position.get('entry_price', 0)}
            Mark Price: {position.get('mark_price', 0)}
            Position Size: {position.get('position_amt', 0)}
            Unrealized PnL: {position.get('unrealized_pnl', 0)}
            
            Provide a risk analysis and recommendations.
            Format your response as JSON with the following fields:
            - risk_rating: A number from 1-10 (10 being highest risk)
            - analysis: A brief textual analysis of the position
            - recommendation: A specific recommendation
            - stop_loss: A recommended stop loss price
            - take_profit: A recommended take profit price
            """
            
            # Create the chat completion
            response = self.client.messages.create(
                model=self.model,
                system="You are an expert trading risk analyst. You provide JSON-formatted responses only.",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.2
            )
            
            # Extract and parse the JSON response
            response_text = response.content[0].text
            
            # Find the JSON part of the response (in case there's other text)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                analysis = json.loads(json_str)
            else:
                # Fallback if JSON parsing fails
                analysis = {
                    "risk_rating": 5,
                    "analysis": "Could not generate structured analysis. Please see full response.",
                    "recommendation": "Consider reviewing the position manually.",
                    "stop_loss": position.get('entry_price', 0) * 0.95 if position.get('side') == 'long' else position.get('entry_price', 0) * 1.05,
                    "take_profit": position.get('entry_price', 0) * 1.1 if position.get('side') == 'long' else position.get('entry_price', 0) * 0.9,
                    "full_response": response_text
                }
            
            log_event(
                self.logger,
                "AI_POSITION_ANALYSIS",
                f"Analyzed position {symbol} on {exchange}",
                context={"symbol": symbol, "exchange": exchange, "risk_rating": analysis.get("risk_rating", "unknown")}
            )
            
            return analysis
        except Exception as e:
            log_event(
                self.logger,
                "AI_ASSISTANT_ERROR",
                f"Error analyzing position: {str(e)}",
                level="ERROR",
                context={"symbol": symbol, "exchange": exchange}
            )
            return {
                "error": f"Error analyzing position: {str(e)}",
                "status": "error"
            }
    
    async def get_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get AI-generated trading recommendations.
        
        Returns:
            List of dicts containing trading recommendations.
        """
        try:
            # Get portfolio info
            portfolio_info = self._get_default_portfolio_info()
            
            # Create the prompt
            prompt = f"""
            Based on the following portfolio information and current market conditions,
            provide 3-5 trading recommendations:
            
            Portfolio Information:
            {json.dumps(portfolio_info, indent=2)}
            
            Market Conditions:
            {json.dumps(self._get_market_conditions(), indent=2)}
            
            Format your response as a JSON array of recommendations, where each recommendation has:
            - symbol: The trading pair
            - action: "BUY", "SELL", "HOLD", or "REDUCE"
            - reason: A brief explanation
            - confidence: A number from 1-10
            - target_price: A price target (if applicable)
            - time_frame: "short_term", "medium_term", or "long_term"
            """
            
            # Create the chat completion
            response = self.client.messages.create(
                model=self.model,
                system="You are an expert trading advisor. You provide JSON-formatted responses only.",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            # Extract and parse the JSON response
            response_text = response.content[0].text
            
            # Find the JSON array part of the response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                recommendations = json.loads(json_str)
            else:
                # Fallback if JSON parsing fails
                recommendations = [
                    {
                        "symbol": "BTCUSDT",
                        "action": "HOLD",
                        "reason": "Could not generate structured recommendations. Please try again later.",
                        "confidence": 5,
                        "target_price": None,
                        "time_frame": "medium_term"
                    }
                ]
            
            log_event(
                self.logger,
                "AI_RECOMMENDATIONS",
                f"Generated {len(recommendations)} trading recommendations",
                context={"recommendation_count": len(recommendations)}
            )
            
            return recommendations
        except Exception as e:
            log_event(
                self.logger,
                "AI_ASSISTANT_ERROR",
                f"Error generating recommendations: {str(e)}",
                level="ERROR"
            )
            return [
                {
                    "symbol": "ERROR",
                    "action": "NONE",
                    "reason": f"Error generating recommendations: {str(e)}",
                    "confidence": 0,
                    "target_price": None,
                    "time_frame": "none"
                }
            ]
    
    def _get_default_portfolio_info(self) -> Dict[str, Any]:
        """
        Get default portfolio information for the AI assistant.
        
        In a real implementation, this would fetch live data from the risk monitor.
        
        Returns:
            Dict containing portfolio information.
        """
        # This is mock data for demonstration
        return {
            "total_equity": 125000,
            "available_balance": 75000,
            "unrealized_pnl": 5000,
            "positions": [
                {
                    "symbol": "BTCUSDT",
                    "exchange": "binance",
                    "side": "long",
                    "entry_price": 40000,
                    "mark_price": 42000,
                    "position_amt": 0.75,
                    "leverage": 5,
                    "unrealized_pnl": 1500,
                    "liquidation_price": 35200
                },
                {
                    "symbol": "ETHUSDT",
                    "exchange": "hyperliquid",
                    "side": "long",
                    "entry_price": 2500,
                    "mark_price": 2600,
                    "position_amt": 8,
                    "leverage": 3,
                    "unrealized_pnl": 800,
                    "liquidation_price": 2100
                }
            ]
        }
    
    def _get_market_conditions(self) -> Dict[str, Any]:
        """
        Get current market conditions for the AI assistant.
        
        In a real implementation, this would fetch live market data.
        
        Returns:
            Dict containing market conditions.
        """
        # Mock data for demonstration
        return {
            "btc_price": 42000,
            "eth_price": 2600,
            "btc_24h_change": 2.5,
            "eth_24h_change": 3.2,
            "btc_volatility": 3.5,
            "market_sentiment": "bullish",
            "funding_rates": {
                "BTCUSDT": 0.01,
                "ETHUSDT": 0.015
            },
            "major_events": [
                "Federal Reserve meeting scheduled in 2 days",
                "Recent Bitcoin ETF inflows increased by 15%"
            ]
        }
    
    def _get_risk_parameters(self) -> Dict[str, Any]:
        """
        Get risk parameters for the AI assistant.
        
        In a real implementation, this would fetch from the risk configuration.
        
        Returns:
            Dict containing risk parameters.
        """
        # Mock data for demonstration
        return {
            "max_position_size_pct": 10,  # Max position size as percentage of portfolio
            "max_leverage": 10,  # Maximum allowed leverage
            "risk_per_trade_pct": 2,  # Maximum risk per trade as percentage of portfolio
            "max_drawdown_pct": 15,  # Maximum acceptable drawdown
            "position_correlation_limit": 0.8  # Maximum correlation between positions
        }
    
    def _get_position_info(self, symbol: str, exchange: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific position.
        
        In a real implementation, this would fetch from the risk monitor.
        
        Args:
            symbol: The trading pair symbol.
            exchange: The exchange name.
            
        Returns:
            Dict containing position information or None if position not found.
        """
        # Mock data for demonstration
        positions = {
            "BTCUSDT_binance": {
                "symbol": "BTCUSDT",
                "exchange": "binance",
                "side": "long",
                "entry_price": 40000,
                "mark_price": 42000,
                "position_amt": 0.75,
                "leverage": 5,
                "unrealized_pnl": 1500,
                "liquidation_price": 35200
            },
            "ETHUSDT_hyperliquid": {
                "symbol": "ETHUSDT",
                "exchange": "hyperliquid",
                "side": "long",
                "entry_price": 2500,
                "mark_price": 2600,
                "position_amt": 8,
                "leverage": 3,
                "unrealized_pnl": 800,
                "liquidation_price": 2100
            }
        }
        
        position_key = f"{symbol}_{exchange}"
        return positions.get(position_key) 