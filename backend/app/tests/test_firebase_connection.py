"""
Firebase connection and integration tests.

This module contains tests specifically for Firebase connectivity,
configuration validation, and basic CRUD operations. These tests
require proper Firebase configuration to run.

These tests are marked as integration tests and can be skipped
in environments where Firebase is not configured.
"""

import pytest
import os
from unittest.mock import patch, MagicMock

from ..core.config import settings
from ..domain.entities import CreateUserDto, CreateSessionDto
from ..domain.exceptions import ConfigurationError, RepositoryError
from ..services.container import ServiceContainer, DatabaseProvider


@pytest.mark.skipif(
    not os.getenv('FIREBASE_PROJECT_ID') or not os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH'),
    reason="Firebase configuration not available"
)
@pytest.mark.integration
class TestFirebaseConnection:
    """Integration tests for Firebase connection (requires Firebase config)."""
    
    async def test_firebase_connection_real(self):
        """Test real Firebase connection with proper configuration."""
        # This test only runs if Firebase is properly configured
        try:
            from ..adapters.firebase_adapter import FirebaseConnection
            
            connection = FirebaseConnection()
            await connection.connect()
            
            assert connection.is_connected()
            
            # Test health check
            health = await connection.health_check()
            assert health["status"] == "healthy"
            assert "project_id" in health["details"]
            
            await connection.disconnect()
            
        except ImportError:
            pytest.skip("Firebase modules not available")
        except Exception as e:
            pytest.fail(f"Firebase connection failed: {e}")
    
    async def test_firebase_service_container_real(self):
        """Test Firebase service container with real configuration."""
        try:
            container = ServiceContainer(DatabaseProvider.FIREBASE)
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
            
            # Test health check
            health = await container.health_check()
            assert health["container"]["status"] == "healthy"
            assert health["database"]["status"] == "healthy"
            
            await container.shutdown()
            
        except Exception as e:
            pytest.fail(f"Firebase service container failed: {e}")


class TestFirebaseConnectionMocked:
    """Tests for Firebase connection with mocking (no real Firebase needed)."""
    
    @patch('app.adapters.firebase_adapter.firebase_admin')
    @patch('app.adapters.firebase_adapter.credentials')
    @patch('app.adapters.firebase_adapter.firestore')
    async def test_firebase_connection_initialization(self, mock_firestore, mock_credentials, mock_firebase_admin):
        """Test Firebase connection initialization with mocks."""
        # Mock Firebase components
        mock_app = MagicMock()
        mock_db = MagicMock()
        mock_cred = MagicMock()
        
        mock_credentials.Certificate.return_value = mock_cred
        mock_firebase_admin.initialize_app.return_value = mock_app
        mock_firestore.client.return_value = mock_db
        
        # Mock settings
        with patch.object(settings, 'FIREBASE_PROJECT_ID', 'test-project'), \
             patch.object(settings, 'FIREBASE_SERVICE_ACCOUNT_PATH', '/fake/path.json'), \
             patch.object(settings, 'validate_firebase_config', return_value=True), \
             patch('os.path.exists', return_value=True):
            
            from ..adapters.firebase_adapter import FirebaseConnection
            
            connection = FirebaseConnection()
            await connection.connect()
            
            assert connection.is_connected()
            mock_credentials.Certificate.assert_called_once()
            mock_firebase_admin.initialize_app.assert_called_once()
            mock_firestore.client.assert_called_once()
    
    async def test_firebase_connection_config_error(self):
        """Test Firebase connection with configuration errors."""
        with patch.object(settings, 'validate_firebase_config', side_effect=ValueError("Missing config")):
            from ..adapters.firebase_adapter import FirebaseConnection
            
            connection = FirebaseConnection()
            
            with pytest.raises(RepositoryError) as exc_info:
                await connection.connect()
            
            assert "Failed to initialize Firebase connection" in str(exc_info.value)
    
    @patch('app.adapters.firebase_adapter.firebase_admin')
    @patch('app.adapters.firebase_adapter.firestore')
    async def test_firebase_health_check_mocked(self, mock_firestore, mock_firebase_admin):
        """Test Firebase health check with mocks."""
        # Mock Firestore operations
        mock_doc = MagicMock()
        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc
        
        mock_db = MagicMock()
        mock_db.collection.return_value = mock_collection
        mock_firestore.client.return_value = mock_db
        
        with patch.object(settings, 'FIREBASE_PROJECT_ID', 'test-project'), \
             patch.object(settings, 'validate_firebase_config', return_value=True), \
             patch('os.path.exists', return_value=True):
            
            from ..adapters.firebase_adapter import FirebaseConnection
            
            connection = FirebaseConnection()
            connection._db = mock_db  # Directly set the mock db
            connection._initialized = True
            
            health = await connection.health_check()
            
            assert health["status"] == "healthy"
            assert health["details"]["project_id"] == "test-project"
            assert health["details"]["connected"] is True
            
            # Verify health check operations
            mock_db.collection.assert_called_with("health_check")
            mock_doc.set.assert_called_once()
            mock_doc.delete.assert_called_once()
    
    async def test_firebase_health_check_error(self):
        """Test Firebase health check with database error."""
        from ..adapters.firebase_adapter import FirebaseConnection
        
        connection = FirebaseConnection()
        connection._initialized = False
        
        health = await connection.health_check()
        
        assert health["status"] == "unhealthy"
        assert "Firebase not initialized" in health["details"]


