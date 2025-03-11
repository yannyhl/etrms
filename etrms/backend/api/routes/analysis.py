"""
Enhanced Trading Risk Management System - Market Analysis API Routes

This module provides API endpoints for accessing market analysis data.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status
from pydantic import BaseModel

from services.market_analysis_service import MarketAnalysisService
from api.dependencies import get_market_analysis_service, get_current_user
from data.models.user import User


router = APIRouter(prefix="/analysis", tags=["analysis"])


class MarketRegimeResponse(BaseModel):
    """Response model for market regime data"""
    exchange: str
    symbol: str
    market_regime: str
    volatility_regime: str
    liquidity_regime: str
    timestamp: str


class TradingRecommendationResponse(BaseModel):
    """Response model for trading recommendations"""
    exchange: str
    symbol: str
    position_sizing: str
    risk_adjustment: float
    strategy_type: str
    notes: List[str]
    timestamp: str


class CorrelationResponse(BaseModel):
    """Response model for correlation data"""
    exchange: str
    correlation_regime: str
    diversification_score: float
    timestamp: str


@router.get("/market-regimes", response_model=List[MarketRegimeResponse])
async def get_market_regimes(
    exchange: Optional[str] = None,
    symbol: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    market_analysis_service: MarketAnalysisService = Depends(get_market_analysis_service)
):
    """
    Get current market regimes for all or specific exchanges and symbols.
    
    Args:
        exchange: Optional exchange name to filter by
        symbol: Optional symbol to filter by
        
    Returns:
        List of market regime data
    """
    analysis = market_analysis_service.get_market_analysis(exchange, symbol)
    
    if not analysis:
        return []
    
    result = []
    
    # Process the analysis data
    if exchange and symbol:
        # Single exchange and symbol
        if analysis:
            result.append({
                "exchange": exchange,
                "symbol": symbol,
                "market_regime": analysis.get("market_regime", "unknown"),
                "volatility_regime": analysis.get("volatility_regime", "normal"),
                "liquidity_regime": analysis.get("liquidity_regime", "medium"),
                "timestamp": analysis.get("timestamp", "").isoformat() if analysis.get("timestamp") else ""
            })
    elif exchange:
        # Single exchange, all symbols
        for symbol, symbol_analysis in analysis.items():
            if symbol != "correlation" and isinstance(symbol_analysis, dict):
                result.append({
                    "exchange": exchange,
                    "symbol": symbol,
                    "market_regime": symbol_analysis.get("market_regime", "unknown"),
                    "volatility_regime": symbol_analysis.get("volatility_regime", "normal"),
                    "liquidity_regime": symbol_analysis.get("liquidity_regime", "medium"),
                    "timestamp": symbol_analysis.get("timestamp", "").isoformat() if symbol_analysis.get("timestamp") else ""
                })
    else:
        # All exchanges and symbols
        for exchange_name, exchange_analysis in analysis.items():
            for symbol, symbol_analysis in exchange_analysis.items():
                if symbol != "correlation" and isinstance(symbol_analysis, dict):
                    result.append({
                        "exchange": exchange_name,
                        "symbol": symbol,
                        "market_regime": symbol_analysis.get("market_regime", "unknown"),
                        "volatility_regime": symbol_analysis.get("volatility_regime", "normal"),
                        "liquidity_regime": symbol_analysis.get("liquidity_regime", "medium"),
                        "timestamp": symbol_analysis.get("timestamp", "").isoformat() if symbol_analysis.get("timestamp") else ""
                    })
    
    return result


@router.get("/trading-recommendations", response_model=List[TradingRecommendationResponse])
async def get_trading_recommendations(
    exchange: Optional[str] = None,
    symbol: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    market_analysis_service: MarketAnalysisService = Depends(get_market_analysis_service)
):
    """
    Get trading recommendations for all or specific exchanges and symbols.
    
    Args:
        exchange: Optional exchange name to filter by
        symbol: Optional symbol to filter by
        
    Returns:
        List of trading recommendations
    """
    analysis = market_analysis_service.get_market_analysis(exchange, symbol)
    
    if not analysis:
        return []
    
    result = []
    
    # Process the analysis data
    if exchange and symbol:
        # Single exchange and symbol
        if analysis:
            recommendations = analysis.get("trading_recommendations", {})
            result.append({
                "exchange": exchange,
                "symbol": symbol,
                "position_sizing": recommendations.get("position_sizing", "normal"),
                "risk_adjustment": recommendations.get("risk_adjustment", 1.0),
                "strategy_type": recommendations.get("strategy_type", "neutral"),
                "notes": recommendations.get("notes", []),
                "timestamp": analysis.get("timestamp", "").isoformat() if analysis.get("timestamp") else ""
            })
    elif exchange:
        # Single exchange, all symbols
        for symbol, symbol_analysis in analysis.items():
            if symbol != "correlation" and isinstance(symbol_analysis, dict):
                recommendations = symbol_analysis.get("trading_recommendations", {})
                result.append({
                    "exchange": exchange,
                    "symbol": symbol,
                    "position_sizing": recommendations.get("position_sizing", "normal"),
                    "risk_adjustment": recommendations.get("risk_adjustment", 1.0),
                    "strategy_type": recommendations.get("strategy_type", "neutral"),
                    "notes": recommendations.get("notes", []),
                    "timestamp": symbol_analysis.get("timestamp", "").isoformat() if symbol_analysis.get("timestamp") else ""
                })
    else:
        # All exchanges and symbols
        for exchange_name, exchange_analysis in analysis.items():
            for symbol, symbol_analysis in exchange_analysis.items():
                if symbol != "correlation" and isinstance(symbol_analysis, dict):
                    recommendations = symbol_analysis.get("trading_recommendations", {})
                    result.append({
                        "exchange": exchange_name,
                        "symbol": symbol,
                        "position_sizing": recommendations.get("position_sizing", "normal"),
                        "risk_adjustment": recommendations.get("risk_adjustment", 1.0),
                        "strategy_type": recommendations.get("strategy_type", "neutral"),
                        "notes": recommendations.get("notes", []),
                        "timestamp": symbol_analysis.get("timestamp", "").isoformat() if symbol_analysis.get("timestamp") else ""
                    })
    
    return result


@router.get("/correlations", response_model=List[CorrelationResponse])
async def get_correlations(
    exchange: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    market_analysis_service: MarketAnalysisService = Depends(get_market_analysis_service)
):
    """
    Get correlation data for all or specific exchanges.
    
    Args:
        exchange: Optional exchange name to filter by
        
    Returns:
        List of correlation data
    """
    analysis = market_analysis_service.get_market_analysis(exchange)
    
    if not analysis:
        return []
    
    result = []
    
    # Process the analysis data
    if exchange:
        # Single exchange
        correlation_data = analysis.get("correlation", {})
        if correlation_data:
            result.append({
                "exchange": exchange,
                "correlation_regime": correlation_data.get("correlation_regime", "normal"),
                "diversification_score": correlation_data.get("diversification_score", 0.5),
                "timestamp": correlation_data.get("timestamp", "").isoformat() if correlation_data.get("timestamp") else ""
            })
    else:
        # All exchanges
        for exchange_name, exchange_analysis in analysis.items():
            correlation_data = exchange_analysis.get("correlation", {})
            if correlation_data:
                result.append({
                    "exchange": exchange_name,
                    "correlation_regime": correlation_data.get("correlation_regime", "normal"),
                    "diversification_score": correlation_data.get("diversification_score", 0.5),
                    "timestamp": correlation_data.get("timestamp", "").isoformat() if correlation_data.get("timestamp") else ""
                })
    
    return result


@router.get("/correlation-matrix/{exchange}")
async def get_correlation_matrix(
    exchange: str = Path(..., title="Exchange name"),
    current_user: User = Depends(get_current_user),
    market_analysis_service: MarketAnalysisService = Depends(get_market_analysis_service)
):
    """
    Get the correlation matrix for a specific exchange.
    
    Args:
        exchange: Exchange name
        
    Returns:
        Correlation matrix data
    """
    analysis = market_analysis_service.get_market_analysis(exchange)
    
    if not analysis or "correlation" not in analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Correlation data not found for exchange: {exchange}"
        )
    
    correlation_data = analysis["correlation"]
    
    return {
        "exchange": exchange,
        "correlation_matrix": correlation_data.get("correlation_matrix", {}),
        "timestamp": correlation_data.get("timestamp", "").isoformat() if correlation_data.get("timestamp") else ""
    }


@router.get("/liquidity-metrics/{exchange}/{symbol}")
async def get_liquidity_metrics(
    exchange: str = Path(..., title="Exchange name"),
    symbol: str = Path(..., title="Symbol"),
    current_user: User = Depends(get_current_user),
    market_analysis_service: MarketAnalysisService = Depends(get_market_analysis_service)
):
    """
    Get detailed liquidity metrics for a specific symbol.
    
    Args:
        exchange: Exchange name
        symbol: Symbol
        
    Returns:
        Liquidity metrics data
    """
    analysis = market_analysis_service.get_market_analysis(exchange, symbol)
    
    if not analysis or "liquidity_metrics" not in analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Liquidity metrics not found for {exchange}/{symbol}"
        )
    
    liquidity_metrics = analysis["liquidity_metrics"]
    
    return {
        "exchange": exchange,
        "symbol": symbol,
        "liquidity_metrics": liquidity_metrics,
        "timestamp": analysis.get("timestamp", "").isoformat() if analysis.get("timestamp") else ""
    }


@router.get("/volatility/{exchange}/{symbol}")
async def get_volatility(
    exchange: str = Path(..., title="Exchange name"),
    symbol: str = Path(..., title="Symbol"),
    model: Optional[str] = Query("historical", title="Volatility model"),
    current_user: User = Depends(get_current_user),
    market_analysis_service: MarketAnalysisService = Depends(get_market_analysis_service)
):
    """
    Get volatility data for a specific symbol.
    
    Args:
        exchange: Exchange name
        symbol: Symbol
        model: Volatility model to use
        
    Returns:
        Volatility data
    """
    analysis = market_analysis_service.get_market_analysis(exchange, symbol)
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis data not found for {exchange}/{symbol}"
        )
    
    # Get historical data
    historical_data = market_analysis_service.historical_data.get(exchange, {}).get(symbol)
    
    if historical_data is None or historical_data.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Historical data not found for {exchange}/{symbol}"
        )
    
    # Calculate volatility using the specified model
    volatility = market_analysis_service.volatility_analyzer.calculate_historical_volatility(
        historical_data,
        model=model
    )
    
    # Calculate volatility surface
    volatility_surface = market_analysis_service.volatility_analyzer.calculate_volatility_surface(
        historical_data
    )
    
    return {
        "exchange": exchange,
        "symbol": symbol,
        "volatility": volatility,
        "volatility_regime": analysis.get("volatility_regime", "normal"),
        "volatility_surface": volatility_surface,
        "timestamp": analysis.get("timestamp", "").isoformat() if analysis.get("timestamp") else ""
    } 