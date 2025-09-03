"""
Authentication API router for Financial Analytics Platform
Handles user login, registration, and password management
"""

from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from src.backend.services.auth_service import auth_service, get_current_user
from src.backend.services.user_service import user_service
from src.backend.models.database import User, UserCreate, UserResponse
from src.common.models.base import BaseResponse

# Create router
router = APIRouter()

# Security
security = HTTPBearer()


@router.post("/login", response_model=dict)
async def login(email: str, password: str):
    """
    User login endpoint
    
    Authenticates user with email and password, returns JWT access token
    """
    try:
        result = await auth_service.login(email, password)
        return {
            "success": True,
            "message": "Login successful",
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/register", response_model=dict)
async def register(user_create: UserCreate):
    """
    User registration endpoint
    
    Creates new user account with hashed password
    """
    try:
        user = await auth_service.create_user(user_create)
        return {
            "success": True,
            "message": "User registered successfully",
            "data": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value,
                "organization_id": str(user.organization_id)
            },
            "timestamp": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/logout", response_model=BaseResponse)
async def logout(current_user: User = Depends(get_current_user)):
    """
    User logout endpoint
    
    Note: JWT tokens are stateless, so this endpoint is mainly for client-side cleanup
    """
    return BaseResponse(
        success=True,
        message="Logout successful",
        timestamp=datetime.utcnow()
    )


@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information
    
    Returns authenticated user's profile information
    """
    try:
        user_response = user_service.to_response_model(current_user)
        return {
            "success": True,
            "message": "User information retrieved successfully",
            "data": user_response.dict(),
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user information: {str(e)}"
        )


@router.post("/refresh", response_model=dict)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """
    Refresh access token
    
    Creates new access token for authenticated user
    """
    try:
        # Create new access token
        access_token_expires = datetime.utcnow() + datetime.timedelta(minutes=auth_service.access_token_expire_minutes)
        access_token = auth_service.create_access_token(
            data={"sub": str(current_user.id), "email": current_user.email, "role": current_user.role.value, "org_id": str(current_user.organization_id)},
            expires_delta=access_token_expires
        )
        
        return {
            "success": True,
            "message": "Token refreshed successfully",
            "data": {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": auth_service.access_token_expire_minutes * 60
            },
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/forgot-password", response_model=BaseResponse)
async def forgot_password(email: str):
    """
    Forgot password endpoint
    
    Sends password reset token to user's email
    """
    try:
        # Check if user exists
        user = await user_service.get_user_by_email(email)
        if not user:
            # Don't reveal if user exists or not for security
            return BaseResponse(
                success=True,
                message="If the email exists, a password reset link has been sent",
                timestamp=datetime.utcnow()
            )
        
        # Create password reset token
        reset_token = auth_service.create_password_reset_token(email)
        
        # TODO: Send email with reset token
        # For now, just return success message
        
        return BaseResponse(
            success=True,
            message="Password reset link sent to email",
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}"
        )


@router.post("/reset-password", response_model=BaseResponse)
async def reset_password(token: str, new_password: str):
    """
    Reset password endpoint
    
    Resets user password using reset token
    """
    try:
        success = await auth_service.reset_password(token, new_password)
        if success:
            return BaseResponse(
                success=True,
                message="Password reset successfully",
                timestamp=datetime.utcnow()
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}"
        )


@router.post("/change-password", response_model=BaseResponse)
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user)
):
    """
    Change password endpoint
    
    Changes user password after verifying current password
    """
    try:
        # Verify current password
        if not auth_service.verify_password(current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        hashed_password = auth_service.get_password_hash(new_password)
        
        # Update password
        await user_service.update_user_password(current_user.id, hashed_password)
        
        return BaseResponse(
            success=True,
            message="Password changed successfully",
            timestamp=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change failed: {str(e)}"
        )


@router.get("/health", response_model=dict)
async def auth_health():
    """
    Authentication service health check
    """
    return {
        "success": True,
        "message": "Authentication service is healthy",
        "timestamp": datetime.utcnow(),
        "service": "auth"
    }