class TestFirebaseConfiguration:
    """Tests for Firebase configuration validation."""
    
    def test_configuration_validation_success(self):
        """Test successful Firebase configuration validation."""
        with patch.object(settings, 'DATABASE_TYPE', 'firebase'), \
             patch.object(settings, 'FIREBASE_PROJECT_ID', 'test-project'), \
             patch.object(settings, 'FIREBASE_SERVICE_ACCOUNT_PATH', '/fake/path.json'), \
             patch('os.path.exists', return_value=True):
            
            # Should not raise exception
            result = settings.validate_firebase_config()
            assert result is True
    
    def test_configuration_validation_missing_project_id(self):
        """Test configuration validation with missing project ID."""
        with patch.object(settings, 'DATABASE_TYPE', 'firebase'), \
             patch.object(settings, 'FIREBASE_PROJECT_ID', None):
            
            with pytest.raises(ValueError) as exc_info:
                settings.validate_firebase_config()
            
            assert "FIREBASE_PROJECT_ID is required" in str(exc_info.value)
    
    def test_configuration_validation_missing_service_account(self):
        """Test configuration validation with missing service account."""
        with patch.object(settings, 'DATABASE_TYPE', 'firebase'), \
             patch.object(settings, 'FIREBASE_PROJECT_ID', 'test-project'), \
             patch.object(settings, 'FIREBASE_SERVICE_ACCOUNT_PATH', None):
            
            with pytest.raises(ValueError) as exc_info:
                settings.validate_firebase_config()
            
            assert "FIREBASE_SERVICE_ACCOUNT_PATH is required" in str(exc_info.value)
    
    def test_configuration_validation_file_not_exists(self):
        """Test configuration validation with non-existent service account file."""
        with patch.object(settings, 'DATABASE_TYPE', 'firebase'), \
             patch.object(settings, 'FIREBASE_PROJECT_ID', 'test-project'), \
             patch.object(settings, 'FIREBASE_SERVICE_ACCOUNT_PATH', '/nonexistent/path.json'), \
             patch('os.path.exists', return_value=False):
            
            with pytest.raises(ValueError) as exc_info:
                settings.validate_firebase_config()
            
            assert "Firebase service account file not found" in str(exc_info.value)
    
    def test_configuration_validation_non_firebase_database(self):
        """Test configuration validation with non-Firebase database."""
        with patch.object(settings, 'DATABASE_TYPE', 'memory'):
            
            # Should not validate Firebase config for other database types
            result = settings.validate_firebase_config()
            assert result is True


