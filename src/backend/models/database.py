"""
Database models for Financial Analytics Platform
SQLModel-based models with multitenancy and RBAC support
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr

from src.common.models.enums import Role, Permission


class OrganizationBase(SQLModel):
    """Base organization model"""
    
    name: str = Field(..., max_length=255, description="Organization name")
    slug: str = Field(..., max_length=100, unique=True, description="Organization slug")
    description: Optional[str] = Field(None, max_length=1000, description="Organization description")
    website: Optional[str] = Field(None, max_length=255, description="Organization website")
    industry: Optional[str] = Field(None, max_length=100, description="Industry sector")
    size: Optional[str] = Field(None, max_length=50, description="Organization size")
    is_active: bool = Field(default=True, description="Organization active status")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")


class Organization(OrganizationBase, table=True):
    """Organization model with multitenancy support"""
    
    __tablename__ = "organizations"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True, description="Organization ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Soft delete timestamp")
    
    # Relationships
    users: List["User"] = Relationship(back_populates="organization")
    accounts: List["Account"] = Relationship(back_populates="organization")
    transactions: List["Transaction"] = Relationship(back_populates="organization")
    budgets: List["Budget"] = Relationship(back_populates="organization")
    categories: List["Category"] = Relationship(back_populates="organization")


class UserBase(SQLModel):
    """Base user model"""
    
    email: EmailStr = Field(..., unique=True, description="User email address")
    first_name: str = Field(..., max_length=100, description="User first name")
    last_name: str = Field(..., max_length=100, description="User last name")
    role: Role = Field(default=Role.VIEWER, description="User role")
    is_active: bool = Field(default=True, description="User active status")
    is_verified: bool = Field(default=False, description="Email verification status")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    timezone: Optional[str] = Field(default="UTC", max_length=50, description="User timezone")
    preferences: Optional[dict] = Field(default_factory=dict, description="User preferences")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")


class User(UserBase, table=True):
    """User model with RBAC support"""
    
    __tablename__ = "users"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True, description="User ID")
    organization_id: UUID = Field(..., foreign_key="organizations.id", description="Organization ID")
    hashed_password: str = Field(..., description="Hashed password")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Soft delete timestamp")
    
    # Relationships
    organization: Organization = Relationship(back_populates="users")
    user_permissions: List["UserPermission"] = Relationship(back_populates="user")
    accounts: List["Account"] = Relationship(back_populates="owner")
    transactions: List["Transaction"] = Relationship(back_populates="user")
    budgets: List["Budget"] = Relationship(back_populates="owner")
    categories: List["Category"] = Relationship(back_populates="owner")


class UserPermission(SQLModel, table=True):
    """User-specific permissions for granular RBAC"""
    
    __tablename__ = "user_permissions"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True, description="Permission ID")
    user_id: UUID = Field(..., foreign_key="users.id", description="User ID")
    permission: Permission = Field(..., description="Permission type")
    resource_type: str = Field(..., max_length=100, description="Resource type")
    resource_id: Optional[UUID] = Field(None, description="Specific resource ID")
    granted_at: datetime = Field(default_factory=datetime.utcnow, description="Permission granted timestamp")
    granted_by: UUID = Field(..., foreign_key="users.id", description="Granted by user ID")
    expires_at: Optional[datetime] = Field(None, description="Permission expiration")
    
    # Relationships
    user: User = Relationship(back_populates="user_permissions")


class AccountBase(SQLModel):
    """Base account model"""
    
    name: str = Field(..., max_length=255, description="Account name")
    account_type: str = Field(..., max_length=100, description="Account type")
    institution: str = Field(..., max_length=255, description="Financial institution")
    account_number: Optional[str] = Field(None, max_length=100, description="Account number")
    routing_number: Optional[str] = Field(None, max_length=100, description="Routing number")
    currency: str = Field(default="USD", max_length=3, description="Account currency")
    balance: float = Field(default=0.0, description="Current balance")
    is_active: bool = Field(default=True, description="Account active status")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")


class Account(AccountBase, table=True):
    """Account model with multitenancy"""
    
    __tablename__ = "accounts"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True, description="Account ID")
    organization_id: UUID = Field(..., foreign_key="organizations.id", description="Organization ID")
    owner_id: UUID = Field(..., foreign_key="users.id", description="Account owner ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Soft delete timestamp")
    
    # Relationships
    organization: Organization = Relationship(back_populates="accounts")
    owner: User = Relationship(back_populates="accounts")
    transactions: List["Transaction"] = Relationship(back_populates="account")


class CategoryBase(SQLModel):
    """Base category model"""
    
    name: str = Field(..., max_length=255, description="Category name")
    description: Optional[str] = Field(None, max_length=1000, description="Category description")
    color: Optional[str] = Field(None, max_length=7, description="Category color (hex)")
    icon: Optional[str] = Field(None, max_length=100, description="Category icon")
    is_active: bool = Field(default=True, description="Category active status")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")


class Category(CategoryBase, table=True):
    """Category model with multitenancy"""
    
    __tablename__ = "categories"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True, description="Category ID")
    organization_id: UUID = Field(..., foreign_key="organizations.id", description="Organization ID")
    owner_id: UUID = Field(..., foreign_key="users.id", description="Category owner ID")
    parent_id: Optional[UUID] = Field(None, foreign_key="categories.id", description="Parent category ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Soft delete timestamp")
    
    # Relationships
    organization: Organization = Relationship(back_populates="categories")
    owner: User = Relationship(back_populates="categories")
    parent: Optional["Category"] = Relationship(back_populates="children", remote_side=[id])
    children: List["Category"] = Relationship(back_populates="parent")
    transactions: List["Transaction"] = Relationship(back_populates="category")


class TransactionBase(SQLModel):
    """Base transaction model"""
    
    amount: float = Field(..., description="Transaction amount")
    description: str = Field(..., max_length=1000, description="Transaction description")
    transaction_type: str = Field(..., max_length=100, description="Transaction type")
    date: datetime = Field(..., description="Transaction date")
    reference: Optional[str] = Field(None, max_length=255, description="Reference number")
    notes: Optional[str] = Field(None, max_length=2000, description="Additional notes")
    is_recurring: bool = Field(default=False, description="Recurring transaction flag")
    is_active: bool = Field(default=True, description="Transaction active status")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")


class Transaction(TransactionBase, table=True):
    """Transaction model with multitenancy"""
    
    __tablename__ = "transactions"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True, description="Transaction ID")
    organization_id: UUID = Field(..., foreign_key="organizations.id", description="Organization ID")
    user_id: UUID = Field(..., foreign_key="users.id", description="User ID")
    account_id: UUID = Field(..., foreign_key="accounts.id", description="Account ID")
    category_id: Optional[UUID] = Field(None, foreign_key="categories.id", description="Category ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Soft delete timestamp")
    
    # Relationships
    organization: Organization = Relationship(back_populates="transactions")
    user: User = Relationship(back_populates="transactions")
    account: Account = Relationship(back_populates="transactions")
    category: Optional[Category] = Relationship(back_populates="transactions")


class BudgetBase(SQLModel):
    """Base budget model"""
    
    name: str = Field(..., max_length=255, description="Budget name")
    description: Optional[str] = Field(None, max_length=1000, description="Budget description")
    amount: float = Field(..., description="Budget amount")
    period: str = Field(..., max_length=50, description="Budget period (monthly, yearly)")
    start_date: datetime = Field(..., description="Budget start date")
    end_date: datetime = Field(..., description="Budget end date")
    is_active: bool = Field(default=True, description="Budget active status")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")


class Budget(BudgetBase, table=True):
    """Budget model with multitenancy"""
    
    __tablename__ = "budgets"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True, description="Budget ID")
    organization_id: UUID = Field(..., foreign_key="organizations.id", description="Organization ID")
    owner_id: UUID = Field(..., foreign_key="users.id", description="Budget owner ID")
    category_id: Optional[UUID] = Field(None, foreign_key="categories.id", description="Category ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Soft delete timestamp")
    
    # Relationships
    organization: Organization = Relationship(back_populates="budgets")
    owner: User = Relationship(back_populates="budgets")
    category: Optional[Category] = Relationship(back_populates="budgets")


class AuditLog(SQLModel, table=True):
    """Audit log for security and compliance"""
    
    __tablename__ = "audit_logs"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True, description="Audit log ID")
    organization_id: UUID = Field(..., foreign_key="organizations.id", description="Organization ID")
    user_id: Optional[UUID] = Field(None, foreign_key="users.id", description="User ID")
    action: str = Field(..., max_length=100, description="Action performed")
    resource_type: str = Field(..., max_length=100, description="Resource type")
    resource_id: Optional[UUID] = Field(None, description="Resource ID")
    details: Optional[dict] = Field(default_factory=dict, description="Action details")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP address")
    user_agent: Optional[str] = Field(None, max_length=500, description="User agent")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Action timestamp")
    success: bool = Field(default=True, description="Action success status")


# Pydantic models for API requests/responses
class OrganizationCreate(OrganizationBase):
    """Organization creation request"""
    pass


class OrganizationUpdate(SQLModel):
    """Organization update request"""
    name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[dict] = None


class OrganizationResponse(OrganizationBase):
    """Organization response"""
    id: UUID
    created_at: datetime
    updated_at: datetime


class UserCreate(UserBase):
    """User creation request"""
    password: str = Field(..., min_length=8, description="User password")
    organization_id: UUID = Field(..., description="Organization ID")


class UserUpdate(SQLModel):
    """User update request"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[Role] = None
    is_active: Optional[bool] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    preferences: Optional[dict] = None
    metadata: Optional[dict] = None


