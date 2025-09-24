"""
Domain entities following SOLID principles.
Contains core business objects with validation and business rules.

This module defines the fundamental entities of the Focus Tracker application:
- User: Represents a user account with authentication details
- Session: Represents a focus tracking session with timing information

All entities include comprehensive validation, proper error handling,
and maintain data integrity through business rules.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any
from uuid import uuid4

from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict


class SessionStatus(str, Enum):
    """
    Enumeration of possible session states.
    
    Following Single Responsibility Principle by clearly defining
    all possible session states in one location.
    """
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class User(BaseModel):
    """
    User entity representing a registered user of the Focus Tracker application.
    
    Follows SOLID principles:
    - Single Responsibility: Manages user data and validation only
    - Open/Closed: Extensible through inheritance without modification
    - Liskov Substitution: Can be substituted by any User subclass
    - Interface Segregation: Minimal interface focused on user data
    - Dependency Inversion: Doesn't depend on concrete implementations
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique user identifier")
    email: EmailStr = Field(..., description="User's email address (unique)")
    display_name: Optional[str] = Field(None, max_length=100, description="User's display name")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Account creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last profile update timestamp")
    is_active: bool = Field(default=True, description="Whether the user account is active")
    timezone: str = Field(default="UTC", description="User's preferred timezone")
    
    # User preferences
    daily_goal_minutes: int = Field(default=25, ge=5, le=480, description="Daily focus goal in minutes")
    reminder_enabled: bool = Field(default=True, description="Whether reminders are enabled")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        },
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "display_name": "John Doe",
                "daily_goal_minutes": 120,
                "timezone": "America/New_York"
            }
        }
    )

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        """Ensure email is properly formatted and not empty."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Email cannot be empty')
        return v.strip().lower()

    @field_validator('display_name')
    @classmethod
    def validate_display_name(cls, v):
        """Validate display name if provided."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
            if len(v) < 2:
                raise ValueError('Display name must be at least 2 characters')
        return v

    @field_validator('timezone')
    @classmethod
    def validate_timezone(cls, v):
        """Basic timezone validation."""
        # Basic validation - in a real app you might want to validate against pytz
        if not v or len(v.strip()) == 0:
            return "UTC"
        return v.strip()

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert User entity to dictionary format for storage.
        
        Returns:
            Dictionary representation suitable for database storage
        """
        return {
            "id": self.id,
            "email": self.email,
            "display_name": self.display_name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active,
            "timezone": self.timezone,
            "daily_goal_minutes": self.daily_goal_minutes,
            "reminder_enabled": self.reminder_enabled
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """
        Create User entity from dictionary data.
        
        Args:
            data: Dictionary containing user data from storage
            
        Returns:
            User entity instance
        """
        # Handle datetime parsing
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            
        return cls(**data)


class Session(BaseModel):
    """
    Session entity representing a focus tracking session.
    
    Follows SOLID principles:
    - Single Responsibility: Manages session data and timing logic only
    - Open/Closed: Extensible for different session types
    - Liskov Substitution: Can be substituted by session subclasses
    - Interface Segregation: Focused interface for session management
    - Dependency Inversion: Independent of storage implementation
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique session identifier")
    user_id: str = Field(..., description="ID of the user who owns this session")
    title: Optional[str] = Field(None, max_length=200, description="Optional session title/description")
    
    # Session timing
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Session start timestamp")
    end_time: Optional[datetime] = Field(None, description="Session end timestamp")
    duration_minutes: Optional[int] = Field(None, ge=0, description="Session duration in minutes")
    
    # Session state
    status: SessionStatus = Field(default=SessionStatus.ACTIVE, description="Current session status")
    
    # Session metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Session creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last session update timestamp")
    
    # Optional session details
    notes: Optional[str] = Field(None, max_length=1000, description="Optional session notes")
    tags: Optional[list[str]] = Field(default_factory=list, description="Optional session tags")

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        },
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Morning Focus Session",
                "duration_minutes": 25,
                "status": "completed",
                "notes": "Worked on project documentation",
                "tags": ["work", "documentation"]
            }
        }
    )

    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        """Ensure user_id is provided and not empty."""
        if not v or len(v.strip()) == 0:
            raise ValueError('User ID is required')
        return v.strip()

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Validate session title if provided."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v

    @field_validator('notes')
    @classmethod
    def validate_notes(cls, v):
        """Validate session notes if provided."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Validate and clean session tags."""
        if not v:
            return []
        # Clean tags: strip whitespace, remove empty tags, limit to 10 tags
        cleaned_tags = [tag.strip().lower() for tag in v if tag and tag.strip()]
        return cleaned_tags[:10]  # Limit to 10 tags

    @field_validator('end_time')
    @classmethod
    def validate_end_time(cls, v, info):
        """Ensure end_time is after start_time if provided."""
        if v is not None and 'start_time' in info.data:
            if v <= info.data['start_time']:
                raise ValueError('End time must be after start time')
        return v

    def complete_session(self, end_time: Optional[datetime] = None) -> None:
        """
        Complete the session and calculate duration.
        
        Args:
            end_time: Optional end time. If not provided, uses current time.
        """
        if self.status == SessionStatus.COMPLETED:
            return  # Already completed
            
        self.end_time = end_time or datetime.now(timezone.utc)
        self.status = SessionStatus.COMPLETED
        
        # Calculate duration in minutes
        time_diff = self.end_time - self.start_time
        self.duration_minutes = max(0, int(time_diff.total_seconds() / 60))
        
        self.update_timestamp()

    def pause_session(self) -> None:
        """Pause an active session."""
        if self.status == SessionStatus.ACTIVE:
            self.status = SessionStatus.PAUSED
            self.update_timestamp()

    def resume_session(self) -> None:
        """Resume a paused session."""
        if self.status == SessionStatus.PAUSED:
            self.status = SessionStatus.ACTIVE
            self.update_timestamp()

    def cancel_session(self) -> None:
        """Cancel the session."""
        self.status = SessionStatus.CANCELLED
        self.update_timestamp()

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.now(timezone.utc)

    @property
    def is_active(self) -> bool:
        """Check if session is currently active."""
        return self.status == SessionStatus.ACTIVE

    @property
    def is_completed(self) -> bool:
        """Check if session is completed."""
        return self.status == SessionStatus.COMPLETED

    @property
    def current_duration_minutes(self) -> int:
        """
        Get current session duration in minutes.
        For active sessions, calculates from start to now.
        For completed sessions, returns stored duration.
        """
        if self.duration_minutes is not None:
            return self.duration_minutes
            
        if self.status == SessionStatus.ACTIVE:
            current_time = datetime.now(timezone.utc)
            time_diff = current_time - self.start_time
            return max(0, int(time_diff.total_seconds() / 60))
            
        return 0

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Session entity to dictionary format for storage.
        
        Returns:
            Dictionary representation suitable for database storage
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_minutes": self.duration_minutes,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "notes": self.notes,
            "tags": self.tags or []
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """
        Create Session entity from dictionary data.
        
        Args:
            data: Dictionary containing session data from storage
            
        Returns:
            Session entity instance
        """
        # Handle datetime parsing
        if isinstance(data.get('start_time'), str):
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        if isinstance(data.get('end_time'), str):
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            
        # Handle status enum
        if isinstance(data.get('status'), str):
            data['status'] = SessionStatus(data['status'])
            
        return cls(**data)