@pytest.mark.skipif(
    not os.getenv('FIREBASE_PROJECT_ID') or not os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH'),
    reason="Firebase configuration not available"
)
@pytest.mark.integration
class TestFirebaseCRUDOperations:
    """Integration tests for Firebase CRUD operations (requires Firebase config)."""
    
    async def test_firebase_user_repository_crud(self):
        """Test Firebase user repository CRUD operations."""
        try:
            container = ServiceContainer(DatabaseProvider.FIREBASE)
            await container.initialize()
            
            user_repo = container.get_user_repository()
            
            # Create user
            user_dto = CreateUserDto(
                email="firebase-test@example.com",
                display_name="Firebase Test User"
            )
            created_user = await user_repo.create(user_dto)
            
            assert created_user.email == "firebase-test@example.com"
            assert created_user.display_name == "Firebase Test User"
            
            # Find user by ID
            found_user = await user_repo.find_by_id(created_user.id)
            assert found_user is not None
            assert found_user.email == created_user.email
            
            # Find user by email
            found_by_email = await user_repo.find_by_email("firebase-test@example.com")
            assert found_by_email is not None
            assert found_by_email.id == created_user.id
            
            # Update user
            updates = {"display_name": "Updated Firebase User"}
            updated_user = await user_repo.update(created_user.id, updates)
            assert updated_user.display_name == "Updated Firebase User"
            
            # Delete user
            deleted = await user_repo.delete(created_user.id)
            assert deleted is True
            
            # Verify deletion
            not_found = await user_repo.find_by_id(created_user.id)
            assert not_found is None
            
            await container.shutdown()
            
        except Exception as e:
            pytest.fail(f"Firebase CRUD operations failed: {e}")
    
    async def test_firebase_session_repository_crud(self):
        """Test Firebase session repository CRUD operations."""
        try:
            container = ServiceContainer(DatabaseProvider.FIREBASE)
            await container.initialize()
            
            user_repo = container.get_user_repository()
            session_repo = container.get_session_repository()
            
            # Create test user first
            user_dto = CreateUserDto(email="session-test@example.com")
            test_user = await user_repo.create(user_dto)
            
            # Create session
            session_dto = CreateSessionDto(
                user_id=test_user.id,
                title="Firebase Test Session"
            )
            created_session = await session_repo.create(session_dto)
            
            assert created_session.user_id == test_user.id
            assert created_session.title == "Firebase Test Session"
            
            # Find session by ID
            found_session = await session_repo.find_by_id(created_session.id)
            assert found_session is not None
            assert found_session.title == created_session.title
            
            # Find sessions by user ID
            user_sessions = await session_repo.find_by_user_id(test_user.id)
            assert len(user_sessions) == 1
            assert user_sessions[0].id == created_session.id
            
            # Complete session
            completed_session = await session_repo.complete_session(created_session.id)
            assert completed_session.status.value == "completed"
            assert completed_session.duration_minutes is not None
            
            # Delete session
            deleted = await session_repo.delete(created_session.id)
            assert deleted is True
            
            # Cleanup: delete test user
            await user_repo.delete(test_user.id)
            
            await container.shutdown()
            
        except Exception as e:
            pytest.fail(f"Firebase session CRUD operations failed: {e}")


class TestConnectionTestUtility:
    """Tests for the connection test utility itself."""
    
    async def test_memory_connection_test(self):
        """Test that connection test works with memory provider."""
        container = ServiceContainer(DatabaseProvider.MEMORY)
        await container.initialize()
        
        # Test health check
        health = await container.health_check()
        assert health["container"]["status"] == "healthy"
        assert health["database"]["status"] == "healthy"
        
        # Test basic operations
        user_repo = container.get_user_repository()
        user_dto = CreateUserDto(email="connection-test@example.com")
        user = await user_repo.create(user_dto)
        
        found_user = await user_repo.find_by_id(user.id)
        assert found_user is not None
        assert found_user.email == user.email
        
        await container.shutdown()


