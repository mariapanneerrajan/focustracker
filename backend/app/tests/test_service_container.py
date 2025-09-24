"""
Tests for service container and dependency injection.

This module tests the service container implementation, factory pattern,
and dependency injection functionality. Tests validate that different
service implementations can be created and swapped seamlessly.
"""

import pytest
from unittest.mock import patch, AsyncMock

from ..services.container import (
    ServiceContainer, DatabaseProvider, FirebaseServiceFactory, MemoryServiceFactory,
    get_service_container, shutdown_service_container
)
from ..domain.exceptions import ConfigurationError


class TestDatabaseProvider:
    """Test cases for DatabaseProvider enum."""
    
    def test_database_provider_values(self):
        """Test database provider enum values."""
        assert DatabaseProvider.FIREBASE == "firebase"
        assert DatabaseProvider.MEMORY == "memory"
        
        # Test string conversion
        assert str(DatabaseProvider.FIREBASE) == "firebase"
        assert str(DatabaseProvider.MEMORY) == "memory"


class TestMemoryServiceFactory:
    """Test cases for MemoryServiceFactory."""
    
    async def test_create_database_connection(self):
        """Test creating memory database connection."""
        factory = MemoryServiceFactory()
        connection = await factory.create_database_connection()
        
        assert connection is not None
        assert connection.is_connected()
        
        # Cleanup
        await connection.disconnect()
    
    async def test_create_user_repository(self):
        """Test creating memory user repository."""
        factory = MemoryServiceFactory()
        connection = await factory.create_database_connection()
        
        repository = await factory.create_user_repository(connection)
        
        assert repository is not None
        assert hasattr(repository, 'create')
        assert hasattr(repository, 'find_by_id')
        
        # Cleanup
        await connection.disconnect()
    
    async def test_create_session_repository(self):
        """Test creating memory session repository."""
        factory = MemoryServiceFactory()
        connection = await factory.create_database_connection()
        
        repository = await factory.create_session_repository(connection)
        
        assert repository is not None
        assert hasattr(repository, 'create')
        assert hasattr(repository, 'find_by_id')
        
        # Cleanup
        await connection.disconnect()
    
    async def test_create_auth_service(self):
        """Test creating memory auth service."""
        factory = MemoryServiceFactory()
        connection = await factory.create_database_connection()
        
        auth_service = await factory.create_auth_service(connection)
        
        assert auth_service is not None
        assert hasattr(auth_service, 'create_user_account')
        assert hasattr(auth_service, 'verify_credentials')
        
        # Cleanup
        await connection.disconnect()


@patch('app.services.container.settings')
class TestFirebaseServiceFactory:
    """Test cases for FirebaseServiceFactory (mocked)."""
    
    async def test_create_database_connection_success(self, mock_settings):
        """Test creating Firebase connection successfully."""
        # Mock settings
        mock_settings.DATABASE_TYPE = "firebase"
        mock_settings.FIREBASE_PROJECT_ID = "test-project"
        mock_settings.FIREBASE_SERVICE_ACCOUNT_PATH = "/path/to/service-account.json"
        mock_settings.validate_firebase_config.return_value = True
        
        # Mock Firebase imports and initialization
        with patch('app.services.container.firebase_admin'), \
             patch('app.services.container.credentials'), \
             patch('app.services.container.firestore'):
            
            # Mock the Firebase connection class
            with patch('app.adapters.firebase_adapter.FirebaseConnection') as mock_connection_class:
                mock_connection = AsyncMock()
                mock_connection.is_connected.return_value = True
                mock_connection_class.return_value = mock_connection
                
                factory = FirebaseServiceFactory()
                connection = await factory.create_database_connection()
                
                assert connection is not None
                mock_connection.connect.assert_called_once()
    
    async def test_create_database_connection_config_error(self, mock_settings):
        """Test Firebase connection creation with config error."""
        # Mock settings to raise configuration error
        mock_settings.validate_firebase_config.side_effect = ValueError("Missing config")
        
        factory = FirebaseServiceFactory()
        
        with pytest.raises(ConfigurationError) as exc_info:
            await factory.create_database_connection()
        
        assert "Failed to create Firebase database connection" in str(exc_info.value)


