"""
Tests for repository implementations.

This module contains comprehensive tests for both memory and Firebase
repository implementations, ensuring they follow the same contracts
and provide consistent behavior.

Following TDD principles, these tests define the expected behavior
of repository interfaces and validate all implementations.
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any

from ..domain.entities import CreateUserDto, CreateSessionDto, UpdateSessionDto, SessionStatus
from ..domain.exceptions import UserAlreadyExistsError, RepositoryError
from ..repositories.memory_repository import (
    MemoryConnection, MemoryUserRepository, MemorySessionRepository, MemoryAuthService
)


@pytest.fixture
async def memory_connection():
    """Create a fresh memory connection for testing."""
    connection = MemoryConnection()
    await connection.connect()
    yield connection
    await connection.disconnect()


@pytest.fixture
async def user_repository(memory_connection):
    """Create a memory user repository for testing."""
    return MemoryUserRepository(memory_connection)


@pytest.fixture
async def session_repository(memory_connection):
    """Create a memory session repository for testing."""
    return MemorySessionRepository(memory_connection)


@pytest.fixture
async def auth_service(memory_connection):
    """Create a memory auth service for testing."""
    return MemoryAuthService(memory_connection)


class TestMemoryConnection:
    """Test cases for memory connection."""
    
    def test_connection_initialization(self):
        """Test connection initialization."""
        connection = MemoryConnection()
        assert not connection.is_connected()
        assert "users" in connection.data_store
        assert "sessions" in connection.data_store
        assert "auth_users" in connection.data_store
    
    async def test_connection_lifecycle(self):
        """Test connection connect/disconnect lifecycle."""
        connection = MemoryConnection()
        
        # Initially not connected
        assert not connection.is_connected()
        
        # Connect
        await connection.connect()
        assert connection.is_connected()
        
        # Disconnect
        await connection.disconnect()
        assert not connection.is_connected()
    
    async def test_health_check(self):
        """Test connection health check."""
        connection = MemoryConnection()
        
        # Health check when not connected
        health = await connection.health_check()
        assert health["status"] == "unhealthy"
        
        # Health check when connected
        await connection.connect()
        health = await connection.health_check()
        assert health["status"] == "healthy"
        assert "details" in health
        assert "timestamp" in health
    
    async def test_clear_data(self):
        """Test clearing all data."""
        connection = MemoryConnection()
        await connection.connect()
        
        # Add some test data
        connection.data_store["users"]["test-id"] = {"name": "test"}
        connection.data_store["sessions"]["session-id"] = {"title": "test"}
        
        # Clear data
        connection.clear_all_data()
        
        # Verify data is cleared
        assert len(connection.data_store["users"]) == 0
        assert len(connection.data_store["sessions"]) == 0


class TestMemoryUserRepository:
    """Test cases for memory user repository."""
    
    async def test_create_user_success(self, user_repository):
        """Test successful user creation."""
        user_dto = CreateUserDto(
            email="test@example.com",
            display_name="Test User",
            daily_goal_minutes=90
        )
        
        user = await user_repository.create(user_dto)
        
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"
        assert user.daily_goal_minutes == 90
        assert user.id is not None
        assert user.is_active is True
    
    async def test_create_duplicate_user(self, user_repository):
        """Test creating user with duplicate email."""
        user_dto = CreateUserDto(email="duplicate@example.com")
        
        # Create first user
        await user_repository.create(user_dto)
        
        # Try to create duplicate
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await user_repository.create(user_dto)
        
        assert exc_info.value.email == "duplicate@example.com"
    
    async def test_find_user_by_id(self, user_repository):
        """Test finding user by ID."""
        # Create test user
        user_dto = CreateUserDto(email="findme@example.com")
        created_user = await user_repository.create(user_dto)
        
        # Find by ID
        found_user = await user_repository.find_by_id(created_user.id)
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == "findme@example.com"
        
        # Find non-existent user
        not_found = await user_repository.find_by_id("non-existent-id")
        assert not_found is None
    
    async def test_find_user_by_email(self, user_repository):
        """Test finding user by email."""
        # Create test user
        user_dto = CreateUserDto(email="findme@example.com")
        created_user = await user_repository.create(user_dto)
        
        # Find by email
        found_user = await user_repository.find_by_email("findme@example.com")
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == "findme@example.com"
        
        # Find with different case
        found_user_upper = await user_repository.find_by_email("FINDME@EXAMPLE.COM")
        assert found_user_upper is not None
        assert found_user_upper.id == created_user.id
        
        # Find non-existent user
        not_found = await user_repository.find_by_email("notfound@example.com")
        assert not_found is None
    
    async def test_update_user(self, user_repository):
        """Test updating user data."""
        # Create test user
        user_dto = CreateUserDto(email="update@example.com")
        created_user = await user_repository.create(user_dto)
        
        # Update user
        updates = {
            "display_name": "Updated Name",
            "daily_goal_minutes": 120
        }
        updated_user = await user_repository.update(created_user.id, updates)
        
        assert updated_user is not None
        assert updated_user.display_name == "Updated Name"
        assert updated_user.daily_goal_minutes == 120
        assert updated_user.updated_at > created_user.updated_at
        
        # Update non-existent user
        not_updated = await user_repository.update("non-existent-id", updates)
        assert not_updated is None
    
    async def test_delete_user(self, user_repository):
        """Test deleting user."""
        # Create test user
        user_dto = CreateUserDto(email="delete@example.com")
        created_user = await user_repository.create(user_dto)
        
        # Delete user
        deleted = await user_repository.delete(created_user.id)
        assert deleted is True
        
        # Verify user is deleted
        not_found = await user_repository.find_by_id(created_user.id)
        assert not_found is None
        
        # Delete non-existent user
        not_deleted = await user_repository.delete("non-existent-id")
        assert not_deleted is False
    
    async def test_list_users(self, user_repository):
        """Test listing users with pagination."""
        # Create multiple test users
        for i in range(5):
            user_dto = CreateUserDto(email=f"user{i}@example.com")
            await user_repository.create(user_dto)
        
        # List all users
        all_users = await user_repository.list_users()
        assert len(all_users) == 5
        
        # List with limit
        limited_users = await user_repository.list_users(limit=3)
        assert len(limited_users) == 3
        
        # List with offset
        offset_users = await user_repository.list_users(limit=2, offset=2)
        assert len(offset_users) == 2
    
    async def test_count_users(self, user_repository):
        """Test counting users."""
        # Initially no users
        count = await user_repository.count_users()
        assert count == 0
        
        # Create some users
        for i in range(3):
            user_dto = CreateUserDto(email=f"count{i}@example.com")
            await user_repository.create(user_dto)
        
        # Count should be 3
        count = await user_repository.count_users()
        assert count == 3
    
    async def test_user_exists(self, user_repository):
        """Test checking if user exists."""
        # Create test user
        user_dto = CreateUserDto(email="exists@example.com")
        created_user = await user_repository.create(user_dto)
        
        # User should exist
        exists = await user_repository.exists(created_user.id)
        assert exists is True
        
        # Non-existent user should not exist
        not_exists = await user_repository.exists("non-existent-id")
        assert not_exists is False


@pytest.fixture
async def test_user_id(user_repository):
    """Create a test user and return its ID."""
    user_dto = CreateUserDto(email="testuser@example.com")
    user = await user_repository.create(user_dto)
    return user.id


class TestMemorySessionRepository:
    """Test cases for memory session repository."""
    
    async def test_create_session_success(self, session_repository, test_user_id):
        """Test successful session creation."""
        session_dto = CreateSessionDto(
            user_id=test_user_id,
            title="Test Session",
            notes="Test notes",
            tags=["work", "focus"]
        )
        
        session = await session_repository.create(session_dto)
        
        assert session.user_id == test_user_id
        assert session.title == "Test Session"
        assert session.notes == "Test notes"
        assert session.tags == ["work", "focus"]
        assert session.status == SessionStatus.ACTIVE
        assert session.id is not None
    
    async def test_find_session_by_id(self, session_repository, test_user_id):
        """Test finding session by ID."""
        # Create test session
        session_dto = CreateSessionDto(user_id=test_user_id, title="Find Me")
        created_session = await session_repository.create(session_dto)
        
        # Find by ID
        found_session = await session_repository.find_by_id(created_session.id)
        
        assert found_session is not None
        assert found_session.id == created_session.id
        assert found_session.title == "Find Me"
        
        # Find non-existent session
        not_found = await session_repository.find_by_id("non-existent-id")
        assert not_found is None
    
    async def test_find_sessions_by_user_id(self, session_repository, test_user_id):
        """Test finding sessions by user ID."""
        # Create multiple sessions for the user
        for i in range(3):
            session_dto = CreateSessionDto(
                user_id=test_user_id,
                title=f"Session {i}"
            )
            await session_repository.create(session_dto)
        
        # Find sessions by user ID
        user_sessions = await session_repository.find_by_user_id(test_user_id)
        
        assert len(user_sessions) == 3
        for session in user_sessions:
            assert session.user_id == test_user_id
    
    async def test_find_sessions_with_pagination(self, session_repository, test_user_id):
        """Test finding sessions with pagination."""
        # Create multiple sessions
        for i in range(5):
            session_dto = CreateSessionDto(
                user_id=test_user_id,
                title=f"Session {i}"
            )
            await session_repository.create(session_dto)
        
        # Get with limit
        limited_sessions = await session_repository.find_by_user_id(test_user_id, limit=3)
        assert len(limited_sessions) == 3
        
        # Get with offset
        offset_sessions = await session_repository.find_by_user_id(test_user_id, limit=2, offset=2)
        assert len(offset_sessions) == 2
    
    async def test_update_session(self, session_repository, test_user_id):
        """Test updating session data."""
        # Create test session
        session_dto = CreateSessionDto(user_id=test_user_id, title="Original")
        created_session = await session_repository.create(session_dto)
        
        # Update session
        updates = UpdateSessionDto(
            title="Updated Title",
            notes="Updated notes",
            tags=["updated", "tags"]
        )
        updated_session = await session_repository.update(created_session.id, updates)
        
        assert updated_session is not None
        assert updated_session.title == "Updated Title"
        assert updated_session.notes == "Updated notes"
        assert updated_session.tags == ["updated", "tags"]
        assert updated_session.updated_at > created_session.updated_at
        
        # Update non-existent session
        not_updated = await session_repository.update("non-existent-id", updates)
        assert not_updated is None
    
    async def test_delete_session(self, session_repository, test_user_id):
        """Test deleting session."""
        # Create test session
        session_dto = CreateSessionDto(user_id=test_user_id, title="Delete Me")
        created_session = await session_repository.create(session_dto)
        
        # Delete session
        deleted = await session_repository.delete(created_session.id)
        assert deleted is True
        
        # Verify session is deleted
        not_found = await session_repository.find_by_id(created_session.id)
        assert not_found is None
        
        # Delete non-existent session
        not_deleted = await session_repository.delete("non-existent-id")
        assert not_deleted is False
    
    async def test_complete_session(self, session_repository, test_user_id):
        """Test completing a session."""
        # Create test session
        session_dto = CreateSessionDto(user_id=test_user_id)
        created_session = await session_repository.create(session_dto)
        
        # Complete session
        completed_session = await session_repository.complete_session(created_session.id)
        
        assert completed_session is not None
        assert completed_session.status == SessionStatus.COMPLETED
        assert completed_session.end_time is not None
        assert completed_session.duration_minutes is not None
        
        # Complete non-existent session
        not_completed = await session_repository.complete_session("non-existent-id")
        assert not_completed is None
    
    async def test_get_active_sessions(self, session_repository, test_user_id):
        """Test getting active sessions."""
        # Create sessions with different statuses
        active_dto = CreateSessionDto(user_id=test_user_id, title="Active")
        active_session = await session_repository.create(active_dto)
        
        completed_dto = CreateSessionDto(user_id=test_user_id, title="Completed")
        completed_session = await session_repository.create(completed_dto)
        await session_repository.complete_session(completed_session.id)
        
        # Get active sessions
        active_sessions = await session_repository.get_active_sessions(test_user_id)
        
        assert len(active_sessions) == 1
        assert active_sessions[0].id == active_session.id
        assert active_sessions[0].status == SessionStatus.ACTIVE
    
    async def test_count_sessions(self, session_repository, test_user_id):
        """Test counting sessions for a user."""
        # Initially no sessions
        count = await session_repository.count_sessions(test_user_id)
        assert count == 0
        
        # Create some sessions
        for i in range(3):
            session_dto = CreateSessionDto(user_id=test_user_id)
            await session_repository.create(session_dto)
        
        # Count should be 3
        count = await session_repository.count_sessions(test_user_id)
        assert count == 3


class TestMemoryAuthService:
    """Test cases for memory auth service."""
    
    async def test_create_user_account(self, auth_service):
        """Test creating user account."""
        auth_user_id = await auth_service.create_user_account("test@example.com", "password123")
        
        assert auth_user_id is not None
        assert auth_user_id.startswith("auth_")
    
    async def test_create_duplicate_account(self, auth_service):
        """Test creating duplicate account."""
        # Create first account
        await auth_service.create_user_account("duplicate@example.com", "password123")
        
        # Try to create duplicate
        with pytest.raises(UserAlreadyExistsError):
            await auth_service.create_user_account("duplicate@example.com", "different_password")
    
    async def test_verify_credentials(self, auth_service):
        """Test verifying credentials."""
        # Create account
        auth_user_id = await auth_service.create_user_account("verify@example.com", "password123")
        
        # Verify correct credentials
        verified_id = await auth_service.verify_credentials("verify@example.com", "password123")
        assert verified_id == auth_user_id
        
        # Verify with wrong password should raise error
        with pytest.raises(Exception):  # AuthenticationError
            await auth_service.verify_credentials("verify@example.com", "wrong_password")
        
        # Verify with non-existent user should raise error
        with pytest.raises(Exception):  # AuthenticationError
            await auth_service.verify_credentials("notfound@example.com", "password123")
    
    async def test_delete_user_account(self, auth_service):
        """Test deleting user account."""
        # Create account
        auth_user_id = await auth_service.create_user_account("delete@example.com", "password123")
        
        # Delete account
        deleted = await auth_service.delete_user_account(auth_user_id)
        assert deleted is True
        
        # Delete non-existent account
        not_deleted = await auth_service.delete_user_account("non-existent-id")
        assert not_deleted is False
    
    async def test_update_password(self, auth_service):
        """Test updating user password."""
        # Create account
        auth_user_id = await auth_service.create_user_account("update@example.com", "old_password")
        
        # Update password
        updated = await auth_service.update_user_password(auth_user_id, "new_password")
        assert updated is True
        
        # Verify new password works
        verified_id = await auth_service.verify_credentials("update@example.com", "new_password")
        assert verified_id == auth_user_id
        
        # Update password for non-existent user
        not_updated = await auth_service.update_user_password("non-existent-id", "password")
        assert not_updated is False
    
    async def test_verify_token(self, auth_service):
        """Test verifying authentication token."""
        # Create account
        auth_user_id = await auth_service.create_user_account("token@example.com", "password123")
        
        # Verify valid token
        token = f"token_{auth_user_id}"
        verified_id = await auth_service.verify_token(token)
        assert verified_id == auth_user_id
        
        # Verify invalid token
        invalid_token = await auth_service.verify_token("invalid_token")
        assert invalid_token is None
        
        # Verify token for non-existent user
        non_existent_token = await auth_service.verify_token("token_non_existent")
        assert non_existent_token is None


@pytest.mark.integration
class TestRepositoryIntegration:
    """Integration tests for repositories working together."""
    
    async def test_user_and_session_integration(self, user_repository, session_repository):
        """Test user and session repositories working together."""
        # Create user
        user_dto = CreateUserDto(email="integration@example.com")
        user = await user_repository.create(user_dto)
        
        # Create sessions for user
        for i in range(3):
            session_dto = CreateSessionDto(
                user_id=user.id,
                title=f"Integration Session {i}"
            )
            await session_repository.create(session_dto)
        
        # Verify sessions exist for user
        sessions = await session_repository.find_by_user_id(user.id)
        assert len(sessions) == 3
        
        # Delete user (sessions should remain but be orphaned)
        deleted = await user_repository.delete(user.id)
        assert deleted is True
        
        # Sessions should still exist
        sessions_after_delete = await session_repository.find_by_user_id(user.id)
        assert len(sessions_after_delete) == 3
    
    async def test_full_session_lifecycle(self, session_repository, test_user_id):
        """Test complete session lifecycle."""
        # Create session
        session_dto = CreateSessionDto(
            user_id=test_user_id,
            title="Lifecycle Test"
        )
        session = await session_repository.create(session_dto)
        
        # Verify it's active
        active_sessions = await session_repository.get_active_sessions(test_user_id)
        assert len(active_sessions) == 1
        
        # Update session
        update_dto = UpdateSessionDto(notes="Added some notes")
        updated_session = await session_repository.update(session.id, update_dto)
        assert updated_session.notes == "Added some notes"
        
        # Complete session
        completed_session = await session_repository.complete_session(session.id)
        assert completed_session.status == SessionStatus.COMPLETED
        
        # Verify no longer active
        active_sessions_after = await session_repository.get_active_sessions(test_user_id)
        assert len(active_sessions_after) == 0
        
        # Session should still exist
        final_session = await session_repository.find_by_id(session.id)
        assert final_session is not None
        assert final_session.status == SessionStatus.COMPLETED