def create_connection_test_script():
    """
    Create a standalone script for testing Firebase connection.
    
    This function creates a test script that can be run independently
    to validate Firebase configuration and connectivity.
    """
    script_content = '''#!/usr/bin/env python3
"""
Firebase Connection Test Script

This script tests Firebase connectivity and configuration.
Run this script to validate your Firebase setup before running the full application.

Usage:
    python test_firebase_connection.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from app.services.container import ServiceContainer, DatabaseProvider
from app.domain.entities import CreateUserDto, CreateSessionDto
from app.core.config import settings


async def test_firebase_configuration():
    """Test Firebase configuration validation."""
    print("\\n=== Testing Firebase Configuration ===")
    
    try:
        # Test configuration validation
        settings.validate_firebase_config()
        print("✅ Firebase configuration is valid")
        
        print(f"Project ID: {settings.FIREBASE_PROJECT_ID}")
        print(f"Service Account Path: {settings.FIREBASE_SERVICE_ACCOUNT_PATH}")
        print(f"Database Type: {settings.DATABASE_TYPE}")
        
        return True
        
    except Exception as e:
        print(f"❌ Firebase configuration error: {e}")
        return False


async def test_firebase_connection():
    """Test Firebase connection."""
    print("\\n=== Testing Firebase Connection ===")
    
    try:
        container = ServiceContainer(DatabaseProvider.FIREBASE)
        await container.initialize()
        
        print("✅ Firebase connection established")
        
        # Test health check
        health = await container.health_check()
        if health["database"]["status"] == "healthy":
            print("✅ Database health check passed")
        else:
            print(f"❌ Database health check failed: {health['database']}")
            return False
        
        await container.shutdown()
        return True
        
    except Exception as e:
        print(f"❌ Firebase connection error: {e}")
        return False


async def test_firebase_operations():
    """Test basic Firebase operations."""
    print("\\n=== Testing Firebase Operations ===")
    
    try:
        container = ServiceContainer(DatabaseProvider.FIREBASE)
        await container.initialize()
        
        user_repo = container.get_user_repository()
        session_repo = container.get_session_repository()
        
        # Test user operations
        print("Testing user operations...")
        user_dto = CreateUserDto(
            email="test-connection@example.com",
            display_name="Connection Test User"
        )
        user = await user_repo.create(user_dto)
        print(f"✅ Created user: {user.id}")
        
        found_user = await user_repo.find_by_id(user.id)
        if found_user:
            print("✅ User retrieval successful")
        else:
            print("❌ User retrieval failed")
            return False
        
        # Test session operations
        print("Testing session operations...")
        session_dto = CreateSessionDto(
            user_id=user.id,
            title="Connection Test Session"
        )
        session = await session_repo.create(session_dto)
        print(f"✅ Created session: {session.id}")
        
        found_session = await session_repo.find_by_id(session.id)
        if found_session:
            print("✅ Session retrieval successful")
        else:
            print("❌ Session retrieval failed")
            return False
        
        # Cleanup
        print("Cleaning up test data...")
        await session_repo.delete(session.id)
        await user_repo.delete(user.id)
        print("✅ Cleanup completed")
        
        await container.shutdown()
        return True
        
    except Exception as e:
        print(f"❌ Firebase operations error: {e}")
        return False


async def main():
    """Main test function."""
    print("Firebase Connection Test")
    print("=" * 50)
    
    all_passed = True
    
    # Test configuration
    if not await test_firebase_configuration():
        all_passed = False
    
    # Test connection
    if not await test_firebase_connection():
        all_passed = False
    
    # Test operations
    if not await test_firebase_operations():
        all_passed = False
    
    # Summary
    print("\\n" + "=" * 50)
    if all_passed:
        print("🎉 All Firebase tests passed!")
        print("Your Firebase configuration is working correctly.")
        sys.exit(0)
    else:
        print("❌ Some Firebase tests failed.")
        print("Please check your Firebase configuration and try again.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
'''
    
    return script_content


# Create the test script if this module is run directly
if __name__ == "__main__":
    script_content = create_connection_test_script()
    script_path = Path(__file__).parent.parent / "test_firebase_connection.py"
    
    with open(script_path, "w") as f:
        f.write(script_content)
    
    print(f"Created Firebase connection test script at: {script_path}")
    print("Run it with: python test_firebase_connection.py")

