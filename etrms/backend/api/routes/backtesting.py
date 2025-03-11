"""
Enhanced Trading Risk Management System Backtesting API Routes

This module provides API endpoints for backtesting functionality.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Path
from sqlalchemy.orm import Session

from api.dependencies import get_db, get_current_user
from data.repositories.backtesting import BacktestRepository
from exchange.backtesting.backtesting_engine import run_backtest
from exchange.backtesting.strategy_factory import StrategyFactory
from exchange.backtesting.historical_data_downloader import download_historical_data
from exchange.backtesting.monte_carlo import run_monte_carlo_simulation
from exchange.backtesting.parameter_optimizer import run_parameter_optimization
from exchange.backtesting.walk_forward import run_walk_forward_analysis
from utils.logger import get_logger, log_event


# Create router
router = APIRouter(
    prefix="/api/backtesting",
    tags=["backtesting"],
    responses={404: {"description": "Not found"}},
)

logger = get_logger(__name__)


@router.post("/download-data")
async def api_download_historical_data(
    exchange: str,
    symbols: List[str],
    timeframes: List[str],
    start_date: str,
    end_date: str,
    data_path: str = "data/historical",
    download_orderbooks: bool = False,
    orderbook_interval_minutes: int = 60,
    background_tasks: BackgroundTasks = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Download historical data for backtesting.
    
    Args:
        exchange: Exchange name ('binance' or 'hyperliquid')
        symbols: List of trading pair symbols
        timeframes: List of timeframes (e.g., ['1h', '4h', '1d'])
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        data_path: Path to save downloaded data
        download_orderbooks: Whether to download orderbook snapshots
        orderbook_interval_minutes: Interval between orderbook snapshots
        background_tasks: Background tasks (for long-running operations)
        current_user: Current authenticated user
        
    Returns:
        Dict containing information about the download task
    """
    if exchange.lower() not in ["binance", "hyperliquid"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported exchange: {exchange}. Supported exchanges: binance, hyperliquid"
        )
    
    # Get API keys from user settings
    # In a real implementation, you would retrieve these from a secure storage
    api_key = current_user.get("api_keys", {}).get(exchange.lower(), {}).get("api_key")
    api_secret = current_user.get("api_keys", {}).get(exchange.lower(), {}).get("api_secret")
    
    log_event(
        logger,
        "DOWNLOAD_HISTORICAL_DATA_REQUEST",
        f"Historical data download requested for {exchange}",
        context={
            "exchange": exchange,
            "symbols": symbols,
            "timeframes": timeframes,
            "start_date": start_date,
            "end_date": end_date,
            "user_id": current_user.get("id")
        }
    )
    
    # If the request is expected to take a long time, run it in the background
    if background_tasks and (len(symbols) > 2 or len(timeframes) > 2 or download_orderbooks):
        task_id = f"download_{exchange}_{start_date}_{end_date}_{'-'.join(symbols)}"
        
        background_tasks.add_task(
            download_historical_data,
            exchange=exchange,
            symbols=symbols,
            timeframes=timeframes,
            start_date=start_date,
            end_date=end_date,
            data_path=data_path,
            download_orderbooks=download_orderbooks,
            orderbook_interval_minutes=orderbook_interval_minutes,
            api_key=api_key,
            api_secret=api_secret
        )
        
        return {
            "message": "Historical data download started in the background",
            "task_id": task_id,
            "status": "running",
            "details": {
                "exchange": exchange,
                "symbols": symbols,
                "timeframes": timeframes,
                "start_date": start_date,
                "end_date": end_date
            }
        }
    else:
        # For smaller requests, run synchronously
        success = await download_historical_data(
            exchange=exchange,
            symbols=symbols,
            timeframes=timeframes,
            start_date=start_date,
            end_date=end_date,
            data_path=data_path,
            download_orderbooks=download_orderbooks,
            orderbook_interval_minutes=orderbook_interval_minutes,
            api_key=api_key,
            api_secret=api_secret
        )
        
        if success:
            return {
                "message": "Historical data downloaded successfully",
                "status": "completed",
                "details": {
                    "exchange": exchange,
                    "symbols": symbols,
                    "timeframes": timeframes,
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to download historical data. Check logs for details."
            )


@router.get("/available-strategies")
async def get_available_strategies(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get a list of available backtesting strategies.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        List of available strategies with descriptions
    """
    strategies = StrategyFactory.get_available_strategies()
    
    return strategies


@router.post("/tasks")
async def create_backtest_task(
    strategy_name: str,
    symbols: List[str],
    timeframe: str,
    start_date: str,
    end_date: str,
    initial_balance: float = 10000.0,
    fee_rate: float = 0.0004,
    slippage: float = 0.0001,
    risk_per_trade: float = 0.01,
    name: Optional[str] = None,
    description: Optional[str] = None,
    strategy_params: Optional[Dict[str, Any]] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a new backtest task.
    
    Args:
        strategy_name: Name of the strategy to use
        symbols: List of symbols to include in the backtest
        timeframe: Timeframe for historical data
        start_date: Start date for the backtest in 'YYYY-MM-DD' format
        end_date: End date for the backtest in 'YYYY-MM-DD' format
        initial_balance: Initial account balance
        fee_rate: Trading fee rate
        slippage: Simulated slippage
        risk_per_trade: Risk per trade as a percentage of account balance
        name: Optional name for the backtest
        description: Optional description for the backtest
        strategy_params: Optional parameters for the strategy
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict containing the created backtest task
    """
    # Validate strategy
    available_strategies = StrategyFactory.get_available_strategies()
    if not any(s["id"] == strategy_name for s in available_strategies):
        raise HTTPException(
            status_code=400,
            detail=f"Strategy '{strategy_name}' not found"
        )
    
    # Create task in database
    task = await BacktestRepository.create_task(
        db=db,
        user_id=current_user.get("id"),
        strategy_name=strategy_name,
        symbols=symbols,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        initial_balance=initial_balance,
        fee_rate=fee_rate,
        slippage=slippage,
        risk_per_trade=risk_per_trade,
        name=name,
        description=description,
        strategy_params=strategy_params
    )
    
    return task.to_dict()


@router.post("/run")
async def run_backtest_api(
    task_id: str,
    save_results: bool = True,
    generate_report: bool = True,
    background_tasks: BackgroundTasks = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Run a backtest for a previously created task.
    
    Args:
        task_id: ID of the backtest task to run
        save_results: Whether to save results to a file
        generate_report: Whether to generate an HTML report
        background_tasks: Background tasks (for long-running operations)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict containing information about the backtest task
    """
    # Get the task
    task = await BacktestRepository.get_task(db, task_id)
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Backtest task with ID '{task_id}' not found"
        )
    
    # Check if user owns the task
    if task.user_id != current_user.get("id"):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to run this backtest task"
        )
    
    # Check if task is already running or completed
    if task.status in ["running", "completed"]:
        return {
            "message": f"Backtest task is already {task.status}",
            "task_id": task_id,
            "status": task.status
        }
    
    # Log the request
    log_event(
        logger,
        "RUN_BACKTEST_REQUEST",
        f"Backtest requested for task: {task_id}",
        context={
            "task_id": task_id,
            "strategy": task.strategy_name,
            "symbols": task.symbols,
            "timeframe": task.timeframe,
            "user_id": current_user.get("id")
        }
    )
    
    # Get the strategy
    try:
        strategy = StrategyFactory.get_strategy(
            strategy_name=task.strategy_name,
            **(task.strategy_params or {})
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid strategy: {str(e)}"
        )
    
    # Update task status to running
    await BacktestRepository.update_task_status(
        db,
        task_id,
        "running",
        started_at=datetime.utcnow()
    )
    
    # If the request is expected to take a long time, run it in the background
    if background_tasks:
        background_tasks.add_task(
            _run_backtest_and_save_results,
            db=db,
            task=task,
            strategy=strategy,
            save_results=save_results,
            generate_report=generate_report
        )
        
        return {
            "message": "Backtest started in the background",
            "task_id": task_id,
            "status": "running",
            "details": {
                "strategy": task.strategy_name,
                "symbols": task.symbols,
                "timeframe": task.timeframe,
                "start_date": task.start_date,
                "end_date": task.end_date
            }
        }
    else:
        # For smaller/faster backtests, run synchronously
        results = await _run_backtest_and_save_results(
            db=db,
            task=task,
            strategy=strategy,
            save_results=save_results,
            generate_report=generate_report
        )
        
        return {
            "message": "Backtest completed successfully",
            "task_id": task_id,
            "status": "completed",
            "results": results
        }


@router.get("/tasks")
async def get_backtest_tasks(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a list of backtest tasks for the current user.
    
    Args:
        limit: Maximum number of tasks to return
        offset: Offset for pagination
        status: Optional filter by status
        sort_by: Field to sort by
        sort_order: Sort order ('asc' or 'desc')
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict containing the list of backtest tasks and pagination information
    """
    tasks = await BacktestRepository.get_tasks_for_user(
        db=db,
        user_id=current_user.get("id"),
        limit=limit,
        offset=offset,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return {
        "tasks": [task.to_dict() for task in tasks],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": len(tasks)  # This should be replaced with a count query in a real implementation
        }
    }


@router.get("/tasks/{task_id}")
async def get_backtest_task(
    task_id: str = Path(..., description="ID of the backtest task"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a backtest task by ID.
    
    Args:
        task_id: ID of the backtest task
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict containing the backtest task
    """
    task = await BacktestRepository.get_task(db, task_id)
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Backtest task with ID '{task_id}' not found"
        )
    
    # Check if user owns the task
    if task.user_id != current_user.get("id"):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to view this backtest task"
        )
    
    return task.to_dict()


@router.delete("/tasks/{task_id}")
async def delete_backtest_task(
    task_id: str = Path(..., description="ID of the backtest task"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Delete a backtest task and its associated data.
    
    Args:
        task_id: ID of the backtest task
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict containing the status of the operation
    """
    task = await BacktestRepository.get_task(db, task_id)
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Backtest task with ID '{task_id}' not found"
        )
    
    # Check if user owns the task
    if task.user_id != current_user.get("id"):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to delete this backtest task"
        )
    
    success = await BacktestRepository.delete_task(db, task_id)
    
    if success:
        return {
            "message": f"Backtest task '{task_id}' deleted successfully",
            "task_id": task_id
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete backtest task '{task_id}'"
        )


@router.get("/results/{task_id}")
async def get_backtest_results(
    task_id: str = Path(..., description="ID of the backtest task"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get the results of a backtest.
    
    Args:
        task_id: ID of the backtest task
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict containing the results of the backtest
    """
    # Check if task exists and user has permission
    task = await BacktestRepository.get_task(db, task_id)
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Backtest task with ID '{task_id}' not found"
        )
    
    # Check if user owns the task
    if task.user_id != current_user.get("id"):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to view these backtest results"
        )
    
    # Get result
    result = await BacktestRepository.get_result(db, task_id)
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No results found for backtest task '{task_id}'"
        )
    
    # Include task information with the results
    response = {
        "task": task.to_dict(),
        "results": result.to_dict()
    }
    
    return response


@router.get("/trades/{task_id}")
async def get_backtest_trades(
    task_id: str = Path(..., description="ID of the backtest task"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    sort_by: str = "entry_time",
    sort_order: str = "asc",
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get trades for a backtest task.
    
    Args:
        task_id: ID of the backtest task
        limit: Maximum number of trades to return
        offset: Offset for pagination
        sort_by: Field to sort by
        sort_order: Sort order ('asc' or 'desc')
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict containing the trades for the backtest task
    """
    # Check if task exists and user has permission
    task = await BacktestRepository.get_task(db, task_id)
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Backtest task with ID '{task_id}' not found"
        )
    
    # Check if user owns the task
    if task.user_id != current_user.get("id"):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to view these trades"
        )
    
    # Get trades
    trades = await BacktestRepository.get_trades(
        db=db,
        task_id=task_id,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return {
        "trades": [trade.to_dict() for trade in trades],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": len(trades)  # This should be replaced with a count query in a real implementation
        }
    }


@router.get("/comparison")
async def compare_backtests(
    task_ids: List[str],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Compare multiple backtest results.
    
    Args:
        task_ids: List of backtest task IDs to compare
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict containing the comparison of the backtests
    """
    comparison_results = []
    
    for task_id in task_ids:
        # Check if task exists and user has permission
        task = await BacktestRepository.get_task(db, task_id)
        
        if not task:
            continue
        
        # Check if user owns the task
        if task.user_id != current_user.get("id"):
            continue
        
        # Get result
        result = await BacktestRepository.get_result(db, task_id)
        
        if not result:
            continue
        
        # Add to comparison
        comparison_results.append({
            "task_id": task_id,
            "name": task.name,
            "strategy": task.strategy_name,
            "symbols": task.symbols,
            "timeframe": task.timeframe,
            "start_date": task.start_date,
            "end_date": task.end_date,
            "metrics": {
                "total_return_percentage": result.total_return_percentage,
                "sharpe_ratio": result.sharpe_ratio,
                "max_drawdown_percentage": result.max_drawdown_percentage,
                "win_rate": result.win_rate,
                "profit_factor": result.profit_factor,
                "total_trades": result.total_trades
            }
        })
    
    return {
        "results": comparison_results,
        "count": len(comparison_results)
    }


@router.post("/monte-carlo/{task_id}")
async def run_monte_carlo(
    task_id: str = Path(..., description="ID of the backtest task"),
    simulations: int = Query(1000, ge=100, le=10000),
    random_seed: Optional[int] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Run a Monte Carlo simulation on a backtest result.
    
    Args:
        task_id: ID of the backtest task
        simulations: Number of simulations to run
        random_seed: Optional random seed for reproducibility
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict containing the Monte Carlo simulation results
    """
    # Check if task exists and user has permission
    task = await BacktestRepository.get_task(db, task_id)
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Backtest task with ID '{task_id}' not found"
        )
    
    # Check if user owns the task
    if task.user_id != current_user.get("id"):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to run Monte Carlo simulation on this backtest"
        )
    
    # Get trades for the backtest
    trades = await BacktestRepository.get_trades(
        db=db,
        task_id=task_id,
        limit=10000,  # Get all trades, up to a reasonable limit
        offset=0
    )
    
    if not trades:
        raise HTTPException(
            status_code=400,
            detail=f"No trades found for backtest task '{task_id}'"
        )
    
    # Convert trades to dictionaries
    trades_dict = [trade.to_dict() for trade in trades]
    
    # Run Monte Carlo simulation
    try:
        monte_carlo_results = run_monte_carlo_simulation(
            trades=trades_dict,
            initial_balance=task.initial_balance,
            simulations=simulations,
            random_seed=random_seed
        )
        
        return {
            "task_id": task_id,
            "monte_carlo_results": monte_carlo_results,
            "simulations": simulations
        }
    except Exception as e:
        log_event(
            logger,
            "MONTE_CARLO_ERROR",
            f"Error running Monte Carlo simulation for task {task_id}: {str(e)}",
            level="ERROR",
            context={
                "task_id": task_id,
                "error": str(e)
            }
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error running Monte Carlo simulation: {str(e)}"
        )


@router.post("/optimize")
async def optimize_strategy_parameters(
    strategy_name: str,
    parameter_grid: Dict[str, List[Any]],
    start_date: str,
    end_date: str,
    symbols: List[str],
    timeframe: str = "1h",
    initial_balance: float = 10000.0,
    fee_rate: float = 0.0004,
    slippage: float = 0.0001,
    risk_per_trade: float = 0.01,
    optimization_metric: str = "sharpe_ratio",
    save_results: bool = True,
    background_tasks: BackgroundTasks = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Optimize strategy parameters through grid search.
    
    Args:
        strategy_name: Name of the strategy to optimize
        parameter_grid: Dictionary mapping parameter names to lists of values
        start_date: Start date for backtesting in 'YYYY-MM-DD' format
        end_date: End date for backtesting in 'YYYY-MM-DD' format
        symbols: List of symbols to include in backtests
        timeframe: Timeframe for historical data
        initial_balance: Initial account balance
        fee_rate: Trading fee rate
        slippage: Simulated slippage
        risk_per_trade: Risk per trade as a percentage of account balance
        optimization_metric: Metric to optimize
        save_results: Whether to save results to a file
        background_tasks: Background tasks for long-running operations
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dictionary with information about the optimization task
    """
    # Validate strategy
    available_strategies = StrategyFactory.get_available_strategies()
    if not any(s["id"] == strategy_name for s in available_strategies):
        raise HTTPException(
            status_code=400,
            detail=f"Strategy '{strategy_name}' not found"
        )
    
    # Validate parameter grid
    if not parameter_grid:
        raise HTTPException(
            status_code=400,
            detail="Parameter grid cannot be empty"
        )
    
    for param_name, param_values in parameter_grid.items():
        if not isinstance(param_values, list) or not param_values:
            raise HTTPException(
                status_code=400,
                detail=f"Parameter '{param_name}' must have a non-empty list of values"
            )
    
    # Validate optimization metric
    valid_metrics = [
        "sharpe_ratio", "total_return", "total_return_percentage", 
        "max_drawdown_percentage", "win_rate", "profit_factor",
        "calmar_ratio", "recovery_factor"
    ]
    if optimization_metric not in valid_metrics:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid optimization metric: {optimization_metric}. Valid options: {valid_metrics}"
        )
    
    # Check for excessive parameter combinations
    # Calculate the total number of combinations
    total_combinations = 1
    for param_values in parameter_grid.values():
        total_combinations *= len(param_values)
    
    # Set a reasonable limit (adjust as needed)
    max_combinations = 100
    if total_combinations > max_combinations:
        raise HTTPException(
            status_code=400,
            detail=f"Too many parameter combinations: {total_combinations}. Maximum allowed: {max_combinations}"
        )
    
    # Generate a task ID for this optimization
    optimization_id = f"optimize_{strategy_name}_{start_date}_{end_date}_{'-'.join(symbols)}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Log the request
    log_event(
        logger,
        "PARAMETER_OPTIMIZATION_REQUEST",
        f"Parameter optimization requested for strategy '{strategy_name}'",
        context={
            "strategy": strategy_name,
            "parameter_grid": parameter_grid,
            "optimization_metric": optimization_metric,
            "symbols": symbols,
            "user_id": current_user.get("id")
        }
    )
    
    # Create a backtest task for tracking purposes
    task = await BacktestRepository.create_task(
        db=db,
        user_id=current_user.get("id"),
        strategy_name=strategy_name,
        symbols=symbols,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        initial_balance=initial_balance,
        fee_rate=fee_rate,
        slippage=slippage,
        risk_per_trade=risk_per_trade,
        name=f"Optimization: {strategy_name}",
        description=f"Parameter optimization for {strategy_name} strategy using {optimization_metric} as the optimization metric",
        strategy_params={"parameter_grid": parameter_grid, "optimization_metric": optimization_metric}
    )
    
    # Update task status
    await BacktestRepository.update_task_status(
        db=db,
        task_id=task.task_id,
        status="optimization_running",
        started_at=datetime.utcnow()
    )
    
    # Run in background if requested
    if background_tasks:
        background_tasks.add_task(
            _run_parameter_optimization_and_save,
            db=db,
            task_id=task.task_id,
            strategy_name=strategy_name,
            parameter_grid=parameter_grid,
            start_date=start_date,
            end_date=end_date,
            symbols=symbols,
            timeframe=timeframe,
            initial_balance=initial_balance,
            fee_rate=fee_rate,
            slippage=slippage,
            risk_per_trade=risk_per_trade,
            optimization_metric=optimization_metric,
            save_results=save_results
        )
        
        return {
            "message": "Parameter optimization started in the background",
            "task_id": task.task_id,
            "status": "optimization_running",
            "details": {
                "strategy": strategy_name,
                "parameter_grid": parameter_grid,
                "optimization_metric": optimization_metric,
                "symbols": symbols,
                "timeframe": timeframe
            }
        }
    else:
        # Run synchronously for smaller optimizations
        try:
            optimization_results = await run_parameter_optimization(
                strategy_name=strategy_name,
                parameter_grid=parameter_grid,
                start_date=start_date,
                end_date=end_date,
                symbols=symbols,
                timeframe=timeframe,
                initial_balance=initial_balance,
                fee_rate=fee_rate,
                slippage=slippage,
                risk_per_trade=risk_per_trade,
                optimization_metric=optimization_metric,
                save_results=save_results
            )
            
            # Create a result for this task with the best parameters
            if optimization_results.get("best_result"):
                # Store the best result
                best_result = optimization_results["best_result"]
                
                await BacktestRepository.create_result(
                    db=db,
                    task_id=task.task_id,
                    performance_metrics=best_result,
                    equity_history=[],  # Not available in optimization results
                    monthly_returns={},  # Not available in optimization results
                    report_path=optimization_results.get("results_file")
                )
            
            # Update task status
            await BacktestRepository.update_task_status(
                db=db,
                task_id=task.task_id,
                status="optimization_completed",
                completed_at=datetime.utcnow()
            )
            
            return {
                "message": "Parameter optimization completed",
                "task_id": task.task_id,
                "status": "optimization_completed",
                "best_parameters": optimization_results.get("best_parameters"),
                "best_result": optimization_results.get("best_result"),
                "results_count": len(optimization_results.get("all_results", [])),
                "results_file": optimization_results.get("results_file")
            }
        except Exception as e:
            # Update task status to failed
            await BacktestRepository.update_task_status(
                db=db,
                task_id=task.task_id,
                status="optimization_failed"
            )
            
            log_event(
                logger,
                "PARAMETER_OPTIMIZATION_ERROR",
                f"Error during parameter optimization: {str(e)}",
                level="ERROR",
                context={
                    "task_id": task.task_id,
                    "strategy": strategy_name,
                    "error": str(e)
                }
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Error during parameter optimization: {str(e)}"
            )


@router.get("/optimize/results/{task_id}")
async def get_optimization_results(
    task_id: str = Path(..., description="ID of the optimization task"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get the results of a parameter optimization.
    
    Args:
        task_id: ID of the optimization task
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dictionary containing the optimization results
    """
    # Check if task exists and user has permission
    task = await BacktestRepository.get_task(db, task_id)
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Optimization task with ID '{task_id}' not found"
        )
    
    # Check if user owns the task
    if task.user_id != current_user.get("id"):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to view these optimization results"
        )
    
    # Check if task is an optimization task
    if "optimization" not in task.status:
        raise HTTPException(
            status_code=400,
            detail=f"Task '{task_id}' is not an optimization task"
        )
    
    # Get the result
    result = await BacktestRepository.get_result(db, task_id)
    
    # Check result status
    status = task.status
    if status == "optimization_running":
        return {
            "message": "Parameter optimization is still running",
            "task_id": task_id,
            "status": status
        }
    elif status == "optimization_failed":
        return {
            "message": "Parameter optimization failed",
            "task_id": task_id,
            "status": status
        }
    elif status == "optimization_completed":
        if not result:
            return {
                "message": "Parameter optimization completed but no results were saved",
                "task_id": task_id,
                "status": status
            }
        
        # Get best parameters from task
        best_parameters = task.strategy_params.get("parameter_grid", {}) if task.strategy_params else {}
        
        return {
            "message": "Parameter optimization results retrieved",
            "task_id": task_id,
            "status": status,
            "strategy_name": task.strategy_name,
            "optimization_metric": task.strategy_params.get("optimization_metric") if task.strategy_params else None,
            "best_parameters": best_parameters,
            "best_result": result.to_dict() if result else None,
            "report_path": result.report_path if result else None
        }
    else:
        return {
            "message": f"Unexpected optimization status: {status}",
            "task_id": task_id,
            "status": status
        }


@router.post("/walk-forward")
async def run_walk_forward_analysis_api(
    strategy_name: str,
    parameter_grid: Dict[str, List[Any]],
    start_date: str,
    end_date: str,
    symbols: List[str],
    timeframe: str = "1h",
    initial_balance: float = 10000.0,
    fee_rate: float = 0.0004,
    slippage: float = 0.0001,
    risk_per_trade: float = 0.01,
    optimization_metric: str = "sharpe_ratio",
    window_size_days: int = 90,
    step_size_days: int = 30,
    in_sample_pct: float = 0.7,
    save_results: bool = True,
    background_tasks: BackgroundTasks = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Run walk-forward analysis for a trading strategy.
    
    Args:
        strategy_name: Name of the strategy to analyze
        parameter_grid: Dictionary mapping parameter names to lists of values
        start_date: Start date for analysis in 'YYYY-MM-DD' format
        end_date: End date for analysis in 'YYYY-MM-DD' format
        symbols: List of symbols to include in the analysis
        timeframe: Timeframe for historical data
        initial_balance: Initial account balance
        fee_rate: Trading fee rate
        slippage: Simulated slippage
        risk_per_trade: Risk per trade as a percentage of account balance
        optimization_metric: Metric to optimize during in-sample periods
        window_size_days: Size of each window in days
        step_size_days: Number of days to step forward between windows
        in_sample_pct: Percentage of each window to use for in-sample optimization
        save_results: Whether to save results to a file
        background_tasks: Background tasks for long-running operations
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dictionary with information about the walk-forward analysis task
    """
    # Validate strategy
    available_strategies = StrategyFactory.get_available_strategies()
    if not any(s["id"] == strategy_name for s in available_strategies):
        raise HTTPException(
            status_code=400,
            detail=f"Strategy '{strategy_name}' not found"
        )
    
    # Validate parameter grid
    if not parameter_grid:
        raise HTTPException(
            status_code=400,
            detail="Parameter grid cannot be empty"
        )
    
    for param_name, param_values in parameter_grid.items():
        if not isinstance(param_values, list) or not param_values:
            raise HTTPException(
                status_code=400,
                detail=f"Parameter '{param_name}' must have a non-empty list of values"
            )
    
    # Validate date parameters
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        if start_dt >= end_dt:
            raise HTTPException(
                status_code=400,
                detail="Start date must be before end date"
            )
        
        # Check if date range is long enough for at least one window
        days_diff = (end_dt - start_dt).days
        if days_diff < window_size_days:
            raise HTTPException(
                status_code=400,
                detail=f"Date range is too short. Minimum required: {window_size_days} days"
            )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Expected 'YYYY-MM-DD'"
        )
    
    # Validate window parameters
    if window_size_days <= 0:
        raise HTTPException(
            status_code=400,
            detail="Window size must be positive"
        )
    
    if step_size_days <= 0:
        raise HTTPException(
            status_code=400,
            detail="Step size must be positive"
        )
    
    if in_sample_pct <= 0 or in_sample_pct >= 1:
        raise HTTPException(
            status_code=400,
            detail="In-sample percentage must be between 0 and 1"
        )
    
    # Generate a task ID for this analysis
    task_id = f"walkforward_{strategy_name}_{start_date}_{end_date}_{'-'.join(symbols)}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Log the request
    log_event(
        logger,
        "WALK_FORWARD_ANALYSIS_REQUEST",
        f"Walk-forward analysis requested for strategy '{strategy_name}'",
        context={
            "strategy": strategy_name,
            "parameter_grid": parameter_grid,
            "optimization_metric": optimization_metric,
            "symbols": symbols,
            "window_size_days": window_size_days,
            "step_size_days": step_size_days,
            "in_sample_pct": in_sample_pct,
            "user_id": current_user.get("id")
        }
    )
    
    # Create a backtest task for tracking purposes
    task = await BacktestRepository.create_task(
        db=db,
        user_id=current_user.get("id"),
        strategy_name=strategy_name,
        symbols=symbols,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        initial_balance=initial_balance,
        fee_rate=fee_rate,
        slippage=slippage,
        risk_per_trade=risk_per_trade,
        name=f"Walk-Forward: {strategy_name}",
        description=f"Walk-forward analysis for {strategy_name} strategy using {optimization_metric} as the optimization metric",
        strategy_params={
            "parameter_grid": parameter_grid,
            "optimization_metric": optimization_metric,
            "window_size_days": window_size_days,
            "step_size_days": step_size_days,
            "in_sample_pct": in_sample_pct
        }
    )
    
    # Update task status
    await BacktestRepository.update_task_status(
        db=db,
        task_id=task.task_id,
        status="walkforward_running",
        started_at=datetime.utcnow()
    )
    
    # Run in background if requested
    if background_tasks:
        background_tasks.add_task(
            _run_walk_forward_analysis_and_save,
            db=db,
            task_id=task.task_id,
            strategy_name=strategy_name,
            parameter_grid=parameter_grid,
            start_date=start_date,
            end_date=end_date,
            symbols=symbols,
            timeframe=timeframe,
            initial_balance=initial_balance,
            fee_rate=fee_rate,
            slippage=slippage,
            risk_per_trade=risk_per_trade,
            optimization_metric=optimization_metric,
            window_size_days=window_size_days,
            step_size_days=step_size_days,
            in_sample_pct=in_sample_pct,
            save_results=save_results
        )
        
        return {
            "message": "Walk-forward analysis started in the background",
            "task_id": task.task_id,
            "status": "walkforward_running",
            "details": {
                "strategy": strategy_name,
                "parameter_grid": parameter_grid,
                "optimization_metric": optimization_metric,
                "window_size_days": window_size_days,
                "step_size_days": step_size_days,
                "in_sample_pct": in_sample_pct,
                "symbols": symbols
            }
        }
    else:
        # For smaller analyses, run synchronously
        try:
            wf_results = await run_walk_forward_analysis(
                strategy_name=strategy_name,
                parameter_grid=parameter_grid,
                start_date=start_date,
                end_date=end_date,
                symbols=symbols,
                timeframe=timeframe,
                initial_balance=initial_balance,
                fee_rate=fee_rate,
                slippage=slippage,
                risk_per_trade=risk_per_trade,
                optimization_metric=optimization_metric,
                window_size_days=window_size_days,
                step_size_days=step_size_days,
                in_sample_pct=in_sample_pct,
                parallel=False,
                save_results=save_results
            )
            
            # Create a result for this task with the combined metrics
            if wf_results.get("combined_results") and wf_results["combined_results"].get("metrics"):
                # Store the combined result
                combined_metrics = wf_results["combined_results"]["metrics"]
                
                await BacktestRepository.create_result(
                    db=db,
                    task_id=task.task_id,
                    performance_metrics=combined_metrics,
                    equity_history=wf_results["combined_results"].get("equity_curve", []),
                    monthly_returns={},  # Not available in walk-forward results
                    report_path=wf_results.get("results_file")
                )
            
            # Update task status
            await BacktestRepository.update_task_status(
                db=db,
                task_id=task.task_id,
                status="walkforward_completed",
                completed_at=datetime.utcnow()
            )
            
            return {
                "message": "Walk-forward analysis completed",
                "task_id": task.task_id,
                "status": "walkforward_completed",
                "windows_count": len(wf_results.get("windows", [])),
                "combined_metrics": wf_results.get("combined_results", {}).get("metrics", {}),
                "parameters_evolution": wf_results.get("combined_results", {}).get("parameters_evolution", []),
                "results_file": wf_results.get("results_file")
            }
        except Exception as e:
            # Update task status to failed
            await BacktestRepository.update_task_status(
                db=db,
                task_id=task.task_id,
                status="walkforward_failed"
            )
            
            log_event(
                logger,
                "WALK_FORWARD_ANALYSIS_ERROR",
                f"Error during walk-forward analysis: {str(e)}",
                level="ERROR",
                context={
                    "task_id": task.task_id,
                    "strategy": strategy_name,
                    "error": str(e)
                }
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Error during walk-forward analysis: {str(e)}"
            )


@router.get("/walk-forward/results/{task_id}")
async def get_walk_forward_results(
    task_id: str = Path(..., description="ID of the walk-forward analysis task"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get the results of a walk-forward analysis.
    
    Args:
        task_id: ID of the walk-forward analysis task
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dictionary containing the walk-forward analysis results
    """
    # Check if task exists and user has permission
    task = await BacktestRepository.get_task(db, task_id)
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Walk-forward analysis task with ID '{task_id}' not found"
        )
    
    # Check if user owns the task
    if task.user_id != current_user.get("id"):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to view these walk-forward analysis results"
        )
    
    # Check if task is a walk-forward analysis task
    if "walkforward" not in task.status:
        raise HTTPException(
            status_code=400,
            detail=f"Task '{task_id}' is not a walk-forward analysis task"
        )
    
    # Get the result
    result = await BacktestRepository.get_result(db, task_id)
    
    # Check result status
    status = task.status
    if status == "walkforward_running":
        return {
            "message": "Walk-forward analysis is still running",
            "task_id": task_id,
            "status": status
        }
    elif status == "walkforward_failed":
        return {
            "message": "Walk-forward analysis failed",
            "task_id": task_id,
            "status": status
        }
    elif status == "walkforward_completed":
        if not result:
            return {
                "message": "Walk-forward analysis completed but no results were saved",
                "task_id": task_id,
                "status": status
            }
        
        # Get parameters from task
        parameters = task.strategy_params or {}
        
        return {
            "message": "Walk-forward analysis results retrieved",
            "task_id": task_id,
            "status": status,
            "strategy_name": task.strategy_name,
            "optimization_metric": parameters.get("optimization_metric"),
            "window_size_days": parameters.get("window_size_days"),
            "step_size_days": parameters.get("step_size_days"),
            "in_sample_pct": parameters.get("in_sample_pct"),
            "combined_metrics": result.to_dict() if result else None,
            "report_path": result.report_path if result else None
        }
    else:
        return {
            "message": f"Unexpected walk-forward analysis status: {status}",
            "task_id": task_id,
            "status": status
        }


