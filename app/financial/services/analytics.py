"""
Financial Analytics Engine

Provides comprehensive financial analysis including:
- Financial ratios and metrics
- Trend analysis and forecasting
- Budget variance analysis
- Cash flow analysis
- Performance indicators
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime, timedelta
from django.db.models import Sum, Avg, Count, Q, F
from django.db.models.functions import TruncMonth, TruncYear, ExtractYear, ExtractMonth
from django.utils import timezone
from ..models import Transaction, Account, Category, Budget, BudgetCategory
from app.core.audit import audit_logger

logger = logging.getLogger(__name__)


class FinancialCalculator:
    """Core financial calculations and metrics"""
    
    def __init__(self, user, start_date: Optional[date] = None, end_date: Optional[date] = None):
        self.user = user
        self.start_date = start_date or (timezone.now().date() - timedelta(days=365))
        self.end_date = end_date or timezone.now().date()
        self._transactions = None
        self._accounts = None
    
    @property
    def transactions(self):
        """Get transactions for the date range"""
        if self._transactions is None:
            self._transactions = Transaction.objects.filter(
                account__user=self.user,
                transaction_date__range=[self.start_date, self.end_date]
            ).select_related('account', 'category')
        return self._transactions
    
    @property
    def accounts(self):
        """Get user accounts"""
        if self._accounts is None:
            self._accounts = Account.objects.filter(user=self.user, is_active=True)
        return self._accounts
    
    def calculate_total_income(self) -> Decimal:
        """Calculate total income for the period"""
        return self.transactions.filter(
            transaction_type='income'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    def calculate_total_expenses(self) -> Decimal:
        """Calculate total expenses for the period"""
        return self.transactions.filter(
            transaction_type='expense'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    def calculate_net_income(self) -> Decimal:
        """Calculate net income (income - expenses)"""
        return self.calculate_total_income() - self.calculate_total_expenses()
    
    def calculate_savings_rate(self) -> Decimal:
        """Calculate savings rate as percentage of income"""
        total_income = self.calculate_total_income()
        if total_income > 0:
            net_income = self.calculate_net_income()
            return (net_income / total_income * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return Decimal('0.00')
    
    def calculate_expense_ratio(self) -> Decimal:
        """Calculate expense ratio (expenses / income)"""
        total_income = self.calculate_total_income()
        if total_income > 0:
            total_expenses = self.calculate_total_expenses()
            return (total_expenses / total_income * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return Decimal('0.00')
    
    def calculate_average_monthly_expenses(self) -> Decimal:
        """Calculate average monthly expenses"""
        months = self._calculate_period_months()
        if months > 0:
            total_expenses = self.calculate_total_expenses()
            return (total_expenses / months).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return Decimal('0.00')
    
    def calculate_average_monthly_income(self) -> Decimal:
        """Calculate average monthly income"""
        months = self._calculate_period_months()
        if months > 0:
            total_income = self.calculate_total_income()
            return (total_income / months).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return Decimal('0.00')
    
    def _calculate_period_months(self) -> int:
        """Calculate the number of months in the period"""
        start = self.start_date
        end = self.end_date
        return (end.year - start.year) * 12 + (end.month - start.month) + 1


class TrendAnalyzer:
    """Analyze financial trends over time"""
    
    def __init__(self, user, start_date: Optional[date] = None, end_date: Optional[date] = None):
        self.user = user
        self.start_date = start_date or (timezone.now().date() - timedelta(days=365))
        self.end_date = end_date or timezone.now().date()
    
    def get_monthly_trends(self) -> List[Dict[str, Any]]:
        """Get monthly income and expense trends"""
        monthly_data = Transaction.objects.filter(
            account__user=self.user,
            transaction_date__range=[self.start_date, self.end_date]
        ).annotate(
            month=TruncMonth('transaction_date')
        ).values('month').annotate(
            income=Sum('amount', filter=Q(transaction_type='income')),
            expenses=Sum('amount', filter=Q(transaction_type='expense'))
        ).order_by('month')
        
        trends = []
        for data in monthly_data:
            trends.append({
                'month': data['month'].strftime('%Y-%m'),
                'income': data['income'] or Decimal('0.00'),
                'expenses': abs(data['expenses'] or Decimal('0.00')),
                'net_income': (data['income'] or Decimal('0.00')) + (data['expenses'] or Decimal('0.00'))
            })
        
        return trends
    
    def get_category_trends(self) -> List[Dict[str, Any]]:
        """Get spending trends by category"""
        category_data = Transaction.objects.filter(
            account__user=self.user,
            transaction_date__range=[self.start_date, self.end_date],
            transaction_type='expense'
        ).values('category__name').annotate(
            total_spent=Sum('amount'),
            transaction_count=Count('id')
        ).order_by('-total_spent')
        
        trends = []
        for data in category_data:
            trends.append({
                'category': data['category__name'] or 'Uncategorized',
                'total_spent': abs(data['total_spent']),
                'transaction_count': data['transaction_count'],
                'average_transaction': abs(data['total_spent'] / data['transaction_count'])
            })
        
        return trends
    
    def get_spending_patterns(self) -> Dict[str, Any]:
        """Analyze spending patterns and identify trends"""
        # Get daily spending patterns
        daily_patterns = Transaction.objects.filter(
            account__user=self.user,
            transaction_date__range=[self.start_date, self.end_date],
            transaction_type='expense'
        ).extra(
            select={'day_of_week': "EXTRACT(dow FROM transaction_date)"}
        ).values('day_of_week').annotate(
            total_spent=Sum('amount'),
            transaction_count=Count('id')
        ).order_by('day_of_week')
        
        # Get monthly spending patterns
        monthly_patterns = Transaction.objects.filter(
            account__user=self.user,
            transaction_date__range=[self.start_date, self.end_date],
            transaction_type='expense'
        ).extra(
            select={'month': "EXTRACT(month FROM transaction_date)"}
        ).values('month').annotate(
            total_spent=Sum('amount'),
            transaction_count=Count('id')
        ).order_by('month')
        
        return {
            'daily_patterns': list(daily_patterns),
            'monthly_patterns': list(monthly_patterns)
        }
    
    def forecast_expenses(self, months_ahead: int = 3) -> List[Dict[str, Any]]:
        """Forecast future expenses based on historical data"""
        # Calculate average monthly expenses by category
        category_averages = Transaction.objects.filter(
            account__user=self.user,
            transaction_date__range=[self.start_date, self.end_date],
            transaction_type='expense'
        ).values('category__name').annotate(
            monthly_average=Avg('amount')
        )
        
        forecasts = []
        current_date = self.end_date
        
        for month in range(1, months_ahead + 1):
            forecast_date = current_date + timedelta(days=30 * month)
            month_forecast = {
                'month': forecast_date.strftime('%Y-%m'),
                'total_forecast': Decimal('0.00'),
                'category_forecasts': []
            }
            
            for category_avg in category_averages:
                category_name = category_avg['category__name'] or 'Uncategorized'
                monthly_avg = abs(category_avg['monthly_average'])
                
                month_forecast['category_forecasts'].append({
                    'category': category_name,
                    'forecasted_amount': monthly_avg
                })
                month_forecast['total_forecast'] += monthly_avg
            
            forecasts.append(month_forecast)
        
        return forecasts


class BudgetTracker:
    """Track budget performance and variances"""
    
    def __init__(self, user, budget: Optional[Budget] = None):
        self.user = user
        self.budget = budget
    
    def get_budget_performance(self) -> Dict[str, Any]:
        """Get overall budget performance"""
        if not self.budget:
            return {}
        
        # Get actual spending by category
        actual_spending = Transaction.objects.filter(
            account__user=self.user,
            transaction_date__range=[self.budget.start_date, self.budget.end_date],
            transaction_type='expense'
        ).values('category__name').annotate(
            actual_amount=Sum('amount')
        )
        
        # Get budget allocations
        budget_categories = BudgetCategory.objects.filter(budget=self.budget)
        
        performance = {
            'budget_name': self.budget.name,
            'period': f"{self.budget.start_date} to {self.budget.end_date}",
            'total_budget': self.budget.total_amount,
            'total_spent': Decimal('0.00'),
            'remaining_budget': self.budget.total_amount,
            'categories': []
        }
        
        # Calculate performance by category
        for budget_cat in budget_categories:
            category_name = budget_cat.category.name
            planned_amount = budget_cat.planned_amount
            
            # Find actual spending for this category
            actual_amount = next(
                (abs(item['actual_amount']) for item in actual_spending 
                 if item['category__name'] == category_name),
                Decimal('0.00')
            )
            
            variance = planned_amount - actual_amount
            variance_percentage = (variance / planned_amount * 100) if planned_amount > 0 else Decimal('0.00')
            
            performance['categories'].append({
                'category': category_name,
                'planned_amount': planned_amount,
                'actual_amount': actual_amount,
                'variance': variance,
                'variance_percentage': variance_percentage,
                'status': self._get_variance_status(variance_percentage)
            })
            
            performance['total_spent'] += actual_amount
        
        performance['remaining_budget'] = performance['total_budget'] - performance['total_spent']
        performance['overall_variance'] = performance['total_budget'] - performance['total_spent']
        performance['overall_variance_percentage'] = (
            performance['overall_variance'] / performance['total_budget'] * 100
        ) if performance['total_budget'] > 0 else Decimal('0.00')
        
        return performance
    
    def _get_variance_status(self, variance_percentage: Decimal) -> str:
        """Get status based on variance percentage"""
        if variance_percentage >= 10:
            return 'over_budget'
        elif variance_percentage <= -10:
            return 'under_budget'
        else:
            return 'on_track'
    
    def get_budget_alerts(self) -> List[Dict[str, Any]]:
        """Get budget alerts for significant variances"""
        if not self.budget:
            return []
        
        performance = self.get_budget_performance()
        alerts = []
        
        for category in performance.get('categories', []):
            if category['variance_percentage'] <= -15:  # 15% over budget
                alerts.append({
                    'type': 'over_budget',
                    'category': category['category'],
                    'severity': 'high' if category['variance_percentage'] <= -25 else 'medium',
                    'message': f"{category['category']} is {abs(category['variance_percentage']):.1f}% over budget",
                    'variance_percentage': category['variance_percentage']
                })
            elif category['variance_percentage'] >= 20:  # 20% under budget
                alerts.append({
                    'type': 'under_budget',
                    'category': category['category'],
                    'severity': 'low',
                    'message': f"{category['category']} is {category['variance_percentage']:.1f}% under budget",
                    'variance_percentage': category['variance_percentage']
                })
        
        return alerts


class CashFlowAnalyzer:
    """Analyze cash flow patterns and liquidity"""
    
    def __init__(self, user, start_date: Optional[date] = None, end_date: Optional[date] = None):
        self.user = user
        self.start_date = start_date or (timezone.now().date() - timedelta(days=90))
        self.end_date = end_date or timezone.now().date()
    
    def get_cash_flow_statement(self) -> Dict[str, Any]:
        """Generate cash flow statement"""
        # Operating activities (income and expenses)
        operating_income = Transaction.objects.filter(
            account__user=self.user,
            transaction_date__range=[self.start_date, self.end_date],
            transaction_type='income'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        operating_expenses = Transaction.objects.filter(
            account__user=self.user,
            transaction_date__range=[self.start_date, self.end_date],
            transaction_type='expense'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        net_operating_cash_flow = operating_income + operating_expenses
        
        # Investing activities (asset purchases/sales)
        investing_activities = Transaction.objects.filter(
            account__user=self.user,
            transaction_date__range=[self.start_date, self.end_date],
            category__name__icontains='investment'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Financing activities (loans, transfers)
        financing_activities = Transaction.objects.filter(
            account__user=self.user,
            transaction_date__range=[self.start_date, self.end_date],
            transaction_type='transfer'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        net_cash_flow = net_operating_cash_flow + investing_activities + financing_activities
        
        return {
            'period': f"{self.start_date} to {self.end_date}",
            'operating_activities': {
                'income': operating_income,
                'expenses': abs(operating_expenses),
                'net_operating_cash_flow': net_operating_cash_flow
            },
            'investing_activities': investing_activities,
            'financing_activities': financing_activities,
            'net_cash_flow': net_cash_flow
        }
    
    def get_liquidity_ratios(self) -> Dict[str, Decimal]:
        """Calculate liquidity ratios"""
        # Get current account balances
        total_assets = self.user.financial_accounts.filter(is_active=True).aggregate(
            total=Sum('balance')
        )['total'] or Decimal('0.00')
        
        # Get monthly expenses for liquidity calculation
        monthly_expenses = Transaction.objects.filter(
            account__user=self.user,
            transaction_date__range=[self.start_date, self.end_date],
            transaction_type='expense'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        monthly_expenses = abs(monthly_expenses) / 3  # Average over 3 months
        
        # Calculate ratios
        current_ratio = total_assets / monthly_expenses if monthly_expenses > 0 else Decimal('0.00')
        quick_ratio = total_assets / monthly_expenses if monthly_expenses > 0 else Decimal('0.00')
        
        return {
            'current_ratio': current_ratio.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'quick_ratio': quick_ratio.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'months_of_expenses_covered': (total_assets / monthly_expenses).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP) if monthly_expenses > 0 else Decimal('0.0')
        }
    
    def get_cash_flow_forecast(self, months_ahead: int = 6) -> List[Dict[str, Any]]:
        """Forecast future cash flow"""
        # Get historical monthly cash flows
        monthly_cash_flows = Transaction.objects.filter(
            account__user=self.user,
            transaction_date__range=[self.start_date, self.end_date]
        ).annotate(
            month=TruncMonth('transaction_date')
        ).values('month').annotate(
            net_cash_flow=Sum('amount')
        ).order_by('month')
        
        # Calculate average monthly cash flow
        total_cash_flow = sum(item['net_cash_flow'] for item in monthly_cash_flows)
        months_count = len(monthly_cash_flows)
        average_monthly_cash_flow = total_cash_flow / months_count if months_count > 0 else Decimal('0.00')
        
        # Generate forecast
        forecast = []
        current_date = self.end_date
        
        for month in range(1, months_ahead + 1):
            forecast_date = current_date + timedelta(days=30 * month)
            forecast.append({
                'month': forecast_date.strftime('%Y-%m'),
                'forecasted_cash_flow': average_monthly_cash_flow,
                'confidence': 'medium' if months_count >= 3 else 'low'
            })
        
        return forecast


class PerformanceMetrics:
    """Calculate financial performance metrics and KPIs"""
    
    def __init__(self, user, start_date: Optional[date] = None, end_date: Optional[date] = None):
        self.user = user
        self.start_date = start_date or (timezone.now().date() - timedelta(days=365))
        self.end_date = end_date or timezone.now().date()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        calculator = FinancialCalculator(self.user, self.start_date, self.end_date)
        trend_analyzer = TrendAnalyzer(self.user, self.start_date, self.end_date)
        cash_flow_analyzer = CashFlowAnalyzer(self.user, self.start_date, self.end_date)
        
        return {
            'period': f"{self.start_date} to {self.end_date}",
            'income_metrics': {
                'total_income': calculator.calculate_total_income(),
                'average_monthly_income': calculator.calculate_average_monthly_income(),
                'income_growth_rate': self._calculate_growth_rate('income')
            },
            'expense_metrics': {
                'total_expenses': calculator.calculate_total_expenses(),
                'average_monthly_expenses': calculator.calculate_average_monthly_expenses(),
                'expense_growth_rate': self._calculate_growth_rate('expense')
            },
            'profitability_metrics': {
                'net_income': calculator.calculate_net_income(),
                'savings_rate': calculator.calculate_savings_rate(),
                'expense_ratio': calculator.calculate_expense_ratio()
            },
            'liquidity_metrics': cash_flow_analyzer.get_liquidity_ratios(),
            'trends': {
                'monthly_trends': trend_analyzer.get_monthly_trends()[-6:],  # Last 6 months
                'top_categories': trend_analyzer.get_category_trends()[:5]  # Top 5 categories
            }
        }
    
    def _calculate_growth_rate(self, metric_type: str) -> Decimal:
        """Calculate growth rate for income or expenses"""
        # Split period in half
        mid_point = self.start_date + (self.end_date - self.start_date) / 2
        
        # Calculate first half
        first_half = Transaction.objects.filter(
            account__user=self.user,
            transaction_date__range=[self.start_date, mid_point],
            transaction_type=metric_type
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Calculate second half
        second_half = Transaction.objects.filter(
            account__user=self.user,
            transaction_date__range=[mid_point, self.end_date],
            transaction_type=metric_type
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        if first_half > 0:
            growth_rate = ((second_half - first_half) / first_half * 100)
            return growth_rate.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return Decimal('0.00')
    
    def get_roi_metrics(self) -> Dict[str, Any]:
        """Calculate return on investment metrics"""
        # This would typically involve investment account data
        # For now, return basic structure
        return {
            'total_investments': Decimal('0.00'),
            'investment_returns': Decimal('0.00'),
            'roi_percentage': Decimal('0.00'),
            'annualized_return': Decimal('0.00')
        }
    
    def get_efficiency_metrics(self) -> Dict[str, Any]:
        """Calculate efficiency metrics"""
        total_transactions = Transaction.objects.filter(
            account__user=self.user,
            transaction_date__range=[self.start_date, self.end_date]
        ).count()
        
        total_categories = Category.objects.filter(
            transactions__account__user=self.user,
            transactions__transaction_date__range=[self.start_date, self.end_date]
        ).distinct().count()
        
        return {
            'transactions_per_month': total_transactions / 12 if total_transactions > 0 else 0,
            'category_utilization': total_categories,
            'average_transaction_amount': self._calculate_average_transaction_amount()
        }
    
    def _calculate_average_transaction_amount(self) -> Decimal:
        """Calculate average transaction amount"""
        result = Transaction.objects.filter(
            account__user=self.user,
            transaction_date__range=[self.start_date, self.end_date]
        ).aggregate(
            average=Avg('amount')
        )['average']
        
        return result or Decimal('0.00')