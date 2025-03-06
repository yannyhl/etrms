"""
Enhanced Trading Risk Management System Configuration API

This module provides endpoints for managing risk configuration settings.
"""
from typing import Dict, Any, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body

from risk import RiskConfig

# Create a router instance
router = APIRouter()

# Create a risk configuration instance
risk_config = RiskConfig()


async def get_risk_config():
    """
    Dependency to get the risk configuration instance.
    
    Returns:
        The risk configuration instance.
    """
    return risk_config


@router.get("/", summary="Get all risk configuration settings")
async def get_all_config(
    config: RiskConfig = Depends(get_risk_config)
) -> Dict[str, Any]:
    """
    Get all risk configuration settings.
    
    Returns:
        Dict containing all risk configuration settings.
    """
    return config.config


@router.get("/global", summary="Get global risk configuration settings")
async def get_global_config(
    config: RiskConfig = Depends(get_risk_config)
) -> Dict[str, Any]:
    """
    Get global risk configuration settings.
    
    Returns:
        Dict containing global risk configuration settings.
    """
    return config.get_global_config()


@router.put("/global", summary="Update global risk configuration settings")
async def update_global_config(
    settings: Dict[str, Any] = Body(..., description="Global risk configuration settings to update"),
    config: RiskConfig = Depends(get_risk_config)
) -> Dict[str, Any]:
    """
    Update global risk configuration settings.
    
    Args:
        settings: Global risk configuration settings to update.
        
    Returns:
        Dict containing the updated global risk configuration settings.
    """
    try:
        for param, value in settings.items():
            config.set_global_param(param, value)
        
        return {
            "status": "global_config_updated",
            "global_config": config.get_global_config()
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error updating global configuration: {str(e)}"
        )


@router.get("/symbols", summary="Get all symbol-specific risk configuration settings")
async def get_all_symbol_configs(
    config: RiskConfig = Depends(get_risk_config)
) -> Dict[str, Any]:
    """
    Get all symbol-specific risk configuration settings.
    
    Returns:
        Dict containing symbol-specific risk configuration settings.
    """
    return config.config["symbols"]


@router.get("/symbols/{symbol}", summary="Get risk configuration settings for a specific symbol")
async def get_symbol_config(
    symbol: str = Path(..., description="Symbol (e.g., 'BTCUSDT')"),
    config: RiskConfig = Depends(get_risk_config)
) -> Dict[str, Any]:
    """
    Get risk configuration settings for a specific symbol.
    
    Args:
        symbol: The symbol.
        
    Returns:
        Dict containing risk configuration settings for the symbol.
    """
    return config.get_symbol_config(symbol)


@router.put("/symbols/{symbol}", summary="Update risk configuration settings for a specific symbol")
async def update_symbol_config(
    symbol: str = Path(..., description="Symbol (e.g., 'BTCUSDT')"),
    settings: Dict[str, Any] = Body(..., description="Symbol-specific risk configuration settings to update"),
    config: RiskConfig = Depends(get_risk_config)
) -> Dict[str, Any]:
    """
    Update risk configuration settings for a specific symbol.
    
    Args:
        symbol: The symbol.
        settings: Symbol-specific risk configuration settings to update.
        
    Returns:
        Dict containing the updated risk configuration settings for the symbol.
    """
    try:
        for param, value in settings.items():
            config.set_symbol_param(symbol, param, value)
        
        return {
            "status": "symbol_config_updated",
            "symbol": symbol,
            "symbol_config": config.get_symbol_config(symbol)
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error updating symbol configuration: {str(e)}"
        )


@router.get("/exchanges", summary="Get all exchange-specific risk configuration settings")
async def get_all_exchange_configs(
    config: RiskConfig = Depends(get_risk_config)
) -> Dict[str, Any]:
    """
    Get all exchange-specific risk configuration settings.
    
    Returns:
        Dict containing exchange-specific risk configuration settings.
    """
    return config.config["exchanges"]


@router.get("/exchanges/{exchange}", summary="Get risk configuration settings for a specific exchange")
async def get_exchange_config(
    exchange: str = Path(..., description="Exchange name (e.g., 'binance', 'hyperliquid')"),
    config: RiskConfig = Depends(get_risk_config)
) -> Dict[str, Any]:
    """
    Get risk configuration settings for a specific exchange.
    
    Args:
        exchange: The exchange name.
        
    Returns:
        Dict containing risk configuration settings for the exchange.
    """
    return config.get_exchange_config(exchange)


@router.put("/exchanges/{exchange}", summary="Update risk configuration settings for a specific exchange")
async def update_exchange_config(
    exchange: str = Path(..., description="Exchange name (e.g., 'binance', 'hyperliquid')"),
    settings: Dict[str, Any] = Body(..., description="Exchange-specific risk configuration settings to update"),
    config: RiskConfig = Depends(get_risk_config)
) -> Dict[str, Any]:
    """
    Update risk configuration settings for a specific exchange.
    
    Args:
        exchange: The exchange name.
        settings: Exchange-specific risk configuration settings to update.
        
    Returns:
        Dict containing the updated risk configuration settings for the exchange.
    """
    try:
        for param, value in settings.items():
            config.set_exchange_param(exchange, param, value)
        
        return {
            "status": "exchange_config_updated",
            "exchange": exchange,
            "exchange_config": config.get_exchange_config(exchange)
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error updating exchange configuration: {str(e)}"
        )


