"""
Users API router for Financial Analytics Platform
Handles user CRUD operations and management
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query

from src.backend.services.auth_service import get_current_user, get_current_active_user
from src.backend.services.user_service import user_service
from src.backend.models.database import User, UserCreate, UserUpdate, UserResponse
from src.common.models.base import BaseResponse, PaginatedResponse

# Create router
router = APIRouter()


@router.post("/", response_model=dict)
async def create_user(
    user_create: UserCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create new user
    
    Only admin users can create new users
    """
    try:
        # Check if current user has admin role
        if current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can create new users"
            )
        
        # Create user
        user = await user_service.create_user(user_create.dict())
        user_response = user_service.to_response_model(user)
        
        return {
            "success": True,
            "message": "User created successfully",
            "data": user_response.dict(),
            "timestamp": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/", response_model=dict)
async def get_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search query for name or email"),
    role: Optional[str] = Query(None, description="Filter by user role"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get users in current user's organization
    
    Supports pagination, search, and role filtering
    """
    try:
        # Get users by organization
        if search:
            users = await user_service.search_users(
                current_user.organization_id, search, skip, limit
            )
        elif role:
            users = await user_service.get_users_by_role(
                current_user.organization_id, role, skip, limit
            )
        else:
            users = await user_service.get_users_by_organization(
                current_user.organization_id, skip, limit
            )
        
        # Convert to response models
        user_responses = [user_service.to_response_model(user) for user in users]
        
        # Get total count
        total_count = await user_service.get_user_count_by_organization(current_user.organization_id)
        
        return {
            "success": True,
            "message": "Users retrieved successfully",
            "data": {
                "users": [user.dict() for user in user_responses],
                "pagination": {
                    "skip": skip,
                    "limit": limit,
                    "total": total_count,
                    "has_more": skip + limit < total_count
                }
            },
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}"
        )


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user by ID
    
    Users can only view users in their own organization
    """
    try:
        # Get user
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user is in same organization
        if user.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to user in different organization"
            )
        
        user_response = user_service.to_response_model(user)
        
        return {
            "success": True,
            "message": "User retrieved successfully",
            "data": user_response.dict(),
            "timestamp": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user: {str(e)}"
        )


@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update user information
    
    Users can update their own profile, admins can update any user in their organization
    """
    try:
        # Get user to update
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user is in same organization
        if user.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to user in different organization"
            )
        
        # Check permissions
        if current_user.id != user_id and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can update other users"
            )
        
        # Update user
        updated_user = await user_service.update_user(user_id, user_update)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_response = user_service.to_response_model(updated_user)
        
        return {
            "success": True,
            "message": "User updated successfully",
            "data": user_response.dict(),
            "timestamp": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/{user_id}", response_model=BaseResponse)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete user (soft delete)
    
    Only admin users can delete users
    """
    try:
        # Check if current user has admin role
        if current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can delete users"
            )
        
        # Get user to delete
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user is in same organization
        if user.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to user in different organization"
            )
        
        # Prevent self-deletion
        if current_user.id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        # Deactivate user
        await user_service.deactivate_user(user_id)
        
        return BaseResponse(
            success=True,
            message="User deactivated successfully",
            timestamp=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.post("/{user_id}/activate", response_model=BaseResponse)
async def activate_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user)
):
    """
    Activate user
    
    Only admin users can activate users
    """
    try:
        # Check if current user has admin role
        if current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can activate users"
            )
        
        # Get user to activate
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user is in same organization
        if user.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to user in different organization"
            )
        
        # Activate user
        await user_service.activate_user(user_id)
        
        return BaseResponse(
            success=True,
            message="User activated successfully",
            timestamp=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate user: {str(e)}"
        )


@router.get("/profile", response_model=dict)
async def get_user_profile(current_user: User = Depends(get_current_active_user)):
    """
    Get current user's profile
    
    Returns authenticated user's complete profile information
    """
    try:
        user_response = user_service.to_response_model(current_user)
        
        return {
            "success": True,
            "message": "Profile retrieved successfully",
            "data": user_response.dict(),
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve profile: {str(e)}"
        )


@router.put("/profile", response_model=dict)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update current user's profile
    
    Users can update their own profile information
    """
    try:
        # Update user
        updated_user = await user_service.update_user(current_user.id, user_update)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_response = user_service.to_response_model(updated_user)
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "data": user_response.dict(),
            "timestamp": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.get("/stats/count", response_model=dict)
async def get_user_count(current_user: User = Depends(get_current_active_user)):
    """
    Get user count in current organization
    
    Returns total number of active users
    """
    try:
        count = await user_service.get_user_count_by_organization(current_user.organization_id)
        
        return {
            "success": True,
            "message": "User count retrieved successfully",
            "data": {"count": count},
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user count: {str(e)}"
        )


@router.get("/health", response_model=dict)
async def users_health():
    """
    Users service health check
    """
    return {
        "success": True,
        "message": "Users service is healthy",
        "timestamp": datetime.utcnow(),
        "service": "users"
    }