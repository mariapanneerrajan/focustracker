"""
Application Configuration

Centralizes all configuration settings following the Single Responsibility Principle.
Uses environment variables for configuration, following 12-factor app principles.
"""

import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application settings configuration.
    
    Follows SOLID principles:
    - Single Responsibility: Only handles configuration
    - Open/Closed: Can be extended with new settings without modification
    """
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Focus Tracker"
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings()
