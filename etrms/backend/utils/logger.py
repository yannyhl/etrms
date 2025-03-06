"""
Enhanced Trading Risk Management System Logger Utility
"""
import logging
import sys
from typing import Any, Dict, Optional

from config.settings import settings


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: The logger name, typically the module name.
        
    Returns:
        A configured logger instance.
    """
    # Configure the root logger
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("etrms.log"),
        ],
    )
    
    # Get a logger for the specified name
    logger = logging.getLogger(name)
    
    return logger


def log_event(
    logger: logging.Logger,
    event_type: str,
    message: str,
    level: str = "INFO",
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log a structured event.
    
    Args:
        logger: The logger instance.
        event_type: The type of event (e.g., "POSITION_CLOSED", "CIRCUIT_BREAKER_TRIGGERED").
        message: The message to log.
        level: The log level (e.g., "INFO", "WARNING", "ERROR").
        context: Additional context information to include in the log.
    """
    log_data = {
        "event_type": event_type,
        "message": message,
    }
    
    if context:
        log_data["context"] = context
    
    log_method = getattr(logger, level.lower())
    log_method(log_data) 