@router.get("/circuit-breakers", summary="Get circuit breaker configurations")
async def get_circuit_breaker_configs(
    config: RiskConfig = Depends(get_risk_config)
) -> Dict[str, Any]:
    """
    Get circuit breaker configurations.
    
    Returns:
        Dict containing circuit breaker configurations.
    """
    return {
        "circuit_breakers": config.get_circuit_breakers()
    }


@router.post("/circuit-breakers", summary="Add a circuit breaker configuration")
async def add_circuit_breaker_config(
    circuit_breaker: Dict[str, Any] = Body(..., description="Circuit breaker configuration to add"),
    config: RiskConfig = Depends(get_risk_config)
) -> Dict[str, Any]:
    """
    Add a circuit breaker configuration.
    
    Args:
        circuit_breaker: Circuit breaker configuration to add.
        
    Returns:
        Dict containing the result of the operation.
    """
    try:
        # Check if a circuit breaker with the same name already exists
        for breaker in config.get_circuit_breakers():
            if breaker["name"] == circuit_breaker["name"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"A circuit breaker with the name '{circuit_breaker['name']}' already exists."
                )
        
        config.add_circuit_breaker(circuit_breaker)
        
        return {
            "status": "circuit_breaker_added",
            "circuit_breaker": circuit_breaker
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        
        raise HTTPException(
            status_code=400,
            detail=f"Error adding circuit breaker configuration: {str(e)}"
        )


@router.put("/circuit-breakers/{name}", summary="Update a circuit breaker configuration")
async def update_circuit_breaker_config(
    name: str = Path(..., description="Name of the circuit breaker to update"),
    updates: Dict[str, Any] = Body(..., description="Updates to apply to the circuit breaker"),
    config: RiskConfig = Depends(get_risk_config)
) -> Dict[str, Any]:
    """
    Update a circuit breaker configuration.
    
    Args:
        name: Name of the circuit breaker to update.
        updates: Updates to apply to the circuit breaker.
        
    Returns:
        Dict containing the result of the operation.
    """
    try:
        result = config.update_circuit_breaker(name, updates)
        
        if result:
            return {
                "status": "circuit_breaker_updated",
                "name": name,
                "updates": updates
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No circuit breaker found with the name '{name}'."
            )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        
        raise HTTPException(
            status_code=400,
            detail=f"Error updating circuit breaker configuration: {str(e)}"
        )


@router.delete("/circuit-breakers/{name}", summary="Remove a circuit breaker configuration")
async def remove_circuit_breaker_config(
    name: str = Path(..., description="Name of the circuit breaker to remove"),
    config: RiskConfig = Depends(get_risk_config)
) -> Dict[str, Any]:
    """
    Remove a circuit breaker configuration.
    
    Args:
        name: Name of the circuit breaker to remove.
        
    Returns:
        Dict containing the result of the operation.
    """
    try:
        result = config.remove_circuit_breaker(name)
        
        if result:
            return {
                "status": "circuit_breaker_removed",
                "name": name
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No circuit breaker found with the name '{name}'."
            )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        
        raise HTTPException(
            status_code=400,
            detail=f"Error removing circuit breaker configuration: {str(e)}"
        )


@router.post("/save", summary="Save the current configuration to a file")
async def save_config(
    config_path: Optional[str] = Body(None, description="Path where to save the configuration"),
    config: RiskConfig = Depends(get_risk_config)
) -> Dict[str, Any]:
    """
    Save the current configuration to a file.
    
    Args:
        config_path: Path where to save the configuration. If not provided,
                    a default path will be used.
        
    Returns:
        Dict containing status information.
    """
    # If no path provided, use default path
    if not config_path:
        config_path = "config/risk_config.json"
    
    # Validate the configuration before saving
    validation_result = config.validate_configuration()
    if not validation_result["is_valid"]:
        return {
            "status": "error",
            "message": "Invalid configuration cannot be saved",
            "errors": validation_result["errors"]
        }
    
    # Save the configuration
    success = config.save(config_path)
    
    if success:
        return {
            "status": "success",
            "message": f"Configuration saved to {config_path}",
            "path": config_path
        }
    else:
        return {
            "status": "error",
            "message": f"Failed to save configuration to {config_path}"
        }


@router.post("/reset", summary="Reset configuration to default values")
async def reset_config(
    config: RiskConfig = Depends(get_risk_config)
) -> Dict[str, Any]:
    """
    Reset the configuration to default values.
    
    Returns:
        Dict containing the result of the operation.
    """
    try:
        config.reset_to_default()
        
        return {
            "status": "config_reset",
            "message": "Configuration reset to default values."
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error resetting configuration: {str(e)}"
        ) 