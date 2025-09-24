"""
In-memory repository implementations for testing and development.

This module provides in-memory implementations of the repository interfaces,
following the same contracts as the Firebase implementations. These are ideal
for unit testing and development environments where you don't want to depend
on external services.

All implementations follow SOLID principles and maintain the same behavior
as their Firebase counterparts.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from copy import deepcopy

from ..domain.entities import User, Session, CreateUserDto, CreateSessionDto, UpdateSessionDto, SessionStatus
from ..domain.interfaces import IUserRepository, ISessionRepository, IAuthService, IDatabaseConnection
from ..domain.exceptions import (
    RepositoryError, UserAlreadyExistsError, UserNotFoundError, SessionNotFoundError,
    AuthenticationError, ValidationError
)


logger = logging.getLogger(__name__)


class MemoryConnection(IDatabaseConnection):
    """
    In-memory database connection for testing.
    
    Provides a consistent interface for health checks and connection management
    while using in-memory storage.
    """
    
    def __init__(self):
        """Initialize memory connection."""
        self._connected = False
        self._data_store = {
            "users": {},
            "sessions": {},
            "auth_users": {}  # For auth service simulation
        }
    
    async def connect(self) -> None:
        """Establish in-memory connection."""
        self._connected = True
        logger.info("Memory connection established")
    
    async def disconnect(self) -> None:
        """Close in-memory connection."""
        self._connected = False
        self._data_store.clear()
        logger.info("Memory connection closed")
    
    def is_connected(self) -> bool:
        """Check if memory connection is active."""
        return self._connected
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on memory connection."""
        return {
            "status": "healthy" if self._connected else "unhealthy",
            "details": {
                "type": "memory",
                "connected": self._connected,
                "users_count": len(self._data_store.get("users", {})),
                "sessions_count": len(self._data_store.get("sessions", {}))
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def clear_all_data(self) -> None:
        """Clear all data (for testing)."""
        self._data_store = {
            "users": {},
            "sessions": {},
            "auth_users": {}
        }
        logger.info("Cleared all memory data")
    
    @property
    def data_store(self) -> Dict[str, Any]:
        """Get reference to the data store."""
        return self._data_store


class MemoryUserRepository(IUserRepository):
    """
    In-memory implementation of user repository interface.
    
    Provides the same interface as FirebaseUserRepository but stores data
    in memory, making it perfect for unit testing and development.
    
    Follows SOLID principles:
    - Single Responsibility: Only handles user data persistence in memory
    - Open/Closed: Implements interface without requiring changes
    - Liskov Substitution: Can be substituted for any IUserRepository
    - Interface Segregation: Implements only required methods
    - Dependency Inversion: Depends on connection abstraction
    """
    
    def __init__(self, connection: MemoryConnection):
        """
        Initialize memory user repository.
        
        Args:
            connection: Memory connection instance
        """
        self._connection = connection
    
    @property
    def _users(self) -> Dict[str, Dict[str, Any]]:
        """Get users data store."""
        return self._connection.data_store["users"]
    
    async def create(self, user_dto: CreateUserDto) -> User:
        """Create a new user in memory storage."""
        try:
            # Check if user already exists
            existing_user = await self.find_by_email(user_dto.email)
            if existing_user:
                raise UserAlreadyExistsError(email=user_dto.email)
            
            # Create new user entity
            user = User(**user_dto.dict())
            
            # Store in memory
            self._users[user.id] = user.to_dict()
            
            logger.info(f"Created user with ID: {user.id}")
            return deepcopy(user)
            
        except UserAlreadyExistsError:
            raise
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise RepositoryError(
                message=f"Failed to create user with email {user_dto.email}",
                operation="create_user",
                cause=e
            )
    
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Find a user by their ID."""
        try:
            user_data = self._users.get(user_id)
            if user_data:
                return User.from_dict(deepcopy(user_data))
            return None
            
        except Exception as e:
            logger.error(f"Failed to find user by ID {user_id}: {e}")
            raise RepositoryError(
                message=f"Failed to find user with ID {user_id}",
                operation="find_user_by_id",
                cause=e
            )
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by their email address."""
        try:
            email_normalized = email.lower().strip()
            
            for user_data in self._users.values():
                if user_data.get("email", "").lower() == email_normalized:
                    return User.from_dict(deepcopy(user_data))
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find user by email {email}: {e}")
            raise RepositoryError(
                message=f"Failed to find user with email {email}",
                operation="find_user_by_email",
                cause=e
            )
    
    async def update(self, user_id: str, updates: Dict[str, Any]) -> Optional[User]:
        """Update an existing user with new data."""
        try:
            if user_id not in self._users:
                return None
            
            # Update user data
            user_data = self._users[user_id].copy()
            user_data.update(updates)
            user_data["updated_at"] = datetime.now().isoformat()
            
            # Store updated data
            self._users[user_id] = user_data
            
            # Return updated user
            return User.from_dict(deepcopy(user_data))
            
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            raise RepositoryError(
                message=f"Failed to update user with ID {user_id}",
                operation="update_user",
                cause=e
            )
    
    async def delete(self, user_id: str) -> bool:
        """Delete a user from memory storage."""
        try:
            if user_id in self._users:
                del self._users[user_id]
                logger.info(f"Deleted user with ID: {user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise RepositoryError(
                message=f"Failed to delete user with ID {user_id}",
                operation="delete_user",
                cause=e
            )
    
    async def list_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List users with pagination support."""
        try:
            all_users = list(self._users.values())
            
            # Apply pagination
            paginated_users = all_users[offset:offset + limit]
            
            # Convert to User entities
            users = []
            for user_data in paginated_users:
                users.append(User.from_dict(deepcopy(user_data)))
            
            return users
            
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            raise RepositoryError(
                message="Failed to list users",
                operation="list_users",
                cause=e
            )
    
    async def count_users(self) -> int:
        """Count total number of users in memory storage."""
        try:
            return len(self._users)
        except Exception as e:
            logger.error(f"Failed to count users: {e}")
            raise RepositoryError(
                message="Failed to count users",
                operation="count_users",
                cause=e
            )
    
    async def exists(self, user_id: str) -> bool:
        """Check if a user exists in memory storage."""
        try:
            return user_id in self._users
        except Exception as e:
            logger.error(f"Failed to check if user {user_id} exists: {e}")
            raise RepositoryError(
                message=f"Failed to check if user {user_id} exists",
                operation="user_exists",
                cause=e
            )


class MemorySessionRepository(ISessionRepository):
    """
    In-memory implementation of session repository interface.
    
    Provides the same interface as FirebaseSessionRepository but stores data
    in memory for testing and development purposes.
    """
    
    def __init__(self, connection: MemoryConnection):
        """
        Initialize memory session repository.
        
        Args:
            connection: Memory connection instance
        """
        self._connection = connection
    
    @property
    def _sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get sessions data store."""
        return self._connection.data_store["sessions"]
    
    async def create(self, session_dto: CreateSessionDto) -> Session:
        """Create a new session in memory storage."""
        try:
            # Create new session entity
            session = Session(**session_dto.dict())
            
            # Store in memory
            self._sessions[session.id] = session.to_dict()
            
            logger.info(f"Created session with ID: {session.id}")
            return deepcopy(session)
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise RepositoryError(
                message="Failed to create session",
                operation="create_session",
                cause=e
            )
    
    async def find_by_id(self, session_id: str) -> Optional[Session]:
        """Find a session by its ID."""
        try:
            session_data = self._sessions.get(session_id)
            if session_data:
                return Session.from_dict(deepcopy(session_data))
            return None
            
        except Exception as e:
            logger.error(f"Failed to find session by ID {session_id}: {e}")
            raise RepositoryError(
                message=f"Failed to find session with ID {session_id}",
                operation="find_session_by_id",
                cause=e
            )
    
    async def find_by_user_id(
        self, 
        user_id: str, 
        limit: int = 100, 
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Session]:
        """Find sessions belonging to a specific user."""
        try:
            # Filter sessions by user_id
            user_sessions = []
            for session_data in self._sessions.values():
                if session_data.get("user_id") == user_id:
                    # Apply date filters if provided
                    session_start = datetime.fromisoformat(session_data["start_time"])
                    
                    if start_date and session_start < start_date:
                        continue
                    if end_date and session_start > end_date:
                        continue
                    
                    user_sessions.append(session_data)
            
            # Sort by start_time (newest first)
            user_sessions.sort(key=lambda x: x["start_time"], reverse=True)
            
            # Apply pagination
            paginated_sessions = user_sessions[offset:offset + limit]
            
            # Convert to Session entities
            sessions = []
            for session_data in paginated_sessions:
                sessions.append(Session.from_dict(deepcopy(session_data)))
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to find sessions for user {user_id}: {e}")
            raise RepositoryError(
                message=f"Failed to find sessions for user {user_id}",
                operation="find_sessions_by_user",
                cause=e
            )
    
    async def update(self, session_id: str, updates: UpdateSessionDto) -> Optional[Session]:
        """Update an existing session."""
        try:
            if session_id not in self._sessions:
                return None
            
            # Convert DTO to dict and remove None values
            update_data = {k: v for k, v in updates.dict().items() if v is not None}
            
            # Handle status enum serialization
            if "status" in update_data and isinstance(update_data["status"], SessionStatus):
                update_data["status"] = update_data["status"].value
            
            # Update session data
            session_data = self._sessions[session_id].copy()
            session_data.update(update_data)
            session_data["updated_at"] = datetime.now().isoformat()
            
            # Store updated data
            self._sessions[session_id] = session_data
            
            # Return updated session
            return Session.from_dict(deepcopy(session_data))
            
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            raise RepositoryError(
                message=f"Failed to update session with ID {session_id}",
                operation="update_session",
                cause=e
            )
    
    async def delete(self, session_id: str) -> bool:
        """Delete a session from memory storage."""
        try:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(f"Deleted session with ID: {session_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise RepositoryError(
                message=f"Failed to delete session with ID {session_id}",
                operation="delete_session",
                cause=e
            )
    
    async def complete_session(self, session_id: str, end_time: Optional[datetime] = None) -> Optional[Session]:
        """Complete an active session and calculate duration."""
        try:
            session = await self.find_by_id(session_id)
            if not session:
                return None
            
            # Complete the session
            session.complete_session(end_time)
            
            # Update in memory storage
            self._sessions[session_id] = session.to_dict()
            
            logger.info(f"Completed session with ID: {session_id}")
            return deepcopy(session)
            
        except Exception as e:
            logger.error(f"Failed to complete session {session_id}: {e}")
            raise RepositoryError(
                message=f"Failed to complete session with ID {session_id}",
                operation="complete_session",
                cause=e
            )
    
    async def get_active_sessions(self, user_id: str) -> List[Session]:
        """Get all active sessions for a user."""
        try:
            active_sessions = []
            
            for session_data in self._sessions.values():
                if (session_data.get("user_id") == user_id and 
                    session_data.get("status") == "active"):
                    active_sessions.append(Session.from_dict(deepcopy(session_data)))
            
            return active_sessions
            
        except Exception as e:
            logger.error(f"Failed to get active sessions for user {user_id}: {e}")
            raise RepositoryError(
                message=f"Failed to get active sessions for user {user_id}",
                operation="get_active_sessions",
                cause=e
            )
    
    async def count_sessions(self, user_id: str) -> int:
        """Count total number of sessions for a user."""
        try:
            count = 0
            for session_data in self._sessions.values():
                if session_data.get("user_id") == user_id:
                    count += 1
            return count
            
        except Exception as e:
            logger.error(f"Failed to count sessions for user {user_id}: {e}")
            raise RepositoryError(
                message=f"Failed to count sessions for user {user_id}",
                operation="count_sessions",
                cause=e
            )


class MemoryAuthService(IAuthService):
    """
    In-memory authentication service for testing.
    
    Simulates authentication operations without requiring external services.
    Useful for unit testing and development environments.
    """
    
    def __init__(self, connection: MemoryConnection):
        """
        Initialize memory auth service.
        
        Args:
            connection: Memory connection instance
        """
        self._connection = connection
    
    @property
    def _auth_users(self) -> Dict[str, Dict[str, Any]]:
        """Get auth users data store."""
        return self._connection.data_store["auth_users"]
    
    async def create_user_account(self, email: str, password: str) -> str:
        """Create a new user account in memory auth system."""
        try:
            # Check if user already exists
            email_normalized = email.lower().strip()
            for auth_data in self._auth_users.values():
                if auth_data.get("email", "").lower() == email_normalized:
                    raise UserAlreadyExistsError(email=email)
            
            # Create new auth user
            auth_user_id = f"auth_{len(self._auth_users) + 1:04d}"
            self._auth_users[auth_user_id] = {
                "uid": auth_user_id,
                "email": email_normalized,
                "password_hash": f"hash_{password}",  # Simulated password hash
                "created_at": datetime.now().isoformat(),
                "email_verified": False
            }
            
            logger.info(f"Created memory auth user account: {auth_user_id}")
            return auth_user_id
            
        except UserAlreadyExistsError:
            raise
        except Exception as e:
            logger.error(f"Failed to create memory auth user account: {e}")
            raise AuthenticationError(
                message="Failed to create user account",
                auth_operation="create_user",
                cause=e
            )
    
    async def verify_credentials(self, email: str, password: str) -> str:
        """Verify user credentials against memory auth system."""
        try:
            email_normalized = email.lower().strip()
            password_hash = f"hash_{password}"  # Simulated password hash
            
            for auth_data in self._auth_users.values():
                if (auth_data.get("email", "").lower() == email_normalized and 
                    auth_data.get("password_hash") == password_hash):
                    return auth_data["uid"]
            
            raise AuthenticationError(
                message="Invalid credentials",
                auth_operation="verify_credentials"
            )
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Failed to verify credentials: {e}")
            raise AuthenticationError(
                message="Failed to verify credentials",
                auth_operation="verify_credentials",
                cause=e
            )
    
    async def delete_user_account(self, auth_user_id: str) -> bool:
        """Delete a user account from memory auth system."""
        try:
            if auth_user_id in self._auth_users:
                del self._auth_users[auth_user_id]
                logger.info(f"Deleted memory auth user account: {auth_user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete memory auth user account: {e}")
            raise AuthenticationError(
                message="Failed to delete user account",
                auth_operation="delete_user",
                cause=e
            )
    
    async def update_user_password(self, auth_user_id: str, new_password: str) -> bool:
        """Update a user's password in memory auth system."""
        try:
            if auth_user_id in self._auth_users:
                self._auth_users[auth_user_id]["password_hash"] = f"hash_{new_password}"
                logger.info(f"Updated password for memory auth user: {auth_user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to update user password: {e}")
            raise AuthenticationError(
                message="Failed to update user password",
                auth_operation="update_password",
                cause=e
            )
    
    async def verify_token(self, token: str) -> Optional[str]:
        """Verify an authentication token (simulated for memory auth)."""
        try:
            # Simple token format: "token_{auth_user_id}"
            if token.startswith("token_"):
                auth_user_id = token.replace("token_", "")
                if auth_user_id in self._auth_users:
                    return auth_user_id
            return None
            
        except Exception as e:
            logger.warning(f"Token verification failed: {e}")
            return None

