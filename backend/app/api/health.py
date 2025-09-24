"""
Health Check API Endpoints

Provides health status and system information endpoints.
Follows SOLID principles:
- Single Responsibility: Only handles health-related endpoints
- Interface Segregation: Simple, focused health check interface
"""

from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, status
from pydantic import BaseModel

class HealthResponse(BaseModel):
    """
    Health check response model.
    
    Provides structured health information following the
    Interface Segregation Principle - only includes necessary fields.
    """
    status: str
    timestamp: datetime
    version: str
    environment: str

# Create router following the Router pattern for modularity
router = APIRouter()

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Returns the health status of the API server"
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        HealthResponse: Current health status and system information
        
    This endpoint follows SOLID principles:
    - Single Responsibility: Only checks and returns health status
    - Dependency Inversion: Could be extended to depend on health service abstraction
    """
    from app.core.config import settings
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        environment=settings.ENVIRONMENT
    )

@router.get(
    "/health/detailed",
    status_code=status.HTTP_200_OK,
    summary="Detailed Health Check",
    description="Returns detailed health information including system metrics"
)
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check endpoint.
    
    Returns comprehensive system health information.
    This can be extended to include database connectivity,
    external service status, etc.
    
    Returns:
        Dict[str, Any]: Detailed health information
    """
    from app.core.config import settings
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "system": {
            "api_version": settings.API_V1_STR,
            "project_name": settings.PROJECT_NAME
        },
        "services": {
            "database": "not_configured",  # Will be updated in Phase 2
            "authentication": "not_configured"  # Will be updated in Phase 3
        }
    }