async def _run_backtest_and_save_results(
    db: Session,
    task: Any,
    strategy: Any,
    save_results: bool = True,
    generate_report: bool = True
) -> Dict[str, Any]:
    """
    Run a backtest and save the results to the database.
    
    Args:
        db: Database session
        task: Backtest task
        strategy: Strategy function
        save_results: Whether to save results to a file
        generate_report: Whether to generate an HTML report
        
    Returns:
        Dict containing the results of the backtest
    """
    try:
        # Run backtest
        results = await run_backtest(
            start_date=task.start_date,
            end_date=task.end_date,
            symbols=task.symbols,
            timeframe=task.timeframe,
            initial_balance=task.initial_balance,
            fee_rate=task.fee_rate,
            slippage=task.slippage,
            risk_per_trade=task.risk_per_trade,
            strategy=strategy,
            save_results=save_results,
            generate_report=generate_report
        )
        
        # Extract report path if available
        report_path = results.get("report_path", None)
        
        # Save results to database
        result = await BacktestRepository.create_result(
            db=db,
            task_id=task.task_id,
            performance_metrics=results.get("performance_metrics", {}),
            equity_history=results.get("equity_history", []),
            drawdown_history=results.get("drawdown_history", []),
            monthly_returns=results.get("monthly_returns", {}),
            report_path=report_path
        )
        
        # Save trades to database
        if "trade_history" in results and results["trade_history"]:
            await BacktestRepository.create_trades_batch(
                db=db,
                task_id=task.task_id,
                trades_data=results["trade_history"]
            )
        
        # Update task status to completed
        await BacktestRepository.update_task_status(
            db=db,
            task_id=task.task_id,
            status="completed",
            completed_at=datetime.utcnow()
        )
        
        return results
    except Exception as e:
        # Update task status to failed
        await BacktestRepository.update_task_status(
            db=db,
            task_id=task.task_id,
            status="failed"
        )
        
        log_event(
            logger,
            "BACKTEST_EXECUTION_ERROR",
            f"Error running backtest for task {task.task_id}: {str(e)}",
            level="ERROR",
            context={
                "task_id": task.task_id,
                "error": str(e)
            }
        )
        
        raise 

