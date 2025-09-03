"""
Organization service for Financial Analytics Platform
Handles organization CRUD operations and management
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlmodel import select, Session, update
from fastapi import HTTPException, status

from src.backend.models.database import Organization, OrganizationCreate, OrganizationUpdate, OrganizationResponse
from src.backend.database import get_session


class OrganizationService:
    """Service for organization management operations"""
    
    def __init__(self):
        pass
    
    async def create_organization(self, organization_data: Dict[str, Any]) -> Organization:
        """Create a new organization"""
        async with get_session() as session:
            # Check if organization with slug already exists
            existing_org = await self.get_organization_by_slug(organization_data["slug"])
            if existing_org:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Organization with this slug already exists"
                )
            
            organization = Organization(**organization_data)
            session.add(organization)
            await session.commit()
            await session.refresh(organization)
            return organization
    
    async def get_organization_by_id(self, organization_id: UUID) -> Optional[Organization]:
        """Get organization by ID"""
        async with get_session() as session:
            statement = select(Organization).where(Organization.id == organization_id, Organization.deleted_at.is_(None))
            result = await session.exec(statement)
            return result.first()
    
    async def get_organization_by_slug(self, slug: str) -> Optional[Organization]:
        """Get organization by slug"""
        async with get_session() as session:
            statement = select(Organization).where(Organization.slug == slug, Organization.deleted_at.is_(None))
            result = await session.exec(statement)
            return result.first()
    
    async def get_all_organizations(self, skip: int = 0, limit: int = 100) -> List[Organization]:
        """Get all organizations with pagination"""
        async with get_session() as session:
            statement = (
                select(Organization)
                .where(Organization.deleted_at.is_(None))
                .offset(skip)
                .limit(limit)
            )
            result = await session.exec(statement)
            return result.all()
    
    async def update_organization(self, organization_id: UUID, organization_update: OrganizationUpdate) -> Optional[Organization]:
        """Update organization information"""
        async with get_session() as session:
            # Get current organization
            statement = select(Organization).where(Organization.id == organization_id, Organization.deleted_at.is_(None))
            result = await session.exec(statement)
            organization = result.first()
            
            if not organization:
                return None
            
            # Check slug uniqueness if updating
            if organization_update.slug and organization_update.slug != organization.slug:
                existing_org = await self.get_organization_by_slug(organization_update.slug)
                if existing_org:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Organization with this slug already exists"
                    )
            
            # Update fields
            update_data = organization_update.dict(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow()
            
            statement = (
                update(Organization)
                .where(Organization.id == organization_id)
                .values(**update_data)
            )
            await session.exec(statement)
            await session.commit()
            
            # Return updated organization
            return await self.get_organization_by_id(organization_id)
    
    async def deactivate_organization(self, organization_id: UUID) -> bool:
        """Deactivate organization (soft delete)"""
        async with get_session() as session:
            statement = (
                update(Organization)
                .where(Organization.id == organization_id)
                .values(is_active=False, deleted_at=datetime.utcnow(), updated_at=datetime.utcnow())
            )
            await session.exec(statement)
            await session.commit()
            return True
    
    async def activate_organization(self, organization_id: UUID) -> bool:
        """Activate organization"""
        async with get_session() as session:
            statement = (
                update(Organization)
                .where(Organization.id == organization_id)
                .values(is_active=True, deleted_at=None, updated_at=datetime.utcnow())
            )
            await session.exec(statement)
            await session.commit()
            return True
    
    async def delete_organization(self, organization_id: UUID) -> bool:
        """Hard delete organization"""
        async with get_session() as session:
            statement = select(Organization).where(Organization.id == organization_id)
            result = await session.exec(statement)
            organization = result.first()
            
            if not organization:
                return False
            
            await session.delete(organization)
            await session.commit()
            return True
    
    async def get_organization_count(self) -> int:
        """Get total organization count"""
        async with get_session() as session:
            statement = select(Organization).where(Organization.deleted_at.is_(None))
            result = await session.exec(statement)
            return len(result.all())
    
    async def search_organizations(self, query: str, skip: int = 0, limit: int = 100) -> List[Organization]:
        """Search organizations by name, description, or industry"""
        async with get_session() as session:
            statement = (
                select(Organization)
                .where(
                    Organization.deleted_at.is_(None),
                    (Organization.name.contains(query) | 
                     Organization.description.contains(query) | 
                     Organization.industry.contains(query))
                )
                .offset(skip)
                .limit(limit)
            )
            result = await session.exec(statement)
            return result.all()
    
    async def get_organizations_by_industry(self, industry: str, skip: int = 0, limit: int = 100) -> List[Organization]:
        """Get organizations by industry"""
        async with get_session() as session:
            statement = (
                select(Organization)
                .where(
                    Organization.industry == industry,
                    Organization.deleted_at.is_(None)
                )
                .offset(skip)
                .limit(limit)
            )
            result = await session.exec(statement)
            return result.all()
    
    async def get_organizations_by_size(self, size: str, skip: int = 0, limit: int = 100) -> List[Organization]:
        """Get organizations by size"""
        async with get_session() as session:
            statement = (
                select(Organization)
                .where(
                    Organization.size == size,
                    Organization.deleted_at.is_(None)
                )
                .offset(skip)
                .limit(limit)
            )
            result = await session.exec(statement)
            return result.all()
    
    def to_response_model(self, organization: Organization) -> OrganizationResponse:
        """Convert Organization model to OrganizationResponse"""
        return OrganizationResponse(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
            description=organization.description,
            website=organization.website,
            industry=organization.industry,
            size=organization.size,
            is_active=organization.is_active,
            metadata=organization.metadata,
            created_at=organization.created_at,
            updated_at=organization.updated_at
        )


# Global organization service instance
organization_service = OrganizationService()


# Export functions and classes
__all__ = [
    "OrganizationService",
    "organization_service"
]