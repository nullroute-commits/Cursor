"""
Analytics service for Financial Analytics Platform
Handles financial analysis, reporting, and machine learning models
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple
from uuid import UUID
from decimal import Decimal
import json
import statistics
from collections import defaultdict

from fastapi import HTTPException, status
from sqlmodel import select, func, and_, or_
import numpy as np
import pandas as pd

from src.backend.models.database import Transaction, Account, Category, Budget
from src.backend.database import get_session
from src.common.models.enums import TransactionType, AccountType
from src.common.models.financial import Amount, DateRange, FinancialMetrics
from src.common.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AnalyticsService:
    """Service for financial analytics and reporting"""
    
    def __init__(self):
        pass
    
    async def get_financial_overview(
        self,
        organization_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get comprehensive financial overview"""
        
        try:
            async with get_session() as session:
                # Get basic transaction summary
                summary = await self._get_transaction_summary(
                    session, organization_id, start_date, end_date, user_id
                )
                
                # Get spending patterns
                spending_patterns = await self._get_spending_patterns(
                    session, organization_id, start_date, end_date, user_id
                )
                
                # Get income analysis
                income_analysis = await self._get_income_analysis(
                    session, organization_id, start_date, end_date, user_id
                )
                
                # Get cash flow analysis
                cash_flow = await self._get_cash_flow_analysis(
                    session, organization_id, start_date, end_date, user_id
                )
                
                # Get budget performance
                budget_performance = await self._get_budget_performance(
                    session, organization_id, start_date, end_date, user_id
                )
                
                # Get financial health indicators
                health_indicators = await self._get_financial_health_indicators(
                    session, organization_id, start_date, end_date, user_id
                )
                
                return {
                    "success": True,
                    "message": "Financial overview generated successfully",
                    "data": {
                        "summary": summary,
                        "spending_patterns": spending_patterns,
                        "income_analysis": income_analysis,
                        "cash_flow": cash_flow,
                        "budget_performance": budget_performance,
                        "health_indicators": health_indicators,
                        "period": {
                            "start_date": start_date.isoformat() if start_date else None,
                            "end_date": end_date.isoformat() if end_date else None,
                            "days": (end_date - start_date).days if start_date and end_date else None
                        }
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to generate financial overview: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate financial overview: {str(e)}"
            )
    
    async def get_spending_analysis(
        self,
        organization_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        user_id: Optional[UUID] = None,
        category_id: Optional[UUID] = None,
        account_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get detailed spending analysis"""
        
        try:
            async with get_session() as session:
                # Build base conditions
                conditions = [
                    Transaction.organization_id == organization_id,
                    Transaction.deleted_at.is_(None),
                    Transaction.amount < 0  # Only expenses
                ]
                
                if start_date:
                    conditions.append(Transaction.date >= start_date)
                if end_date:
                    conditions.append(Transaction.date <= end_date)
                if user_id:
                    conditions.append(Transaction.user_id == user_id)
                if category_id:
                    conditions.append(Transaction.category_id == category_id)
                if account_id:
                    conditions.append(Transaction.account_id == account_id)
                
                # Get spending by category
                category_statement = select(
                    Category.name,
                    Category.color,
                    func.sum(Transaction.amount).label("total_spent"),
                    func.count(Transaction.id).label("transaction_count"),
                    func.avg(Transaction.amount).label("average_amount")
                ).join(
                    Category, Transaction.category_id == Category.id
                ).where(
                    and_(*conditions)
                ).group_by(
                    Category.id, Category.name, Category.color
                ).order_by(
                    func.sum(Transaction.amount).asc()  # Most expensive first
                )
                
                category_result = await session.exec(category_statement)
                category_spending = []
                
                for row in category_result:
                    category_spending.append({
                        "category_name": row.name,
                        "category_color": row.color,
                        "total_spent": abs(float(row.total_spent)),
                        "transaction_count": row.transaction_count,
                        "average_amount": abs(float(row.average_amount)),
                        "percentage_of_total": 0  # Will calculate below
                    })
                
                # Calculate percentages
                total_spent = sum(cat["total_spent"] for cat in category_spending)
                if total_spent > 0:
                    for cat in category_spending:
                        cat["percentage_of_total"] = (cat["total_spent"] / total_spent) * 100
                
                # Get spending by day of week
                day_spending_statement = select(
                    func.extract('dow', Transaction.date).label("day_of_week"),
                    func.sum(Transaction.amount).label("total_spent"),
                    func.count(Transaction.id).label("transaction_count")
                ).where(
                    and_(*conditions)
                ).group_by(
                    func.extract('dow', Transaction.date)
                ).order_by(
                    func.extract('dow', Transaction.date)
                )
                
                day_result = await session.exec(day_spending_statement)
                day_spending = []
                
                day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                for row in day_result:
                    day_spending.append({
                        "day": day_names[int(row.day_of_week)],
                        "day_number": int(row.day_of_week),
                        "total_spent": abs(float(row.total_spent)),
                        "transaction_count": row.transaction_count
                    })
                
                # Get spending by month
                month_spending_statement = select(
                    func.extract('month', Transaction.date).label("month"),
                    func.extract('year', Transaction.date).label("year"),
                    func.sum(Transaction.amount).label("total_spent"),
                    func.count(Transaction.id).label("transaction_count")
                ).where(
                    and_(*conditions)
                ).group_by(
                    func.extract('month', Transaction.date),
                    func.extract('year', Transaction.date)
                ).order_by(
                    func.extract('year', Transaction.date),
                    func.extract('month', Transaction.date)
                )
                
                month_result = await session.exec(month_spending_statement)
                month_spending = []
                
                month_names = [
                    "January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"
                ]
                
                for row in month_result:
                    month_spending.append({
                        "month": month_names[int(row.month) - 1],
                        "month_number": int(row.month),
                        "year": int(row.year),
                        "total_spent": abs(float(row.total_spent)),
                        "transaction_count": row.transaction_count
                    })
                
                # Get top spending merchants
                merchant_statement = select(
                    Transaction.merchant_name,
                    func.sum(Transaction.amount).label("total_spent"),
                    func.count(Transaction.id).label("transaction_count")
                ).where(
                    and_(*conditions, Transaction.merchant_name.is_not(None))
                ).group_by(
                    Transaction.merchant_name
                ).order_by(
                    func.sum(Transaction.amount).asc()  # Most expensive first
                ).limit(20)
                
                merchant_result = await session.exec(merchant_statement)
                top_merchants = []
                
                for row in merchant_result:
                    top_merchants.append({
                        "merchant_name": row.merchant_name,
                        "total_spent": abs(float(row.total_spent)),
                        "transaction_count": row.transaction_count
                    })
                
                return {
                    "success": True,
                    "message": "Spending analysis generated successfully",
                    "data": {
                        "category_breakdown": category_spending,
                        "day_of_week_breakdown": day_spending,
                        "monthly_breakdown": month_spending,
                        "top_merchants": top_merchants,
                        "total_spent": total_spent,
                        "total_transactions": sum(cat["transaction_count"] for cat in category_spending),
                        "period": {
                            "start_date": start_date.isoformat() if start_date else None,
                            "end_date": end_date.isoformat() if end_date else None
                        }
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to generate spending analysis: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate spending analysis: {str(e)}"
            )
    
    async def get_income_analysis(
        self,
        organization_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get detailed income analysis"""
        
        try:
            async with get_session() as session:
                # Build base conditions for income
                conditions = [
                    Transaction.organization_id == organization_id,
                    Transaction.deleted_at.is_(None),
                    Transaction.amount > 0  # Only income
                ]
                
                if start_date:
                    conditions.append(Transaction.date >= start_date)
                if end_date:
                    conditions.append(Transaction.date <= end_date)
                if user_id:
                    conditions.append(Transaction.user_id == user_id)
                
                # Get income by category
                category_statement = select(
                    Category.name,
                    Category.color,
                    func.sum(Transaction.amount).label("total_income"),
                    func.count(Transaction.id).label("transaction_count"),
                    func.avg(Transaction.amount).label("average_amount")
                ).join(
                    Category, Transaction.category_id == Category.id
                ).where(
                    and_(*conditions)
                ).group_by(
                    Category.id, Category.name, Category.color
                ).order_by(
                    func.sum(Transaction.amount).desc()  # Highest income first
                )
                
                category_result = await session.exec(category_statement)
                category_income = []
                
                for row in category_result:
                    category_income.append({
                        "category_name": row.name,
                        "category_color": row.color,
                        "total_income": float(row.total_income),
                        "transaction_count": row.transaction_count,
                        "average_amount": float(row.average_amount)
                    })
                
                # Get income by month
                month_statement = select(
                    func.extract('month', Transaction.date).label("month"),
                    func.extract('year', Transaction.date).label("year"),
                    func.sum(Transaction.amount).label("total_income"),
                    func.count(Transaction.id).label("transaction_count")
                ).where(
                    and_(*conditions)
                ).group_by(
                    func.extract('month', Transaction.date),
                    func.extract('year', Transaction.date)
                ).order_by(
                    func.extract('year', Transaction.date),
                    func.extract('month', Transaction.date)
                )
                
                month_result = await session.exec(month_statement)
                month_income = []
                
                month_names = [
                    "January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"
                ]
                
                for row in month_result:
                    month_income.append({
                        "month": month_names[int(row.month) - 1],
                        "month_number": int(row.month),
                        "year": int(row.year),
                        "total_income": float(row.total_income),
                        "transaction_count": row.transaction_count
                    })
                
                # Get income sources (merchants)
                source_statement = select(
                    Transaction.merchant_name,
                    func.sum(Transaction.amount).label("total_income"),
                    func.count(Transaction.id).label("transaction_count")
                ).where(
                    and_(*conditions, Transaction.merchant_name.is_not(None))
                ).group_by(
                    Transaction.merchant_name
                ).order_by(
                    func.sum(Transaction.amount).desc()  # Highest income first
                ).limit(20)
                
                source_result = await session.exec(source_statement)
                income_sources = []
                
                for row in source_result:
                    income_sources.append({
                        "source_name": row.merchant_name,
                        "total_income": float(row.total_income),
                        "transaction_count": row.transaction_count
                    })
                
                # Calculate total income
                total_income = sum(cat["total_income"] for cat in category_income)
                
                return {
                    "success": True,
                    "message": "Income analysis generated successfully",
                    "data": {
                        "category_breakdown": category_income,
                        "monthly_breakdown": month_income,
                        "income_sources": income_sources,
                        "total_income": total_income,
                        "total_transactions": sum(cat["transaction_count"] for cat in category_income),
                        "average_monthly_income": total_income / len(month_income) if month_income else 0,
                        "period": {
                            "start_date": start_date.isoformat() if start_date else None,
                            "end_date": end_date.isoformat() if end_date else None
                        }
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to generate income analysis: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate income analysis: {str(e)}"
            )
    
    async def get_cash_flow_forecast(
        self,
        organization_id: UUID,
        months_ahead: int = 6,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get cash flow forecast based on historical data"""
        
        try:
            async with get_session() as session:
                # Get historical data for the last 12 months
                end_date = date.today()
                start_date = end_date - timedelta(days=365)
                
                # Build conditions
                conditions = [
                    Transaction.organization_id == organization_id,
                    Transaction.deleted_at.is_(None),
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                ]
                
                if user_id:
                    conditions.append(Transaction.user_id == user_id)
                
                # Get monthly income and expenses
                monthly_statement = select(
                    func.extract('month', Transaction.date).label("month"),
                    func.extract('year', Transaction.date).label("year"),
                    func.sum(
                        func.case(
                            (Transaction.amount > 0, Transaction.amount),
                            else_=0
                        )
                    ).label("income"),
                    func.sum(
                        func.case(
                            (Transaction.amount < 0, func.abs(Transaction.amount)),
                            else_=0
                        )
                    ).label("expenses")
                ).where(
                    and_(*conditions)
                ).group_by(
                    func.extract('month', Transaction.date),
                    func.extract('year', Transaction.date)
                ).order_by(
                    func.extract('year', Transaction.date),
                    func.extract('month', Transaction.date)
                )
                
                monthly_result = await session.exec(monthly_statement)
                historical_data = []
                
                for row in monthly_result:
                    historical_data.append({
                        "month": int(row.month),
                        "year": int(row.year),
                        "income": float(row.income),
                        "expenses": float(row.expenses),
                        "net": float(row.income) - float(row.expenses)
                    })
                
                if not historical_data:
                    return {
                        "success": False,
                        "message": "Insufficient historical data for forecasting",
                        "data": None
                    }
                
                # Calculate averages and trends
                avg_income = statistics.mean([m["income"] for m in historical_data])
                avg_expenses = statistics.mean([m["expenses"] for m in historical_data])
                avg_net = statistics.mean([m["net"] for m in historical_data])
                
                # Calculate trends (simple linear regression)
                months = list(range(len(historical_data)))
                income_trend = self._calculate_trend([m["income"] for m in historical_data])
                expense_trend = self._calculate_trend([m["expenses"] for m in historical_data])
                
                # Generate forecast
                forecast = []
                current_month = date.today().month
                current_year = date.today().year
                
                for i in range(months_ahead):
                    # Calculate month and year
                    month = ((current_month - 1 + i) % 12) + 1
                    year = current_year + ((current_month - 1 + i) // 12)
                    
                    # Apply trend to averages
                    trend_factor = i + 1
                    forecast_income = avg_income + (income_trend * trend_factor)
                    forecast_expenses = avg_expenses + (expense_trend * trend_factor)
                    forecast_net = forecast_income - forecast_expenses
                    
                    forecast.append({
                        "month": month,
                        "year": year,
                        "month_name": self._get_month_name(month),
                        "forecasted_income": max(0, forecast_income),
                        "forecasted_expenses": max(0, forecast_expenses),
                        "forecasted_net": forecast_net,
                        "confidence": max(0.1, 1.0 - (i * 0.1))  # Decreasing confidence over time
                    })
                
                # Calculate cash flow metrics
                total_forecasted_income = sum(f["forecasted_income"] for f in forecast)
                total_forecasted_expenses = sum(f["forecasted_expenses"] for f in forecast)
                total_forecasted_net = sum(f["forecasted_net"] for f in forecast)
                
                return {
                    "success": True,
                    "message": "Cash flow forecast generated successfully",
                    "data": {
                        "forecast": forecast,
                        "summary": {
                            "total_forecasted_income": total_forecasted_income,
                            "total_forecasted_expenses": total_forecasted_expenses,
                            "total_forecasted_net": total_forecasted_net,
                            "average_monthly_income": total_forecasted_income / months_ahead,
                            "average_monthly_expenses": total_forecasted_expenses / months_ahead,
                            "average_monthly_net": total_forecasted_net / months_ahead
                        },
                        "historical_analysis": {
                            "average_monthly_income": avg_income,
                            "average_monthly_expenses": avg_expenses,
                            "average_monthly_net": avg_net,
                            "income_trend": income_trend,
                            "expense_trend": expense_trend,
                            "data_points": len(historical_data)
                        },
                        "forecast_period": {
                            "months_ahead": months_ahead,
                            "start_month": forecast[0]["month_name"] if forecast else None,
                            "end_month": forecast[-1]["month_name"] if forecast else None
                        }
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to generate cash flow forecast: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate cash flow forecast: {str(e)}"
            )
    
    async def get_anomaly_detection(
        self,
        organization_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        user_id: Optional[UUID] = None,
        threshold: float = 2.0
    ) -> Dict[str, Any]:
        """Detect anomalous transactions and spending patterns"""
        
        try:
            async with get_session() as session:
                # Build base conditions
                conditions = [
                    Transaction.organization_id == organization_id,
                    Transaction.deleted_at.is_(None)
                ]
                
                if start_date:
                    conditions.append(Transaction.date >= start_date)
                if end_date:
                    conditions.append(Transaction.date <= end_date)
                if user_id:
                    conditions.append(Transaction.user_id == user_id)
                
                # Get all transactions for analysis
                statement = select(Transaction).where(and_(*conditions))
                result = await session.exec(statement)
                transactions = result.all()
                
                if not transactions:
                    return {
                        "success": False,
                        "message": "No transactions found for anomaly detection",
                        "data": None
                    }
                
                # Convert to pandas for analysis
                df = pd.DataFrame([
                    {
                        'id': str(tx.id),
                        'amount': abs(float(tx.amount)),
                        'date': tx.date,
                        'category_id': str(tx.category_id) if tx.category_id else None,
                        'merchant_name': tx.merchant_name,
                        'description': tx.description
                    }
                    for tx in transactions
                ])
                
                anomalies = []
                
                # 1. Amount-based anomalies (Z-score method)
                if len(df) > 1:
                    df['amount_zscore'] = np.abs((df['amount'] - df['amount'].mean()) / df['amount'].std())
                    amount_anomalies = df[df['amount_zscore'] > threshold]
                    
                    for _, row in amount_anomalies.iterrows():
                        anomalies.append({
                            "type": "amount_anomaly",
                            "transaction_id": row['id'],
                            "amount": float(row['amount']),
                            "z_score": float(row['amount_zscore']),
                            "description": row['description'],
                            "merchant": row['merchant_name'],
                            "date": row['date'].isoformat(),
                            "severity": "high" if row['amount_zscore'] > 3.0 else "medium"
                        })
                
                # 2. Category-based anomalies (unusual spending in categories)
                if 'category_id' in df.columns and df['category_id'].notna().any():
                    category_stats = df.groupby('category_id')['amount'].agg(['mean', 'std', 'count'])
                    
                    for category_id, stats in category_stats.iterrows():
                        if stats['count'] > 5 and stats['std'] > 0:  # Need sufficient data
                            category_transactions = df[df['category_id'] == category_id]
                            
                            for _, row in category_transactions.iterrows():
                                if stats['std'] > 0:
                                    category_zscore = abs((row['amount'] - stats['mean']) / stats['std'])
                                    if category_zscore > threshold:
                                        anomalies.append({
                                            "type": "category_anomaly",
                                            "transaction_id": row['id'],
                                            "amount": float(row['amount']),
                                            "category_id": category_id,
                                            "z_score": float(category_zscore),
                                            "description": row['description'],
                                            "merchant": row['merchant_name'],
                                            "date": row['date'].isoformat(),
                                            "severity": "high" if category_zscore > 3.0 else "medium"
                                        })
                
                # 3. Time-based anomalies (unusual spending patterns)
                df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
                df['month'] = pd.to_datetime(df['date']).dt.month
                
                # Day of week anomalies
                day_stats = df.groupby('day_of_week')['amount'].agg(['mean', 'std', 'count'])
                for day, stats in day_stats.iterrows():
                    if stats['count'] > 5 and stats['std'] > 0:
                        day_transactions = df[df['day_of_week'] == day]
                        for _, row in day_transactions.iterrows():
                            if stats['std'] > 0:
                                day_zscore = abs((row['amount'] - stats['mean']) / stats['std'])
                                if day_zscore > threshold:
                                    anomalies.append({
                                        "type": "timing_anomaly",
                                        "transaction_id": row['id'],
                                        "amount": float(row['amount']),
                                        "day_of_week": int(day),
                                        "z_score": float(day_zscore),
                                        "description": row['description'],
                                        "merchant": row['merchant_name'],
                                        "date": row['date'].isoformat(),
                                        "severity": "high" if day_zscore > 3.0 else "medium"
                                    })
                
                # 4. Merchant-based anomalies (unusual spending at specific merchants)
                if 'merchant_name' in df.columns and df['merchant_name'].notna().any():
                    merchant_stats = df.groupby('merchant_name')['amount'].agg(['mean', 'std', 'count'])
                    
                    for merchant, stats in merchant_stats.iterrows():
                        if stats['count'] > 3 and stats['std'] > 0:  # Need sufficient data
                            merchant_transactions = df[df['merchant_name'] == merchant]
                            
                            for _, row in merchant_transactions.iterrows():
                                if stats['std'] > 0:
                                    merchant_zscore = abs((row['amount'] - stats['mean']) / stats['std'])
                                    if merchant_zscore > threshold:
                                        anomalies.append({
                                            "type": "merchant_anomaly",
                                            "transaction_id": row['id'],
                                            "amount": float(row['amount']),
                                            "merchant_name": merchant,
                                            "z_score": float(merchant_zscore),
                                            "description": row['description'],
                                            "date": row['date'].isoformat(),
                                            "severity": "high" if merchant_zscore > 3.0 else "medium"
                                        })
                
                # Remove duplicates and sort by severity
                unique_anomalies = []
                seen_transactions = set()
                
                for anomaly in anomalies:
                    if anomaly['transaction_id'] not in seen_transactions:
                        unique_anomalies.append(anomaly)
                        seen_transactions.add(anomaly['transaction_id'])
                
                # Sort by severity and z-score
                severity_order = {"high": 3, "medium": 2, "low": 1}
                unique_anomalies.sort(key=lambda x: (severity_order[x['severity']], x['z_score']), reverse=True)
                
                return {
                    "success": True,
                    "message": "Anomaly detection completed successfully",
                    "data": {
                        "anomalies": unique_anomalies,
                        "total_anomalies": len(unique_anomalies),
                        "anomaly_breakdown": {
                            "amount_anomalies": len([a for a in unique_anomalies if a['type'] == 'amount_anomaly']),
                            "category_anomalies": len([a for a in unique_anomalies if a['type'] == 'category_anomaly']),
                            "timing_anomalies": len([a for a in unique_anomalies if a['type'] == 'timing_anomaly']),
                            "merchant_anomalies": len([a for a in unique_anomalies if a['type'] == 'merchant_anomaly'])
                        },
                        "severity_breakdown": {
                            "high": len([a for a in unique_anomalies if a['severity'] == 'high']),
                            "medium": len([a for a in unique_anomalies if a['severity'] == 'medium']),
                            "low": len([a for a in unique_anomalies if a['severity'] == 'low'])
                        },
                        "analysis_parameters": {
                            "threshold": threshold,
                            "total_transactions_analyzed": len(transactions),
                            "date_range": {
                                "start_date": start_date.isoformat() if start_date else None,
                                "end_date": end_date.isoformat() if end_date else None
                            }
                        }
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to perform anomaly detection: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to perform anomaly detection: {str(e)}"
            )
    
    async def get_budget_analysis(
        self,
        organization_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get budget vs actual analysis"""
        
        try:
            async with get_session() as session:
                # Get budgets
                budget_conditions = [
                    Budget.organization_id == organization_id,
                    Budget.is_active == True
                ]
                
                if start_date:
                    budget_conditions.append(Budget.start_date <= end_date)
                if end_date:
                    budget_conditions.append(Budget.end_date >= start_date)
                if user_id:
                    budget_conditions.append(Budget.user_id == user_id)
                
                budget_statement = select(Budget).where(and_(*budget_conditions))
                budget_result = await session.exec(budget_statement)
                budgets = budget_result.all()
                
                budget_analysis = []
                
                for budget in budgets:
                    # Get actual spending for this budget period
                    spending_conditions = [
                        Transaction.organization_id == organization_id,
                        Transaction.deleted_at.is_(None),
                        Transaction.amount < 0,  # Only expenses
                        Transaction.date >= budget.start_date,
                        Transaction.date <= budget.end_date
                    ]
                    
                    if budget.category_id:
                        spending_conditions.append(Transaction.category_id == budget.category_id)
                    if user_id:
                        spending_conditions.append(Transaction.user_id == user_id)
                    
                    spending_statement = select(
                        func.sum(func.abs(Transaction.amount))
                    ).where(and_(*spending_conditions))
                    
                    spending_result = await session.exec(spending_statement)
                    actual_spending = spending_result.first() or Decimal('0.00')
                    
                    # Calculate budget performance
                    budget_amount = budget.amount
                    actual_amount = float(actual_spending)
                    remaining = float(budget_amount) - actual_amount
                    percentage_used = (actual_amount / float(budget_amount)) * 100 if budget_amount > 0 else 0
                    
                    # Determine status
                    if percentage_used >= 100:
                        status = "exceeded"
                    elif percentage_used >= 80:
                        status = "warning"
                    else:
                        status = "on_track"
                    
                    budget_analysis.append({
                        "budget_id": str(budget.id),
                        "name": budget.name,
                        "amount": float(budget_amount),
                        "actual_spending": actual_amount,
                        "remaining": remaining,
                        "percentage_used": percentage_used,
                        "status": status,
                        "start_date": budget.start_date.isoformat(),
                        "end_date": budget.end_date.isoformat(),
                        "category": {
                            "id": str(budget.category.id),
                            "name": budget.category.name,
                            "color": budget.category.color
                        } if budget.category else None
                    })
                
                # Calculate overall budget performance
                total_budget = sum(b["amount"] for b in budget_analysis)
                total_spent = sum(b["actual_spending"] for b in budget_analysis)
                total_remaining = sum(b["remaining"] for b in budget_analysis)
                overall_percentage = (total_spent / total_budget) * 100 if total_budget > 0 else 0
                
                return {
                    "success": True,
                    "message": "Budget analysis generated successfully",
                    "data": {
                        "budgets": budget_analysis,
                        "summary": {
                            "total_budgets": len(budget_analysis),
                            "total_budget_amount": total_budget,
                            "total_spent": total_spent,
                            "total_remaining": total_remaining,
                            "overall_percentage_used": overall_percentage,
                            "budgets_exceeded": len([b for b in budget_analysis if b["status"] == "exceeded"]),
                            "budgets_warning": len([b for b in budget_analysis if b["status"] == "warning"]),
                            "budgets_on_track": len([b for b in budget_analysis if b["status"] == "on_track"])
                        },
                        "period": {
                            "start_date": start_date.isoformat() if start_date else None,
                            "end_date": end_date.isoformat() if end_date else None
                        }
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to generate budget analysis: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate budget analysis: {str(e)}"
            )
    
    # Helper methods
    async def _get_transaction_summary(
        self,
        session,
        organization_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get basic transaction summary"""
        
        conditions = [
            Transaction.organization_id == organization_id,
            Transaction.deleted_at.is_(None)
        ]
        
        if start_date:
            conditions.append(Transaction.date >= start_date)
        if end_date:
            conditions.append(Transaction.date <= end_date)
        if user_id:
            conditions.append(Transaction.user_id == user_id)
        
        # Get totals
        income_statement = select(func.sum(Transaction.amount)).where(
            and_(*conditions, Transaction.amount > 0)
        )
        income_result = await session.exec(income_statement)
        total_income = income_result.first() or Decimal('0.00')
        
        expense_statement = select(func.sum(Transaction.amount)).where(
            and_(*conditions, Transaction.amount < 0)
        )
        expense_result = await session.exec(expense_statement)
        total_expenses = abs(expense_result.first() or Decimal('0.00'))
        
        count_statement = select(func.count(Transaction.id)).where(and_(*conditions))
        count_result = await session.exec(count_statement)
        transaction_count = count_result.first() or 0
        
        return {
            "total_income": float(total_income),
            "total_expenses": float(total_expenses),
            "net_income": float(total_income - total_expenses),
            "transaction_count": transaction_count,
            "savings_rate": (float(total_income - total_expenses) / float(total_income) * 100) if total_income > 0 else 0
        }
    
    async def _get_spending_patterns(
        self,
        session,
        organization_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get spending patterns analysis"""
        
        # This would implement spending pattern analysis
        # For now, return basic structure
        return {
            "daily_patterns": [],
            "weekly_patterns": [],
            "monthly_patterns": [],
            "seasonal_patterns": []
        }
    
    async def _get_income_analysis(
        self,
        session,
        organization_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get income analysis"""
        
        # This would implement income analysis
        # For now, return basic structure
        return {
            "income_sources": [],
            "income_stability": 0.0,
            "income_growth_rate": 0.0
        }
    
    async def _get_cash_flow_analysis(
        self,
        session,
        organization_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get cash flow analysis"""
        
        # This would implement cash flow analysis
        # For now, return basic structure
        return {
            "operating_cash_flow": 0.0,
            "investing_cash_flow": 0.0,
            "financing_cash_flow": 0.0,
            "net_cash_flow": 0.0
        }
    
    async def _get_budget_performance(
        self,
        session,
        organization_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get budget performance analysis"""
        
        # This would implement budget performance analysis
        # For now, return basic structure
        return {
            "budgets": [],
            "overall_performance": 0.0,
            "variance_analysis": []
        }
    
    async def _get_financial_health_indicators(
        self,
        session,
        organization_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get financial health indicators"""
        
        # This would implement financial health indicators
        # For now, return basic structure
        return {
            "liquidity_ratio": 0.0,
            "debt_to_income_ratio": 0.0,
            "savings_rate": 0.0,
            "emergency_fund_coverage": 0.0
        }
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate simple linear trend"""
        if len(values) < 2:
            return 0.0
        
        x = list(range(len(values)))
        y = values
        
        # Simple linear regression
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        if n * sum_x2 - sum_x ** 2 == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        return slope
    
    def _get_month_name(self, month: int) -> str:
        """Get month name from month number"""
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        return month_names[month - 1] if 1 <= month <= 12 else "Unknown"


# Global analytics service instance
analytics_service = AnalyticsService()


# Export functions and classes
__all__ = [
    "AnalyticsService",
    "analytics_service"
]