async def _run_parameter_optimization_and_save(
    db: Session,
    task_id: str,
    strategy_name: str,
    parameter_grid: Dict[str, List[Any]],
    start_date: str,
    end_date: str,
    symbols: List[str],
    timeframe: str = "1h",
    initial_balance: float = 10000.0,
    fee_rate: float = 0.0004,
    slippage: float = 0.0001,
    risk_per_trade: float = 0.01,
    optimization_metric: str = "sharpe_ratio",
    save_results: bool = True
) -> None:
    """
    Run parameter optimization in the background and save results.
    
    Args:
        db: Database session
        task_id: ID of the task in the database
        strategy_name: Name of the strategy to optimize
        parameter_grid: Dictionary mapping parameter names to lists of values
        start_date: Start date for backtesting
        end_date: End date for backtesting
        symbols: List of symbols to include in backtests
        timeframe: Timeframe for historical data
        initial_balance: Initial account balance
        fee_rate: Trading fee rate
        slippage: Simulated slippage
        risk_per_trade: Risk per trade as a percentage of account balance
        optimization_metric: Metric to optimize
        save_results: Whether to save results to a file
    """
    try:
        # Run optimization
        optimization_results = await run_parameter_optimization(
            strategy_name=strategy_name,
            parameter_grid=parameter_grid,
            start_date=start_date,
            end_date=end_date,
            symbols=symbols,
            timeframe=timeframe,
            initial_balance=initial_balance,
            fee_rate=fee_rate,
            slippage=slippage,
            risk_per_trade=risk_per_trade,
            optimization_metric=optimization_metric,
            save_results=save_results
        )
        
        # Create a result for this task with the best parameters
        if optimization_results.get("best_result"):
            # Store the best result
            best_result = optimization_results["best_result"]
            
            await BacktestRepository.create_result(
                db=db,
                task_id=task_id,
                performance_metrics=best_result,
                equity_history=[],  # Not available in optimization results
                monthly_returns={},  # Not available in optimization results
                report_path=optimization_results.get("results_file")
            )
        
        # Update task status
        await BacktestRepository.update_task_status(
            db=db,
            task_id=task_id,
            status="optimization_completed",
            completed_at=datetime.utcnow()
        )
        
        log_event(
            logger,
            "PARAMETER_OPTIMIZATION_COMPLETED",
            f"Parameter optimization completed for task {task_id}",
            context={
                "task_id": task_id,
                "strategy": strategy_name,
                "best_parameters": optimization_results.get("best_parameters")
            }
        )
    except Exception as e:
        # Update task status to failed
        await BacktestRepository.update_task_status(
            db=db,
            task_id=task_id,
            status="optimization_failed"
        )
        
        log_event(
            logger,
            "PARAMETER_OPTIMIZATION_ERROR",
            f"Error during parameter optimization: {str(e)}",
            level="ERROR",
            context={
                "task_id": task_id,
                "strategy": strategy_name,
                "error": str(e)
            }
        ) 

