"""
Authentication service for Financial Analytics Platform
Handles JWT tokens, password hashing, and user authentication
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from uuid import UUID
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.common.config import get_settings
from src.backend.models.database import User, UserCreate
from src.backend.services.user_service import UserService

# Password hashing context
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# JWT token security
security = HTTPBearer()

# JWT settings
settings = get_settings()


class AuthService:
    """Authentication service for user management and JWT handling"""
    
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self.user_service = UserService()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = await self.user_service.get_user_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    async def create_user(self, user_create: UserCreate) -> User:
        """Create new user with hashed password"""
        # Check if user already exists
        existing_user = await self.user_service.get_user_by_email(user_create.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Hash password
        hashed_password = self.get_password_hash(user_create.password)
        
        # Create user data
        user_data = user_create.dict()
        user_data.pop("password")
        user_data["hashed_password"] = hashed_password
        
        # Create user
        user = await self.user_service.create_user(user_data)
        return user
    
    async def login(self, email: str, password: str) -> dict:
        """Authenticate user and return access token"""
        user = await self.authenticate_user(email, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # Update last login
        await self.user_service.update_user_last_login(user.id)
        
        # Create access token
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value, "org_id": str(user.organization_id)},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value,
                "organization_id": str(user.organization_id)
            }
        }
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
        """Get current authenticated user from JWT token"""
        token = credentials.credentials
        payload = self.verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = await self.user_service.get_user_by_id(UUID(user_id))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        return user
    
    async def get_current_active_user(self, current_user: User = Depends(get_current_user)) -> User:
        """Get current active user"""
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        return current_user
    
    def create_password_reset_token(self, email: str) -> str:
        """Create password reset token"""
        expire = datetime.utcnow() + timedelta(hours=24)
        to_encode = {"exp": expire, "sub": email, "type": "password_reset"}
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_password_reset_token(self, token: str) -> Optional[str]:
        """Verify password reset token and return email"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            email: str = payload.get("sub")
            token_type: str = payload.get("type")
            if email is None or token_type != "password_reset":
                return None
            return email
        except jwt.JWTError:
            return None
    
    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset user password using reset token"""
        email = self.verify_password_reset_token(token)
        if not email:
            return False
        
        user = await self.user_service.get_user_by_email(email)
        if not user:
            return False
        
        # Hash new password
        hashed_password = self.get_password_hash(new_password)
        
        # Update user password
        await self.user_service.update_user_password(user.id, hashed_password)
        return True


# Global auth service instance
auth_service = AuthService()


# Dependency functions for FastAPI
async def get_current_user() -> User:
    """Get current authenticated user"""
    return await auth_service.get_current_user()


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    return await auth_service.get_current_active_user(current_user)


def get_auth_service() -> AuthService:
    """Get authentication service instance"""
    return auth_service


# Export functions and classes
__all__ = [
    "AuthService",
    "auth_service",
    "get_current_user",
    "get_current_active_user",
    "get_auth_service",
    "verify_password",
    "get_password_hash"
]