class TestServiceContainer:
    """Test cases for ServiceContainer."""
    
    async def test_container_initialization_memory(self):
        """Test container initialization with memory provider."""
        container = ServiceContainer(DatabaseProvider.MEMORY)
        
        assert not container.is_initialized
        assert container.provider == DatabaseProvider.MEMORY
        
        # Initialize container
        await container.initialize()
        
        assert container.is_initialized
        
        # Cleanup
        await container.shutdown()
    
    async def test_container_initialization_default(self):
        """Test container initialization with default provider from settings."""
        with patch('app.services.container.settings') as mock_settings:
            mock_settings.DATABASE_TYPE = "memory"
            
            container = ServiceContainer()
            assert container.provider == DatabaseProvider.MEMORY
    
    async def test_container_double_initialization(self):
        """Test that double initialization is safe."""
        container = ServiceContainer(DatabaseProvider.MEMORY)
        
        # Initialize twice
        await container.initialize()
        await container.initialize()  # Should not raise error
        
        assert container.is_initialized
        
        # Cleanup
        await container.shutdown()
    
    async def test_container_get_services(self):
        """Test getting services from container."""
        container = ServiceContainer(DatabaseProvider.MEMORY)
        await container.initialize()
        
        # Test getting all services
        connection = container.get_database_connection()
        user_repo = container.get_user_repository()
        session_repo = container.get_session_repository()
        auth_service = container.get_auth_service()
        
        assert connection is not None
        assert user_repo is not None
        assert session_repo is not None
        assert auth_service is not None
        
        # Cleanup
        await container.shutdown()
    
    async def test_container_get_services_not_initialized(self):
        """Test getting services from uninitialized container."""
        container = ServiceContainer(DatabaseProvider.MEMORY)
        
        with pytest.raises(ConfigurationError) as exc_info:
            container.get_database_connection()
        
        assert "Service container not initialized" in str(exc_info.value)
    
    async def test_container_unsupported_provider(self):
        """Test container with unsupported provider."""
        # Mock an invalid provider
        with patch('app.services.container.DatabaseProvider') as mock_provider:
            mock_provider.return_value = "invalid_provider"
            
            container = ServiceContainer()
            container._provider = "invalid_provider"
            
            with pytest.raises(ConfigurationError) as exc_info:
                await container.initialize()
            
            assert "Unsupported database provider" in str(exc_info.value)
    
    async def test_container_health_check(self):
        """Test container health check."""
        container = ServiceContainer(DatabaseProvider.MEMORY)
        
        # Health check when not initialized
        health = await container.health_check()
        assert health["container"]["status"] == "unhealthy"
        assert not health["container"]["initialized"]
        
        # Initialize and check again
        await container.initialize()
        health = await container.health_check()
        assert health["container"]["status"] == "healthy"
        assert health["container"]["initialized"]
        assert "database" in health
        
        # Cleanup
        await container.shutdown()
    
    async def test_container_shutdown(self):
        """Test container shutdown."""
        container = ServiceContainer(DatabaseProvider.MEMORY)
        await container.initialize()
        
        assert container.is_initialized
        
        # Shutdown
        await container.shutdown()
        
        assert not container.is_initialized
    
    async def test_container_shutdown_error_handling(self):
        """Test container shutdown with errors."""
        container = ServiceContainer(DatabaseProvider.MEMORY)
        await container.initialize()
        
        # Mock connection disconnect to raise error
        connection = container.get_database_connection()
        with patch.object(connection, 'disconnect', side_effect=Exception("Disconnect error")):
            # Should not raise error, just log it
            await container.shutdown()
        
        assert not container.is_initialized


