"""
Enhanced Trading Risk Management System Configuration Settings
"""
import os
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseSettings, PostgresDsn, validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    # API Configuration
    API_SECRET_KEY: str
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
    JWT_SECRET: str
    JWT_ALGORITHM: str
    JWT_EXPIRATION_MINUTES: int
    
    # Database Configuration
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DATABASE_URI: Optional[PostgresDsn] = None
    
    @validator("DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        """
        Assemble the database connection string from individual components.
        """
        if isinstance(v, str):
            return v
        
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("DB_USER"),
            password=values.get("DB_PASSWORD"),
            host=values.get("DB_HOST"),
            port=values.get("DB_PORT"),
            path=f"/{values.get('DB_NAME') or ''}",
        )
    
    # Redis Configuration
    REDIS_HOST: str
    REDIS_PORT: int
    
    # Exchange Configuration
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_API_SECRET: Optional[str] = None
    BINANCE_TESTNET: bool = False
    
    HYPERLIQUID_API_KEY: Optional[str] = None
    HYPERLIQUID_API_SECRET: Optional[str] = None
    
    # AI Assistant Configuration
    ANTHROPIC_API_KEY: Optional[str] = None
    AI_MODEL: str = "claude-3-opus-20240229"
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    
    class Config:
        """
        Pydantic configuration class.
        """
        env_file = ".env"
        case_sensitive = True


# Create a settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Return the settings instance.
    """
    return settings 