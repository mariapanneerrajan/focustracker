"""
Dependency injection container and factory implementations.

This module implements the Factory and Dependency Injection patterns to provide
loose coupling between the application layers and enable easy switching between
different service implementations (Firebase vs Memory for testing).

Following SOLID principles:
- Single Responsibility: Each factory has one responsibility
- Open/Closed: New service implementations can be added without modification
- Liskov Substitution: All implementations are interchangeable
- Interface Segregation: Focused factory interfaces
- Dependency Inversion: High-level code depends on abstractions
"""

import logging
from typing import Protocol, Dict, Any, Optional
from enum import Enum

from ..core.config import settings
from ..domain.interfaces import IUserRepository, ISessionRepository, IAuthService, IDatabaseConnection
from ..domain.exceptions import ConfigurationError


logger = logging.getLogger(__name__)


class DatabaseProvider(str, Enum):
    """Enumeration of supported database providers."""
    FIREBASE = "firebase"
    MEMORY = "memory"


class IServiceFactory(Protocol):
    """
    Protocol defining the service factory interface.
    
    Follows Interface Segregation Principle by providing a focused
    interface for service creation without implementation details.
    """
    
    async def create_database_connection(self) -> IDatabaseConnection:
        """Create database connection instance."""
        ...
    
    async def create_user_repository(self, connection: IDatabaseConnection) -> IUserRepository:
        """Create user repository instance."""
        ...
    
    async def create_session_repository(self, connection: IDatabaseConnection) -> ISessionRepository:
        """Create session repository instance."""
        ...
    
    async def create_auth_service(self, connection: IDatabaseConnection) -> IAuthService:
        """Create authentication service instance."""
        ...


class FirebaseServiceFactory:
    """
    Factory for creating Firebase-based service implementations.
    
    Implements the Factory pattern to create Firebase service instances,
    following SOLID principles by depending on abstractions and providing
    a single point for Firebase service creation.
    """
    
    async def create_database_connection(self) -> IDatabaseConnection:
        """Create Firebase database connection."""
        try:
            from ..adapters.firebase_adapter import FirebaseConnection
            
            connection = FirebaseConnection()
            await connection.connect()
            
            logger.info("Created Firebase database connection")
            return connection
            
        except Exception as e:
            logger.error(f"Failed to create Firebase connection: {e}")
            raise ConfigurationError(
                message="Failed to create Firebase database connection",
                details={"provider": "firebase", "error": str(e)},
                cause=e
            )
    
    async def create_user_repository(self, connection: IDatabaseConnection) -> IUserRepository:
        """Create Firebase user repository."""
        try:
            from ..adapters.firebase_adapter import FirebaseUserRepository
            
            repository = FirebaseUserRepository(connection)
            logger.info("Created Firebase user repository")
            return repository
            
        except Exception as e:
            logger.error(f"Failed to create Firebase user repository: {e}")
            raise ConfigurationError(
                message="Failed to create Firebase user repository",
                details={"provider": "firebase", "error": str(e)},
                cause=e
            )
    
    async def create_session_repository(self, connection: IDatabaseConnection) -> ISessionRepository:
        """Create Firebase session repository."""
        try:
            from ..adapters.firebase_adapter import FirebaseSessionRepository
            
            repository = FirebaseSessionRepository(connection)
            logger.info("Created Firebase session repository")
            return repository
            
        except Exception as e:
            logger.error(f"Failed to create Firebase session repository: {e}")
            raise ConfigurationError(
                message="Failed to create Firebase session repository",
                details={"provider": "firebase", "error": str(e)},
                cause=e
            )
    
    async def create_auth_service(self, connection: IDatabaseConnection) -> IAuthService:
        """Create Firebase authentication service."""
        try:
            from ..adapters.firebase_adapter import FirebaseAuthService
            
            auth_service = FirebaseAuthService(connection)
            logger.info("Created Firebase authentication service")
            return auth_service
            
        except Exception as e:
            logger.error(f"Failed to create Firebase auth service: {e}")
            raise ConfigurationError(
                message="Failed to create Firebase authentication service",
                details={"provider": "firebase", "error": str(e)},
                cause=e
            )


