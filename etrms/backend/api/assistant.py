"""
Enhanced Trading Risk Management System AI Assistant API

This module provides endpoints for interacting with the AI assistant.
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Path, Query

from ai import Assistant
from utils.logger import get_logger, log_event

# Create a router instance
router = APIRouter()

# Create an AI assistant instance
assistant = Assistant()


async def get_assistant():
    """
    Dependency to get the AI assistant instance.
    
    Returns:
        The AI assistant instance.
    """
    return assistant


@router.post("/chat", summary="Chat with the AI assistant")
async def chat_with_assistant(
    message: str = Body(..., description="The user's message", embed=True),
    assistant: Assistant = Depends(get_assistant)
) -> Dict[str, Any]:
    """
    Send a message to the AI assistant and get a response.
    
    Args:
        message: The user's message.
        
    Returns:
        Dict containing the assistant's response.
    """
    try:
        response = await assistant.chat(message)
        return {
            "response": response
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat message: {str(e)}"
        )


@router.get("/analysis/{exchange}/{symbol}", summary="Get AI analysis for a position")
async def get_position_analysis(
    exchange: str = Path(..., description="Exchange name (e.g., 'binance', 'hyperliquid')"),
    symbol: str = Path(..., description="Symbol (e.g., 'BTCUSDT')"),
    assistant: Assistant = Depends(get_assistant)
) -> Dict[str, Any]:
    """
    Get AI analysis for a specific position.
    
    Args:
        exchange: The exchange name.
        symbol: The symbol.
        
    Returns:
        Dict containing position analysis.
    """
    try:
        analysis = await assistant.analyze_position(symbol, exchange)
        
        if "error" in analysis:
            raise HTTPException(
                status_code=404 if analysis.get("status") == "not_found" else 500,
                detail=analysis["error"]
            )
        
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing position: {str(e)}"
        )


@router.get("/recommendations", summary="Get AI-generated trading recommendations")
async def get_recommendations(
    count: Optional[int] = Query(3, description="Number of recommendations to return", ge=1, le=10),
    assistant: Assistant = Depends(get_assistant)
) -> Dict[str, Any]:
    """
    Get AI-generated trading recommendations.
    
    Args:
        count: Number of recommendations to return.
        
    Returns:
        Dict containing trading recommendations.
    """
    try:
        recommendations = await assistant.get_recommendations()
        
        # Limit the number of recommendations to the requested count
        limited_recommendations = recommendations[:count]
        
        return {
            "recommendations": limited_recommendations
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating recommendations: {str(e)}"
        ) 