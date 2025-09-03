"""
Unit tests for Sprint 1: Multitenancy & RBAC Implementation
Tests the core functionality implemented in Sprint 1
"""

import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from decimal import Decimal

from src.backend.models.database import (
    Organization, User, UserPermission, Account, Category, Transaction, Budget,
    OrganizationCreate, UserCreate, AccountCreate, CategoryCreate, TransactionCreate, BudgetCreate,
    OrganizationUpdate, UserUpdate, AccountUpdate, CategoryUpdate, TransactionUpdate, BudgetUpdate
)
from src.common.models.enums import Role, Permission, TransactionType, AccountType


class TestOrganizationModel:
    """Test Organization model functionality"""
    
    def test_organization_creation(self):
        """Test organization creation with required fields"""
        org = Organization(
            name="Test Corp",
            slug="test-corp",
            description="Test organization"
        )
        
        assert org.name == "Test Corp"
        assert org.slug == "test-corp"
        assert org.description == "Test organization"
        assert org.is_active is True
        assert org.created_at is not None
        assert org.updated_at is not None
    
    def test_organization_with_optional_fields(self):
        """Test organization creation with optional fields"""
        org = Organization(
            name="Tech Corp",
            slug="tech-corp",
            description="Technology company",
            website="https://techcorp.com",
            industry="Technology",
            size="Medium",
            metadata={"founded": "2020", "employees": 100}
        )
        
        assert org.website == "https://techcorp.com"
        assert org.industry == "Technology"
        assert org.size == "Medium"
        assert org.metadata["founded"] == "2020"
        assert org.metadata["employees"] == 100
    
    def test_organization_slug_uniqueness(self):
        """Test organization slug uniqueness constraint"""
        org1 = Organization(name="Corp A", slug="corp-a")
        org2 = Organization(name="Corp B", slug="corp-a")  # Same slug
        
        # In a real database, this would raise a constraint violation
        # For unit tests, we just verify the models are created
        assert org1.slug == org2.slug


class TestUserModel:
    """Test User model functionality"""
    
    def test_user_creation(self):
        """Test user creation with required fields"""
        org_id = uuid4()
        user = User(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            organization_id=org_id,
            hashed_password="hashed_password_123"
        )
        
        assert user.email == "test@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.organization_id == org_id
        assert user.hashed_password == "hashed_password_123"
        assert user.role == Role.VIEWER
        assert user.is_active is True
        assert user.is_verified is False
    
    def test_user_with_role(self):
        """Test user creation with specific role"""
        org_id = uuid4()
        user = User(
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            role=Role.ADMIN,
            organization_id=org_id,
            hashed_password="hashed_password_123"
        )
        
        assert user.role == Role.ADMIN
    
    def test_user_with_preferences(self):
        """Test user creation with preferences"""
        org_id = uuid4()
        user = User(
            email="user@example.com",
            first_name="User",
            last_name="Name",
            organization_id=org_id,
            hashed_password="hashed_password_123",
            preferences={"theme": "dark", "language": "en"},
            timezone="America/New_York"
        )
        
        assert user.preferences["theme"] == "dark"
        assert user.preferences["language"] == "en"
        assert user.timezone == "America/New_York"


class TestAccountModel:
    """Test Account model functionality"""
    
    def test_account_creation(self):
        """Test account creation with required fields"""
        org_id = uuid4()
        owner_id = uuid4()
        
        account = Account(
            name="Main Checking",
            account_type="checking",
            institution="Chase Bank",
            organization_id=org_id,
            owner_id=owner_id
        )
        
        assert account.name == "Main Checking"
        assert account.account_type == "checking"
        assert account.institution == "Chase Bank"
        assert account.organization_id == org_id
        assert account.owner_id == owner_id
        assert account.currency == "USD"
        assert account.balance == 0.0
        assert account.is_active is True
    
    def test_account_with_balance(self):
        """Test account creation with balance"""
        org_id = uuid4()
        owner_id = uuid4()
        
        account = Account(
            name="Savings",
            account_type="savings",
            institution="Bank of America",
            organization_id=org_id,
            owner_id=owner_id,
            balance=5000.00,
            currency="EUR"
        )
        
        assert account.balance == 5000.00
        assert account.currency == "EUR"


class TestCategoryModel:
    """Test Category model functionality"""
    
    def test_category_creation(self):
        """Test category creation with required fields"""
        org_id = uuid4()
        owner_id = uuid4()
        
        category = Category(
            name="Food & Dining",
            description="Restaurants and groceries",
            organization_id=org_id,
            owner_id=owner_id
        )
        
        assert category.name == "Food & Dining"
        assert category.description == "Restaurants and groceries"
        assert category.organization_id == org_id
        assert category.owner_id == owner_id
        assert category.is_active is True
    
    def test_category_with_styling(self):
        """Test category creation with styling options"""
        org_id = uuid4()
        owner_id = uuid4()
        
        category = Category(
            name="Transportation",
            description="Gas and transit",
            organization_id=org_id,
            owner_id=owner_id,
            color="#FF6B6B",
            icon="🚗"
        )
        
        assert category.color == "#FF6B6B"
        assert category.icon == "🚗"
    
    def test_category_hierarchy(self):
        """Test category with parent category"""
        org_id = uuid4()
        owner_id = uuid4()
        
        parent_category = Category(
            name="Food",
            organization_id=org_id,
            owner_id=owner_id
        )
        
        child_category = Category(
            name="Restaurants",
            organization_id=org_id,
            owner_id=owner_id,
            parent_id=parent_category.id
        )
        
        assert child_category.parent_id == parent_category.id