class MemoryServiceFactory:
    """
    Factory for creating in-memory service implementations.
    
    Provides memory-based implementations ideal for testing and development
    environments where external dependencies should be avoided.
    """
    
    async def create_database_connection(self) -> IDatabaseConnection:
        """Create in-memory database connection."""
        try:
            from ..repositories.memory_repository import MemoryConnection
            
            connection = MemoryConnection()
            await connection.connect()
            
            logger.info("Created memory database connection")
            return connection
            
        except Exception as e:
            logger.error(f"Failed to create memory connection: {e}")
            raise ConfigurationError(
                message="Failed to create memory database connection",
                details={"provider": "memory", "error": str(e)},
                cause=e
            )
    
    async def create_user_repository(self, connection: IDatabaseConnection) -> IUserRepository:
        """Create in-memory user repository."""
        try:
            from ..repositories.memory_repository import MemoryUserRepository
            
            repository = MemoryUserRepository(connection)
            logger.info("Created memory user repository")
            return repository
            
        except Exception as e:
            logger.error(f"Failed to create memory user repository: {e}")
            raise ConfigurationError(
                message="Failed to create memory user repository",
                details={"provider": "memory", "error": str(e)},
                cause=e
            )
    
    async def create_session_repository(self, connection: IDatabaseConnection) -> ISessionRepository:
        """Create in-memory session repository."""
        try:
            from ..repositories.memory_repository import MemorySessionRepository
            
            repository = MemorySessionRepository(connection)
            logger.info("Created memory session repository")
            return repository
            
        except Exception as e:
            logger.error(f"Failed to create memory session repository: {e}")
            raise ConfigurationError(
                message="Failed to create memory session repository",
                details={"provider": "memory", "error": str(e)},
                cause=e
            )
    
    async def create_auth_service(self, connection: IDatabaseConnection) -> IAuthService:
        """Create in-memory authentication service."""
        try:
            from ..repositories.memory_repository import MemoryAuthService
            
            auth_service = MemoryAuthService(connection)
            logger.info("Created memory authentication service")
            return auth_service
            
        except Exception as e:
            logger.error(f"Failed to create memory auth service: {e}")
            raise ConfigurationError(
                message="Failed to create memory authentication service",
                details={"provider": "memory", "error": str(e)},
                cause=e
            )


