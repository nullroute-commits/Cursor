"""
Unit tests for common models
Testing financial models and base classes
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from uuid import uuid4

from src.common.models.base import BaseModel, BaseResponse, PaginatedResponse
from src.common.models.enums import Role, Currency, TransactionType
from src.common.models.financial import Amount, DateRange, Category, FinancialMetrics


class TestBaseModel:
    """Test base model functionality"""
    
    def test_base_model_creation(self):
        """Test base model can be created"""
        model = BaseModel()
        assert model is not None


class TestBaseResponse:
    """Test base response functionality"""
    
    def test_base_response_defaults(self):
        """Test base response default values"""
        response = BaseResponse()
        assert response.success is True
        assert response.message is None
        assert response.timestamp is not None
    
    def test_base_response_custom_values(self):
        """Test base response with custom values"""
        response = BaseResponse(
            success=False,
            message="Test error",
            timestamp=datetime.utcnow()
        )
        assert response.success is False
        assert response.message == "Test error"


class TestAmount:
    """Test Amount model functionality"""
    
    def test_amount_creation(self):
        """Test amount creation"""
        amount = Amount(value=Decimal("100.50"), currency=Currency.USD)
        assert amount.value == Decimal("100.50")
        assert amount.currency == Currency.USD
    
    def test_amount_default_currency(self):
        """Test amount with default currency"""
        amount = Amount(value=Decimal("50.00"))
        assert amount.currency == Currency.USD
    
    def test_amount_validation_negative(self):
        """Test amount validation for negative values"""
        with pytest.raises(ValueError, match="Amount cannot be negative"):
            Amount(value=Decimal("-10.00"))
    
    def test_amount_addition(self):
        """Test amount addition"""
        amount1 = Amount(value=Decimal("100.00"), currency=Currency.USD)
        amount2 = Amount(value=Decimal("50.00"), currency=Currency.USD)
        result = amount1 + amount2
        assert result.value == Decimal("150.00")
        assert result.currency == Currency.USD
    
    def test_amount_addition_different_currencies(self):
        """Test amount addition with different currencies fails"""
        amount1 = Amount(value=Decimal("100.00"), currency=Currency.USD)
        amount2 = Amount(value=Decimal("50.00"), currency=Currency.EUR)
        with pytest.raises(ValueError, match="Cannot add amounts with different currencies"):
            amount1 + amount2
    
    def test_amount_multiplication(self):
        """Test amount multiplication"""
        amount = Amount(value=Decimal("100.00"), currency=Currency.USD)
        result = amount * Decimal("2.5")
        assert result.value == Decimal("250.00")
        assert result.currency == Currency.USD
    
    def test_amount_division(self):
        """Test amount division"""
        amount = Amount(value=Decimal("100.00"), currency=Currency.USD)
        result = amount / Decimal("4")
        assert result.value == Decimal("25.00")
        assert result.currency == Currency.USD
    
    def test_amount_division_by_zero(self):
        """Test amount division by zero fails"""
        amount = Amount(value=Decimal("100.00"), currency=Currency.USD)
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            amount / Decimal("0")
    
    def test_amount_to_dict(self):
        """Test amount serialization to dict"""
        amount = Amount(value=Decimal("100.50"), currency=Currency.USD)
        result = amount.to_dict()
        assert result["value"] == 100.50
        assert result["currency"] == "USD"


class TestDateRange:
    """Test DateRange model functionality"""
    
    def test_date_range_creation(self):
        """Test date range creation"""
        start = date(2024, 1, 1)
        end = date(2024, 12, 31)
        date_range = DateRange(start_date=start, end_date=end)
        assert date_range.start_date == start
        assert date_range.end_date == end
    
    def test_date_range_validation_invalid_range(self):
        """Test date range validation for invalid range"""
        start = date(2024, 12, 31)
        end = date(2024, 1, 1)
        with pytest.raises(ValueError, match="End date must be after start date"):
            DateRange(start_date=start, end_date=end)
    
    def test_date_range_days_calculation(self):
        """Test date range days calculation"""
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)
        date_range = DateRange(start_date=start, end_date=end)
        assert date_range.days() == 30
    
    def test_date_range_months_calculation(self):
        """Test date range months calculation"""
        start = date(2024, 1, 1)
        end = date(2024, 3, 1)
        date_range = DateRange(start_date=start, end_date=end)
        assert date_range.months() == 2
    
    def test_date_range_years_calculation(self):
        """Test date range years calculation"""
        start = date(2020, 1, 1)
        end = date(2024, 1, 1)
        date_range = DateRange(start_date=start, end_date=end)
        assert date_range.years() == 4
    
    def test_date_range_contains(self):
        """Test date range contains functionality"""
        start = date(2024, 1, 1)
        end = date(2024, 12, 31)
        date_range = DateRange(start_date=start, end_date=end)
        
        assert date_range.contains(date(2024, 6, 15)) is True
        assert date_range.contains(date(2023, 12, 31)) is False
        assert date_range.contains(date(2025, 1, 1)) is False
    
    def test_date_range_overlaps(self):
        """Test date range overlap functionality"""
        range1 = DateRange(start_date=date(2024, 1, 1), end_date=date(2024, 6, 30))
        range2 = DateRange(start_date=date(2024, 4, 1), end_date=date(2024, 12, 31))
        range3 = DateRange(start_date=date(2024, 7, 1), end_date=date(2024, 12, 31))
        
        assert range1.overlaps(range2) is True
        assert range1.overlaps(range3) is False


class TestCategory:
    """Test Category model functionality"""
    
    def test_category_creation(self):
        """Test category creation"""
        category = Category(
            name="Groceries",
            description="Food and household items",
            color="#FF0000"
        )
        assert category.name == "Groceries"
        assert category.description == "Food and household items"
        assert category.color == "#FF0000"
        assert category.is_active is True
    
    def test_category_with_parent(self):
        """Test category with parent ID"""
        parent_id = uuid4()
        category = Category(
            name="Fresh Produce",
            parent_id=parent_id,
            description="Fresh fruits and vegetables"
        )
        assert category.parent_id == parent_id


class TestFinancialMetrics:
    """Test FinancialMetrics model functionality"""
    
    def test_financial_metrics_creation(self):
        """Test financial metrics creation"""
        metrics = FinancialMetrics(
            total_income=Amount(value=Decimal("5000.00"), currency=Currency.USD),
            total_expenses=Amount(value=Decimal("3000.00"), currency=Currency.USD),
            net_income=Amount(value=Decimal("2000.00"), currency=Currency.USD),
            savings_rate=Decimal("40.0"),
            expense_ratio=Decimal("60.0"),
            cash_flow=Amount(value=Decimal("2000.00"), currency=Currency.USD),
            net_worth=Amount(value=Decimal("10000.00"), currency=Currency.USD)
        )
        assert metrics.savings_rate == Decimal("40.0")
        assert metrics.expense_ratio == Decimal("60.0")
    
    def test_financial_metrics_validation_savings_rate(self):
        """Test financial metrics savings rate validation"""
        with pytest.raises(ValueError, match="Savings rate must be between -100 and 100"):
            FinancialMetrics(
                total_income=Amount(value=Decimal("1000.00"), currency=Currency.USD),
                total_expenses=Amount(value=Decimal("500.00"), currency=Currency.USD),
                net_income=Amount(value=Decimal("500.00"), currency=Currency.USD),
                savings_rate=Decimal("150.0"),  # Invalid
                expense_ratio=Decimal("50.0"),
                cash_flow=Amount(value=Decimal("500.00"), currency=Currency.USD),
                net_worth=Amount(value=Decimal("5000.00"), currency=Currency.USD)
            )
    
    def test_financial_metrics_validation_expense_ratio(self):
        """Test financial metrics expense ratio validation"""
        with pytest.raises(ValueError, match="Expense ratio cannot be negative"):
            FinancialMetrics(
                total_income=Amount(value=Decimal("1000.00"), currency=Currency.USD),
                total_expenses=Amount(value=Decimal("500.00"), currency=Currency.USD),
                net_income=Amount(value=Decimal("500.00"), currency=Currency.USD),
                savings_rate=Decimal("50.0"),
                expense_ratio=Decimal("-10.0"),  # Invalid
                cash_flow=Amount(value=Decimal("500.00"), currency=Currency.USD),
                net_worth=Amount(value=Decimal("5000.00"), currency=Currency.USD)
            )
    
    def test_financial_metrics_to_dict(self):
        """Test financial metrics serialization"""
        metrics = FinancialMetrics(
            total_income=Amount(value=Decimal("5000.00"), currency=Currency.USD),
            total_expenses=Amount(value=Decimal("3000.00"), currency=Currency.USD),
            net_income=Amount(value=Decimal("2000.00"), currency=Currency.USD),
            savings_rate=Decimal("40.0"),
            expense_ratio=Decimal("60.0"),
            cash_flow=Amount(value=Decimal("2000.00"), currency=Currency.USD),
            net_worth=Amount(value=Decimal("10000.00"), currency=Currency.USD)
        )
        result = metrics.to_dict()
        assert result["savings_rate"] == 40.0
        assert result["expense_ratio"] == 60.0
        assert "total_income" in result
        assert "total_expenses" in result


class TestEnums:
    """Test enum functionality"""
    
    def test_role_enum(self):
        """Test role enum values"""
        assert Role.ADMIN == "admin"
        assert Role.ANALYST == "analyst"
        assert Role.VIEWER == "viewer"
    
    def test_currency_enum(self):
        """Test currency enum values"""
        assert Currency.USD == "USD"
        assert Currency.EUR == "EUR"
        assert Currency.GBP == "GBP"
    
    def test_transaction_type_enum(self):
        """Test transaction type enum values"""
        assert TransactionType.DEBIT == "debit"
        assert TransactionType.CREDIT == "credit"
        assert TransactionType.TRANSFER == "transfer"


if __name__ == "__main__":
    pytest.main([__file__])