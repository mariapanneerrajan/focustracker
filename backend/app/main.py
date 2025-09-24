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
from app.api.users import router as users_router
from app.api.sessions import router as sessions_router
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
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Register API routes
    app.include_router(health_router, tags=["Health"])
    app.include_router(users_router, prefix=settings.API_V1_STR, tags=["Users"])
    app.include_router(sessions_router, prefix=settings.API_V1_STR, tags=["Sessions"])

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
