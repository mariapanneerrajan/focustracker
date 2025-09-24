"""
Tests for domain entities.

This module contains comprehensive tests for the domain entities (User, Session)
and their associated DTOs, ensuring they follow business rules and validate
data correctly.

Following TDD principles, these tests define the expected behavior of entities
and serve as documentation for their business rules.
"""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from ..domain.entities import (
    User, Session, SessionStatus, CreateUserDto, CreateSessionDto, UpdateSessionDto
)


class TestUser:
    """Test cases for User entity."""
    
    def test_user_creation_with_valid_data(self):
        """Test creating a user with valid data."""
        user = User(
            email="test@example.com",
            display_name="Test User",
            timezone="America/New_York",
            daily_goal_minutes=120
        )
        
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"
        assert user.timezone == "America/New_York"
        assert user.daily_goal_minutes == 120
        assert user.is_active is True
        assert user.reminder_enabled is True
        assert user.id is not None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
    
    def test_user_creation_with_minimal_data(self):
        """Test creating a user with only required fields."""
        user = User(email="minimal@example.com")
        
        assert user.email == "minimal@example.com"
        assert user.display_name is None
        assert user.timezone == "UTC"
        assert user.daily_goal_minutes == 25
        assert user.is_active is True
        assert user.reminder_enabled is True
    
    def test_user_email_validation(self):
        """Test user email validation."""
        # Valid emails should work
        user = User(email="valid@example.com")
        assert user.email == "valid@example.com"
        
        # Email should be normalized to lowercase
        user = User(email="UPPER@EXAMPLE.COM")
        assert user.email == "upper@example.com"
        
        # Invalid email should raise validation error
        with pytest.raises(ValidationError):
            User(email="invalid-email")
        
        # Empty email should raise validation error
        with pytest.raises(ValidationError):
            User(email="")
    
    def test_display_name_validation(self):
        """Test display name validation."""
        # Valid display name
        user = User(email="test@example.com", display_name="John Doe")
        assert user.display_name == "John Doe"
        
        # None display name should be preserved
        user = User(email="test@example.com", display_name=None)
        assert user.display_name is None
        
        # Empty display name should be converted to None
        user = User(email="test@example.com", display_name="")
        assert user.display_name is None
        
        # Whitespace-only should be converted to None
        user = User(email="test@example.com", display_name="   ")
        assert user.display_name is None
        
        # Too short display name should raise error
        with pytest.raises(ValidationError):
            User(email="test@example.com", display_name="X")
    
    def test_daily_goal_validation(self):
        """Test daily goal minutes validation."""
        # Valid goal within range
        user = User(email="test@example.com", daily_goal_minutes=60)
        assert user.daily_goal_minutes == 60
        
        # Minimum valid value
        user = User(email="test@example.com", daily_goal_minutes=5)
        assert user.daily_goal_minutes == 5
        
        # Maximum valid value
        user = User(email="test@example.com", daily_goal_minutes=480)
        assert user.daily_goal_minutes == 480
        
        # Too low should raise error
        with pytest.raises(ValidationError):
            User(email="test@example.com", daily_goal_minutes=4)
        
        # Too high should raise error
        with pytest.raises(ValidationError):
            User(email="test@example.com", daily_goal_minutes=481)
    
    def test_update_timestamp(self):
        """Test updating the timestamp."""
        user = User(email="test@example.com")
        original_timestamp = user.updated_at
        
        # Sleep briefly to ensure timestamp change
        import time
        time.sleep(0.001)
        
        user.update_timestamp()
        
        assert user.updated_at > original_timestamp
    
    def test_to_dict_conversion(self):
        """Test converting user to dictionary."""
        user = User(
            email="test@example.com",
            display_name="Test User",
            daily_goal_minutes=90
        )
        
        user_dict = user.to_dict()
        
        assert isinstance(user_dict, dict)
        assert user_dict["email"] == "test@example.com"
        assert user_dict["display_name"] == "Test User"
        assert user_dict["daily_goal_minutes"] == 90
        assert "id" in user_dict
        assert "created_at" in user_dict
        assert "updated_at" in user_dict
        assert isinstance(user_dict["created_at"], str)
        assert isinstance(user_dict["updated_at"], str)
    
    def test_from_dict_conversion(self):
        """Test creating user from dictionary."""
        user_data = {
            "id": "test-id",
            "email": "test@example.com",
            "display_name": "Test User",
            "created_at": "2025-01-01T12:00:00+00:00",
            "updated_at": "2025-01-01T12:00:00+00:00",
            "is_active": True,
            "timezone": "America/New_York",
            "daily_goal_minutes": 90,
            "reminder_enabled": True
        }
        
        user = User.from_dict(user_data)
        
        assert user.id == "test-id"
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"
        assert user.daily_goal_minutes == 90
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)