class CreateUserDto(BaseModel):
    """
    Data Transfer Object for creating new users.
    
    Follows Interface Segregation Principle by providing only
    the fields needed for user creation.
    """
    email: EmailStr = Field(..., description="User's email address")
    display_name: Optional[str] = Field(None, max_length=100, description="User's display name")
    timezone: str = Field(default="UTC", description="User's preferred timezone")
    daily_goal_minutes: int = Field(default=25, ge=5, le=480, description="Daily focus goal in minutes")


class CreateSessionDto(BaseModel):
    """
    Data Transfer Object for creating new sessions.
    
    Follows Interface Segregation Principle by providing only
    the fields needed for session creation.
    """
    user_id: str = Field(..., description="ID of the user creating the session")
    title: Optional[str] = Field(None, max_length=200, description="Optional session title")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional session notes")
    tags: Optional[list[str]] = Field(default_factory=list, description="Optional session tags")


class UpdateSessionDto(BaseModel):
    """
    Data Transfer Object for updating existing sessions.
    
    All fields are optional to allow partial updates.
    """
    title: Optional[str] = Field(None, max_length=200, description="Session title")
    notes: Optional[str] = Field(None, max_length=1000, description="Session notes")
    tags: Optional[list[str]] = Field(None, description="Session tags")
    status: Optional[SessionStatus] = Field(None, description="Session status")
