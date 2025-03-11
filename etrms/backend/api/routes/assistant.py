"""
API routes for the AI Trading Assistant.

This module provides API endpoints for accessing the AI Trading Assistant functionality,
including setup detection, strategy recommendations, and decision support.
"""

from fastapi import APIRouter, Depends, Path, Query, HTTPException, Body
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from datetime import datetime

from ...services.ai_assistant_service import AIAssistantService
from ..dependencies import get_ai_assistant_service, get_current_user
from ...data.models.user import User

router = APIRouter(prefix="/assistant", tags=["assistant"])


class SetupResponse(BaseModel):
    """Response model for trading setup data"""
    id: str
    type: str
    quality: float
    exchange: str
    symbol: str
    timeframe: str
    detection_time: str
    market_regime: Optional[str] = None


class RecommendationResponse(BaseModel):
    """Response model for strategy recommendation data"""
    id: str
    strategy_type: str
    position_sizing: str
    risk_percent: float
    order_type: str
    entry_zone: Dict[str, float]
    stop_loss: float
    take_profit: float
    risk_reward: float
    setup_quality: float
    notes: List[str]
    timestamp: str
    setup_id: str
    exchange: str
    symbol: str
    timeframe: str


class RiskAssessmentResponse(BaseModel):
    """Response model for risk assessment data"""
    risk_score: float
    risk_level: str
    warnings: List[str]
    quality_factor: float
    risk_reward_factor: float
    position_sizing: str
    market_regime: Optional[str] = None
    volatility_regime: Optional[str] = None
    liquidity_regime: Optional[str] = None
    portfolio_adjustment: float
    timestamp: str


class ChecklistItemResponse(BaseModel):
    """Response model for checklist item data"""
    category: str
    question: str
    guidance: str
    auto_check: Optional[bool] = None
    importance: str


class ScenarioResponse(BaseModel):
    """Response model for scenario data"""
    type: str
    description: str
    entry_price: float
    exit_price: float
    stop_loss: float
    profit_loss_percent: float
    profit_loss_r: float
    probability: float
    normalized_probability: Optional[float] = None
    expected_value: Optional[float] = None
    time_to_completion: str
    notes: List[str]


class TradeJournalEntryResponse(BaseModel):
    """Response model for trade journal entry data"""
    id: str
    timestamp: str
    trade_details: Dict[str, Any]
    setup_details: Dict[str, Any]
    strategy_details: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    market_conditions: Dict[str, Any]
    trader_notes: Dict[str, Any]
    exit_details: Dict[str, Any]
    post_trade_analysis: Dict[str, Any]


class PortfolioStateModel(BaseModel):
    """Model for portfolio state data"""
    total_exposure: float
    average_correlation: float
    current_drawdown: float
    position_count: int
    largest_position_percent: float
    exchange_exposures: Dict[str, float]


class ExecutionDetailsModel(BaseModel):
    """Model for trade execution details"""
    entry_price: float
    entry_time: str
    position_size: float
    stop_loss: float
    take_profit: float
    direction: str
    risk_percent: float
    emotions: Optional[str] = None
    confidence_level: Optional[float] = None
    trade_plan_adherence: Optional[bool] = None


class ExitDetailsModel(BaseModel):
    """Model for trade exit details"""
    exit_price: float
    exit_time: str
    exit_reason: str


class PostTradeAnalysisModel(BaseModel):
    """Model for post-trade analysis data"""
    lessons_learned: List[str]
    improvement_areas: List[str]
    rating: int
    emotions: str
    notes: str


