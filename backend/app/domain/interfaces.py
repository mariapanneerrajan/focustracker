"""
Repository and service interfaces following SOLID principles.

This module defines the abstract interfaces that decouple the business logic
from concrete implementations. Following the Dependency Inversion Principle,
the high-level modules depend on these abstractions, not concrete classes.

All interfaces are focused and minimal (Interface Segregation Principle),
and each has a single, well-defined responsibility.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any

from .entities import User, Session, CreateUserDto, CreateSessionDto, UpdateSessionDto


class IUserRepository(ABC):
    """
    User repository interface defining data access operations for users.
    
    Follows SOLID principles:
    - Single Responsibility: Only handles user data persistence
    - Open/Closed: Implementations can extend without modifying interface
    - Liskov Substitution: All implementations must be substitutable
    - Interface Segregation: Minimal, focused interface
    - Dependency Inversion: High-level code depends on this abstraction
    """

    @abstractmethod
    async def create(self, user_dto: CreateUserDto) -> User:
        """
        Create a new user in the repository.
        
        Args:
            user_dto: Data transfer object containing user creation data
            
        Returns:
            Created User entity
            
        Raises:
            UserAlreadyExistsError: If user with email already exists
            ValidationError: If user data is invalid
            RepositoryError: If database operation fails
        """
        pass

    @abstractmethod
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """
        Find a user by their unique identifier.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            User entity if found, None otherwise
            
        Raises:
            RepositoryError: If database operation fails
        """
        pass

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """
        Find a user by their email address.
        
        Args:
            email: User's email address
            
        Returns:
            User entity if found, None otherwise
            
        Raises:
            RepositoryError: If database operation fails
        """
        pass

    @abstractmethod
    async def update(self, user_id: str, updates: Dict[str, Any]) -> Optional[User]:
        """
        Update an existing user with new data.
        
        Args:
            user_id: Unique user identifier
            updates: Dictionary containing fields to update
            
        Returns:
            Updated User entity if found, None otherwise
            
        Raises:
            ValidationError: If update data is invalid
            RepositoryError: If database operation fails
        """
        pass

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """
        Delete a user from the repository.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            True if user was deleted, False if user not found
            
        Raises:
            RepositoryError: If database operation fails
        """
        pass

    @abstractmethod
    async def list_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        List users with pagination support.
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            List of User entities
            
        Raises:
            RepositoryError: If database operation fails
        """
        pass

    @abstractmethod
    async def count_users(self) -> int:
        """
        Count total number of users in the repository.
        
        Returns:
            Total user count
            
        Raises:
            RepositoryError: If database operation fails
        """
        pass

    @abstractmethod
    async def exists(self, user_id: str) -> bool:
        """
        Check if a user exists in the repository.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            True if user exists, False otherwise
            
        Raises:
            RepositoryError: If database operation fails
        """
        pass


