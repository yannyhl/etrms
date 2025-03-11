"""
Enhanced Trading Risk Management System Risk Configuration

This module manages risk configuration settings for the risk engine.
"""
import json
import os
from typing import Dict, List, Any, Optional

from utils.logger import get_logger, log_event


class RiskConfig:
    """
    Manages risk configuration settings for the risk engine.
    
    This includes exposure limits, drawdown thresholds, circuit breaker
    conditions, and other risk management parameters.
    """
    
    DEFAULT_CONFIG = {
        "global": {
            "max_total_exposure_usd": 100000.0,
            "max_single_position_usd": 10000.0,
            "max_leverage": 10.0,
            "max_drawdown_percentage": 0.15,  # 15%
            "risk_management_enabled": True
        },
        "symbols": {
            "BTCUSDT": {
                "max_position_size": 1.0,
                "max_leverage": 5.0,
                "max_drawdown_percentage": 0.1,  # 10%
                "take_profit_percentage": 0.05,  # 5%
                "stop_loss_percentage": 0.03    # 3%
            }
        },
        "exchanges": {
            "binance": {
                "max_total_exposure_usd": 50000.0,
                "risk_management_enabled": True
            },
            "hyperliquid": {
                "max_total_exposure_usd": 50000.0,
                "risk_management_enabled": True
            }
        },
        "circuit_breakers": [
            {
                "name": "max_drawdown_breaker",
                "description": "Closes positions when drawdown exceeds threshold",
                "enabled": True,
                "parameters": {
                    "threshold": 0.15  # 15%
                }
            },
            {
                "name": "max_exposure_breaker",
                "description": "Prevents new positions when total exposure exceeds threshold",
                "enabled": True,
                "parameters": {
                    "threshold": 100000.0  # $100,000
                }
            }
        ]
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the risk configuration manager.
        
        Args:
            config_path: Optional path to a JSON configuration file.
        """
        self.logger = get_logger(__name__)
        self.config = self.DEFAULT_CONFIG.copy()
        
        # If config_path is provided, load configuration from file
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                
                # Merge the loaded config with the default config
                self._merge_config(loaded_config)
                
                log_event(
                    self.logger,
                    "RISK_CONFIG_LOADED",
                    f"Loaded risk configuration from {config_path}",
                    context={"config_path": config_path}
                )
            except Exception as e:
                log_event(
                    self.logger,
                    "RISK_CONFIG_LOAD_ERROR",
                    f"Error loading risk configuration from {config_path}: {str(e)}",
                    level="ERROR",
                    context={"config_path": config_path, "error": str(e)}
                )
                # Use default configuration
                log_event(
                    self.logger,
                    "RISK_CONFIG_DEFAULT",
                    "Using default risk configuration"
                )
        else:
            log_event(
                self.logger,
                "RISK_CONFIG_DEFAULT",
                "Using default risk configuration"
            )
    
    def save(self, config_path: Optional[str] = None) -> bool:
        """
        Save the current configuration to a JSON file.
        
        Args:
            config_path: Path to save the configuration. If None, uses the path from initialization.
            
        Returns:
            True if the configuration was saved successfully, False otherwise.
        """
        if not config_path:
            log_event(
                self.logger,
                "RISK_CONFIG_SAVE_ERROR",
                "No config path provided for saving",
                level="ERROR"
            )
            return False
            
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
                
            log_event(
                self.logger,
                "RISK_CONFIG_SAVED",
                f"Saved risk configuration to {config_path}",
                context={"config_path": config_path}
            )
            return True
        except Exception as e:
            log_event(
                self.logger,
                "RISK_CONFIG_SAVE_ERROR",
                f"Error saving risk configuration to {config_path}: {str(e)}",
                level="ERROR",
                context={"config_path": config_path, "error": str(e)}
            )
            return False
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate the current configuration and return validation results.
        
        Returns:
            Dictionary with validation results including any errors.
        """
        validation_result = {
            "is_valid": True,
            "errors": []
        }
        
        # Validate global configuration
        if "global" not in self.config:
            validation_result["is_valid"] = False
            validation_result["errors"].append("Missing global configuration")
        else:
            global_config = self.config["global"]
            
            # Check required global parameters
            required_params = [
                "max_total_exposure_usd",
                "max_single_position_usd",
                "max_leverage",
                "max_drawdown_percentage",
                "risk_management_enabled"
            ]
            
            for param in required_params:
                if param not in global_config:
                    validation_result["is_valid"] = False
                    validation_result["errors"].append(f"Missing required global parameter: {param}")
        
        # Validate circuit breakers
        if "circuit_breakers" not in self.config or not isinstance(self.config["circuit_breakers"], list):
            validation_result["is_valid"] = False
            validation_result["errors"].append("Missing or invalid circuit breakers configuration")
        else:
            for i, breaker in enumerate(self.config["circuit_breakers"]):
                # Check required circuit breaker parameters
                required_params = ["name", "description", "enabled", "parameters"]
                
                for param in required_params:
                    if param not in breaker:
                        validation_result["is_valid"] = False
                        validation_result["errors"].append(f"Missing required parameter {param} in circuit breaker at index {i}")
                
                # Ensure circuit breaker names are unique
                name_count = sum(1 for cb in self.config["circuit_breakers"] if cb.get("name") == breaker.get("name"))
                if name_count > 1:
                    validation_result["is_valid"] = False
                    validation_result["errors"].append(f"Duplicate circuit breaker name: {breaker.get('name')}")
        
        return validation_result
    
    def get_default_symbol_config(self) -> Dict[str, Any]:
        """
        Get default configuration for a symbol.
        
        Returns:
            Default symbol configuration.
        """
        return {
            "max_position_size": 1.0,
            "max_leverage": 5.0,
            "max_drawdown_percentage": 0.1,  # 10%
            "take_profit_percentage": 0.05,  # 5%
            "stop_loss_percentage": 0.03     # 3%
        }
    
    def get_default_exchange_config(self) -> Dict[str, Any]:
        """
        Get default configuration for an exchange.
        
        Returns:
            Default exchange configuration.
        """
        return {
            "max_total_exposure_usd": 50000.0,
            "risk_management_enabled": True
        }
    
    def create_default_circuit_breakers(self) -> List[Dict[str, Any]]:
        """
        Create a set of default circuit breakers.
        
        Returns:
            List of default circuit breaker configurations.
        """
        return [
            {
                "name": "max_drawdown_breaker",
                "description": "Closes positions when drawdown exceeds threshold",
                "enabled": True,
                "parameters": {
                    "threshold": 0.15  # 15%
                }
            },
            {
                "name": "max_exposure_breaker",
                "description": "Prevents new positions when total exposure exceeds threshold",
                "enabled": True,
                "parameters": {
                    "threshold": 0.8  # 80% of max
                }
            },
            {
                "name": "trailing_stop_breaker",
                "description": "Implements a trailing stop for all positions",
                "enabled": True,
                "parameters": {
                    "trail_percentage": 2.0  # 2%
                }
            },
            {
                "name": "volatility_breaker",
                "description": "Reduces position sizes during high volatility",
                "enabled": True,
                "parameters": {
                    "volatility_threshold": 0.3,  # 30% annualized
                    "reduction_factor": 0.5      # Reduce by 50%
                }
            }
        ]
    
    def _merge_config(self, loaded_config: Dict[str, Any]) -> None:
        """
        Merge loaded configuration with current configuration.
        
        Args:
            loaded_config: Configuration loaded from file.
        """
        # Merge global configuration
        if "global" in loaded_config:
            if "global" not in self.config:
                self.config["global"] = {}
            
            for key, value in loaded_config["global"].items():
                self.config["global"][key] = value
        
        # Merge symbols configuration
        if "symbols" in loaded_config:
            if "symbols" not in self.config:
                self.config["symbols"] = {}
            
            for symbol, symbol_config in loaded_config["symbols"].items():
                if symbol not in self.config["symbols"]:
                    self.config["symbols"][symbol] = self.get_default_symbol_config()
                
                for key, value in symbol_config.items():
                    self.config["symbols"][symbol][key] = value
        
        # Merge exchanges configuration
        if "exchanges" in loaded_config:
            if "exchanges" not in self.config:
                self.config["exchanges"] = {}
            
            for exchange, exchange_config in loaded_config["exchanges"].items():
                if exchange not in self.config["exchanges"]:
                    self.config["exchanges"][exchange] = self.get_default_exchange_config()
                
                for key, value in exchange_config.items():
                    self.config["exchanges"][exchange][key] = value
        
        # Merge circuit breakers
        if "circuit_breakers" in loaded_config:
            self.config["circuit_breakers"] = loaded_config["circuit_breakers"]
    
    def get_exchange_names(self) -> List[str]:
        """
        Get a list of all configured exchanges.
        
        Returns:
            List of exchange names.
        """
        return list(self.config.get("exchanges", {}).keys())
    
    def get_symbol_names(self) -> List[str]:
        """
        Get a list of all configured symbols.
        
        Returns:
            List of symbol names.
        """
        return list(self.config.get("symbols", {}).keys())
    
    def is_risk_management_enabled(self, exchange: Optional[str] = None) -> bool:
        """
        Check if risk management is enabled globally or for a specific exchange.
        
        Args:
            exchange: Optional exchange name to check.
            
        Returns:
            True if risk management is enabled, False otherwise.
        """
        # Check if risk management is enabled globally
        global_enabled = self.config.get("global", {}).get("risk_management_enabled", True)
        
        if not exchange:
            return global_enabled
            
        # Check if risk management is enabled for the specific exchange
        exchange_config = self.get_exchange_config(exchange)
        exchange_enabled = exchange_config.get("risk_management_enabled", global_enabled)
        
        return global_enabled and exchange_enabled
    
    def reset_to_default(self) -> None:
        """
        Reset the configuration to the default values.
        """
        self.config = self.DEFAULT_CONFIG.copy()
        
        log_event(
            self.logger,
            "CONFIG_RESET",
            "Reset risk configuration to default values"
        )
    
    def get_global_config(self) -> Dict[str, Any]:
        """
        Get global risk configuration.
        
        Returns:
            Dict containing global risk settings.
        """
        return self.config["global"].copy()
    
    def get_symbol_config(self, symbol: str) -> Dict[str, Any]:
        """
        Get risk configuration for a specific symbol.
        
        Args:
            symbol: The trading pair symbol.
            
        Returns:
            Dict containing symbol-specific risk settings.
        """
        # Symbol config with global defaults
        symbol_config = self.get_global_config()
        
        # Override with symbol-specific settings if they exist
        if symbol in self.config["symbols"]:
            symbol_config.update(self.config["symbols"][symbol])
        
        return symbol_config
    
    def get_exchange_config(self, exchange: str) -> Dict[str, Any]:
        """
        Get risk configuration for a specific exchange.
        
        Args:
            exchange: The exchange name.
            
        Returns:
            Dict containing exchange-specific risk settings.
        """
        # Exchange config with global defaults
        exchange_config = self.get_global_config()
        
        # Override with exchange-specific settings if they exist
        if exchange in self.config["exchanges"]:
            exchange_config.update(self.config["exchanges"][exchange])
        
        return exchange_config
    
    def get_circuit_breakers(self) -> List[Dict[str, Any]]:
        """
        Get circuit breaker configurations.
        
        Returns:
            List of circuit breaker configurations.
        """
        return self.config["circuit_breakers"].copy()
    
    def set_global_param(self, param: str, value: Any) -> None:
        """
        Set a global risk parameter.
        
        Args:
            param: The parameter name.
            value: The parameter value.
        """
        self.config["global"][param] = value
        
        log_event(
            self.logger,
            "GLOBAL_PARAM_UPDATED",
            f"Updated global parameter {param}",
            context={"param": param, "value": value}
        )
    
    def set_symbol_param(self, symbol: str, param: str, value: Any) -> None:
        """
        Set a symbol-specific risk parameter.
        
        Args:
            symbol: The trading pair symbol.
            param: The parameter name.
            value: The parameter value.
        """
        if symbol not in self.config["symbols"]:
            self.config["symbols"][symbol] = {}
            
        self.config["symbols"][symbol][param] = value
        
        log_event(
            self.logger,
            "SYMBOL_PARAM_UPDATED",
            f"Updated {param} for {symbol}",
            context={"symbol": symbol, "param": param, "value": value}
        )
    
    def set_exchange_param(self, exchange: str, param: str, value: Any) -> None:
        """
        Set an exchange-specific risk parameter.
        
        Args:
            exchange: The exchange name.
            param: The parameter name.
            value: The parameter value.
        """
        if exchange not in self.config["exchanges"]:
            self.config["exchanges"][exchange] = {}
            
        self.config["exchanges"][exchange][param] = value
        
        log_event(
            self.logger,
            "EXCHANGE_PARAM_UPDATED",
            f"Updated {param} for {exchange}",
            context={"exchange": exchange, "param": param, "value": value}
        )
    
    def add_circuit_breaker(self, circuit_breaker: Dict[str, Any]) -> None:
        """
        Add a circuit breaker configuration.
        
        Args:
            circuit_breaker: The circuit breaker configuration.
        """
        self.config["circuit_breakers"].append(circuit_breaker)
        
        log_event(
            self.logger,
            "CIRCUIT_BREAKER_ADDED",
            f"Added circuit breaker: {circuit_breaker['name']}",
            context={"circuit_breaker": circuit_breaker}
        )
    
    def update_circuit_breaker(self, name: str, updates: Dict[str, Any]) -> bool:
        """
        Update a circuit breaker configuration.
        
        Args:
            name: The name of the circuit breaker.
            updates: The updates to apply.
            
        Returns:
            True if the circuit breaker was updated, False if it wasn't found.
        """
        for i, breaker in enumerate(self.config["circuit_breakers"]):
            if breaker["name"] == name:
                self.config["circuit_breakers"][i].update(updates)
                
                log_event(
                    self.logger,
                    "CIRCUIT_BREAKER_UPDATED",
                    f"Updated circuit breaker: {name}",
                    context={"circuit_breaker": name, "updates": updates}
                )
                
                return True
                
        return False
    
    def remove_circuit_breaker(self, name: str) -> bool:
        """
        Remove a circuit breaker configuration.
        
        Args:
            name: The name of the circuit breaker.
            
        Returns:
            True if the circuit breaker was removed, False if it wasn't found.
        """
        for i, breaker in enumerate(self.config["circuit_breakers"]):
            if breaker["name"] == name:
                self.config["circuit_breakers"].pop(i)
                
                log_event(
                    self.logger,
                    "CIRCUIT_BREAKER_REMOVED",
                    f"Removed circuit breaker: {name}",
                    context={"circuit_breaker": name}
                )
                
                return True
                
        return False 