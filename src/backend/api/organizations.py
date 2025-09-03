"""
Organizations API router for Financial Analytics Platform
Handles organization CRUD operations and management
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query

from src.backend.services.auth_service import get_current_user, get_current_active_user
from src.backend.services.organization_service import organization_service
from src.backend.models.database import User, Organization, OrganizationCreate, OrganizationUpdate, OrganizationResponse
from src.common.models.base import BaseResponse

# Create router
router = APIRouter()


@router.post("/", response_model=dict)
async def create_organization(organization_create: OrganizationCreate):
    """
    Create new organization
    
    Anyone can create a new organization
    """
    try:
        # Create organization
        organization = await organization_service.create_organization(organization_create.dict())
        organization_response = organization_service.to_response_model(organization)
        
        return {
            "success": True,
            "message": "Organization created successfully",
            "data": organization_response.dict(),
            "timestamp": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create organization: {str(e)}"
        )


@router.get("/", response_model=dict)
async def get_organizations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search query for name, description, or industry"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    size: Optional[str] = Query(None, description="Filter by organization size")
):
    """
    Get all organizations
    
    Supports pagination, search, and filtering
    """
    try:
        # Get organizations
        if search:
            organizations = await organization_service.search_organizations(search, skip, limit)
        elif industry:
            organizations = await organization_service.get_organizations_by_industry(industry, skip, limit)
        elif size:
            organizations = await organization_service.get_organizations_by_size(size, skip, limit)
        else:
            organizations = await organization_service.get_all_organizations(skip, limit)
        
        # Convert to response models
        organization_responses = [organization_service.to_response_model(org) for org in organizations]
        
        # Get total count
        total_count = await organization_service.get_organization_count()
        
        return {
            "success": True,
            "message": "Organizations retrieved successfully",
            "data": {
                "organizations": [org.dict() for org in organization_responses],
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
            detail=f"Failed to retrieve organizations: {str(e)}"
        )


@router.get("/{organization_id}", response_model=dict)
async def get_organization(
    organization_id: UUID,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get organization by ID
    
    Users can only view organizations they belong to
    """
    try:
        # Get organization
        organization = await organization_service.get_organization_by_id(organization_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Check if user belongs to this organization
        if organization.id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to organization"
            )
        
        organization_response = organization_service.to_response_model(organization)
        
        return {
            "success": True,
            "message": "Organization retrieved successfully",
            "data": organization_response.dict(),
            "timestamp": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve organization: {str(e)}"
        )


@router.put("/{organization_id}", response_model=dict)
async def update_organization(
    organization_id: UUID,
    organization_update: OrganizationUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update organization information
    
    Only admin users can update organization information
    """
    try:
        # Check if current user has admin role
        if current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can update organization information"
            )
        
        # Check if user belongs to this organization
        if organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to organization"
            )
        
        # Update organization
        updated_organization = await organization_service.update_organization(organization_id, organization_update)
        if not updated_organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        organization_response = organization_service.to_response_model(updated_organization)
        
        return {
            "success": True,
            "message": "Organization updated successfully",
            "data": organization_response.dict(),
            "timestamp": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update organization: {str(e)}"
        )


@router.delete("/{organization_id}", response_model=BaseResponse)
async def delete_organization(
    organization_id: UUID,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete organization (soft delete)
    
    Only admin users can delete organizations
    """
    try:
        # Check if current user has admin role
        if current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can delete organizations"
            )
        
        # Check if user belongs to this organization
        if organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to organization"
            )
        
        # Deactivate organization
        await organization_service.deactivate_organization(organization_id)
        
        return BaseResponse(
            success=True,
            message="Organization deactivated successfully",
            timestamp=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete organization: {str(e)}"
        )


@router.post("/{organization_id}/activate", response_model=BaseResponse)
async def activate_organization(
    organization_id: UUID,
    current_user: User = Depends(get_current_active_user)
):
    """
    Activate organization
    
    Only admin users can activate organizations
    """
    try:
        # Check if current user has admin role
        if current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can activate organizations"
            )
        
        # Check if user belongs to this organization
        if organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to organization"
            )
        
        # Activate organization
        await organization_service.activate_organization(organization_id)
        
        return BaseResponse(
            success=True,
            message="Organization activated successfully",
            timestamp=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate organization: {str(e)}"
        )


@router.get("/my", response_model=dict)
async def get_my_organization(current_user: User = Depends(get_current_active_user)):
    """
    Get current user's organization
    
    Returns organization information for authenticated user
    """
    try:
        organization = await organization_service.get_organization_by_id(current_user.organization_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        organization_response = organization_service.to_response_model(organization)
        
        return {
            "success": True,
            "message": "Organization retrieved successfully",
            "data": organization_response.dict(),
            "timestamp": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve organization: {str(e)}"
        )


@router.get("/stats/count", response_model=dict)
async def get_organization_count():
    """
    Get total organization count
    
    Returns total number of active organizations
    """
    try:
        count = await organization_service.get_organization_count()
        
        return {
            "success": True,
            "message": "Organization count retrieved successfully",
            "data": {"count": count},
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve organization count: {str(e)}"
        )


@router.get("/health", response_model=dict)
async def organizations_health():
    """
    Organizations service health check
    """
    return {
        "success": True,
        "message": "Organizations service is healthy",
        "timestamp": datetime.utcnow(),
        "service": "organizations"
    }