class ISessionRepository(ABC):
    """
    Session repository interface defining data access operations for sessions.
    
    Follows SOLID principles by providing a focused interface for session
    data operations, independent of the underlying storage implementation.
    """

    @abstractmethod
    async def create(self, session_dto: CreateSessionDto) -> Session:
        """
        Create a new session in the repository.
        
        Args:
            session_dto: Data transfer object containing session creation data
            
        Returns:
            Created Session entity
            
        Raises:
            ValidationError: If session data is invalid
            RepositoryError: If database operation fails
        """
        pass

    @abstractmethod
    async def find_by_id(self, session_id: str) -> Optional[Session]:
        """
        Find a session by its unique identifier.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Session entity if found, None otherwise
            
        Raises:
            RepositoryError: If database operation fails
        """
        pass

    @abstractmethod
    async def find_by_user_id(
        self, 
        user_id: str, 
        limit: int = 100, 
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Session]:
        """
        Find sessions belonging to a specific user with optional date filtering.
        
        Args:
            user_id: Unique user identifier
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of Session entities
            
        Raises:
            RepositoryError: If database operation fails
        """
        pass

    @abstractmethod
    async def update(self, session_id: str, updates: UpdateSessionDto) -> Optional[Session]:
        """
        Update an existing session with new data.
        
        Args:
            session_id: Unique session identifier
            updates: Data transfer object containing updates
            
        Returns:
            Updated Session entity if found, None otherwise
            
        Raises:
            ValidationError: If update data is invalid
            RepositoryError: If database operation fails
        """
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """
        Delete a session from the repository.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if session was deleted, False if session not found
            
        Raises:
            RepositoryError: If database operation fails
        """
        pass

    @abstractmethod
    async def complete_session(self, session_id: str, end_time: Optional[datetime] = None) -> Optional[Session]:
        """
        Complete an active session and calculate duration.
        
        Args:
            session_id: Unique session identifier
            end_time: Optional end time. If not provided, uses current time.
            
        Returns:
            Updated Session entity if found, None otherwise
            
        Raises:
            RepositoryError: If database operation fails
        """
        pass

    @abstractmethod
    async def get_active_sessions(self, user_id: str) -> List[Session]:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            List of active Session entities
            
        Raises:
            RepositoryError: If database operation fails
        """
        pass

    @abstractmethod
    async def count_sessions(self, user_id: str) -> int:
        """
        Count total number of sessions for a user.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            Total session count for the user
            
        Raises:
            RepositoryError: If database operation fails
        """
        pass


class IAuthService(ABC):
    """
    Authentication service interface defining authentication operations.
    
    Abstracts authentication logic from specific implementations (Firebase, etc.)
    following the Dependency Inversion Principle.
    """

    @abstractmethod
    async def create_user_account(self, email: str, password: str) -> str:
        """
        Create a new user account in the authentication system.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Authentication system user ID
            
        Raises:
            AuthenticationError: If account creation fails
            UserAlreadyExistsError: If user already exists
        """
        pass

    @abstractmethod
    async def verify_credentials(self, email: str, password: str) -> str:
        """
        Verify user credentials and return user ID if valid.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Authentication system user ID
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        pass

    @abstractmethod
    async def delete_user_account(self, auth_user_id: str) -> bool:
        """
        Delete a user account from the authentication system.
        
        Args:
            auth_user_id: Authentication system user ID
            
        Returns:
            True if account was deleted
            
        Raises:
            AuthenticationError: If deletion fails
        """
        pass

    @abstractmethod
    async def update_user_password(self, auth_user_id: str, new_password: str) -> bool:
        """
        Update a user's password in the authentication system.
        
        Args:
            auth_user_id: Authentication system user ID
            new_password: New password
            
        Returns:
            True if password was updated
            
        Raises:
            AuthenticationError: If password update fails
        """
        pass

    @abstractmethod
    async def verify_token(self, token: str) -> Optional[str]:
        """
        Verify an authentication token and return user ID if valid.
        
        Args:
            token: Authentication token to verify
            
        Returns:
            Authentication system user ID if token is valid, None otherwise
            
        Raises:
            AuthenticationError: If token verification fails
        """
        pass


class IDatabaseConnection(ABC):
    """
    Database connection interface for health checks and connection management.
    
    Provides a unified interface for different database implementations
    to report their connection status and health.
    """

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the database connection.
        
        Returns:
            Dictionary containing health check results:
            - status: "healthy" or "unhealthy"
            - details: Additional health information
            - timestamp: Health check timestamp
            
        Raises:
            RepositoryError: If health check fails
        """
        pass

    @abstractmethod
    async def connect(self) -> None:
        """
        Establish connection to the database.
        
        Raises:
            RepositoryError: If connection fails
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close connection to the database.
        
        Raises:
            RepositoryError: If disconnection fails
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if database connection is active.
        
        Returns:
            True if connected, False otherwise
        """
        pass