class TestSession:
    """Test cases for Session entity."""
    
    def test_session_creation_with_valid_data(self):
        """Test creating a session with valid data."""
        session = Session(
            user_id="user-123",
            title="Focus Session",
            notes="Working on project",
            tags=["work", "focus"]
        )
        
        assert session.user_id == "user-123"
        assert session.title == "Focus Session"
        assert session.notes == "Working on project"
        assert session.tags == ["work", "focus"]
        assert session.status == SessionStatus.ACTIVE
        assert session.duration_minutes is None
        assert session.end_time is None
        assert isinstance(session.start_time, datetime)
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)
    
    def test_session_creation_with_minimal_data(self):
        """Test creating a session with only required fields."""
        session = Session(user_id="user-123")
        
        assert session.user_id == "user-123"
        assert session.title is None
        assert session.notes is None
        assert session.tags == []
        assert session.status == SessionStatus.ACTIVE
    
    def test_session_user_id_validation(self):
        """Test user ID validation."""
        # Valid user ID
        session = Session(user_id="user-123")
        assert session.user_id == "user-123"
        
        # Empty user ID should raise error
        with pytest.raises(ValidationError):
            Session(user_id="")
        
        # Whitespace-only user ID should raise error
        with pytest.raises(ValidationError):
            Session(user_id="   ")
    
    def test_session_title_validation(self):
        """Test title validation."""
        # Valid title
        session = Session(user_id="user-123", title="Test Session")
        assert session.title == "Test Session"
        
        # None title should be preserved
        session = Session(user_id="user-123", title=None)
        assert session.title is None
        
        # Empty title should be converted to None
        session = Session(user_id="user-123", title="")
        assert session.title is None
        
        # Whitespace-only title should be converted to None
        session = Session(user_id="user-123", title="   ")
        assert session.title is None
    
    def test_session_tags_validation(self):
        """Test tags validation."""
        # Valid tags
        session = Session(user_id="user-123", tags=["work", "Focus", "PROJECT"])
        assert session.tags == ["work", "focus", "project"]  # Should be lowercase
        
        # Empty tags should be converted to empty list
        session = Session(user_id="user-123", tags=[])
        assert session.tags == []
        
        # None tags should be converted to empty list
        session = Session(user_id="user-123", tags=None)
        assert session.tags == []
        
        # Tags with empty strings should be filtered out
        session = Session(user_id="user-123", tags=["work", "", "   ", "focus"])
        assert session.tags == ["work", "focus"]
        
        # Too many tags should be limited to 10
        many_tags = [f"tag{i}" for i in range(15)]
        session = Session(user_id="user-123", tags=many_tags)
        assert len(session.tags) == 10
    
    def test_session_end_time_validation(self):
        """Test end time validation."""
        # End time after start time should be valid
        start_time = datetime.now(timezone.utc)
        end_time = start_time.replace(hour=start_time.hour + 1 if start_time.hour < 23 else 0)
        
        session = Session(
            user_id="user-123",
            start_time=start_time,
            end_time=end_time
        )
        assert session.end_time == end_time
        
        # End time before start time should raise error
        with pytest.raises(ValidationError):
            Session(
                user_id="user-123",
                start_time=start_time,
                end_time=start_time.replace(hour=start_time.hour - 1 if start_time.hour > 0 else 23)
            )
    
    def test_complete_session(self):
        """Test completing a session."""
        session = Session(user_id="user-123")
        start_time = session.start_time
        original_updated_at = session.updated_at
        
        # Sleep briefly to ensure timestamp change
        import time
        time.sleep(0.001)
        
        # Complete session (add 25 minutes using timedelta)
        from datetime import timedelta
        end_time = start_time + timedelta(minutes=25)
        session.complete_session(end_time)
        
        assert session.status == SessionStatus.COMPLETED
        assert session.end_time == end_time
        assert session.duration_minutes == 25
        assert session.updated_at > original_updated_at
    
    def test_complete_session_with_current_time(self):
        """Test completing a session with current time."""
        session = Session(user_id="user-123")
        
        # Complete session without specifying end time
        session.complete_session()
        
        assert session.status == SessionStatus.COMPLETED
        assert session.end_time is not None
        assert session.duration_minutes is not None
        assert session.duration_minutes >= 0
    
    def test_complete_already_completed_session(self):
        """Test completing an already completed session."""
        session = Session(user_id="user-123")
        session.complete_session()
        
        original_end_time = session.end_time
        original_duration = session.duration_minutes
        
        # Try to complete again
        session.complete_session()
        
        # Should remain unchanged
        assert session.end_time == original_end_time
        assert session.duration_minutes == original_duration
    
    def test_pause_and_resume_session(self):
        """Test pausing and resuming a session."""
        session = Session(user_id="user-123")
        
        # Pause active session
        session.pause_session()
        assert session.status == SessionStatus.PAUSED
        
        # Resume paused session
        session.resume_session()
        assert session.status == SessionStatus.ACTIVE
    
    def test_cancel_session(self):
        """Test canceling a session."""
        session = Session(user_id="user-123")
        
        session.cancel_session()
        assert session.status == SessionStatus.CANCELLED
    
    def test_session_properties(self):
        """Test session property methods."""
        session = Session(user_id="user-123")
        
        # Test is_active property
        assert session.is_active is True
        assert session.is_completed is False
        
        session.complete_session()
        
        assert session.is_active is False
        assert session.is_completed is True
    
    def test_current_duration_minutes(self):
        """Test current duration calculation."""
        start_time = datetime.now(timezone.utc)
        session = Session(user_id="user-123", start_time=start_time)
        
        # For active session, should calculate from start to now
        duration = session.current_duration_minutes
        assert duration >= 0
        
        # For completed session, should return stored duration
        session.complete_session()
        stored_duration = session.duration_minutes
        assert session.current_duration_minutes == stored_duration
    
    def test_to_dict_conversion(self):
        """Test converting session to dictionary."""
        session = Session(
            user_id="user-123",
            title="Test Session",
            notes="Test notes",
            tags=["work", "test"]
        )
        
        session_dict = session.to_dict()
        
        assert isinstance(session_dict, dict)
        assert session_dict["user_id"] == "user-123"
        assert session_dict["title"] == "Test Session"
        assert session_dict["notes"] == "Test notes"
        assert session_dict["tags"] == ["work", "test"]
        assert session_dict["status"] == "active"
        assert "id" in session_dict
        assert "start_time" in session_dict
        assert isinstance(session_dict["start_time"], str)
    
    def test_from_dict_conversion(self):
        """Test creating session from dictionary."""
        session_data = {
            "id": "session-123",
            "user_id": "user-123",
            "title": "Test Session",
            "start_time": "2025-01-01T12:00:00+00:00",
            "end_time": "2025-01-01T12:25:00+00:00",
            "duration_minutes": 25,
            "status": "completed",
            "created_at": "2025-01-01T12:00:00+00:00",
            "updated_at": "2025-01-01T12:25:00+00:00",
            "notes": "Test notes",
            "tags": ["work", "test"]
        }
        
        session = Session.from_dict(session_data)
        
        assert session.id == "session-123"
        assert session.user_id == "user-123"
        assert session.title == "Test Session"
        assert session.duration_minutes == 25
        assert session.status == SessionStatus.COMPLETED
        assert isinstance(session.start_time, datetime)
        assert isinstance(session.end_time, datetime)


