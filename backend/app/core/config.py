"""
Application Configuration

Centralizes all configuration settings following the Single Responsibility Principle.
Uses environment variables for configuration, following 12-factor app principles.
"""

import os
from typing import List, Optional
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
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    @property
    def cors_origins(self) -> List[str]:
        """Convert CORS origins string to list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Firebase Configuration
    FIREBASE_PROJECT_ID: Optional[str] = os.getenv("FIREBASE_PROJECT_ID")
    FIREBASE_SERVICE_ACCOUNT_PATH: Optional[str] = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    
    # Database Configuration
    DATABASE_TYPE: str = os.getenv("DATABASE_TYPE", "firebase")  # Options: firebase, memory
    
    def validate_firebase_config(self) -> bool:
        """
        Validate Firebase configuration if Firebase is selected as database.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If Firebase configuration is missing
        """
        if self.DATABASE_TYPE == "firebase":
            if not self.FIREBASE_PROJECT_ID:
                raise ValueError("FIREBASE_PROJECT_ID is required when using Firebase database")
            if not self.FIREBASE_SERVICE_ACCOUNT_PATH:
                raise ValueError("FIREBASE_SERVICE_ACCOUNT_PATH is required when using Firebase database")
            if not os.path.exists(self.FIREBASE_SERVICE_ACCOUNT_PATH):
                raise ValueError(f"Firebase service account file not found: {self.FIREBASE_SERVICE_ACCOUNT_PATH}")
        return True
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'

# Create global settings instance
settings = Settings()
