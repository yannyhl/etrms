"""
Enhanced Trading Risk Management System Configuration Settings
"""
import os
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    # API Configuration
    API_SECRET_KEY: str = "development_secret_key"
    API_TITLE: str = "Enhanced Trading Risk Management System API"
    API_DESCRIPTION: str = "API for managing trading risk, analyzing markets, and providing AI-powered trading assistance"
    API_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # JWT Configuration
    JWT_SECRET: str = "development_jwt_secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    
    # Database Configuration
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "etrms"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DATABASE_URI: Optional[str] = "sqlite:///./etrms.db"
    
    @validator("DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        """
        Assemble the database connection string from individual components.
        """
        if isinstance(v, str):
            return v
        
        try:
            return f"postgresql://{values.get('DB_USER')}:{values.get('DB_PASSWORD')}@{values.get('DB_HOST')}:{values.get('DB_PORT')}/{values.get('DB_NAME')}"
        except Exception:
            return "sqlite:///./etrms.db"
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # Exchange Configuration
    BINANCE_API_KEY: Optional[str] = "development_binance_api_key"
    BINANCE_API_SECRET: Optional[str] = "development_binance_api_secret"
    BINANCE_TESTNET: bool = True
    
    HYPERLIQUID_API_KEY: Optional[str] = "development_hyperliquid_api_key"
    HYPERLIQUID_API_SECRET: Optional[str] = "development_hyperliquid_api_secret"
    
    # AI Assistant Configuration
    ANTHROPIC_API_KEY: Optional[str] = "development_anthropic_api_key"
    AI_MODEL: str = "claude-3-opus-20240229"
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    
    # Development Mode
    DEBUG: bool = True
    TESTING: bool = True
    
    class Config:
        """
        Pydantic configuration class.
        """
        env_file = ".env"
        case_sensitive = True


settings = Settings()


def get_settings() -> Settings:
    """
    Get application settings.
    """
    return settings 