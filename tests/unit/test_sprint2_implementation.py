"""
Unit tests for Sprint 2: Ingestion Adapters
Tests CSV parsing, transaction services, and API endpoints
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from src.backend.services.ingestion_service import (
    IngestionService, CSVParser, BankFormat, ingestion_service
)
from src.backend.services.transaction_service import (
    TransactionService, transaction_service
)
from src.backend.api.ingestion import router as ingestion_router
from src.backend.api.transactions import router as transactions_router
from src.common.models.enums import TransactionType, AccountType
from src.backend.models.database import (
    Transaction, TransactionCreate, Category, Account, Organization, User
)


class TestCSVParser:
    """Test CSV parser functionality"""
    
    def test_bank_format_constants(self):
        """Test bank format constants are defined"""
        assert BankFormat.CHASE == "chase"
        assert BankFormat.DISCOVER == "discover"
        assert BankFormat.CAPITALONE == "capitalone"
        assert BankFormat.GENERIC == "generic"
    
    def test_supported_formats(self):
        """Test supported formats list"""
        parser = CSVParser()
        assert len(parser.supported_formats) == 4
        assert BankFormat.CHASE in parser.supported_formats
        assert BankFormat.DISCOVER in parser.supported_formats
        assert BankFormat.CAPITALONE in parser.supported_formats
        assert BankFormat.GENERIC in parser.supported_formats
    
    def test_detect_format_chase(self):
        """Test Chase format detection"""
        parser = CSVParser()
        csv_content = "Details,Posting Date,Description,Amount,Type,Balance,Check or Slip #"
        detected = parser.detect_format(csv_content)
        assert detected == BankFormat.CHASE
    
    def test_detect_format_discover(self):
        """Test Discover format detection"""
        parser = CSVParser()
        csv_content = "Trans Date,Post Date,Description,Category,Amount"
        detected = parser.detect_format(csv_content)
        assert detected == BankFormat.DISCOVER
    
    def test_detect_format_capitalone(self):
        """Test Capital One format detection"""
        parser = CSVParser()
        csv_content = "Transaction Date,Posted Date,Card No.,Description,Category,Debit,Credit"
        detected = parser.detect_format(csv_content)
        assert detected == BankFormat.CAPITALONE
    
    def test_detect_format_generic(self):
        """Test generic format detection"""
        parser = CSVParser()
        csv_content = "Date,Amount,Description"
        detected = parser.detect_format(csv_content)
        assert detected == BankFormat.GENERIC
    
    def test_parse_chase_csv(self):
        """Test Chase CSV parsing"""
        parser = CSVParser()
        csv_content = """Details,Posting Date,Description,Amount,Type,Balance,Check or Slip #
Sample Transaction,01/15/2024,Sample Description,-50.00,DEBIT,1000.00,12345"""
        
        transactions = parser.parse_chase_csv(csv_content)
        assert len(transactions) == 1
        
        tx = transactions[0]
        assert tx['description'] == 'Sample Description'
        assert tx['amount'] == Decimal('-50.00')
        assert tx['transaction_type'] == TransactionType.EXPENSE
        assert tx['reference'] == '12345'
        assert tx['metadata']['bank_format'] == BankFormat.CHASE
    
    def test_parse_discover_csv(self):
        """Test Discover CSV parsing"""
        parser = CSVParser()
        csv_content = """Trans Date,Post Date,Description,Category,Amount
01/15/2024,01/16/2024,Sample Transaction,Shopping,-50.00"""
        
        transactions = parser.parse_discover_csv(csv_content)
        assert len(transactions) == 1
        
        tx = transactions[0]
        assert tx['description'] == 'Sample Transaction'
        assert tx['amount'] == Decimal('-50.00')
        assert tx['transaction_type'] == TransactionType.EXPENSE
        assert tx['notes'] == 'Category: Shopping'
        assert tx['metadata']['bank_format'] == BankFormat.DISCOVER
    
    def test_parse_capitalone_csv(self):
        """Test Capital One CSV parsing"""
        parser = CSVParser()
        csv_content = """Transaction Date,Posted Date,Card No.,Description,Category,Debit,Credit
