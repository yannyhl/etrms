"""
Enhanced Trading Risk Management System Risk Routes

This module provides API routes for risk management, including 
circuit breaker configuration and risk metrics.
"""
from typing import List, Dict, Any, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path

from auth.auth_service import get_current_user
from data.models.user import User
from data.models.circuit_breakers import CircuitBreaker
from data.repositories.circuit_breakers import CircuitBreakerRepository
from utils.logger import get_logger, log_event


router = APIRouter(prefix="/risk", tags=["Risk Management"])
logger = get_logger(__name__)


# Pydantic models for request/response validation
from pydantic import BaseModel, Field


class CircuitBreakerParameters(BaseModel):
    """Model for circuit breaker parameters."""
    threshold: float = Field(..., description="Threshold value for the condition")
    reduction_percentage: Optional[float] = Field(None, description="Percentage to reduce position by")
    close_all: Optional[bool] = Field(None, description="Whether to close all positions")


class CircuitBreakerCreate(BaseModel):
    """Model for creating a circuit breaker."""
    name: str = Field(..., description="Name of the circuit breaker")
    description: Optional[str] = Field(None, description="Description of the circuit breaker")
    condition: str = Field(..., description="Condition type (e.g., max_drawdown, max_position_size)")
    action: str = Field(..., description="Action to take when triggered (e.g., notify, close_position)")
    parameters: CircuitBreakerParameters = Field(..., description="Parameters for the condition and action")
    symbols: List[str] = Field(default=[], description="Symbols to apply the circuit breaker to")
    exchanges: List[str] = Field(default=[], description="Exchanges to apply the circuit breaker to")
    enabled: bool = Field(default=True, description="Whether the circuit breaker is enabled")


class CircuitBreakerUpdate(CircuitBreakerCreate):
    """Model for updating a circuit breaker."""
    pass


class CircuitBreakerResponse(CircuitBreakerCreate):
    """Model for circuit breaker response."""
    id: str = Field(..., description="ID of the circuit breaker")
    account_id: str = Field(..., description="ID of the account")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Update timestamp")
    last_triggered_at: Optional[str] = Field(None, description="Last trigger timestamp")


class CircuitBreakerEventResponse(BaseModel):
    """Model for circuit breaker event response."""
    id: str = Field(..., description="ID of the event")
    circuit_breaker_id: str = Field(..., description="ID of the circuit breaker")
    timestamp: str = Field(..., description="Timestamp of the event")
    trigger_values: Dict[str, Any] = Field(..., description="Values that triggered the circuit breaker")
    action_taken: str = Field(..., description="Action that was taken")
    action_result: Dict[str, Any] = Field(..., description="Result of the action")
    positions_affected: Dict[str, Any] = Field(..., description="Positions affected by the action")


# API routes

@router.get("/circuit-breakers", response_model=List[CircuitBreakerResponse])
async def get_circuit_breakers(
    current_user: User = Depends(get_current_user),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status")
):
    """
    Get all circuit breakers for the current user.
    
    Args:
        current_user: The current authenticated user
        enabled: Optional filter for enabled status
        
    Returns:
        List of circuit breakers
    """
    repo = CircuitBreakerRepository()
    circuit_breakers = await repo.get_by_account_id(current_user.id, enabled)
    
    return [cb.to_dict() for cb in circuit_breakers]


