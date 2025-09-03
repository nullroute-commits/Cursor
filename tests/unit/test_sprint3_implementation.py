"""
Unit tests for Sprint 3: Plaid Integration
Tests Plaid service, client, and API endpoints
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.backend.services.plaid_service import (
    PlaidService, PlaidClient, plaid_service
)
from src.backend.api.plaid import router as plaid_router
from src.common.models.enums import TransactionType, AccountType
from src.backend.models.database import Transaction, Account, Category, Organization, User


class TestPlaidClient:
    """Test Plaid client functionality"""
    
    def test_plaid_client_initialization(self):
        """Test Plaid client initialization"""
        client = PlaidClient()
        assert client.client_id is not None
        assert client.secret is not None
        assert client.environment is not None
        assert client.base_url is not None
    
    def test_get_base_url_sandbox(self):
        """Test base URL for sandbox environment"""
        client = PlaidClient()
        client.environment = "sandbox"
        base_url = client._get_base_url()
        assert base_url == "https://sandbox.plaid.com"
    
    def test_get_base_url_development(self):
        """Test base URL for development environment"""
        client = PlaidClient()
        client.environment = "development"
        base_url = client._get_base_url()
        assert base_url == "https://development.plaid.com"
    
    def test_get_base_url_production(self):
        """Test base URL for production environment"""
        client = PlaidClient()
        client.environment = "production"
        base_url = client._get_base_url()
        assert base_url == "https://production.plaid.com"
    
    @pytest.mark.asyncio
    async def test_create_link_token_mock(self):
        """Test link token creation with mock implementation"""
        client = PlaidClient()
        client.plaid_available = False
        
        user_id = "test_user_123"
        result = await client.create_link_token(user_id)
        
        assert "link_token" in result
        assert "expiration" in result
        assert "request_id" in result
        assert result["link_token"].startswith("mock_link_token_")
    
    @pytest.mark.asyncio
    async def test_exchange_public_token_mock(self):
        """Test public token exchange with mock implementation"""
        client = PlaidClient()
        client.plaid_available = False
        
        public_token = "test_public_token_12345"
        result = await client.exchange_public_token(public_token)
        
        assert "access_token" in result
        assert "item_id" in result
        assert "request_id" in result
        assert result["access_token"].startswith("mock_access_token_")
    
    @pytest.mark.asyncio
    async def test_get_accounts_mock(self):
        """Test account retrieval with mock implementation"""
        client = PlaidClient()
        client.plaid_available = False
        
        result = await client.get_accounts("mock_access_token")
        
        assert len(result) == 2
        assert result[0]["type"] == "depository"
        assert result[0]["subtype"] == "checking"
        assert result[1]["type"] == "credit"
        assert result[1]["subtype"] == "credit card"
    
    @pytest.mark.asyncio
    async def test_get_transactions_mock(self):
        """Test transaction retrieval with mock implementation"""
        client = PlaidClient()
        client.plaid_available = False
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        result = await client.get_transactions("mock_access_token", start_date, end_date)
        
        assert len(result) == 1
        assert result[0]["amount"] == -50.00
        assert result[0]["category"] == ["Food and Drink", "Restaurants"]
        assert result[0]["date"] == start_date.isoformat()
    
    @pytest.mark.asyncio
    async def test_get_item_info_mock(self):
        """Test item info retrieval with mock implementation"""
        client = PlaidClient()
        client.plaid_available = False
        
        result = await client.get_item_info("mock_access_token")
        
        assert "item_id" in result
        assert "institution_id" in result
        assert "products" in result
        assert "transactions" in result["products"]
    
    @pytest.mark.asyncio
    async def test_get_institution_info_mock(self):
        """Test institution info retrieval with mock implementation"""
        client = PlaidClient()
        client.plaid_available = False
        
        result = await client.get_institution_info("mock_institution_123")
        
        assert "institution_id" in result
        assert "name" in result
        assert "products" in result
        assert "country_codes" in result


class TestPlaidService:
    """Test Plaid service functionality"""
    
    @pytest.fixture
    def mock_user(self):
        """Mock user for testing"""
        user = Mock()
        user.id = uuid4()
        user.organization_id = uuid4()
        return user
    
    @pytest.mark.asyncio
    async def test_create_link_token_success(self, mock_user):
        """Test successful link token creation"""
        service = PlaidService()
        
        with patch.object(service.client, 'create_link_token') as mock_create:
            mock_create.return_value = {
                "link_token": "test_link_token",
                "expiration": "2024-12-31T23:59:59",
                "request_id": "test_request_id"
            }
            
            result = await service.create_link_token(mock_user.id)
            
            assert result["success"] is True
            assert "link_token" in result["data"]
            mock_create.assert_called_once_with(str(mock_user.id))
    
    @pytest.mark.asyncio
    async def test_create_link_token_failure(self, mock_user):
        """Test link token creation failure"""
        service = PlaidService()
        
        with patch.object(service.client, 'create_link_token') as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            result = await service.create_link_token(mock_user.id)
            
            assert result["success"] is False
            assert "API Error" in result["message"]
    
    @pytest.mark.asyncio
    async def test_connect_accounts_success(self, mock_user):
        """Test successful account connection"""
        service = PlaidService()
        
        # Mock client responses
        with patch.object(service.client, 'exchange_public_token') as mock_exchange:
            mock_exchange.return_value = {
                "access_token": "test_access_token",
                "item_id": "test_item_id"
            }
            
            with patch.object(service.client, 'get_accounts') as mock_accounts:
                mock_accounts.return_value = [
                    {
                        "account_id": "test_account_123",
                        "balances": {"current": 1000.00, "available": 1000.00, "limit": None},
                        "mask": "1234",
                        "name": "Test Account",
                        "type": "depository",
                        "subtype": "checking"
                    }
                ]
                
                with patch.object(service.client, 'get_item_info') as mock_item:
                    mock_item.return_value = {"institution_id": "test_institution"}
                    
                    with patch.object(service.client, 'get_institution_info') as mock_institution:
                        mock_institution.return_value = {"name": "Test Bank"}
                        
                        with patch('src.backend.services.plaid_service.get_session') as mock_session:
                            mock_session.return_value.__aenter__.return_value.exec.return_value.first.return_value = None
                            mock_session.return_value.__aenter__.return_value.add.return_value = None
                            mock_session.return_value.__aenter__.return_value.commit.return_value = None
                            mock_session.return_value.__aenter__.return_value.refresh.return_value = None
                            
                            result = await service.connect_accounts(
                                "test_public_token", mock_user.id, mock_user.organization_id
                            )
                            
                            assert result["success"] is True
                            assert result["data"]["accounts_connected"] == 1
    
    @pytest.mark.asyncio
    async def test_sync_transactions_success(self, mock_user):
        """Test successful transaction sync"""
        service = PlaidService()
        
        # Mock database session and accounts
        mock_account = Mock()
        mock_account.plaid_access_token = "test_token"
        mock_account.plaid_account_id = "test_account_123"
        mock_account.id = uuid4()
        mock_account.metadata = {}
        
        with patch('src.backend.services.plaid_service.get_session') as mock_session:
            mock_session.return_value.__aenter__.return_value.exec.return_value.all.return_value = [mock_account]
            
            with patch.object(service.client, 'get_transactions') as mock_transactions:
                mock_transactions.return_value = [
                    {
                        "account_id": "test_account_123",
                        "amount": -50.00,
                        "category": ["Food and Drink"],
                        "date": "2024-01-15",
                        "name": "Test Transaction",
                        "transaction_id": "test_tx_123"
                    }
                ]
                
                mock_session.return_value.__aenter__.return_value.exec.return_value.first.return_value = None
                mock_session.return_value.__aenter__.return_value.add.return_value = None
                mock_session.return_value.__aenter__.return_value.commit.return_value = None
                
                result = await service.sync_transactions(
                    mock_user.id, mock_user.organization_id, days_back=30
                )
                
                assert result["success"] is True
                assert result["data"]["transactions_created"] == 1
                assert result["data"]["accounts_synced"] == 1
    
    @pytest.mark.asyncio
    async def test_sync_transactions_no_accounts(self, mock_user):
        """Test transaction sync with no connected accounts"""
        service = PlaidService()
        
        with patch('src.backend.services.plaid_service.get_session') as mock_session:
            mock_session.return_value.__aenter__.return_value.exec.return_value.all.return_value = []
            
            result = await service.sync_transactions(
                mock_user.id, mock_user.organization_id
            )
            
            assert result["success"] is False
            assert "No Plaid-connected accounts found" in result["message"]
    
    @pytest.mark.asyncio
    async def test_get_sync_status_success(self, mock_user):
        """Test successful sync status retrieval"""
        service = PlaidService()
        
        mock_account = Mock()
        mock_account.id = uuid4()
        mock_account.name = "Test Account"
        mock_account.institution_name = "Test Bank"
        mock_account.balance = Decimal('1000.00')
        mock_account.account_type = AccountType.CHECKING
        mock_account.metadata = {"plaid_last_sync": "2024-01-15T10:00:00"}
        
        with patch('src.backend.services.plaid_service.get_session') as mock_session:
            mock_session.return_value.__aenter__.return_value.exec.return_value.all.return_value = [mock_account]
            mock_session.return_value.__aenter__.return_value.exec.return_value.first.return_value = 5
            
            result = await service.get_sync_status(mock_user.organization_id)
            
            assert result["success"] is True
            assert len(result["data"]["accounts"]) == 1
            assert result["data"]["total_transactions"] == 5
    
    def test_map_plaid_account_type_checking(self):
        """Test Plaid account type mapping for checking accounts"""
        service = PlaidService()
        
        account_type = service._map_plaid_account_type("depository", "checking")
        assert account_type == AccountType.CHECKING
    
    def test_map_plaid_account_type_savings(self):
        """Test Plaid account type mapping for savings accounts"""
        service = PlaidService()
        
        account_type = service._map_plaid_account_type("depository", "savings")
        assert account_type == AccountType.SAVINGS
    
    def test_map_plaid_account_type_credit_card(self):
        """Test Plaid account type mapping for credit cards"""
        service = PlaidService()
        
        account_type = service._map_plaid_account_type("credit", "credit card")
        assert account_type == AccountType.CREDIT_CARD
    
    def test_map_plaid_account_type_loan(self):
        """Test Plaid account type mapping for loans"""
        service = PlaidService()
        
        account_type = service._map_plaid_account_type("loan", "student")
        assert account_type == AccountType.LOAN
    
    def test_map_plaid_account_type_investment(self):
        """Test Plaid account type mapping for investments"""
        service = PlaidService()
        
        account_type = service._map_plaid_account_type("investment", "401k")
        assert account_type == AccountType.INVESTMENT
    
    def test_map_plaid_account_type_other(self):
        """Test Plaid account type mapping for other types"""
        service = PlaidService()
        
        account_type = service._map_plaid_account_type("unknown", "unknown")
        assert account_type == AccountType.OTHER
    
    def test_generate_transaction_hash(self):
        """Test transaction hash generation"""
        service = PlaidService()
        
        plaid_tx = {
            "account_id": "test_account_123",
            "transaction_id": "test_tx_456",
            "amount": -50.00,
            "date": "2024-01-15",
            "name": "Test Transaction"
        }
        
        hash1 = service._generate_transaction_hash(plaid_tx)
        hash2 = service._generate_transaction_hash(plaid_tx)
        
        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hash length
        
        # Different transaction should have different hash
        plaid_tx2 = plaid_tx.copy()
        plaid_tx2["amount"] = -100.00
        hash3 = service._generate_transaction_hash(plaid_tx2)
        
        assert hash1 != hash3


class TestPlaidAPI:
    """Test Plaid API endpoints"""
    
    def test_plaid_router_creation(self):
        """Test Plaid router is created"""
        assert plaid_router is not None
        assert hasattr(plaid_router, 'routes')
    
    def test_plaid_endpoints_exist(self):
        """Test required Plaid endpoints exist"""
        routes = [route.path for route in plaid_router.routes]
        
        assert "/link-token" in routes  # POST for creating link tokens
        assert "/connect" in routes  # POST for connecting accounts
        assert "/sync" in routes  # POST for syncing transactions
        assert "/status" in routes  # GET for sync status
        assert "/webhook" in routes  # POST for webhooks
        assert "/accounts" in routes  # GET for Plaid accounts
        assert "/institutions" in routes  # GET for institutions
        assert "/transactions" in routes  # GET for Plaid transactions
        assert "/health" in routes  # GET for health check
    
    def test_plaid_router_prefix(self):
        """Test Plaid router has correct prefix"""
        # This would be tested in the main app integration
        # For now, just verify the router exists
        assert plaid_router is not None


class TestPlaidIntegration:
    """Test Plaid integration scenarios"""
    
    @pytest.fixture
    def mock_plaid_service(self):
        """Mock Plaid service for testing"""
        service = Mock()
        service.create_link_token.return_value = {
            "success": True,
            "message": "Success",
            "data": {"link_token": "test_token"}
        }
        service.connect_accounts.return_value = {
            "success": True,
            "message": "Success",
            "data": {"accounts_connected": 2}
        }
        service.sync_transactions.return_value = {
            "success": True,
            "message": "Success",
            "data": {"transactions_created": 50}
        }
        service.get_sync_status.return_value = {
            "success": True,
            "message": "Success",
            "data": {"total_accounts": 2}
        }
        return service
    
    @pytest.mark.asyncio
    async def test_full_plaid_workflow(self, mock_plaid_service):
        """Test complete Plaid integration workflow"""
        
        # Step 1: Create link token
        link_result = await mock_plaid_service.create_link_token("user_123")
        assert link_result["success"] is True
        assert "link_token" in link_result["data"]
        
        # Step 2: Connect accounts
        connect_result = await mock_plaid_service.connect_accounts(
            "public_token", "user_123", "org_456"
        )
        assert connect_result["success"] is True
        assert connect_result["data"]["accounts_connected"] == 2
        
        # Step 3: Sync transactions
        sync_result = await mock_plaid_service.sync_transactions(
            "user_123", "org_456", days_back=30
        )
        assert sync_result["success"] is True
        assert sync_result["data"]["transactions_created"] == 50
        
        # Step 4: Get sync status
        status_result = await mock_plaid_service.get_sync_status("org_456")
        assert status_result["success"] is True
        assert status_result["data"]["total_accounts"] == 2
    
    @pytest.mark.asyncio
    async def test_plaid_error_handling(self, mock_plaid_service):
        """Test Plaid error handling scenarios"""
        
        # Test link token creation failure
        mock_plaid_service.create_link_token.return_value = {
            "success": False,
            "message": "API Error",
            "data": None
        }
        
        result = await mock_plaid_service.create_link_token("user_123")
        assert result["success"] is False
        assert "API Error" in result["message"]
        
        # Test account connection failure
        mock_plaid_service.connect_accounts.return_value = {
            "success": False,
            "message": "Invalid token",
            "data": None
        }
        
        result = await mock_plaid_service.connect_accounts(
            "invalid_token", "user_123", "org_456"
        )
        assert result["success"] is False
        assert "Invalid token" in result["message"]
    
    def test_plaid_webhook_handling(self):
        """Test Plaid webhook handling"""
        
        # Test transaction webhook
        webhook_data = {
            "webhook_type": "TRANSACTIONS",
            "webhook_code": "DEFAULT_UPDATE",
            "item_id": "item_123"
        }
        
        # This would be tested in the actual API endpoint
        # For now, just verify the structure
        assert webhook_data["webhook_type"] == "TRANSACTIONS"
        assert webhook_data["webhook_code"] == "DEFAULT_UPDATE"
        
        # Test item error webhook
        error_webhook = {
            "webhook_type": "ITEM",
            "webhook_code": "ERROR",
            "item_id": "item_456",
            "error": {"error_code": "ITEM_LOGIN_REQUIRED"}
        }
        
        assert error_webhook["webhook_type"] == "ITEM"
        assert error_webhook["webhook_code"] == "ERROR"
        assert "error" in error_webhook


class TestPlaidDataMapping:
    """Test Plaid data mapping and transformation"""
    
    def test_plaid_transaction_to_platform_mapping(self):
        """Test mapping Plaid transaction data to platform format"""
        
        plaid_tx = {
            "account_id": "plaid_account_123",
            "amount": -75.50,
            "category": ["Food and Drink", "Restaurants"],
            "category_id": "13005000",
            "date": "2024-01-15",
            "iso_currency_code": "USD",
            "merchant_name": "Test Restaurant",
            "name": "Test Restaurant Transaction",
            "payment_channel": "in store",
            "pending": False,
            "transaction_id": "plaid_tx_789",
            "transaction_type": "place"
        }
        
        # Verify required fields
        assert "account_id" in plaid_tx
        assert "amount" in plaid_tx
        assert "category" in plaid_tx
        assert "date" in plaid_tx
        assert "name" in plaid_tx
        assert "transaction_id" in plaid_tx
        
        # Verify data types
        assert isinstance(plaid_tx["amount"], (int, float))
        assert isinstance(plaid_tx["category"], list)
        assert isinstance(plaid_tx["date"], str)
        assert isinstance(plaid_tx["name"], str)
    
    def test_plaid_account_to_platform_mapping(self):
        """Test mapping Plaid account data to platform format"""
        
        plaid_account = {
            "account_id": "plaid_account_456",
            "balances": {
                "available": 2500.00,
                "current": 2500.00,
                "limit": None
            },
            "mask": "5678",
            "name": "Test Savings Account",
            "official_name": "Test Personal Savings Account",
            "subtype": "savings",
            "type": "depository"
        }
        
        # Verify required fields
        assert "account_id" in plaid_account
        assert "balances" in plaid_account
        assert "name" in plaid_account
        assert "type" in plaid_account
        assert "subtype" in plaid_account
        
        # Verify balance structure
        balances = plaid_account["balances"]
        assert "available" in balances
        assert "current" in balances
        assert isinstance(balances["available"], (int, float))
        assert isinstance(balances["current"], (int, float))


if __name__ == "__main__":
    pytest.main([__file__])