@router.get("/setups", response_model=List[SetupResponse])
async def get_setups(
    exchange: Optional[str] = None,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    min_quality: Optional[float] = Query(None, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    ai_assistant_service: AIAssistantService = Depends(get_ai_assistant_service)
):
    """
    Get detected trading setups with optional filtering.
    
    Args:
        exchange: Filter by exchange
        symbol: Filter by symbol
        timeframe: Filter by timeframe
        min_quality: Filter by minimum setup quality (0.0-1.0)
        
    Returns:
        List of detected setups
    """
    setups = ai_assistant_service.get_setups(
        exchange=exchange,
        symbol=symbol,
        timeframe=timeframe,
        min_quality=min_quality
    )
    
    return setups


@router.get("/recommendations", response_model=List[RecommendationResponse])
async def get_recommendations(
    exchange: Optional[str] = None,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    strategy_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    ai_assistant_service: AIAssistantService = Depends(get_ai_assistant_service)
):
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
    recommendations = ai_assistant_service.get_recommendations(
        exchange=exchange,
        symbol=symbol,
        timeframe=timeframe,
        strategy_type=strategy_type
    )
    
    return [rec["recommendation"] for rec in recommendations]


@router.post("/risk-assessment/{setup_id}", response_model=RiskAssessmentResponse)
async def assess_trade_risk(
    setup_id: str = Path(..., title="Setup ID"),
    recommendation_id: Optional[str] = Query(None, title="Recommendation ID"),
    portfolio_state: Optional[PortfolioStateModel] = Body(None),
    current_user: User = Depends(get_current_user),
    ai_assistant_service: AIAssistantService = Depends(get_ai_assistant_service)
):
    """
    Assess the risk of a potential trade.
    
    Args:
        setup_id: ID of the detected setup
        recommendation_id: ID of the strategy recommendation (optional)
        portfolio_state: Current portfolio state (optional)
        
    Returns:
        Risk assessment results
    """
    risk_assessment = ai_assistant_service.assess_trade_risk(
        setup_id=setup_id,
        recommendation_id=recommendation_id,
        portfolio_state=portfolio_state.dict() if portfolio_state else None
    )
    
    if "error" in risk_assessment:
        raise HTTPException(status_code=404, detail=risk_assessment["error"])
    
    return risk_assessment


@router.get("/checklist/{setup_id}", response_model=List[ChecklistItemResponse])
async def generate_trade_checklist(
    setup_id: str = Path(..., title="Setup ID"),
    recommendation_id: Optional[str] = Query(None, title="Recommendation ID"),
    current_user: User = Depends(get_current_user),
    ai_assistant_service: AIAssistantService = Depends(get_ai_assistant_service)
):
    """
    Generate a checklist for validating a trade before execution.
    
    Args:
        setup_id: ID of the detected setup
        recommendation_id: ID of the strategy recommendation (optional)
        
    Returns:
        List of checklist items
    """
    checklist = ai_assistant_service.generate_trade_checklist(
        setup_id=setup_id,
        recommendation_id=recommendation_id
    )
    
    if not checklist:
        raise HTTPException(status_code=404, detail="Setup not found")
    
    return checklist


@router.post("/scenarios/{setup_id}", response_model=Dict[str, ScenarioResponse])
async def model_scenarios(
    setup_id: str = Path(..., title="Setup ID"),
    recommendation_id: Optional[str] = Query(None, title="Recommendation ID"),
    current_price: Optional[float] = Query(None, title="Current price"),
    current_user: User = Depends(get_current_user),
    ai_assistant_service: AIAssistantService = Depends(get_ai_assistant_service)
):
    """
    Model different scenarios for a potential trade.
    
    Args:
        setup_id: ID of the detected setup
        recommendation_id: ID of the strategy recommendation (optional)
        current_price: Current price of the asset (optional)
        
    Returns:
        Dict with modeled scenarios
    """
    scenarios = ai_assistant_service.model_scenarios(
        setup_id=setup_id,
        recommendation_id=recommendation_id,
        current_price=current_price
    )
    
    if not scenarios:
        raise HTTPException(status_code=404, detail="Setup not found")
    
    return scenarios


@router.post("/journal-entry/{setup_id}", response_model=TradeJournalEntryResponse)
async def create_trade_journal_entry(
    setup_id: str = Path(..., title="Setup ID"),
    execution_details: ExecutionDetailsModel = Body(...),
    recommendation_id: Optional[str] = Query(None, title="Recommendation ID"),
    notes: Optional[str] = Query(None, title="Additional notes"),
    current_user: User = Depends(get_current_user),
    ai_assistant_service: AIAssistantService = Depends(get_ai_assistant_service)
):
    """
    Create a structured trade journal entry for a trade.
    
    Args:
        setup_id: ID of the detected setup
        execution_details: Details of trade execution
        recommendation_id: ID of the strategy recommendation (optional)
        notes: Additional notes from the trader
        
    Returns:
        Structured trade journal entry
    """
    journal_entry = ai_assistant_service.create_trade_journal_entry(
        setup_id=setup_id,
        recommendation_id=recommendation_id,
        execution_details=execution_details.dict(),
        notes=notes
    )
    
    if "error" in journal_entry:
        raise HTTPException(status_code=404, detail=journal_entry["error"])
    
    return journal_entry 