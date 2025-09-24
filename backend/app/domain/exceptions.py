"""
Custom exceptions for the Focus Tracker application.

This module defines domain-specific exceptions that provide clear error handling
and follow SOLID principles by maintaining single responsibility for error types.

All exceptions include detailed error messages, error codes, and context
information to facilitate debugging and user-friendly error responses.
"""

from typing import Any, Dict, Optional


class FocusTrackerError(Exception):
    """
    Base exception for all Focus Tracker application errors.
    
    Follows Single Responsibility Principle by providing a common base
    for all application-specific exceptions with consistent error handling.
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN_ERROR",
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """
        Initialize the base exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Optional additional error context
            cause: Optional underlying exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary format for API responses.
        
        Returns:
            Dictionary representation of the exception
        """
        result = {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }
        
        if self.cause:
            result["cause"] = str(self.cause)
            
        return result


class ValidationError(FocusTrackerError):
    """
    Raised when input data validation fails.
    
    Used for invalid user input, malformed data, or constraint violations
    that prevent proper processing of user requests.
    """
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        invalid_value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize validation error.
        
        Args:
            message: Validation error message
            field_name: Name of the field that failed validation
            invalid_value: The invalid value that was provided
            details: Additional validation context
        """
        error_details = details or {}
        if field_name:
            error_details["field"] = field_name
        if invalid_value is not None:
            error_details["invalid_value"] = str(invalid_value)
            
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=error_details
        )
        self.field_name = field_name
        self.invalid_value = invalid_value


class RepositoryError(FocusTrackerError):
    """
    Raised when database or repository operations fail.
    
    Encapsulates all database-related errors including connection failures,
    query errors, and data consistency issues.
    """
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """
        Initialize repository error.
        
        Args:
            message: Repository error message
            operation: The database operation that failed
            details: Additional error context
            cause: Underlying database exception
        """
        error_details = details or {}
        if operation:
            error_details["operation"] = operation
            
        super().__init__(
            message=message,
            error_code="REPOSITORY_ERROR",
            details=error_details,
            cause=cause
        )
        self.operation = operation


class UserAlreadyExistsError(FocusTrackerError):
    """
    Raised when attempting to create a user that already exists.
    
    Specific error for user registration conflicts, providing clear
    feedback about duplicate user accounts.
    """
    
    def __init__(
        self,
        email: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize user already exists error.
        
        Args:
            email: Email address of the conflicting user
            details: Additional error context
        """
        message = f"User with email '{email}' already exists"
        error_details = details or {}
        error_details["email"] = email
        
        super().__init__(
            message=message,
            error_code="USER_ALREADY_EXISTS",
            details=error_details
        )
        self.email = email


class UserNotFoundError(FocusTrackerError):
    """
    Raised when attempting to access a user that doesn't exist.
    
    Specific error for operations on non-existent users, providing
    clear feedback about missing user accounts.
    """
    
    def __init__(
        self,
        identifier: str,
        identifier_type: str = "id",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize user not found error.
        
        Args:
            identifier: User identifier that was not found
            identifier_type: Type of identifier (id, email, etc.)
            details: Additional error context
        """
        message = f"User with {identifier_type} '{identifier}' not found"
        error_details = details or {}
        error_details["identifier"] = identifier
        error_details["identifier_type"] = identifier_type
        
        super().__init__(
            message=message,
            error_code="USER_NOT_FOUND",
            details=error_details
        )
        self.identifier = identifier
        self.identifier_type = identifier_type


class SessionNotFoundError(FocusTrackerError):
    """
    Raised when attempting to access a session that doesn't exist.
    
    Specific error for operations on non-existent sessions.
    """
    
    def __init__(
        self,
        session_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize session not found error.
        
        Args:
            session_id: Session identifier that was not found
            details: Additional error context
        """
        message = f"Session with id '{session_id}' not found"
        error_details = details or {}
        error_details["session_id"] = session_id
        
        super().__init__(
            message=message,
            error_code="SESSION_NOT_FOUND",
            details=error_details
        )
        self.session_id = session_id


class AuthenticationError(FocusTrackerError):
    """
    Raised when authentication operations fail.
    
    Encapsulates authentication-related errors including invalid credentials,
    token verification failures, and authentication service errors.
    """
    
    def __init__(
        self,
        message: str,
        auth_operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """
        Initialize authentication error.
        
        Args:
            message: Authentication error message
            auth_operation: The authentication operation that failed
            details: Additional error context
            cause: Underlying authentication exception
        """
        error_details = details or {}
        if auth_operation:
            error_details["auth_operation"] = auth_operation
            
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=error_details,
            cause=cause
        )
        self.auth_operation = auth_operation


class AuthorizationError(FocusTrackerError):
    """
    Raised when a user is not authorized to perform an operation.
    
    Specific error for access control violations and permission denials.
    """
    
    def __init__(
        self,
        message: str,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize authorization error.
        
        Args:
            message: Authorization error message
            user_id: ID of the user attempting the operation
            resource: Resource being accessed
            action: Action being attempted
            details: Additional error context
        """
        error_details = details or {}
        if user_id:
            error_details["user_id"] = user_id
        if resource:
            error_details["resource"] = resource
        if action:
            error_details["action"] = action
            
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=error_details
        )
        self.user_id = user_id
        self.resource = resource
        self.action = action


class BusinessRuleError(FocusTrackerError):
    """
    Raised when business rule validation fails.
    
    Used for domain-specific rule violations that prevent valid
    business operations from completing.
    """
    
    def __init__(
        self,
        message: str,
        rule_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize business rule error.
        
        Args:
            message: Business rule error message
            rule_name: Name of the business rule that was violated
            details: Additional error context
        """
        error_details = details or {}
        if rule_name:
            error_details["rule_name"] = rule_name
            
        super().__init__(
            message=message,
            error_code="BUSINESS_RULE_ERROR",
            details=error_details
        )
        self.rule_name = rule_name


class ConfigurationError(FocusTrackerError):
    """
    Raised when application configuration is invalid or missing.
    
    Used for setup and configuration issues that prevent proper
    application initialization.
    """
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize configuration error.
        
        Args:
            message: Configuration error message
            config_key: Configuration key that is invalid or missing
            details: Additional error context
        """
        error_details = details or {}
        if config_key:
            error_details["config_key"] = config_key
            
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=error_details
        )
        self.config_key = config_key


class ExternalServiceError(FocusTrackerError):
    """
    Raised when external service calls fail.
    
    Encapsulates errors from third-party services including API failures,
    network issues, and service unavailability.
    """
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """
        Initialize external service error.
        
        Args:
            message: External service error message
            service_name: Name of the external service
            operation: The operation that failed
            details: Additional error context
            cause: Underlying service exception
        """
        error_details = details or {}
        if service_name:
            error_details["service_name"] = service_name
        if operation:
            error_details["operation"] = operation
            
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=error_details,
            cause=cause
        )
        self.service_name = service_name
        self.operation = operation