@router.get("/circuit-breakers/{circuit_breaker_id}", response_model=CircuitBreakerResponse)
async def get_circuit_breaker(
    circuit_breaker_id: str = Path(..., description="ID of the circuit breaker"),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific circuit breaker.
    
    Args:
        circuit_breaker_id: ID of the circuit breaker
        current_user: The current authenticated user
        
    Returns:
        The circuit breaker
    """
    repo = CircuitBreakerRepository()
    circuit_breaker = await repo.get_by_id(circuit_breaker_id)
    
    if not circuit_breaker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Circuit breaker not found"
        )
    
    # Check ownership
    if circuit_breaker.account_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this circuit breaker"
        )
    
    return circuit_breaker.to_dict()


@router.post("/circuit-breakers", response_model=CircuitBreakerResponse, status_code=status.HTTP_201_CREATED)
async def create_circuit_breaker(
    circuit_breaker_data: CircuitBreakerCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new circuit breaker.
    
    Args:
        circuit_breaker_data: Data for the new circuit breaker
        current_user: The current authenticated user
        
    Returns:
        The created circuit breaker
    """
    # Convert pydantic model to dict
    data = circuit_breaker_data.dict()
    
    # Add additional data
    data["id"] = str(uuid.uuid4())
    data["account_id"] = current_user.id
    
    # Create the circuit breaker
    repo = CircuitBreakerRepository()
    circuit_breaker = await repo.create(data)
    
    log_event(
        logger,
        "CIRCUIT_BREAKER_CREATED",
        f"User {current_user.username} created circuit breaker {circuit_breaker.name}",
        context={"username": current_user.username, "circuit_breaker_id": circuit_breaker.id}
    )
    
    return circuit_breaker.to_dict()


@router.put("/circuit-breakers/{circuit_breaker_id}", response_model=CircuitBreakerResponse)
async def update_circuit_breaker(
    circuit_breaker_data: CircuitBreakerUpdate,
    circuit_breaker_id: str = Path(..., description="ID of the circuit breaker"),
    current_user: User = Depends(get_current_user)
):
    """
    Update a circuit breaker.
    
    Args:
        circuit_breaker_data: Updated data for the circuit breaker
        circuit_breaker_id: ID of the circuit breaker
        current_user: The current authenticated user
        
    Returns:
        The updated circuit breaker
    """
    # Check if circuit breaker exists
    repo = CircuitBreakerRepository()
    circuit_breaker = await repo.get_by_id(circuit_breaker_id)
    
    if not circuit_breaker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Circuit breaker not found"
        )
    
    # Check ownership
    if circuit_breaker.account_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this circuit breaker"
        )
    
    # Convert pydantic model to dict
    data = circuit_breaker_data.dict()
    
    # Update the circuit breaker
    updated_circuit_breaker = await repo.update(circuit_breaker_id, data)
    
    log_event(
        logger,
        "CIRCUIT_BREAKER_UPDATED",
        f"User {current_user.username} updated circuit breaker {updated_circuit_breaker.name}",
        context={"username": current_user.username, "circuit_breaker_id": circuit_breaker_id}
    )
    
    return updated_circuit_breaker.to_dict()


@router.delete("/circuit-breakers/{circuit_breaker_id}")
async def delete_circuit_breaker(
    circuit_breaker_id: str = Path(..., description="ID of the circuit breaker"),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a circuit breaker.
    
    Args:
        circuit_breaker_id: ID of the circuit breaker
        current_user: The current authenticated user
        
    Returns:
        A success message
    """
    # Check if circuit breaker exists
    repo = CircuitBreakerRepository()
    circuit_breaker = await repo.get_by_id(circuit_breaker_id)
    
    if not circuit_breaker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Circuit breaker not found"
        )
    
    # Check ownership
    if circuit_breaker.account_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this circuit breaker"
        )
    
    # Delete the circuit breaker
    success = await repo.delete(circuit_breaker_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete circuit breaker"
        )
    
    log_event(
        logger,
        "CIRCUIT_BREAKER_DELETED",
        f"User {current_user.username} deleted circuit breaker {circuit_breaker.name}",
        context={"username": current_user.username, "circuit_breaker_id": circuit_breaker_id}
    )
    
    return {"message": "Circuit breaker deleted successfully"}


@router.get("/circuit-breakers/{circuit_breaker_id}/events", response_model=List[CircuitBreakerEventResponse])
async def get_circuit_breaker_events(
    circuit_breaker_id: str = Path(..., description="ID of the circuit breaker"),
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, description="Maximum number of events to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    """
    Get events for a circuit breaker.
    
    Args:
        circuit_breaker_id: ID of the circuit breaker
        current_user: The current authenticated user
        limit: Maximum number of events to return
        offset: Offset for pagination
        
    Returns:
        List of circuit breaker events
    """
    # Check if circuit breaker exists
    repo = CircuitBreakerRepository()
    circuit_breaker = await repo.get_by_id(circuit_breaker_id)
    
    if not circuit_breaker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Circuit breaker not found"
        )
    
    # Check ownership
    if circuit_breaker.account_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this circuit breaker's events"
        )
    
    # Get events
    events = await repo.get_events_by_circuit_breaker_id(circuit_breaker_id, limit, offset)
    
    return [event.to_dict() for event in events]


@router.get("/events", response_model=List[CircuitBreakerEventResponse])
async def get_all_circuit_breaker_events(
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, description="Maximum number of events to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    """
    Get all circuit breaker events for the current user.
    
    Args:
        current_user: The current authenticated user
        limit: Maximum number of events to return
        offset: Offset for pagination
        
    Returns:
        List of circuit breaker events
    """
    repo = CircuitBreakerRepository()
    events = await repo.get_events_by_account_id(current_user.id, limit, offset)
    
    return [event.to_dict() for event in events]


# Risk metrics endpoints

@router.get("/metrics")
async def get_risk_metrics(
    current_user: User = Depends(get_current_user)
):
    """
    Get current risk metrics.
    
    This endpoint provides a snapshot of current risk metrics across all
    exchanges and positions for the current user.
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        Current risk metrics
    """
    # This endpoint would typically call the RiskMonitor to get real-time metrics
    # For now, we'll return a placeholder response
    
    return {
        "message": "Risk metrics endpoint will be implemented in a future update"
    } 