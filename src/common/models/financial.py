"""
Financial models for Financial Analytics Platform
Financial data structures and calculations
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from uuid import UUID

from .enums import Currency, TransactionType, AccountType


class Amount(BaseModel):
    """Financial amount with currency"""
    
    value: Decimal = Field(..., description="Amount value")
    currency: Currency = Field(default=Currency.USD, description="Currency code")
    
    @validator('value')
    def validate_value(cls, v):
        if v < 0:
            raise ValueError('Amount cannot be negative')
        return v
    
    def __add__(self, other: 'Amount') -> 'Amount':
        if self.currency != other.currency:
            raise ValueError('Cannot add amounts with different currencies')
        return Amount(value=self.value + other.value, currency=self.currency)
    
    def __sub__(self, other: 'Amount') -> 'Amount':
        if self.currency != other.currency:
            raise ValueError('Cannot subtract amounts with different currencies')
        return Amount(value=self.value - other.value, currency=self.currency)
    
    def __mul__(self, multiplier: Decimal) -> 'Amount':
        return Amount(value=self.value * multiplier, currency=self.currency)
    
    def __truediv__(self, divisor: Decimal) -> 'Amount':
        if divisor == 0:
            raise ValueError('Cannot divide by zero')
        return Amount(value=self.value / divisor, currency=self.currency)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'value': float(self.value),
            'currency': self.currency.value
        }


class DateRange(BaseModel):
    """Date range for filtering and analysis"""
    
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('End date must be after start date')
        return v
    
    def days(self) -> int:
        """Calculate number of days in range"""
        return (self.end_date - self.start_date).days
    
    def months(self) -> int:
        """Calculate number of months in range"""
        return (self.end_date.year - self.start_date.year) * 12 + (self.end_date.month - self.start_date.month)
    
    def years(self) -> int:
        """Calculate number of years in range"""
        return self.end_date.year - self.start_date.year
    
    def contains(self, check_date: date) -> bool:
        """Check if a date is within the range"""
        return self.start_date <= check_date <= self.end_date
    
    def overlaps(self, other: 'DateRange') -> bool:
        """Check if this range overlaps with another"""
        return not (self.end_date < other.start_date or other.end_date < self.start_date)


class Category(BaseModel):
    """Transaction category"""
    
    id: Optional[UUID] = Field(default=None, description="Category ID")
    name: str = Field(..., description="Category name")
    parent_id: Optional[UUID] = Field(default=None, description="Parent category ID")
    description: Optional[str] = Field(default=None, description="Category description")
    color: Optional[str] = Field(default=None, description="Category color (hex)")
    icon: Optional[str] = Field(default=None, description="Category icon")
    is_active: bool = Field(default=True, description="Whether category is active")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        from_attributes = True


class Budget(BaseModel):
    """Budget for a category or time period"""
    
    id: Optional[UUID] = Field(default=None, description="Budget ID")
    org_id: UUID = Field(..., description="Organization ID")
    category_id: Optional[UUID] = Field(default=None, description="Category ID")
    name: str = Field(..., description="Budget name")
    amount: Amount = Field(..., description="Budget amount")
    period: str = Field(default="monthly", description="Budget period")
    start_date: date = Field(..., description="Budget start date")
    end_date: Optional[date] = Field(default=None, description="Budget end date")
    is_active: bool = Field(default=True, description="Whether budget is active")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        from_attributes = True


class ExchangeRate(BaseModel):
    """Currency exchange rate"""
    
    from_currency: Currency = Field(..., description="Source currency")
    to_currency: Currency = Field(..., description="Target currency")
    rate: Decimal = Field(..., description="Exchange rate")
    date: date = Field(..., description="Rate date")
    source: str = Field(..., description="Rate source")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Rate timestamp")
    
    @validator('rate')
    def validate_rate(cls, v):
        if v <= 0:
            raise ValueError('Exchange rate must be positive')
        return v
    
    def convert(self, amount: Amount) -> Amount:
        """Convert an amount using this exchange rate"""
        if amount.currency != self.from_currency:
            raise ValueError(f'Amount currency {amount.currency} does not match from_currency {self.from_currency}')
        
        converted_value = amount.value * self.rate
        return Amount(value=converted_value, currency=self.to_currency)


class FinancialMetrics(BaseModel):
    """Financial metrics and KPIs"""
    
    total_income: Amount = Field(..., description="Total income")
    total_expenses: Amount = Field(..., description="Total expenses")
    net_income: Amount = Field(..., description="Net income (income - expenses)")
    savings_rate: Decimal = Field(..., description="Savings rate as percentage")
    expense_ratio: Decimal = Field(..., description="Expense to income ratio")
    cash_flow: Amount = Field(..., description="Cash flow")
    net_worth: Amount = Field(..., description="Net worth")
    
    @validator('savings_rate')
    def validate_savings_rate(cls, v):
        if not -100 <= v <= 100:
            raise ValueError('Savings rate must be between -100 and 100')
        return v
    
    @validator('expense_ratio')
    def validate_expense_ratio(cls, v):
        if v < 0:
            raise ValueError('Expense ratio cannot be negative')
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_income': self.total_income.to_dict(),
            'total_expenses': self.total_expenses.to_dict(),
            'net_income': self.net_income.to_dict(),
            'savings_rate': float(self.savings_rate),
            'expense_ratio': float(self.expense_ratio),
            'cash_flow': self.cash_flow.to_dict(),
            'net_worth': self.net_worth.to_dict()
        }


class TransactionSummary(BaseModel):
    """Transaction summary for reporting"""
    
    count: int = Field(..., description="Number of transactions")
    total_amount: Amount = Field(..., description="Total transaction amount")
    average_amount: Amount = Field(..., description="Average transaction amount")
    min_amount: Amount = Field(..., description="Minimum transaction amount")
    max_amount: Amount = Field(..., description="Maximum transaction amount")
    categories: Dict[str, int] = Field(default_factory=dict, description="Transaction count by category")
    daily_average: Amount = Field(..., description="Daily average transaction amount")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'count': self.count,
            'total_amount': self.total_amount.to_dict(),
            'average_amount': self.average_amount.to_dict(),
            'min_amount': self.min_amount.to_dict(),
            'max_amount': self.max_amount.to_dict(),
            'categories': self.categories,
            'daily_average': self.daily_average.to_dict()
        }


class RecurringTransaction(BaseModel):
    """Recurring transaction pattern"""
    
    id: Optional[UUID] = Field(default=None, description="Recurring transaction ID")
    org_id: UUID = Field(..., description="Organization ID")
    account_id: UUID = Field(..., description="Account ID")
    description: str = Field(..., description="Transaction description")
    amount: Amount = Field(..., description="Transaction amount")
    category: Optional[str] = Field(default=None, description="Transaction category")
    frequency: str = Field(..., description="Recurrence frequency")
    interval: int = Field(default=1, description="Recurrence interval")
    start_date: date = Field(..., description="Recurrence start date")
    end_date: Optional[date] = Field(default=None, description="Recurrence end date")
    last_occurrence: Optional[date] = Field(default=None, description="Last occurrence date")
    next_occurrence: Optional[date] = Field(default=None, description="Next occurrence date")
    is_active: bool = Field(default=True, description="Whether recurring transaction is active")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        from_attributes = True


class Portfolio(BaseModel):
    """Investment portfolio"""
    
    id: Optional[UUID] = Field(default=None, description="Portfolio ID")
    org_id: UUID = Field(..., description="Organization ID")
    name: str = Field(..., description="Portfolio name")
    description: Optional[str] = Field(default=None, description="Portfolio description")
    total_value: Amount = Field(..., description="Total portfolio value")
    cash_balance: Amount = Field(..., description="Cash balance")
    invested_amount: Amount = Field(..., description="Invested amount")
    unrealized_gain_loss: Amount = Field(..., description="Unrealized gain/loss")
    realized_gain_loss: Amount = Field(..., description="Realized gain/loss")
    total_return: Decimal = Field(..., description="Total return percentage")
    risk_score: Optional[Decimal] = Field(default=None, description="Risk score")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    class Config:
        from_attributes = True
    
    @property
    def return_on_investment(self) -> Decimal:
        """Calculate return on investment"""
        if self.invested_amount.value == 0:
            return Decimal('0')
        return (self.total_value.value - self.invested_amount.value) / self.invested_amount.value * 100