class TestCreateUserDto:
    """Test cases for CreateUserDto."""
    
    def test_create_user_dto_with_valid_data(self):
        """Test creating DTO with valid data."""
        dto = CreateUserDto(
            email="test@example.com",
            display_name="Test User",
            timezone="America/New_York",
            daily_goal_minutes=90
        )
        
        assert dto.email == "test@example.com"
        assert dto.display_name == "Test User"
        assert dto.timezone == "America/New_York"
        assert dto.daily_goal_minutes == 90
    
    def test_create_user_dto_with_minimal_data(self):
        """Test creating DTO with only required fields."""
        dto = CreateUserDto(email="test@example.com")
        
        assert dto.email == "test@example.com"
        assert dto.display_name is None
        assert dto.timezone == "UTC"
        assert dto.daily_goal_minutes == 25


class TestCreateSessionDto:
    """Test cases for CreateSessionDto."""
    
    def test_create_session_dto_with_valid_data(self):
        """Test creating DTO with valid data."""
        dto = CreateSessionDto(
            user_id="user-123",
            title="Test Session",
            notes="Test notes",
            tags=["work", "test"]
        )
        
        assert dto.user_id == "user-123"
        assert dto.title == "Test Session"
        assert dto.notes == "Test notes"
        assert dto.tags == ["work", "test"]
    
    def test_create_session_dto_with_minimal_data(self):
        """Test creating DTO with only required fields."""
        dto = CreateSessionDto(user_id="user-123")
        
        assert dto.user_id == "user-123"
        assert dto.title is None
        assert dto.notes is None
        assert dto.tags == []


class TestUpdateSessionDto:
    """Test cases for UpdateSessionDto."""
    
    def test_update_session_dto_partial_updates(self):
        """Test creating DTO with partial update data."""
        # Update only title
        dto = UpdateSessionDto(title="Updated Title")
        assert dto.title == "Updated Title"
        assert dto.notes is None
        assert dto.tags is None
        assert dto.status is None
        
        # Update status
        dto = UpdateSessionDto(status=SessionStatus.COMPLETED)
        assert dto.status == SessionStatus.COMPLETED
        
        # Update multiple fields
        dto = UpdateSessionDto(
            title="Updated Title",
            notes="Updated notes",
            tags=["updated", "tags"]
        )
        assert dto.title == "Updated Title"
        assert dto.notes == "Updated notes"
        assert dto.tags == ["updated", "tags"]
