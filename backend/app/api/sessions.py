"""
Session API Endpoints

Provides CRUD operations for session management.
Follows SOLID principles:
- Single Responsibility: Only handles session-related endpoints
- Interface Segregation: Clean, focused API interface
- Dependency Inversion: Depends on service abstractions
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel

from ..domain.entities import Session, CreateSessionDto, UpdateSessionDto
from ..domain.exceptions import RepositoryError, ValidationError
from ..services.container import get_service_container


class SessionResponse(BaseModel):
    """Session response model for API endpoints."""
    id: str
    user_id: str
    title: Optional[str]
    notes: Optional[str]
    tags: List[str]
    start_time: str
    end_time: Optional[str]
    duration_minutes: Optional[int]
    status: str
    created_at: str
    updated_at: str


# Create router
router = APIRouter(prefix="/sessions", tags=["Sessions"])


def _build_session_response(session: Session) -> SessionResponse:
    """Convert a Session entity into a SessionResponse model."""
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        title=session.title,
        notes=session.notes,
        tags=session.tags or [],
        start_time=session.start_time.isoformat(),
        end_time=session.end_time.isoformat() if session.end_time else None,
        duration_minutes=session.duration_minutes,
        status=session.status.value if hasattr(session.status, "value") else session.status,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
    )


@router.post(
    "/",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Session",
    description="Create a new focus session"
)
async def create_session(session_dto: CreateSessionDto) -> SessionResponse:
    """
    Create a new focus session.
    
    Args:
        session_dto: Session creation data
        
    Returns:
        SessionResponse: Created session information
        
    Raises:
        400: If validation fails
        500: If database operation fails
    """
    try:
        container = await get_service_container()
        session_repo = container.session_repository
        
        session = await session_repo.create(session_dto)
        
        return _build_session_response(session)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Get Session",
    description="Get a specific session by ID"
)
async def get_session(session_id: str) -> SessionResponse:
    """
    Get a session by ID.
    
    Args:
        session_id: Session identifier
        
    Returns:
        SessionResponse: Session information
        
    Raises:
        404: If session not found
        500: If database operation fails
    """
    try:
        container = await get_service_container()
        session_repo = container.session_repository
        
        session = await session_repo.find_by_id(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID {session_id} not found"
            )
        
        return _build_session_response(session)
        
    except RepositoryError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session"
        )


@router.get(
    "/user/{user_id}",
    response_model=List[SessionResponse],
    summary="Get User Sessions",
    description="Get sessions for a specific user with optional date filtering"
)
async def get_user_sessions(
    user_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    start_date: Optional[str] = Query(default=None, description="ISO format date string"),
    end_date: Optional[str] = Query(default=None, description="ISO format date string")
) -> List[SessionResponse]:
    """
    Get sessions for a specific user.
    
    Args:
        user_id: User identifier
        limit: Maximum number of sessions to return
        offset: Number of sessions to skip
        start_date: Optional start date filter (ISO format)
        end_date: Optional end date filter (ISO format)
        
    Returns:
        List[SessionResponse]: List of sessions
    """
    try:
        container = await get_service_container()
        session_repo = container.session_repository
        
        # Parse date strings if provided
        parsed_start_date = None
        parsed_end_date = None
        
        if start_date:
            try:
                parsed_start_date = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                )
        
        if end_date:
            try:
                parsed_end_date = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                )
        
        sessions = await session_repo.find_by_user_id(
            user_id=user_id,
            limit=limit,
            offset=offset,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        
        return [_build_session_response(session) for session in sessions]
        
    except RepositoryError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user sessions"
        )


@router.put(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Update Session",
    description="Update a session's information"
)
async def update_session(session_id: str, updates: UpdateSessionDto) -> SessionResponse:
    """
    Update a session's information.
    
    Args:
        session_id: Session identifier
        updates: Fields to update
        
    Returns:
        SessionResponse: Updated session information
        
    Raises:
        404: If session not found
        400: If validation fails
        500: If database operation fails
    """
    try:
        container = await get_service_container()
        session_repo = container.session_repository
        
        session = await session_repo.update(session_id, updates)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID {session_id} not found"
            )
        
        return _build_session_response(session)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RepositoryError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update session"
        )


@router.post(
    "/{session_id}/complete",
    response_model=SessionResponse,
    summary="Complete Session",
    description="Mark a session as completed and calculate duration"
)
async def complete_session(session_id: str) -> SessionResponse:
    """
    Complete an active session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        SessionResponse: Completed session information
        
    Raises:
        404: If session not found
        500: If database operation fails
    """
    try:
        container = await get_service_container()
        session_repo = container.session_repository
        
        session = await session_repo.complete_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID {session_id} not found"
            )
        
        return _build_session_response(session)
        
    except RepositoryError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete session"
        )


@router.get(
    "/user/{user_id}/active",
    response_model=List[SessionResponse],
    summary="Get Active Sessions",
    description="Get all active sessions for a user"
)
async def get_active_sessions(user_id: str) -> List[SessionResponse]:
    """
    Get active sessions for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        List[SessionResponse]: List of active sessions
    """
    try:
        container = await get_service_container()
        session_repo = container.session_repository
        
        sessions = await session_repo.get_active_sessions(user_id)
        
        return [_build_session_response(session) for session in sessions]
        
    except RepositoryError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve active sessions"
        )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Session",
    description="Delete a session from the system"
)
async def delete_session(session_id: str):
    """
    Delete a session.
    
    Args:
        session_id: Session identifier
        
    Raises:
        404: If session not found
        500: If database operation fails
    """
    try:
        container = await get_service_container()
        session_repo = container.session_repository
        
        deleted = await session_repo.delete(session_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID {session_id} not found"
            )
        
    except RepositoryError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )

