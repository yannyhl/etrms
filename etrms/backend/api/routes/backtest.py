"""
API routes for backtesting operations.
"""

from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from typing import Optional

from etrms.backend.models.backtest import (
    BacktestCreate,
    BacktestUpdate,
    BacktestResponse,
    BacktestListResponse
)
from etrms.backend.models.user import User
from etrms.backend.services.backtest_service import BacktestService
from etrms.backend.repositories.backtest_repository import BacktestRepository
from etrms.backend.api.dependencies import get_current_user
from etrms.backend.utils.error_handler import NotFoundException, ConflictException

router = APIRouter(prefix="/backtest", tags=["backtest"])

def get_backtest_repository():
    """Dependency to get the backtest repository"""
    return BacktestRepository()

def get_backtest_service(repository: BacktestRepository = Depends(get_backtest_repository)):
    """Dependency to get the backtest service"""
    return BacktestService(repository)

@router.get("", response_model=BacktestListResponse)
async def get_backtests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    backtest_service: BacktestService = Depends(get_backtest_service)
):
    """
    Get all backtests with pagination.
    
    Args:
        skip: Number of backtests to skip
        limit: Maximum number of backtests to return
        current_user: The current authenticated user
        backtest_service: The backtest service
        
    Returns:
        A list of backtests
    """
    return backtest_service.get_all_backtests(skip, limit)

@router.get("/{backtest_id}", response_model=BacktestResponse)
async def get_backtest(
    backtest_id: str = Path(..., title="The ID of the backtest to get"),
    current_user: User = Depends(get_current_user),
    backtest_service: BacktestService = Depends(get_backtest_service)
):
    """
    Get a backtest by ID.
    
    Args:
        backtest_id: The ID of the backtest to get
        current_user: The current authenticated user
        backtest_service: The backtest service
        
    Returns:
        The backtest
        
    Raises:
        HTTPException: If the backtest is not found
    """
    try:
        return backtest_service.get_backtest(backtest_id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("", response_model=BacktestResponse, status_code=status.HTTP_201_CREATED)
async def create_backtest(
    backtest_create: BacktestCreate,
    current_user: User = Depends(get_current_user),
    backtest_service: BacktestService = Depends(get_backtest_service)
):
    """
    Create a new backtest.
    
    Args:
        backtest_create: The backtest to create
        current_user: The current authenticated user
        backtest_service: The backtest service
        
    Returns:
        The created backtest
        
    Raises:
        HTTPException: If the backtest could not be created
    """
    try:
        return backtest_service.create_backtest(backtest_create)
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

@router.put("/{backtest_id}", response_model=BacktestResponse)
async def update_backtest(
    backtest_update: BacktestUpdate,
    backtest_id: str = Path(..., title="The ID of the backtest to update"),
    current_user: User = Depends(get_current_user),
    backtest_service: BacktestService = Depends(get_backtest_service)
):
    """
    Update a backtest.
    
    Args:
        backtest_update: The backtest update data
        backtest_id: The ID of the backtest to update
        current_user: The current authenticated user
        backtest_service: The backtest service
        
    Returns:
        The updated backtest
        
    Raises:
        HTTPException: If the backtest is not found or could not be updated
    """
    try:
        return backtest_service.update_backtest(backtest_id, backtest_update)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

@router.delete("/{backtest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backtest(
    backtest_id: str = Path(..., title="The ID of the backtest to delete"),
    current_user: User = Depends(get_current_user),
    backtest_service: BacktestService = Depends(get_backtest_service)
):
    """
    Delete a backtest.
    
    Args:
        backtest_id: The ID of the backtest to delete
        current_user: The current authenticated user
        backtest_service: The backtest service
        
    Raises:
        HTTPException: If the backtest is not found
    """
    try:
        backtest_service.delete_backtest(backtest_id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/{backtest_id}/cancel", response_model=BacktestResponse)
async def cancel_backtest(
    backtest_id: str = Path(..., title="The ID of the backtest to cancel"),
    current_user: User = Depends(get_current_user),
    backtest_service: BacktestService = Depends(get_backtest_service)
):
    """
    Cancel a running backtest.
    
    Args:
        backtest_id: The ID of the backtest to cancel
        current_user: The current authenticated user
        backtest_service: The backtest service
        
    Returns:
        The cancelled backtest
        
    Raises:
        HTTPException: If the backtest is not found or could not be cancelled
    """
    try:
        return backtest_service.cancel_backtest(backtest_id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) 