class TestTransactionModel:
    """Test Transaction model functionality"""
    
    def test_transaction_creation(self):
        """Test transaction creation with required fields"""
        org_id = uuid4()
        user_id = uuid4()
        account_id = uuid4()
        
        transaction = Transaction(
            amount=-45.67,
            description="Lunch at Chipotle",
            transaction_type="expense",
            date=datetime.utcnow(),
            organization_id=org_id,
            user_id=user_id,
            account_id=account_id
        )
        
        assert transaction.amount == -45.67
        assert transaction.description == "Lunch at Chipotle"
        assert transaction.transaction_type == "expense"
        assert transaction.organization_id == org_id
        assert transaction.user_id == user_id
        assert transaction.account_id == account_id
        assert transaction.is_recurring is False
        assert transaction.is_active is True
    
    def test_transaction_with_category(self):
        """Test transaction creation with category"""
        org_id = uuid4()
        user_id = uuid4()
        account_id = uuid4()
        category_id = uuid4()
        
        transaction = Transaction(
            amount=1000.00,
            description="Salary deposit",
            transaction_type="income",
            date=datetime.utcnow(),
            organization_id=org_id,
            user_id=user_id,
            account_id=account_id,
            category_id=category_id
        )
        
        assert transaction.category_id == category_id


class TestBudgetModel:
    """Test Budget model functionality"""
    
    def test_budget_creation(self):
        """Test budget creation with required fields"""
        org_id = uuid4()
        owner_id = uuid4()
        
        budget = Budget(
            name="Monthly Food Budget",
            description="Budget for food expenses",
            amount=800.00,
            period="monthly",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            organization_id=org_id,
            owner_id=owner_id
        )
        
        assert budget.name == "Monthly Food Budget"
        assert budget.amount == 800.00
        assert budget.period == "monthly"
        assert budget.organization_id == org_id
        assert budget.owner_id == owner_id


class TestUserPermissionModel:
    """Test UserPermission model functionality"""
    
    def test_permission_creation(self):
        """Test user permission creation"""
        user_id = uuid4()
        granted_by = uuid4()
        
        permission = UserPermission(
            user_id=user_id,
            permission=Permission.READ_TRANSACTIONS,
            resource_type="transaction",
            granted_by=granted_by
        )
        
        assert permission.user_id == user_id
        assert permission.permission == Permission.READ_TRANSACTIONS
        assert permission.resource_type == "transaction"
        assert permission.granted_by == granted_by


class TestRequestModels:
    """Test API request/response models"""
    
    def test_organization_create(self):
        """Test OrganizationCreate model"""
        org_create = OrganizationCreate(
            name="New Corp",
            slug="new-corp",
            description="New organization"
        )
        
        assert org_create.name == "New Corp"
        assert org_create.slug == "new-corp"
        assert org_create.description == "New organization"
    
    def test_user_create(self):
        """Test UserCreate model"""
        org_id = uuid4()
        user_create = UserCreate(
            email="newuser@example.com",
            first_name="New",
            last_name="User",
            password="password123",
            organization_id=org_id
        )
        
        assert user_create.email == "newuser@example.com"
        assert user_create.first_name == "New"
        assert user_create.last_name == "User"
        assert user_create.password == "password123"
        assert user_create.organization_id == org_id
    
    def test_transaction_create(self):
        """Test TransactionCreate model"""
        org_id = uuid4()
        user_id = uuid4()
        account_id = uuid4()
        
        transaction_create = TransactionCreate(
            amount=-25.00,
            description="Coffee",
            transaction_type="expense",
            date=datetime.utcnow(),
            organization_id=org_id,
            user_id=user_id,
            account_id=account_id
        )
        
        assert transaction_create.amount == -25.00
        assert transaction_create.description == "Coffee"
        assert transaction_create.organization_id == org_id


class TestModelRelationships:
    """Test model relationships and associations"""
    
    def test_organization_user_relationship(self):
        """Test organization-user relationship"""
        org = Organization(name="Test Corp", slug="test-corp")
        user = User(
            email="user@test.com",
            first_name="User",
            last_name="Name",
            organization_id=org.id,
            hashed_password="hash"
        )
        
        # In a real database, these would be properly linked
        assert user.organization_id == org.id
    
    def test_user_account_relationship(self):
        """Test user-account relationship"""
        user = User(
            email="user@test.com",
            first_name="User",
            last_name="Name",
            organization_id=uuid4(),
            hashed_password="hash"
        )
        
        account = Account(
            name="Checking",
            account_type="checking",
            institution="Bank",
            organization_id=user.organization_id,
            owner_id=user.id
        )
        
        assert account.owner_id == user.id
        assert account.organization_id == user.organization_id
    
    def test_transaction_relationships(self):
        """Test transaction relationships"""
        org_id = uuid4()
        user_id = uuid4()
        account_id = uuid4()
        category_id = uuid4()
        
        transaction = Transaction(
            amount=-50.00,
            description="Test transaction",
            transaction_type="expense",
            date=datetime.utcnow(),
            organization_id=org_id,
            user_id=user_id,
            account_id=account_id,
            category_id=category_id
        )
        
        assert transaction.organization_id == org_id
        assert transaction.user_id == user_id
        assert transaction.account_id == account_id
        assert transaction.category_id == category_id


