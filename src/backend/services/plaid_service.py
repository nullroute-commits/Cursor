"""
Plaid service for Financial Analytics Platform
Handles Plaid API integration for automated bank data fetching
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Union
from uuid import UUID
from decimal import Decimal
import json
import hashlib

from fastapi import HTTPException, status
from sqlmodel import select, func

from src.backend.models.database import Transaction, TransactionCreate, Account, Category
from src.backend.database import get_session
from src.common.models.enums import TransactionType, AccountType
from src.common.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PlaidClient:
    """Plaid API client wrapper"""
    
    def __init__(self):
        self.client_id = settings.plaid_client_id
        self.secret = settings.plaid_secret
        self.environment = settings.plaid_environment
        self.base_url = self._get_base_url()
        
        # Import plaid-python if available
        try:
            import plaid
            from plaid.api import plaid_api
            from plaid.model import link_token_create_request, link_token_create_request_user
            from plaid.model import item_public_token_exchange_request
            from plaid.model import transactions_get_request
            from plaid.model import accounts_get_request
            from plaid.model import item_get_request
            from plaid.model import institutions_get_by_id_request
            
            self.plaid = plaid
            self.plaid_api = plaid_api
            self.models = plaid.model
            
            # Configure client
            configuration = plaid.Configuration(
                host=self.base_url,
                api_key={
                    'clientId': self.client_id,
                    'secret': self.secret,
                }
            )
            
            api_client = plaid.ApiClient(configuration)
            self.client = plaid_api.PlaidApi(api_client)
            self.plaid_available = True
            
        except ImportError:
            logger.warning("plaid-python not available, using mock implementation")
            self.plaid_available = False
            self.client = None
            self.models = None
    
    def _get_base_url(self) -> str:
        """Get Plaid API base URL based on environment"""
        if self.environment == "sandbox":
            return "https://sandbox.plaid.com"
        elif self.environment == "development":
            return "https://development.plaid.com"
        else:
            return "https://production.plaid.com"
    
    async def create_link_token(self, user_id: str, access_token: Optional[str] = None) -> Dict[str, Any]:
        """Create a Plaid Link token for connecting accounts"""
        
        if not self.plaid_available:
            # Mock implementation for testing
            return {
                "link_token": f"mock_link_token_{user_id}_{datetime.now().timestamp()}",
                "expiration": (datetime.now() + timedelta(hours=24)).isoformat(),
                "request_id": f"mock_request_{user_id}"
            }
        
        try:
            user = self.models.link_token_create_request_user(
                client_user_id=user_id
            )
            
            request = self.models.link_token_create_request(
                user=user,
                client_name="Financial Analytics Platform",
                country_codes=["US"],
                language="en",
                products=["transactions"],
                account_filters={
                    "depository": {
                        "account_subtypes": ["checking", "savings"]
                    },
                    "credit": {
                        "account_subtypes": ["credit card"]
                    }
                }
            )
            
            response = self.client.link_token_create(request)
            
            return {
                "link_token": response.link_token,
                "expiration": response.expiration.isoformat(),
                "request_id": response.request_id
            }
            
        except Exception as e:
            logger.error(f"Failed to create Plaid link token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create Plaid link token: {str(e)}"
            )
    
    async def exchange_public_token(self, public_token: str) -> Dict[str, Any]:
        """Exchange public token for access token"""
        
        if not self.plaid_available:
            # Mock implementation for testing
            return {
                "access_token": f"mock_access_token_{public_token[:8]}",
                "item_id": f"mock_item_{public_token[:8]}",
                "request_id": f"mock_request_{public_token[:8]}"
            }
        
        try:
            request = self.models.item_public_token_exchange_request(
                public_token=public_token
            )
            
            response = self.client.item_public_token_exchange(request)
            
            return {
                "access_token": response.access_token,
                "item_id": response.item_id,
                "request_id": response.request_id
            }
            
        except Exception as e:
            logger.error(f"Failed to exchange Plaid public token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to exchange Plaid public token: {str(e)}"
            )
    
    async def get_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """Get accounts for a Plaid item"""
        
        if not self.plaid_available:
            # Mock implementation for testing
            return [
                {
                    "account_id": "mock_checking_123",
                    "balances": {"available": 1000.00, "current": 1000.00, "limit": None},
                    "mask": "1234",
                    "name": "Mock Checking Account",
                    "official_name": "Mock Personal Checking Account",
                    "subtype": "checking",
                    "type": "depository"
                },
                {
                    "account_id": "mock_credit_456",
                    "balances": {"available": 5000.00, "current": 5000.00, "limit": 10000.00},
                    "mask": "5678",
                    "name": "Mock Credit Card",
                    "official_name": "Mock Credit Card Account",
                    "subtype": "credit card",
                    "type": "credit"
                }
            ]
        
        try:
            request = self.models.accounts_get_request(
                access_token=access_token
            )
            
            response = self.client.accounts_get(request)
            
            accounts = []
            for account in response.accounts:
                accounts.append({
                    "account_id": account.account_id,
                    "balances": {
                        "available": account.balances.available,
                        "current": account.balances.current,
                        "limit": account.balances.limit
                    },
                    "mask": account.mask,
                    "name": account.name,
                    "official_name": account.official_name,
                    "subtype": account.subtype,
                    "type": account.type
                })
            
            return accounts
            
        except Exception as e:
            logger.error(f"Failed to get Plaid accounts: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get Plaid accounts: {str(e)}"
            )
    
    async def get_transactions(
        self,
        access_token: str,
        start_date: date,
        end_date: date,
        account_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get transactions for a Plaid item"""
        
        if not self.plaid_available:
            # Mock implementation for testing
            return [
                {
                    "account_id": "mock_checking_123",
                    "amount": -50.00,
                    "category": ["Food and Drink", "Restaurants"],
                    "category_id": "13005000",
                    "date": start_date.isoformat(),
                    "iso_currency_code": "USD",
                    "merchant_name": "Mock Restaurant",
                    "name": "Mock Restaurant Transaction",
                    "payment_channel": "in store",
                    "pending": False,
                    "transaction_id": f"mock_tx_{start_date.strftime('%Y%m%d')}_1",
                    "transaction_type": "place"
                }
            ]
        
        try:
            request = self.models.transactions_get_request(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date,
                options={
                    "account_ids": account_ids
                } if account_ids else None
            )
            
            response = self.client.transactions_get(request)
            
            transactions = []
            for tx in response.transactions:
                transactions.append({
                    "account_id": tx.account_id,
                    "amount": tx.amount,
                    "category": tx.category,
                    "category_id": tx.category_id,
                    "date": tx.date.isoformat(),
                    "iso_currency_code": tx.iso_currency_code,
                    "merchant_name": tx.merchant_name,
                    "name": tx.name,
                    "payment_channel": tx.payment_channel,
                    "pending": tx.pending,
                    "transaction_id": tx.transaction_id,
                    "transaction_type": tx.transaction_type
                })
            
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to get Plaid transactions: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get Plaid transactions: {str(e)}"
            )
    
    async def get_item_info(self, access_token: str) -> Dict[str, Any]:
        """Get information about a Plaid item"""
        
        if not self.plaid_available:
            # Mock implementation for testing
            return {
                "item_id": "mock_item_123",
                "institution_id": "mock_institution_456",
                "webhook": None,
                "error": None,
                "available_products": ["transactions"],
                "billed_products": [],
                "products": ["transactions"],
                "consent_expiration_time": None,
                "update_type": "background"
            }
        
        try:
            request = self.models.item_get_request(
                access_token=access_token
            )
            
            response = self.client.item_get(request)
            
            return {
                "item_id": response.item.item_id,
                "institution_id": response.item.institution_id,
                "webhook": response.item.webhook,
                "error": response.item.error.dict() if response.item.error else None,
                "available_products": response.item.available_products,
                "billed_products": response.item.billed_products,
                "products": response.item.products,
                "consent_expiration_time": response.item.consent_expiration_time.isoformat() if response.item.consent_expiration_time else None,
                "update_type": response.item.update_type
            }
            
        except Exception as e:
            logger.error(f"Failed to get Plaid item info: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get Plaid item info: {str(e)}"
            )
    
    async def get_institution_info(self, institution_id: str) -> Dict[str, Any]:
        """Get information about a financial institution"""
        
        if not self.plaid_available:
            # Mock implementation for testing
            return {
                "institution_id": institution_id,
                "name": "Mock Bank",
                "products": ["transactions"],
                "country_codes": ["US"],
                "url": "https://mockbank.com",
                "primary_color": "#000000",
                "logo": None,
                "routing_numbers": ["123456789"]
            }
        
        try:
            request = self.models.institutions_get_by_id_request(
                institution_id=institution_id,
                country_codes=["US"]
            )
            
            response = self.client.institutions_get_by_id(request)
            institution = response.institution
            
            return {
                "institution_id": institution.institution_id,
                "name": institution.name,
                "products": institution.products,
                "country_codes": institution.country_codes,
                "url": institution.url,
                "primary_color": institution.primary_color,
                "logo": institution.logo,
                "routing_numbers": institution.routing_numbers
            }
            
        except Exception as e:
            logger.error(f"Failed to get Plaid institution info: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get Plaid institution info: {str(e)}"
            )


