"""
Configuration settings for Hummingbot MCP Server
"""

import os
from typing import Optional
from pydantic import BaseModel, Field, validator, field_validator
import aiohttp

from mcp_hummingbot.exceptions import ConfigurationError


class Settings(BaseModel):
    """Application settings"""
    
    # API Configuration
    api_url: str = Field(default="http://localhost:8000")
    api_username: str = Field(default="admin")
    api_password: str = Field(default="admin") 
    default_account: str = Field(default="master_account")
    
    # Connection settings
    connection_timeout: float = Field(default=30.0)
    max_retries: int = Field(default=3)
    retry_delay: float = Field(default=2.0)
    
    # Logging
    log_level: str = Field(default="INFO")
    
    @field_validator('api_url', mode='before')
    def validate_api_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('API URL must start with http:// or https://')
        return v
    
    @field_validator('log_level', mode='before')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()
    
    @property
    def client_timeout(self) -> aiohttp.ClientTimeout:
        """Get aiohttp ClientTimeout object"""
        return aiohttp.ClientTimeout(total=self.connection_timeout)


def get_settings() -> Settings:
    """Get application settings from environment variables"""
    try:
        return Settings(
            api_url=os.getenv("HUMMINGBOT_API_URL", "http://localhost:8000"),
            api_username=os.getenv("HUMMINGBOT_USERNAME", "admin"),
            api_password=os.getenv("HUMMINGBOT_PASSWORD", "admin"),
            connection_timeout=float(os.getenv("HUMMINGBOT_TIMEOUT", "30.0")),
            max_retries=int(os.getenv("HUMMINGBOT_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("HUMMINGBOT_RETRY_DELAY", "2.0")),
            log_level=os.getenv("HUMMINGBOT_LOG_LEVEL", "INFO"),
        )
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration: {e}")


# Global settings instance
settings = get_settings()