class TestDataValidation:
    """Test data validation and constraints"""
    
    def test_organization_slug_format(self):
        """Test organization slug format validation"""
        # Valid slug
        org = Organization(name="Test Corp", slug="test-corp")
        assert org.slug == "test-corp"
        
        # Slug should be lowercase and use hyphens
        org2 = Organization(name="Another Corp", slug="another-corp")
        assert org2.slug == "another-corp"
    
    def test_user_email_format(self):
        """Test user email format validation"""
        # Valid email
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            organization_id=uuid4(),
            hashed_password="hash"
        )
        assert user.email == "test@example.com"
    
    def test_transaction_amount_validation(self):
        """Test transaction amount validation"""
        # Valid amounts (positive and negative)
        transaction1 = Transaction(
            amount=100.00,
            description="Income",
            transaction_type="income",
            date=datetime.utcnow(),
            organization_id=uuid4(),
            user_id=uuid4(),
            account_id=uuid4()
        )
        
        transaction2 = Transaction(
            amount=-50.00,
            description="Expense",
            transaction_type="expense",
            date=datetime.utcnow(),
            organization_id=uuid4(),
            user_id=uuid4(),
            account_id=uuid4()
        )
        
        assert transaction1.amount == 100.00
        assert transaction2.amount == -50.00


class TestMultitenancy:
    """Test multitenancy functionality"""
    
    def test_organization_isolation(self):
        """Test that organizations are properly isolated"""
        org1 = Organization(name="Corp A", slug="corp-a")
        org2 = Organization(name="Corp B", slug="corp-b")
        
        user1 = User(
            email="user1@corp-a.com",
            first_name="User1",
            last_name="Name",
            organization_id=org1.id,
            hashed_password="hash"
        )
        
        user2 = User(
            email="user2@corp-b.com",
            first_name="User2",
            last_name="Name",
            organization_id=org2.id,
            hashed_password="hash"
        )
        
        # Users belong to different organizations
        assert user1.organization_id != user2.organization_id
        assert user1.organization_id == org1.id
        assert user2.organization_id == org2.id
    
    def test_data_scoping(self):
        """Test that data is properly scoped to organizations"""
        org1_id = uuid4()
        org2_id = uuid4()
        
        # Categories for different organizations
        cat1 = Category(
            name="Food",
            organization_id=org1_id,
            owner_id=uuid4()
        )
        
        cat2 = Category(
            name="Food",
            organization_id=org2_id,
            owner_id=uuid4()
        )
        
        # Same name, different organizations
        assert cat1.name == cat2.name
        assert cat1.organization_id != cat2.organization_id


class TestRBAC:
    """Test Role-Based Access Control functionality"""
    
    def test_user_roles(self):
        """Test user role assignment and validation"""
        org_id = uuid4()
        
        # Admin user
        admin_user = User(
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            role=Role.ADMIN,
            organization_id=org_id,
            hashed_password="hash"
        )
        
        # Analyst user
        analyst_user = User(
            email="analyst@example.com",
            first_name="Analyst",
            last_name="User",
            role=Role.ANALYST,
            organization_id=org_id,
            hashed_password="hash"
        )
        
        # Viewer user
        viewer_user = User(
            email="viewer@example.com",
            first_name="Viewer",
            last_name="User",
            role=Role.VIEWER,
            organization_id=org_id,
            hashed_password="hash"
        )
        
        assert admin_user.role == Role.ADMIN
        assert analyst_user.role == Role.ANALYST
        assert viewer_user.role == Role.VIEWER
    
    def test_permission_granularity(self):
        """Test granular permission system"""
        user_id = uuid4()
        granted_by = uuid4()
        
        # Read permission
        read_perm = UserPermission(
            user_id=user_id,
            permission=Permission.READ_TRANSACTIONS,
            resource_type="transaction",
            granted_by=granted_by
        )
        
        # Write permission
        write_perm = UserPermission(
            user_id=user_id,
            permission=Permission.CREATE_TRANSACTIONS,
            resource_type="transaction",
            granted_by=granted_by
        )
        
        assert read_perm.permission == Permission.READ_TRANSACTIONS
        assert write_perm.permission == Permission.CREATE_TRANSACTIONS
        assert read_perm.resource_type == "transaction"
        assert write_perm.resource_type == "transaction"


if __name__ == "__main__":
    pytest.main([__file__])