async def _run_walk_forward_analysis_and_save(
    db: Session,
    task_id: str,
    strategy_name: str,
    parameter_grid: Dict[str, List[Any]],
    start_date: str,
    end_date: str,
    symbols: List[str],
    timeframe: str = "1h",
    initial_balance: float = 10000.0,
    fee_rate: float = 0.0004,
    slippage: float = 0.0001,
    risk_per_trade: float = 0.01,
    optimization_metric: str = "sharpe_ratio",
    window_size_days: int = 90,
    step_size_days: int = 30,
    in_sample_pct: float = 0.7,
    save_results: bool = True
) -> None:
    """
    Run walk-forward analysis in the background and save results.
    
    Args:
        db: Database session
        task_id: ID of the task in the database
        strategy_name: Name of the strategy to analyze
        parameter_grid: Dictionary mapping parameter names to lists of values
        start_date: Start date for analysis
        end_date: End date for analysis
        symbols: List of symbols to include in the analysis
        timeframe: Timeframe for historical data
        initial_balance: Initial account balance
        fee_rate: Trading fee rate
        slippage: Simulated slippage
        risk_per_trade: Risk per trade as a percentage of account balance
        optimization_metric: Metric to optimize
        window_size_days: Size of each window in days
        step_size_days: Number of days to step forward between windows
        in_sample_pct: Percentage of each window to use for in-sample optimization
        save_results: Whether to save results to a file
    """
    try:
        # Run walk-forward analysis
        wf_results = await run_walk_forward_analysis(
            strategy_name=strategy_name,
            parameter_grid=parameter_grid,
            start_date=start_date,
            end_date=end_date,
            symbols=symbols,
            timeframe=timeframe,
            initial_balance=initial_balance,
            fee_rate=fee_rate,
            slippage=slippage,
            risk_per_trade=risk_per_trade,
            optimization_metric=optimization_metric,
            window_size_days=window_size_days,
            step_size_days=step_size_days,
            in_sample_pct=in_sample_pct,
            parallel=True,  # Use parallel processing in background tasks
            max_workers=4,
            save_results=save_results
        )
        
        # Create a result for this task with the combined metrics
        if wf_results.get("combined_results") and wf_results["combined_results"].get("metrics"):
            # Store the combined result
            combined_metrics = wf_results["combined_results"]["metrics"]
            
            await BacktestRepository.create_result(
                db=db,
                task_id=task_id,
                performance_metrics=combined_metrics,
                equity_history=wf_results["combined_results"].get("equity_curve", []),
                monthly_returns={},  # Not available in walk-forward results
                report_path=wf_results.get("results_file")
            )
        
        # Update task status
        await BacktestRepository.update_task_status(
            db=db,
            task_id=task_id,
            status="walkforward_completed",
            completed_at=datetime.utcnow()
        )
        
        log_event(
            logger,
            "WALK_FORWARD_ANALYSIS_COMPLETED",
            f"Walk-forward analysis completed for task {task_id}",
            context={
                "task_id": task_id,
                "strategy": strategy_name,
                "windows_count": len(wf_results.get("windows", [])),
                "combined_metrics": wf_results.get("combined_results", {}).get("metrics", {})
            }
        )
    except Exception as e:
        # Update task status to failed
        await BacktestRepository.update_task_status(
            db=db,
            task_id=task_id,
            status="walkforward_failed"
        )
        
        log_event(
            logger,
            "WALK_FORWARD_ANALYSIS_ERROR",
            f"Error during walk-forward analysis: {str(e)}",
            level="ERROR",
            context={
                "task_id": task_id,
                "strategy": strategy_name,
                "error": str(e)
            }
        ) 