class PlaidService:
    """Service for managing Plaid integrations"""
    
    def __init__(self):
        self.client = PlaidClient()
    
    async def create_link_token(self, user_id: UUID) -> Dict[str, Any]:
        """Create a Plaid Link token for user account connection"""
        
        try:
            result = await self.client.create_link_token(str(user_id))
            
            return {
                "success": True,
                "message": "Plaid link token created successfully",
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to create Plaid link token: {e}")
            return {
                "success": False,
                "message": f"Failed to create Plaid link token: {str(e)}",
                "data": None
            }
    
    async def connect_accounts(
        self,
        public_token: str,
        user_id: UUID,
        organization_id: UUID
    ) -> Dict[str, Any]:
        """Connect Plaid accounts to the platform"""
        
        try:
            # Exchange public token for access token
            token_result = await self.client.exchange_public_token(public_token)
            access_token = token_result["access_token"]
            item_id = token_result["item_id"]
            
            # Get accounts
            accounts = await self.client.get_accounts(access_token)
            
            # Get item and institution info
            item_info = await self.client.get_item_info(access_token)
            institution_info = await self.client.get_institution_info(item_info["institution_id"])
            
            # Create or update accounts in database
            created_accounts = []
            async with get_session() as session:
                for plaid_account in accounts:
                    # Check if account already exists
                    statement = select(Account).where(
                        Account.plaid_account_id == plaid_account["account_id"],
                        Account.organization_id == organization_id
                    )
                    result = await session.exec(statement)
                    existing_account = result.first()
                    
                    if existing_account:
                        # Update existing account
                        existing_account.balance = plaid_account["balances"]["current"] or Decimal('0.00')
                        existing_account.available_balance = plaid_account["balances"]["available"] or Decimal('0.00')
                        existing_account.credit_limit = plaid_account["balances"]["limit"] or Decimal('0.00')
                        existing_account.updated_at = datetime.utcnow()
                        existing_account.metadata = {
                            **existing_account.metadata or {},
                            "plaid_last_sync": datetime.utcnow().isoformat(),
                            "plaid_account_data": plaid_account
                        }
                        created_accounts.append(existing_account)
                    else:
                        # Create new account
                        account_type = self._map_plaid_account_type(plaid_account["type"], plaid_account["subtype"])
                        
                        new_account = Account(
                            name=plaid_account["name"],
                            account_type=account_type,
                            balance=plaid_account["balances"]["current"] or Decimal('0.00'),
                            available_balance=plaid_account["balances"]["available"] or Decimal('0.00'),
                            credit_limit=plaid_account["balances"]["limit"] or Decimal('0.00'),
                            account_number=plaid_account["mask"],
                            institution_name=institution_info["name"],
                            plaid_account_id=plaid_account["account_id"],
                            plaid_item_id=item_id,
                            plaid_access_token=access_token,
                            organization_id=organization_id,
                            user_id=user_id,
                            is_active=True,
                            metadata={
                                "plaid_account_data": plaid_account,
                                "plaid_institution_data": institution_info,
                                "plaid_item_data": item_info,
                                "plaid_last_sync": datetime.utcnow().isoformat()
                            }
                        )
                        
                        session.add(new_account)
                        created_accounts.append(new_account)
                
                await session.commit()
                
                # Refresh accounts to get IDs
                for account in created_accounts:
                    await session.refresh(account)
            
            return {
                "success": True,
                "message": f"Successfully connected {len(created_accounts)} accounts",
                "data": {
                    "accounts_connected": len(created_accounts),
                    "accounts": [
                        {
                            "id": str(account.id),
                            "name": account.name,
                            "account_type": account.account_type.value,
                            "balance": float(account.balance),
                            "institution": account.institution_name
                        }
                        for account in created_accounts
                    ],
                    "institution": {
                        "name": institution_info["name"],
                        "id": institution_info["institution_id"]
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to connect Plaid accounts: {e}")
            return {
                "success": False,
                "message": f"Failed to connect Plaid accounts: {str(e)}",
                "data": None
            }
    
    async def sync_transactions(
        self,
        user_id: UUID,
        organization_id: UUID,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Sync transactions from Plaid for all connected accounts"""
        
        try:
            # Get all Plaid-connected accounts for the organization
            async with get_session() as session:
                statement = select(Account).where(
                    Account.organization_id == organization_id,
                    Account.plaid_access_token.is_not(None),
                    Account.is_active == True
                )
                result = await session.exec(statement)
                accounts = result.all()
            
            if not accounts:
                return {
                    "success": False,
                    "message": "No Plaid-connected accounts found",
                    "data": None
                }
            
            # Group accounts by access token to minimize API calls
            accounts_by_token = {}
            for account in accounts:
                token = account.plaid_access_token
                if token not in accounts_by_token:
                    accounts_by_token[token] = []
                accounts_by_token[token].append(account)
            
            total_transactions = 0
            total_accounts = 0
            
            for access_token, token_accounts in accounts_by_token.items():
                # Get transactions for all accounts with this token
                account_ids = [acc.plaid_account_id for acc in token_accounts]
                
                end_date = date.today()
                start_date = end_date - timedelta(days=days_back)
                
                plaid_transactions = await self.client.get_transactions(
                    access_token=access_token,
                    start_date=start_date,
                    end_date=end_date,
                    account_ids=account_ids
                )
                
                # Process transactions
                for plaid_tx in plaid_transactions:
                    # Find corresponding account
                    account = next(
                        (acc for acc in token_accounts if acc.plaid_account_id == plaid_tx["account_id"]),
                        None
                    )
                    
                    if not account:
                        continue
                    
                    # Check if transaction already exists
                    tx_hash = self._generate_transaction_hash(plaid_tx)
                    existing_statement = select(Transaction).where(
                        Transaction.plaid_transaction_id == plaid_tx["transaction_id"],
                        Transaction.organization_id == organization_id
                    )
                    existing_result = await session.exec(existing_statement)
                    existing_tx = existing_result.first()
                    
                    if existing_tx:
                        # Update existing transaction
                        existing_tx.amount = Decimal(str(plaid_tx["amount"]))
                        existing_tx.description = plaid_tx["name"]
                        existing_tx.merchant_name = plaid_tx.get("merchant_name")
                        existing_tx.updated_at = datetime.utcnow()
                        existing_tx.metadata = {
                            **existing_tx.metadata or {},
                            "plaid_last_sync": datetime.utcnow().isoformat(),
                            "plaid_transaction_data": plaid_tx
                        }
                    else:
                        # Create new transaction
                        transaction_type = TransactionType.EXPENSE if plaid_tx["amount"] < 0 else TransactionType.INCOME
                        
                        # Auto-categorize based on Plaid category
                        category_id = await self._get_category_for_plaid_category(
                            plaid_tx["category"], organization_id, session
                        )
                        
                        new_transaction = Transaction(
                            amount=Decimal(str(plaid_tx["amount"])),
                            description=plaid_tx["name"],
                            transaction_type=transaction_type,
                            date=datetime.strptime(plaid_tx["date"], "%Y-%m-%d").date(),
                            merchant_name=plaid_tx.get("merchant_name"),
                            reference=plaid_tx.get("transaction_id"),
                            notes=f"Plaid Category: {', '.join(plaid_tx['category']) if plaid_tx['category'] else 'Uncategorized'}",
                            is_recurring=False,
                            organization_id=organization_id,
                            user_id=user_id,
                            account_id=account.id,
                            category_id=category_id,
                            plaid_transaction_id=plaid_tx["transaction_id"],
                            plaid_category_id=plaid_tx.get("category_id"),
                            metadata={
                                "plaid_transaction_data": plaid_tx,
                                "plaid_last_sync": datetime.utcnow().isoformat(),
                                "transaction_hash": tx_hash
                            }
                        )
                        
                        session.add(new_transaction)
                        total_transactions += 1
                
                total_accounts += len(token_accounts)
                
                # Update last sync time for accounts
                for account in token_accounts:
                    account.metadata = {
                        **account.metadata or {},
                        "plaid_last_sync": datetime.utcnow().isoformat()
                    }
            
            await session.commit()
            
            return {
                "success": True,
                "message": f"Successfully synced transactions from {total_accounts} accounts",
                "data": {
                    "accounts_synced": total_accounts,
                    "transactions_created": total_transactions,
                    "sync_period_days": days_back,
                    "sync_timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to sync Plaid transactions: {e}")
            return {
                "success": False,
                "message": f"Failed to sync Plaid transactions: {str(e)}",
                "data": None
            }
    
    async def get_sync_status(
        self,
        organization_id: UUID
    ) -> Dict[str, Any]:
        """Get sync status for all Plaid-connected accounts"""
        
        try:
            async with get_session() as session:
                statement = select(Account).where(
                    Account.organization_id == organization_id,
                    Account.plaid_access_token.is_not(None),
                    Account.is_active == True
                )
                result = await session.exec(statement)
                accounts = result.all()
            
            sync_status = []
            for account in accounts:
                metadata = account.metadata or {}
                last_sync = metadata.get("plaid_last_sync")
                
                # Get transaction count for this account
                tx_statement = select(func.count(Transaction.id)).where(
                    Transaction.account_id == account.id,
                    Transaction.plaid_transaction_id.is_not(None)
                )
                tx_result = await session.exec(tx_statement)
                transaction_count = tx_result.first() or 0
                
                sync_status.append({
                    "account_id": str(account.id),
                    "account_name": account.name,
                    "institution": account.institution_name,
                    "last_sync": last_sync,
                    "transaction_count": transaction_count,
                    "balance": float(account.balance),
                    "account_type": account.account_type.value
                })
            
            return {
                "success": True,
                "message": "Sync status retrieved successfully",
                "data": {
                    "accounts": sync_status,
                    "total_accounts": len(sync_status),
                    "total_transactions": sum(acc["transaction_count"] for acc in sync_status)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            return {
                "success": False,
                "message": f"Failed to get sync status: {str(e)}",
                "data": None
            }
    
    def _map_plaid_account_type(self, plaid_type: str, plaid_subtype: str) -> AccountType:
        """Map Plaid account type to platform account type"""
        
        if plaid_type == "depository":
            if plaid_subtype == "checking":
                return AccountType.CHECKING
            elif plaid_subtype == "savings":
                return AccountType.SAVINGS
            else:
                return AccountType.CHECKING
        elif plaid_type == "credit":
            return AccountType.CREDIT_CARD
        elif plaid_type == "loan":
            return AccountType.LOAN
        elif plaid_type == "investment":
            return AccountType.INVESTMENT
        else:
            return AccountType.OTHER
    
    async def _get_category_for_plaid_category(
        self,
        plaid_categories: List[str],
        organization_id: UUID,
        session
    ) -> Optional[UUID]:
        """Get platform category ID for Plaid category"""
        
        if not plaid_categories:
            return None
        
        # Try to find exact match
        for category_name in plaid_categories:
            statement = select(Category).where(
                Category.name.ilike(f"%{category_name}%"),
                Category.organization_id == organization_id,
                Category.is_active == True
            )
            result = await session.exec(statement)
            category = result.first()
            if category:
                return category.id
        
        # Try to find partial matches
        for category_name in plaid_categories:
            if "food" in category_name.lower() or "restaurant" in category_name.lower():
                statement = select(Category).where(
                    Category.name.ilike("%food%"),
                    Category.organization_id == organization_id,
                    Category.is_active == True
                )
                result = await session.exec(statement)
                category = result.first()
                if category:
                    return category.id
        
        return None
    
    def _generate_transaction_hash(self, plaid_tx: Dict[str, Any]) -> str:
        """Generate hash for Plaid transaction to detect duplicates"""
        
        hash_data = {
            "account_id": plaid_tx["account_id"],
            "transaction_id": plaid_tx["transaction_id"],
            "amount": plaid_tx["amount"],
            "date": plaid_tx["date"],
            "name": plaid_tx["name"]
        }
        
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.md5(hash_string.encode()).hexdigest()


# Global Plaid service instance
plaid_service = PlaidService()


# Export functions and classes
__all__ = [
    "PlaidService",
    "PlaidClient",
    "plaid_service"
]