class ServiceContainer:
    """
    Dependency injection container managing service instances.
    
    Implements the Dependency Injection pattern with singleton management
    to provide centralized service instance management throughout the application.
    
    Follows SOLID principles:
    - Single Responsibility: Only manages service dependencies
    - Open/Closed: New providers can be added without modification
    - Liskov Substitution: All service implementations are interchangeable
    - Interface Segregation: Focused on dependency management only
    - Dependency Inversion: Manages abstractions, not concrete implementations
    """
    
    def __init__(self, provider: Optional[DatabaseProvider] = None):
        """
        Initialize service container.
        
        Args:
            provider: Database provider to use. If None, reads from settings.
        """
        self._provider = provider or DatabaseProvider(settings.DATABASE_TYPE)
        self._services: Dict[str, Any] = {}
        self._factory: Optional[IServiceFactory] = None
        self._initialized = False
        
        logger.info(f"Initialized service container with provider: {self._provider}")
    
    async def initialize(self) -> None:
        """
        Initialize the service container with the configured provider.
        
        Raises:
            ConfigurationError: If provider configuration is invalid
        """
        if self._initialized:
            return
        
        try:
            # Create appropriate factory based on provider
            if self._provider == DatabaseProvider.FIREBASE:
                self._factory = FirebaseServiceFactory()
            elif self._provider == DatabaseProvider.MEMORY:
                self._factory = MemoryServiceFactory()
            else:
                raise ConfigurationError(
                    message=f"Unsupported database provider: {self._provider}",
                    config_key="DATABASE_TYPE"
                )
            
            # Create and store database connection
            connection = await self._factory.create_database_connection()
            self._services["connection"] = connection
            
            # Create and store repositories and services
            self._services["user_repository"] = await self._factory.create_user_repository(connection)
            self._services["session_repository"] = await self._factory.create_session_repository(connection)
            self._services["auth_service"] = await self._factory.create_auth_service(connection)
            
            self._initialized = True
            logger.info(f"Service container initialized successfully with {self._provider} provider")
            
        except Exception as e:
            logger.error(f"Failed to initialize service container: {e}")
            raise ConfigurationError(
                message="Failed to initialize service container",
                details={"provider": self._provider.value, "error": str(e)},
                cause=e
            )
    
    async def shutdown(self) -> None:
        """
        Shutdown the service container and cleanup resources.
        """
        try:
            # Disconnect database connection if exists
            connection = self._services.get("connection")
            if connection and hasattr(connection, "disconnect"):
                await connection.disconnect()
            
            # Clear all services
            self._services.clear()
            self._factory = None
            self._initialized = False
            
            logger.info("Service container shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during service container shutdown: {e}")
    
    def get_database_connection(self) -> IDatabaseConnection:
        """
        Get database connection instance.
        
        Returns:
            Database connection instance
            
        Raises:
            ConfigurationError: If container not initialized or connection not found
        """
        self._ensure_initialized()
        connection = self._services.get("connection")
        if not connection:
            raise ConfigurationError(
                message="Database connection not found in service container",
                details={"provider": self._provider.value}
            )
        return connection
    
    def get_user_repository(self) -> IUserRepository:
        """
        Get user repository instance.
        
        Returns:
            User repository instance
            
        Raises:
            ConfigurationError: If container not initialized or repository not found
        """
        self._ensure_initialized()
        repository = self._services.get("user_repository")
        if not repository:
            raise ConfigurationError(
                message="User repository not found in service container",
                details={"provider": self._provider.value}
            )
        return repository
    
    @property
    def user_repository(self) -> IUserRepository:
        """Property-style access to the user repository."""
        return self.get_user_repository()

    def get_session_repository(self) -> ISessionRepository:
        """
        Get session repository instance.
        
        Returns:
            Session repository instance
            
        Raises:
            ConfigurationError: If container not initialized or repository not found
        """
        self._ensure_initialized()
        repository = self._services.get("session_repository")
        if not repository:
            raise ConfigurationError(
                message="Session repository not found in service container",
                details={"provider": self._provider.value}
            )
        return repository
    
    @property
    def session_repository(self) -> ISessionRepository:
        """Property-style access to the session repository."""
        return self.get_session_repository()

    def get_auth_service(self) -> IAuthService:
        """
        Get authentication service instance.
        
        Returns:
            Authentication service instance
            
        Raises:
            ConfigurationError: If container not initialized or service not found
        """
        self._ensure_initialized()
        auth_service = self._services.get("auth_service")
        if not auth_service:
            raise ConfigurationError(
                message="Authentication service not found in service container",
                details={"provider": self._provider.value}
            )
        return auth_service
    
    @property
    def auth_service(self) -> IAuthService:
        """Property-style access to the authentication service."""
        return self.get_auth_service()

    @property
    def provider(self) -> DatabaseProvider:
        """Get the current database provider."""
        return self._provider
    
    @property
    def is_initialized(self) -> bool:
        """Check if container is initialized."""
        return self._initialized
    
    def _ensure_initialized(self) -> None:
        """
        Ensure container is initialized.
        
        Raises:
            ConfigurationError: If container is not initialized
        """
        if not self._initialized:
            raise ConfigurationError(
                message="Service container not initialized. Call initialize() first.",
                details={"provider": self._provider.value}
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all services in the container.
        
        Returns:
            Dictionary containing health check results for all services
        """
        health_results = {
            "container": {
                "status": "healthy" if self._initialized else "unhealthy",
                "provider": self._provider.value,
                "initialized": self._initialized,
                "services_count": len(self._services)
            }
        }
        
        if self._initialized:
            try:
                # Check database connection health
                connection = self._services.get("connection")
                if connection and hasattr(connection, "health_check"):
                    health_results["database"] = await connection.health_check()
                else:
                    health_results["database"] = {
                        "status": "unknown",
                        "details": "No health check available"
                    }
                    
            except Exception as e:
                health_results["database"] = {
                    "status": "unhealthy",
                    "details": {"error": str(e)}
                }
        
        return health_results


# Global service container instance
_service_container: Optional[ServiceContainer] = None


async def get_service_container() -> ServiceContainer:
    """
    Get the global service container instance.
    
    Creates and initializes the container if it doesn't exist.
    
    Returns:
        Global service container instance
        
    Raises:
        ConfigurationError: If container initialization fails
    """
    global _service_container
    
    if _service_container is None:
        _service_container = ServiceContainer()
        await _service_container.initialize()
    
    return _service_container


async def shutdown_service_container() -> None:
    """
    Shutdown the global service container.
    
    Used for cleanup during application shutdown.
    """
    global _service_container
    
    if _service_container:
        await _service_container.shutdown()
        _service_container = None


# Convenience functions for getting service instances
async def get_user_repository() -> IUserRepository:
    """Get user repository instance from global container."""
    container = await get_service_container()
    return container.get_user_repository()


async def get_session_repository() -> ISessionRepository:
    """Get session repository instance from global container."""
    container = await get_service_container()
    return container.get_session_repository()


async def get_auth_service() -> IAuthService:
    """Get authentication service instance from global container."""
    container = await get_service_container()
    return container.get_auth_service()


async def get_database_connection() -> IDatabaseConnection:
    """Get database connection instance from global container."""
    container = await get_service_container()
    return container.get_database_connection()