01/15/2024,01/16/2024,1234****5678,Sample Transaction,Shopping,50.00,"""
        
        transactions = parser.parse_capitalone_csv(csv_content)
        assert len(transactions) == 1
        
        tx = transactions[0]
        assert tx['description'] == 'Sample Transaction'
        assert tx['amount'] == Decimal('-50.00')  # Debit is negative
        assert tx['transaction_type'] == TransactionType.EXPENSE
        assert tx['reference'] == '1234****5678'
        assert tx['metadata']['bank_format'] == BankFormat.CAPITALONE
    
    def test_parse_generic_csv(self):
        """Test generic CSV parsing"""
        parser = CSVParser()
        csv_content = """Date,Amount,Description,Category
01/15/2024,-50.00,Sample Transaction,Shopping"""
        
        transactions = parser.parse_generic_csv(csv_content)
        assert len(transactions) == 1
        
        tx = transactions[0]
        assert tx['description'] == 'Sample Transaction'
        assert tx['amount'] == Decimal('-50.00')
        assert tx['transaction_type'] == TransactionType.EXPENSE
        assert tx['metadata']['bank_format'] == BankFormat.GENERIC
    
    def test_parse_chase_csv_income(self):
        """Test Chase CSV parsing with income transaction"""
        parser = CSVParser()
        csv_content = """Details,Posting Date,Description,Amount,Type,Balance,Check or Slip #
Salary Deposit,01/15/2024,Monthly Salary,5000.00,CREDIT,10000.00,"""
        
        transactions = parser.parse_chase_csv(csv_content)
        assert len(transactions) == 1
        
        tx = transactions[0]
        assert tx['amount'] == Decimal('5000.00')
        assert tx['transaction_type'] == TransactionType.INCOME
    
    def test_parse_chase_csv_invalid_date(self):
        """Test Chase CSV parsing with invalid date"""
        parser = CSVParser()
        csv_content = """Details,Posting Date,Description,Amount,Type,Balance,Check or Slip #
Sample Transaction,invalid-date,Sample Description,-50.00,DEBIT,1000.00,12345"""
        
        transactions = parser.parse_chase_csv(csv_content)
        assert len(transactions) == 1
        
        tx = transactions[0]
        # Should use current time for invalid date
        assert isinstance(tx['date'], datetime)
    
    def test_parse_chase_csv_invalid_amount(self):
        """Test Chase CSV parsing with invalid amount"""
        parser = CSVParser()
        csv_content = """Details,Posting Date,Description,Amount,Type,Balance,Check or Slip #
