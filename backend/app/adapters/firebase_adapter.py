"""
Firebase adapter implementation for repository interfaces.

This module implements the repository and authentication interfaces using Firebase
services, following SOLID principles by providing concrete implementations that
can be substituted for any other implementation.

The adapter pattern isolates Firebase-specific code from the business logic,
making it easy to switch to different database providers if needed.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

import firebase_admin
from firebase_admin import credentials, firestore, auth as firebase_auth
from google.cloud.firestore import Client as FirestoreClient
from google.cloud.exceptions import NotFound, Conflict

from ..domain.entities import User, Session, CreateUserDto, CreateSessionDto, UpdateSessionDto
from ..domain.interfaces import IUserRepository, ISessionRepository, IAuthService, IDatabaseConnection
from ..domain.exceptions import (
    RepositoryError, UserAlreadyExistsError, UserNotFoundError, SessionNotFoundError,
    AuthenticationError, ValidationError, ConfigurationError
)
from ..core.config import settings


logger = logging.getLogger(__name__)


class FirebaseConnection(IDatabaseConnection):
    """
    Firebase database connection management.
    
    Handles Firebase initialization, connection health checks, and provides
    a centralized way to manage Firebase client instances.
    """
    
    def __init__(self):
        """Initialize Firebase connection."""
        self._app: Optional[firebase_admin.App] = None
        self._db: Optional[FirestoreClient] = None
        self._initialized = False
    
    async def connect(self) -> None:
        """
        Initialize Firebase connection with service account credentials.
        
        Raises:
            ConfigurationError: If Firebase configuration is invalid
            RepositoryError: If Firebase initialization fails
        """
        try:
            # Validate configuration
            settings.validate_firebase_config()
            
            # Initialize Firebase if not already done
            if not self._initialized:
                # Check if Firebase app already exists (for testing)
                try:
                    self._app = firebase_admin.get_app()
                    logger.info("Using existing Firebase app")
                except ValueError:
                    # No app exists, create new one
                    cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
                    self._app = firebase_admin.initialize_app(cred, {
                        'projectId': settings.FIREBASE_PROJECT_ID
                    })
                    logger.info("Initialized new Firebase app")
                
                # Initialize Firestore client
                self._db = firestore.client(app=self._app)
                self._initialized = True
                
                logger.info("Firebase connection established successfully")
                
        except Exception as e:
            logger.error(f"Failed to connect to Firebase: {e}")
            raise RepositoryError(
                message="Failed to initialize Firebase connection",
                operation="connect",
                cause=e
            )
    
    async def disconnect(self) -> None:
        """
        Close Firebase connection.
        
        Note: Firebase Admin SDK manages connections automatically,
        but this method provides a clean interface for testing.
        """
        self._db = None
        self._initialized = False
        logger.info("Firebase connection closed")
    
    def is_connected(self) -> bool:
        """Check if Firebase connection is active."""
        return self._initialized and self._db is not None
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Firebase connection.
        
        Returns:
            Dictionary containing health check results
        """
        try:
            if not self.is_connected():
                return {
                    "status": "unhealthy",
                    "details": "Firebase not initialized",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Test basic Firestore operation
            test_doc = self._db.collection("health_check").document("test")
            test_doc.set({"timestamp": datetime.now(), "status": "test"})
            test_doc.delete()
            
            return {
                "status": "healthy",
                "details": {
                    "project_id": settings.FIREBASE_PROJECT_ID,
                    "connected": True,
                    "firestore": "operational"
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Firebase health check failed: {e}")
            return {
                "status": "unhealthy",
                "details": {"error": str(e)},
                "timestamp": datetime.now().isoformat()
            }
    
    @property
    def db(self) -> FirestoreClient:
        """
        Get Firestore client instance.
        
        Returns:
            Firestore client instance
            
        Raises:
            RepositoryError: If not connected to Firebase
        """
        if not self._db:
            raise RepositoryError(
                message="Firebase not connected. Call connect() first.",
                operation="get_client"
            )
        return self._db


class FirebaseUserRepository(IUserRepository):
    """
    Firebase implementation of user repository interface.
    
    Follows SOLID principles:
    - Single Responsibility: Only handles user data persistence with Firebase
    - Open/Closed: Implements interface without requiring changes to interface
    - Liskov Substitution: Can be substituted for any IUserRepository implementation
    - Interface Segregation: Implements only required user repository methods
    - Dependency Inversion: Depends on Firebase connection abstraction
    """
    
    COLLECTION_NAME = "users"
    
    def __init__(self, connection: FirebaseConnection):
        """
        Initialize Firebase user repository.
        
        Args:
            connection: Firebase connection instance
        """
        self._connection = connection
    
    @property
    def _collection(self):
        """Get users collection reference."""
        return self._connection.db.collection(self.COLLECTION_NAME)
    
    async def create(self, user_dto: CreateUserDto) -> User:
        """
        Create a new user in Firestore.
        
        Args:
            user_dto: User creation data
            
        Returns:
            Created User entity
            
        Raises:
            UserAlreadyExistsError: If user with email already exists
            ValidationError: If user data is invalid
            RepositoryError: If database operation fails
        """
        try:
            # Check if user already exists
            existing_user = await self.find_by_email(user_dto.email)
            if existing_user:
                raise UserAlreadyExistsError(email=user_dto.email)
            
            # Create new user entity
            user = User(**user_dto.dict())
            
            # Save to Firestore
            doc_ref = self._collection.document(user.id)
            doc_ref.set(user.to_dict())
            
            logger.info(f"Created user with ID: {user.id}")
            return user
            
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
        """
        Find a user by their ID.
        
        Args:
            user_id: User identifier
            
        Returns:
            User entity if found, None otherwise
        """
        try:
            doc_ref = self._collection.document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                user_data = doc.to_dict()
                return User.from_dict(user_data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to find user by ID {user_id}: {e}")
            raise RepositoryError(
                message=f"Failed to find user with ID {user_id}",
                operation="find_user_by_id",
                cause=e
            )
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """
        Find a user by their email address.
        
        Args:
            email: User's email address
            
        Returns:
            User entity if found, None otherwise
        """
        try:
            # Query for user with matching email
            query = self._collection.where("email", "==", email.lower().strip())
            docs = query.limit(1).stream()
            
            for doc in docs:
                user_data = doc.to_dict()
                return User.from_dict(user_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find user by email {email}: {e}")
            raise RepositoryError(
                message=f"Failed to find user with email {email}",
                operation="find_user_by_email",
                cause=e
            )
    
    async def update(self, user_id: str, updates: Dict[str, Any]) -> Optional[User]:
        """
        Update an existing user with new data.
        
        Args:
            user_id: User identifier
            updates: Dictionary containing fields to update
            
        Returns:
            Updated User entity if found, None otherwise
        """
        try:
            doc_ref = self._collection.document(user_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            # Add updated timestamp
            updates["updated_at"] = datetime.now().isoformat()
            
            # Update document
            doc_ref.update(updates)
            
            # Return updated user
            updated_doc = doc_ref.get()
            if updated_doc.exists:
                user_data = updated_doc.to_dict()
                return User.from_dict(user_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            raise RepositoryError(
                message=f"Failed to update user with ID {user_id}",
                operation="update_user",
                cause=e
            )
    
    async def delete(self, user_id: str) -> bool:
        """
        Delete a user from Firestore.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if user was deleted, False if user not found
        """
        try:
            doc_ref = self._collection.document(user_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            doc_ref.delete()
            logger.info(f"Deleted user with ID: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise RepositoryError(
                message=f"Failed to delete user with ID {user_id}",
                operation="delete_user",
                cause=e
            )
    
    async def list_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        List users with pagination support.
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            List of User entities
        """
        try:
            query = self._collection.limit(limit).offset(offset)
            docs = query.stream()
            
            users = []
            for doc in docs:
                user_data = doc.to_dict()
                users.append(User.from_dict(user_data))
            
            return users
            
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            raise RepositoryError(
                message="Failed to list users",
                operation="list_users",
                cause=e
            )
    
    async def count_users(self) -> int:
        """
        Count total number of users in the repository.
        
        Returns:
            Total user count
        """
        try:
            # Note: For large collections, consider using aggregation queries
            docs = self._collection.stream()
            count = sum(1 for _ in docs)
            return count
            
        except Exception as e:
            logger.error(f"Failed to count users: {e}")
            raise RepositoryError(
                message="Failed to count users",
                operation="count_users",
                cause=e
            )
    
    async def exists(self, user_id: str) -> bool:
        """
        Check if a user exists in the repository.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if user exists, False otherwise
        """
        try:
            doc_ref = self._collection.document(user_id)
            doc = doc_ref.get()
            return doc.exists
            
        except Exception as e:
            logger.error(f"Failed to check if user {user_id} exists: {e}")
            raise RepositoryError(
                message=f"Failed to check if user {user_id} exists",
                operation="user_exists",
                cause=e
            )


class FirebaseSessionRepository(ISessionRepository):
    """
    Firebase implementation of session repository interface.
    
    Handles session data persistence using Firestore, providing full CRUD
    operations and session-specific business logic.
    """
    
    COLLECTION_NAME = "sessions"
    
    def __init__(self, connection: FirebaseConnection):
        """
        Initialize Firebase session repository.
        
        Args:
            connection: Firebase connection instance
        """
        self._connection = connection
    
    @property
    def _collection(self):
        """Get sessions collection reference."""
        return self._connection.db.collection(self.COLLECTION_NAME)
    
    async def create(self, session_dto: CreateSessionDto) -> Session:
        """
        Create a new session in Firestore.
        
        Args:
            session_dto: Session creation data
            
        Returns:
            Created Session entity
        """
        try:
            # Create new session entity
            session = Session(**session_dto.dict())
            
            # Save to Firestore
            doc_ref = self._collection.document(session.id)
            doc_ref.set(session.to_dict())
            
            logger.info(f"Created session with ID: {session.id}")
            return session
            
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
            doc_ref = self._collection.document(session_id)
            doc = doc_ref.get()
            
            if doc.exists:
                session_data = doc.to_dict()
                return Session.from_dict(session_data)
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
            query = self._collection.where("user_id", "==", user_id)
            
            # Add date filters if provided
            if start_date:
                query = query.where("start_time", ">=", start_date.isoformat())
            if end_date:
                query = query.where("start_time", "<=", end_date.isoformat())
            
            # Add pagination
            query = query.limit(limit).offset(offset)
            
            docs = query.stream()
            
            sessions = []
            for doc in docs:
                session_data = doc.to_dict()
                sessions.append(Session.from_dict(session_data))
            
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
            doc_ref = self._collection.document(session_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            # Convert DTO to dict and remove None values
            update_data = {k: v for k, v in updates.dict().items() if v is not None}
            
            # Add updated timestamp
            update_data["updated_at"] = datetime.now().isoformat()
            
            # Update document
            doc_ref.update(update_data)
            
            # Return updated session
            updated_doc = doc_ref.get()
            if updated_doc.exists:
                session_data = updated_doc.to_dict()
                return Session.from_dict(session_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            raise RepositoryError(
                message=f"Failed to update session with ID {session_id}",
                operation="update_session",
                cause=e
            )
    
    async def delete(self, session_id: str) -> bool:
        """Delete a session from Firestore."""
        try:
            doc_ref = self._collection.document(session_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            doc_ref.delete()
            logger.info(f"Deleted session with ID: {session_id}")
            return True
            
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
            
            # Update in Firestore
            doc_ref = self._collection.document(session_id)
            doc_ref.update(session.to_dict())
            
            logger.info(f"Completed session with ID: {session_id}")
            return session
            
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
            query = (self._collection
                    .where("user_id", "==", user_id)
                    .where("status", "==", "active"))
            
            docs = query.stream()
            
            sessions = []
            for doc in docs:
                session_data = doc.to_dict()
                sessions.append(Session.from_dict(session_data))
            
            return sessions
            
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
            query = self._collection.where("user_id", "==", user_id)
            docs = query.stream()
            count = sum(1 for _ in docs)
            return count
            
        except Exception as e:
            logger.error(f"Failed to count sessions for user {user_id}: {e}")
            raise RepositoryError(
                message=f"Failed to count sessions for user {user_id}",
                operation="count_sessions",
                cause=e
            )


class FirebaseAuthService(IAuthService):
    """
    Firebase authentication service implementation.
    
    Provides authentication operations using Firebase Auth,
    following the adapter pattern to isolate Firebase-specific code.
    """
    
    def __init__(self, connection: FirebaseConnection):
        """
        Initialize Firebase auth service.
        
        Args:
            connection: Firebase connection instance
        """
        self._connection = connection
    
    async def create_user_account(self, email: str, password: str) -> str:
        """Create a new user account in Firebase Auth."""
        try:
            user_record = firebase_auth.create_user(
                email=email,
                password=password,
                email_verified=False
            )
            
            logger.info(f"Created Firebase user account: {user_record.uid}")
            return user_record.uid
            
        except firebase_auth.EmailAlreadyExistsError:
            raise UserAlreadyExistsError(email=email)
        except Exception as e:
            logger.error(f"Failed to create Firebase user account: {e}")
            raise AuthenticationError(
                message="Failed to create user account",
                auth_operation="create_user",
                cause=e
            )
    
    async def verify_credentials(self, email: str, password: str) -> str:
        """
        Verify user credentials.
        
        Note: Firebase Admin SDK doesn't provide password verification.
        This would typically be done on the client side with Firebase Auth SDK.
        For server-side verification, you'd need to implement custom token verification.
        """
        try:
            # Get user by email
            user_record = firebase_auth.get_user_by_email(email)
            
            # In a real implementation, you would verify the password
            # For now, we assume the credentials are valid if user exists
            return user_record.uid
            
        except firebase_auth.UserNotFoundError:
            raise AuthenticationError(
                message="Invalid credentials",
                auth_operation="verify_credentials"
            )
        except Exception as e:
            logger.error(f"Failed to verify credentials: {e}")
            raise AuthenticationError(
                message="Failed to verify credentials",
                auth_operation="verify_credentials",
                cause=e
            )
    
    async def delete_user_account(self, auth_user_id: str) -> bool:
        """Delete a user account from Firebase Auth."""
        try:
            firebase_auth.delete_user(auth_user_id)
            logger.info(f"Deleted Firebase user account: {auth_user_id}")
            return True
            
        except firebase_auth.UserNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Failed to delete Firebase user account: {e}")
            raise AuthenticationError(
                message="Failed to delete user account",
                auth_operation="delete_user",
                cause=e
            )
    
    async def update_user_password(self, auth_user_id: str, new_password: str) -> bool:
        """Update a user's password in Firebase Auth."""
        try:
            firebase_auth.update_user(auth_user_id, password=new_password)
            logger.info(f"Updated password for Firebase user: {auth_user_id}")
            return True
            
        except firebase_auth.UserNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Failed to update user password: {e}")
            raise AuthenticationError(
                message="Failed to update user password",
                auth_operation="update_password",
                cause=e
            )
    
    async def verify_token(self, token: str) -> Optional[str]:
        """Verify an authentication token and return user ID if valid."""
        try:
            # Verify the token
            decoded_token = firebase_auth.verify_id_token(token)
            return decoded_token["uid"]
            
        except Exception as e:
            logger.warning(f"Token verification failed: {e}")
            return None

