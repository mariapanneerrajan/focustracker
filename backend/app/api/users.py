"""
User API Endpoints

Provides CRUD operations for user management.
Follows SOLID principles:
- Single Responsibility: Only handles user-related endpoints
- Interface Segregation: Clean, focused API interface
- Dependency Inversion: Depends on service abstractions
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from ..domain.entities import User, CreateUserDto
from ..domain.exceptions import (
    UserAlreadyExistsError, UserNotFoundError, RepositoryError, ValidationError
)
from ..services.container import get_service_container


class UserResponse(BaseModel):
    """User response model for API endpoints."""
    id: str
    email: str
    display_name: Optional[str] = None
    daily_goal_minutes: int
    timezone: str
    created_at: datetime
    updated_at: datetime


class UserUpdateRequest(BaseModel):
    """User update request model."""
    display_name: Optional[str] = None
    daily_goal_minutes: Optional[int] = None
    timezone: Optional[str] = None


# Create router
router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create User",
    description="Create a new user in the system"
)
async def create_user(user_dto: CreateUserDto) -> UserResponse:
    """
    Create a new user.
    
    Args:
        user_dto: User creation data
        
    Returns:
        UserResponse: Created user information
        
    Raises:
        400: If user with email already exists or validation fails
        500: If database operation fails
    """
    try:
        container = await get_service_container()
        user_repo = container.user_repository
        
        user = await user_repo.create(user_dto)
        
        return UserResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            daily_goal_minutes=user.daily_goal_minutes,
            timezone=user.timezone,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {e.email} already exists"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="List Users",
    description="Get a list of all users with pagination"
)
async def list_users(limit: int = 100, offset: int = 0) -> List[UserResponse]:
    """
    List users with pagination.
    
    Args:
        limit: Maximum number of users to return (default 100)
        offset: Number of users to skip (default 0)
        
    Returns:
        List[UserResponse]: List of users
    """
    try:
        container = await get_service_container()
        user_repo = container.user_repository
        
        users = await user_repo.list_users(limit=limit, offset=offset)
        
        return [
            UserResponse(
                id=user.id,
                email=user.email,
                display_name=user.display_name,
                daily_goal_minutes=user.daily_goal_minutes,
                timezone=user.timezone,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            for user in users
        ]
        
    except RepositoryError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get User",
    description="Get a specific user by ID"
)
async def get_user(user_id: str) -> UserResponse:
    """
    Get a user by ID.
    
    Args:
        user_id: User identifier
        
    Returns:
        UserResponse: User information
        
    Raises:
        404: If user not found
        500: If database operation fails
    """
    try:
        container = await get_service_container()
        user_repo = container.user_repository
        
        user = await user_repo.find_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            daily_goal_minutes=user.daily_goal_minutes,
            timezone=user.timezone,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
    except RepositoryError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update User",
    description="Update a user's information"
)
async def update_user(user_id: str, updates: UserUpdateRequest) -> UserResponse:
    """
    Update a user's information.
    
    Args:
        user_id: User identifier
        updates: Fields to update
        
    Returns:
        UserResponse: Updated user information
        
    Raises:
        404: If user not found
        400: If validation fails
        500: If database operation fails
    """
    try:
        container = await get_service_container()
        user_repo = container.user_repository
        
        # Convert to dict and remove None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields provided for update"
            )
        
        user = await user_repo.update(user_id, update_data)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            daily_goal_minutes=user.daily_goal_minutes,
            timezone=user.timezone,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RepositoryError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete User",
    description="Delete a user from the system"
)
async def delete_user(user_id: str):
    """
    Delete a user.
    
    Args:
        user_id: User identifier
        
    Raises:
        404: If user not found
        500: If database operation fails
    """
    try:
        container = await get_service_container()
        user_repo = container.user_repository
        
        deleted = await user_repo.delete(user_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
    except RepositoryError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


@router.get(
    "/{user_id}/exists",
    response_model=bool,
    summary="Check User Exists",
    description="Check if a user exists in the system"
)
async def user_exists(user_id: str) -> bool:
    """
    Check if a user exists.
    
    Args:
        user_id: User identifier
        
    Returns:
        bool: True if user exists, False otherwise
    """
    try:
        container = await get_service_container()
        user_repo = container.user_repository
        
        return await user_repo.exists(user_id)
        
    except RepositoryError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check user existence"
        )