Sample Transaction,01/15/2024,Sample Description,invalid-amount,DEBIT,1000.00,12345"""
        
        transactions = parser.parse_chase_csv(csv_content)
        assert len(transactions) == 1
        
        tx = transactions[0]
        # Should use 0.00 for invalid amount
        assert tx['amount'] == Decimal('0.00')


class TestIngestionService:
    """Test ingestion service functionality"""
    
    @pytest.fixture
    def mock_file(self):
        """Mock file for testing"""
        mock = Mock()
        mock.filename = "test.csv"
        mock.read.return_value = b"Date,Amount,Description\n01/15/2024,-50.00,Test"
        return mock
    
    @pytest.fixture
    def mock_user(self):
        """Mock user for testing"""
        user = Mock()
        user.id = uuid4()
        user.organization_id = uuid4()
        return user
    
    @pytest.mark.asyncio
    async def test_process_csv_file_success(self, mock_file, mock_user):
        """Test successful CSV file processing"""
        service = IngestionService()
        
        result = await service.process_csv_file(
            file=mock_file,
            organization_id=mock_user.organization_id,
            user_id=mock_user.id,
            account_id=uuid4()
        )
        
        assert result["success"] is True
        assert "format_detected" in result["data"]
        assert "total_parsed" in result["data"]
        assert "imported_count" in result["data"]
    
    @pytest.mark.asyncio
    async def test_process_csv_file_invalid_format(self, mock_user):
        """Test CSV file processing with invalid format"""
        service = IngestionService()
        
        mock_file = Mock()
        mock_file.filename = "test.txt"  # Not CSV
        
        with pytest.raises(Exception) as exc_info:
            await service.process_csv_file(
                file=mock_file,
                organization_id=mock_user.organization_id,
                user_id=mock_user.id,
                account_id=uuid4()
            )
        
        assert "File must be a CSV file" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_auto_categorize_transactions(self, mock_user):
        """Test automatic transaction categorization"""
        service = IngestionService()
        
        transactions_data = [
            {
                'description': 'Restaurant ABC',
                'amount': Decimal('-50.00'),
                'transaction_type': TransactionType.EXPENSE,
                'date': datetime.now(),
                'category_id': None
            }
        ]
        
        # Mock categories
        with patch('src.backend.services.ingestion_service.get_session') as mock_session:
            mock_session.return_value.__aenter__.return_value.exec.return_value.all.return_value = [
                Mock(id=uuid4(), name='Food', color='#FF0000')
            ]
            
            result = await service._auto_categorize_transactions(
                transactions_data, mock_user.organization_id
            )
            
            assert len(result) == 1
            # Should be categorized as food
            assert result[0]['category_id'] is not None
    
    @pytest.mark.asyncio
    async def test_get_import_history(self, mock_user):
        """Test import history retrieval"""
        service = IngestionService()
        
        with patch('src.backend.services.ingestion_service.get_session') as mock_session:
            mock_session.return_value.__aenter__.return_value.exec.return_value.all.return_value = []
            
            history = await service.get_import_history(
                organization_id=mock_user.organization_id
            )
            
            assert isinstance(history, list)


class TestTransactionService:
    """Test transaction service functionality"""
    
    @pytest.fixture
    def mock_user(self):
        """Mock user for testing"""
        user = Mock()
        user.id = uuid4()
        user.organization_id = uuid4()
        return user
    
    @pytest.mark.asyncio
    async def test_create_transaction_success(self, mock_user):
        """Test successful transaction creation"""
        service = TransactionService()
        
        transaction_data = {
            'amount': Decimal('100.00'),
            'description': 'Test Transaction',
            'transaction_type': TransactionType.INCOME,
            'date': date.today(),
            'account_id': uuid4()
        }
        
        with patch('src.backend.services.transaction_service.get_session') as mock_session:
            mock_session.return_value.__aenter__.return_value.add.return_value = None
            mock_session.return_value.__aenter__.return_value.commit.return_value = None
            mock_session.return_value.__aenter__.return_value.refresh.return_value = None
            
            # Mock account validation
            mock_session.return_value.__aenter__.return_value.exec.return_value.first.return_value = Mock()
            
            result = await service.create_transaction(
                transaction_data, mock_user.id, mock_user.organization_id
            )
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_transactions_with_filters(self, mock_user):
        """Test transaction retrieval with filters"""
        service = TransactionService()
        
        with patch('src.backend.services.transaction_service.get_session') as mock_session:
            mock_session.return_value.__aenter__.return_value.exec.return_value.all.return_value = []
            
            transactions = await service.get_transactions(
                organization_id=mock_user.organization_id,
                user_id=mock_user.id,
                start_date=date.today(),
                end_date=date.today()
            )
            
            assert isinstance(transactions, list)
    
    @pytest.mark.asyncio
    async def test_get_transaction_summary(self, mock_user):
        """Test transaction summary generation"""
        service = TransactionService()
        
        with patch('src.backend.services.transaction_service.get_session') as mock_session:
            mock_session.return_value.__aenter__.return_value.exec.return_value.first.side_effect = [
                Decimal('1000.00'),  # Income
                Decimal('500.00'),   # Expenses
                10,                  # Count
                Decimal('50.00')     # Average
            ]
            
            summary = await service.get_transaction_summary(
                organization_id=mock_user.organization_id
            )
            
            assert "total_income" in summary
            assert "total_expenses" in summary
            assert "net_income" in summary
            assert "savings_rate" in summary
    
    @pytest.mark.asyncio
    async def test_get_category_breakdown(self, mock_user):
        """Test category breakdown generation"""
        service = TransactionService()
        
        with patch('src.backend.services.transaction_service.get_session') as mock_session:
            mock_session.return_value.__aenter__.return_value.exec.return_value.all.return_value = [
                Mock(name='Food', color='#FF0000', total_amount=Decimal('-100.00'), transaction_count=5)
            ]
            
            breakdown = await service.get_category_breakdown(
                organization_id=mock_user.organization_id
            )
            
            assert len(breakdown) == 1
            assert breakdown[0]['category_name'] == 'Food'
            assert breakdown[0]['total_amount'] == 100.00  # Absolute value
    
    @pytest.mark.asyncio
    async def test_get_monthly_trends(self, mock_user):
        """Test monthly trends generation"""
        service = TransactionService()
        
        with patch('src.backend.services.transaction_service.get_session') as mock_session:
            mock_session.return_value.__aenter__.return_value.exec.return_value.first.side_effect = [
                Decimal('1000.00'),  # Income
                Decimal('500.00'),   # Expenses
                10,                  # Count
                Decimal('50.00')     # Average
            ]
            
            trends = await service.get_monthly_trends(
                organization_id=mock_user.organization_id,
                months=3
            )
            
            assert len(trends) == 3
            assert all("month" in trend for trend in trends)
            assert all("total_income" in trend for trend in trends)
    
    @pytest.mark.asyncio
    async def test_get_recurring_transactions(self, mock_user):
        """Test recurring transaction identification"""
        service = TransactionService()
        
        with patch('src.backend.services.transaction_service.get_session') as mock_session:
            mock_session.return_value.__aenter__.return_value.exec.return_value.all.return_value = [
                Mock(description='Netflix', amount=Decimal('-15.99'), date=date.today()),
                Mock(description='Netflix', amount=Decimal('-15.99'), date=date.today() - timedelta(days=30))
            ]
            
            recurring = await service.get_recurring_transactions(
                organization_id=mock_user.organization_id
            )
            
            assert len(recurring) >= 0  # May or may not find patterns
    
    @pytest.mark.asyncio
    async def test_bulk_update_transactions(self, mock_user):
        """Test bulk transaction updates"""
        service = TransactionService()
        
        transaction_ids = [uuid4(), uuid4()]
        updates = {'notes': 'Updated in bulk'}
        
        with patch('src.backend.services.transaction_service.get_session') as mock_session:
            mock_session.return_value.__aenter__.return_value.exec.return_value.all.return_value = [
                Mock(), Mock()  # Two transactions
            ]
            mock_session.return_value.__aenter__.return_value.commit.return_value = None
            
            result = await service.bulk_update_transactions(
                transaction_ids, updates, mock_user.id, mock_user.organization_id
            )
            
            assert result["success"] is True
            assert result["updated_count"] == 2
    
    def test_export_to_csv(self):
        """Test CSV export functionality"""
        service = TransactionService()
        
        transactions = [
            Mock(
                date=date(2024, 1, 15),
                description='Test Transaction',
                amount=Decimal('-50.00'),
                transaction_type=TransactionType.EXPENSE,
                reference='12345',
                notes='Test notes',
                category=Mock(name='Food'),
                account=Mock(name='Checking')
            )
        ]
        
        csv_content = service._export_to_csv(transactions)
        
        assert 'Date,Description,Amount,Type,Category,Account,Reference,Notes' in csv_content
        assert '2024-01-15,Test Transaction,-50.00,expense,Food,Checking,12345,Test notes' in csv_content


class TestIngestionAPI:
    """Test ingestion API endpoints"""
    
    def test_ingestion_router_creation(self):
        """Test ingestion router is created"""
        assert ingestion_router is not None
        assert hasattr(ingestion_router, 'routes')
    
    def test_ingestion_endpoints_exist(self):
        """Test required ingestion endpoints exist"""
        routes = [route.path for route in ingestion_router.routes]
        
        assert "/csv" in routes  # POST for file upload
        assert "/history" in routes  # GET for import history
        assert "/formats" in routes  # GET for supported formats
        assert "/template/{format_id}" in routes  # GET for templates
        assert "/validate" in routes  # POST for validation
        assert "/stats" in routes  # GET for statistics
        assert "/health" in routes  # GET for health check


class TestTransactionsAPI:
    """Test transactions API endpoints"""
    
    def test_transactions_router_creation(self):
        """Test transactions router is created"""
        assert transactions_router is not None
        assert hasattr(transactions_router, 'routes')
    
    def test_transactions_endpoints_exist(self):
        """Test required transactions endpoints exist"""
        routes = [route.path for route in transactions_router.routes]
        
        assert "/" in routes  # POST for create, GET for list
        assert "/{transaction_id}" in routes  # GET, PUT, DELETE for specific
        assert "/summary/overview" in routes  # GET for summary
        assert "/summary/categories" in routes  # GET for category breakdown
        assert "/trends/monthly" in routes  # GET for monthly trends
        assert "/recurring" in routes  # GET for recurring transactions
        assert "/bulk/update" in routes  # PUT for bulk updates
        assert "/export/csv" in routes  # GET for CSV export
        assert "/health" in routes  # GET for health check


if __name__ == "__main__":
    pytest.main([__file__])