"""
Focus Tracker FastAPI Application

Main entry point for the Focus Tracker backend API.
This module follows SOLID principles:
- Single Responsibility: Main.py only handles FastAPI app creation and configuration
- Dependency Inversion: Depends on abstractions (future service interfaces)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.health import router as health_router
from app.core.config import settings

def create_app() -> FastAPI:
    """
    Factory function to create FastAPI application.
    
    Follows the Factory Pattern for application creation,
    making it easier to test and configure different environments.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title="Focus Tracker API",
        description="A simple and effective focus tracking application",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Configure CORS middleware for frontend integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Register API routes
    app.include_router(health_router, tags=["Health"])

    return app

# Create the application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
