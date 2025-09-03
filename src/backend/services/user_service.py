"""
User service for Financial Analytics Platform
Handles user CRUD operations and management
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlmodel import select, Session, update
from fastapi import HTTPException, status

from src.backend.models.database import User, UserCreate, UserUpdate, UserResponse
from src.backend.database import get_session


class UserService:
    """Service for user management operations"""
    
    def __init__(self):
        pass
    
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create a new user"""
        async with get_session() as session:
            user = User(**user_data)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        async with get_session() as session:
            statement = select(User).where(User.id == user_id, User.deleted_at.is_(None))
            result = await session.exec(statement)
            return result.first()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        async with get_session() as session:
            statement = select(User).where(User.email == email, User.deleted_at.is_(None))
            result = await session.exec(statement)
            return result.first()
    
    async def get_users_by_organization(self, organization_id: UUID, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users by organization with pagination"""
        async with get_session() as session:
            statement = (
                select(User)
                .where(User.organization_id == organization_id, User.deleted_at.is_(None))
                .offset(skip)
                .limit(limit)
            )
            result = await session.exec(statement)
            return result.all()
    
    async def update_user(self, user_id: UUID, user_update: UserUpdate) -> Optional[User]:
        """Update user information"""
        async with get_session() as session:
            # Get current user
            statement = select(User).where(User.id == user_id, User.deleted_at.is_(None))
            result = await session.exec(statement)
            user = result.first()
            
            if not user:
                return None
            
            # Update fields
            update_data = user_update.dict(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow()
            
            statement = (
                update(User)
                .where(User.id == user_id)
                .values(**update_data)
            )
            await session.exec(statement)
            await session.commit()
            
            # Return updated user
            return await self.get_user_by_id(user_id)
    
    async def update_user_password(self, user_id: UUID, hashed_password: str) -> bool:
        """Update user password"""
        async with get_session() as session:
            statement = (
                update(User)
                .where(User.id == user_id)
                .values(hashed_password=hashed_password, updated_at=datetime.utcnow())
            )
            await session.exec(statement)
            await session.commit()
            return True
    
    async def update_user_last_login(self, user_id: UUID) -> bool:
        """Update user last login timestamp"""
        async with get_session() as session:
            statement = (
                update(User)
                .where(User.id == user_id)
                .values(last_login=datetime.utcnow(), updated_at=datetime.utcnow())
            )
            await session.exec(statement)
            await session.commit()
            return True
    
    async def deactivate_user(self, user_id: UUID) -> bool:
        """Deactivate user (soft delete)"""
        async with get_session() as session:
            statement = (
                update(User)
                .where(User.id == user_id)
                .values(is_active=False, deleted_at=datetime.utcnow(), updated_at=datetime.utcnow())
            )
            await session.exec(statement)
            await session.commit()
            return True
    
    async def activate_user(self, user_id: UUID) -> bool:
        """Activate user"""
        async with get_session() as session:
            statement = (
                update(User)
                .where(User.id == user_id)
                .values(is_active=True, deleted_at=None, updated_at=datetime.utcnow())
            )
            await session.exec(statement)
            await session.commit()
            return True
    
    async def delete_user(self, user_id: UUID) -> bool:
        """Hard delete user"""
        async with get_session() as session:
            statement = select(User).where(User.id == user_id)
            result = await session.exec(statement)
            user = result.first()
            
            if not user:
                return False
            
            await session.delete(user)
            await session.commit()
            return True
    
    async def get_user_count_by_organization(self, organization_id: UUID) -> int:
        """Get user count by organization"""
        async with get_session() as session:
            statement = select(User).where(User.organization_id == organization_id, User.deleted_at.is_(None))
            result = await session.exec(statement)
            return len(result.all())
    
    async def search_users(self, organization_id: UUID, query: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Search users by name or email"""
        async with get_session() as session:
            statement = (
                select(User)
                .where(
                    User.organization_id == organization_id,
                    User.deleted_at.is_(None),
                    (User.first_name.contains(query) | User.last_name.contains(query) | User.email.contains(query))
                )
                .offset(skip)
                .limit(limit)
            )
            result = await session.exec(statement)
            return result.all()
    
    async def get_users_by_role(self, organization_id: UUID, role: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users by role within organization"""
        async with get_session() as session:
            statement = (
                select(User)
                .where(
                    User.organization_id == organization_id,
                    User.role == role,
                    User.deleted_at.is_(None)
                )
                .offset(skip)
                .limit(limit)
            )
            result = await session.exec(statement)
            return result.all()
    
    def to_response_model(self, user: User) -> UserResponse:
        """Convert User model to UserResponse"""
        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            phone=user.phone,
            timezone=user.timezone,
            preferences=user.preferences,
            metadata=user.metadata,
            organization_id=user.organization_id,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at
        )


# Global user service instance
user_service = UserService()


# Export functions and classes
__all__ = [
    "UserService",
    "user_service"
]