class TestGlobalServiceContainer:
    """Test cases for global service container functions."""
    
    async def test_get_global_container(self):
        """Test getting global service container."""
        with patch('app.services.container.settings') as mock_settings:
            mock_settings.DATABASE_TYPE = "memory"
            
            # Get container (should create and initialize)
            container1 = await get_service_container()
            assert container1 is not None
            assert container1.is_initialized
            
            # Get container again (should return same instance)
            container2 = await get_service_container()
            assert container1 is container2
            
            # Cleanup
            await shutdown_service_container()
    
    async def test_shutdown_global_container(self):
        """Test shutting down global service container."""
        with patch('app.services.container.settings') as mock_settings:
            mock_settings.DATABASE_TYPE = "memory"
            
            # Get container
            container = await get_service_container()
            assert container.is_initialized
            
            # Shutdown
            await shutdown_service_container()
            
            # Container should be reset
            # Getting container again should create new instance
            new_container = await get_service_container()
            assert new_container is not container
            
            # Cleanup
            await shutdown_service_container()
    
    async def test_shutdown_no_container(self):
        """Test shutting down when no container exists."""
        # Should not raise error
        await shutdown_service_container()
    
    async def test_convenience_functions(self):
        """Test convenience functions for getting services."""
        with patch('app.services.container.settings') as mock_settings:
            mock_settings.DATABASE_TYPE = "memory"
            
            # Import convenience functions
            from ..services.container import (
                get_user_repository, get_session_repository, 
                get_auth_service, get_database_connection
            )
            
            # Test getting services through convenience functions
            user_repo = await get_user_repository()
            session_repo = await get_session_repository()
            auth_service = await get_auth_service()
            connection = await get_database_connection()
            
            assert user_repo is not None
            assert session_repo is not None
            assert auth_service is not None
            assert connection is not None
            
            # Cleanup
            await shutdown_service_container()


@pytest.mark.integration
class TestServiceContainerIntegration:
    """Integration tests for service container."""
    
    async def test_end_to_end_service_usage(self):
        """Test using services end-to-end through container."""
        container = ServiceContainer(DatabaseProvider.MEMORY)
        await container.initialize()
        
        try:
            # Get services
            user_repo = container.get_user_repository()
            session_repo = container.get_session_repository()
            auth_service = container.get_auth_service()
            
            # Create user account
            auth_user_id = await auth_service.create_user_account("test@example.com", "password123")
            
            # Create user in repository
            from ..domain.entities import CreateUserDto
            user_dto = CreateUserDto(email="test@example.com")
            user = await user_repo.create(user_dto)
            
            # Create session for user
            from ..domain.entities import CreateSessionDto
            session_dto = CreateSessionDto(user_id=user.id, title="Test Session")
            session = await session_repo.create(session_dto)
            
            # Verify everything is connected
            assert auth_user_id is not None
            assert user.email == "test@example.com"
            assert session.user_id == user.id
            assert session.title == "Test Session"
            
            # Test service interactions
            found_user = await user_repo.find_by_email("test@example.com")
            user_sessions = await session_repo.find_by_user_id(user.id)
            
            assert found_user.id == user.id
            assert len(user_sessions) == 1
            assert user_sessions[0].id == session.id
            
        finally:
            # Cleanup
            await container.shutdown()
    
    async def test_service_container_error_recovery(self):
        """Test service container behavior during errors."""
        container = ServiceContainer(DatabaseProvider.MEMORY)
        
        # Test initialization error handling
        with patch.object(container, '_create_services', side_effect=Exception("Init error")):
            with pytest.raises(ConfigurationError):
                await container.initialize()
        
        # Container should not be marked as initialized
        assert not container.is_initialized
        
        # Should be able to initialize successfully after error
        await container.initialize()
        assert container.is_initialized
        
        # Cleanup
        await container.shutdown()
    
    async def test_multiple_containers_isolation(self):
        """Test that multiple containers are isolated."""
        container1 = ServiceContainer(DatabaseProvider.MEMORY)
        container2 = ServiceContainer(DatabaseProvider.MEMORY)
        
        await container1.initialize()
        await container2.initialize()
        
        try:
            # Get user repositories from both containers
            user_repo1 = container1.get_user_repository()
            user_repo2 = container2.get_user_repository()
            
            # Create user in first container
            from ..domain.entities import CreateUserDto
            user_dto = CreateUserDto(email="isolated@example.com")
            user1 = await user_repo1.create(user_dto)
            
            # User should not exist in second container
            found_in_repo2 = await user_repo2.find_by_email("isolated@example.com")
            assert found_in_repo2 is None
            
            # But should exist in first container
            found_in_repo1 = await user_repo1.find_by_email("isolated@example.com")
            assert found_in_repo1 is not None
            assert found_in_repo1.id == user1.id
            
        finally:
            # Cleanup
            await container1.shutdown()
            await container2.shutdown()