class UserResponse(UserBase):
    """User response"""
    id: UUID
    organization_id: UUID
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class AccountCreate(AccountBase):
    """Account creation request"""
    organization_id: UUID = Field(..., description="Organization ID")
    owner_id: UUID = Field(..., description="Account owner ID")


class AccountUpdate(SQLModel):
    """Account update request"""
    name: Optional[str] = None
    account_type: Optional[str] = None
    institution: Optional[str] = None
    account_number: Optional[str] = None
    routing_number: Optional[str] = None
    currency: Optional[str] = None
    balance: Optional[float] = None
    is_active: Optional[bool] = None
    metadata: Optional[dict] = None


class AccountResponse(AccountBase):
    """Account response"""
    id: UUID
    organization_id: UUID
    owner_id: UUID
    created_at: datetime
    updated_at: datetime


class CategoryCreate(CategoryBase):
    """Category creation request"""
    organization_id: UUID = Field(..., description="Organization ID")
    owner_id: UUID = Field(..., description="Category owner ID")
    parent_id: Optional[UUID] = None


class CategoryUpdate(SQLModel):
    """Category update request"""
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    parent_id: Optional[UUID] = None
    metadata: Optional[dict] = None


class CategoryResponse(CategoryBase):
    """Category response"""
    id: UUID
    organization_id: UUID
    owner_id: UUID
    parent_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime


class TransactionCreate(TransactionBase):
    """Transaction creation request"""
    organization_id: UUID = Field(..., description="Organization ID")
    user_id: UUID = Field(..., description="User ID")
    account_id: UUID = Field(..., description="Account ID")
    category_id: Optional[UUID] = None


class TransactionUpdate(SQLModel):
    """Transaction update request"""
    amount: Optional[float] = None
    description: Optional[str] = None
    transaction_type: Optional[str] = None
    date: Optional[datetime] = None
    reference: Optional[str] = None
    notes: Optional[str] = None
    is_recurring: Optional[bool] = None
    category_id: Optional[UUID] = None
    metadata: Optional[dict] = None


class TransactionResponse(TransactionBase):
    """Transaction response"""
    id: UUID
    organization_id: UUID
    user_id: UUID
    account_id: UUID
    category_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime


class BudgetCreate(BudgetBase):
    """Budget creation request"""
    organization_id: UUID = Field(..., description="Organization ID")
    owner_id: UUID = Field(..., description="Budget owner ID")
    category_id: Optional[UUID] = None


class BudgetUpdate(SQLModel):
    """Budget update request"""
    name: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    period: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    category_id: Optional[UUID] = None
    metadata: Optional[dict] = None


class BudgetResponse(BudgetBase):
    """Budget response"""
    id: UUID
    organization_id: UUID
    owner_id: UUID
    category_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime


# Export all models
__all__ = [
    # Database models
    "Organization", "User", "UserPermission", "Account", "Category", "Transaction", "Budget", "AuditLog",
    # Request models
    "OrganizationCreate", "UserCreate", "AccountCreate", "CategoryCreate", "TransactionCreate", "BudgetCreate",
    # Update models
    "OrganizationUpdate", "UserUpdate", "AccountUpdate", "CategoryUpdate", "TransactionUpdate", "BudgetUpdate",
    # Response models
    "OrganizationResponse", "UserResponse", "AccountResponse", "CategoryResponse", "TransactionResponse", "BudgetResponse"
]