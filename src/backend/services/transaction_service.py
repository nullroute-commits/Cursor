"""
Transaction service for Financial Analytics Platform
Handles transaction CRUD operations and financial analysis
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from decimal import Decimal
from sqlmodel import select, func, and_, or_
from fastapi import HTTPException, status, Query

from src.backend.models.database import Transaction, TransactionCreate, TransactionUpdate, TransactionResponse
from src.backend.models.database import Category, Account, User
from src.backend.database import get_session
from src.common.models.enums import TransactionType
from src.common.models.financial import DateRange, Amount, Currency

logger = logging.getLogger(__name__)


class TransactionService:
    """Service for transaction management and analysis"""
    
    def __init__(self):
        pass
    
    async def create_transaction(
        self,
        transaction_data: Dict[str, Any],
        user_id: UUID,
        organization_id: UUID
    ) -> Transaction:
        """Create a new transaction"""
        
        async with get_session() as session:
            # Validate account belongs to organization
            if 'account_id' in transaction_data:
                account_statement = select(Account).where(
                    Account.id == transaction_data['account_id'],
                    Account.organization_id == organization_id,
                    Account.is_active == True
                )
                account_result = await session.exec(account_statement)
                if not account_result.first():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid account ID"
                    )
            
            # Validate category belongs to organization
            if 'category_id' in transaction_data:
                category_statement = select(Category).where(
                    Category.id == transaction_data['category_id'],
                    Category.organization_id == organization_id,
                    Category.is_active == True
                )
                category_result = await session.exec(category_statement)
                if not category_result.first():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid category ID"
                    )
            
            # Create transaction
            transaction_create = TransactionCreate(
                **transaction_data,
                user_id=user_id,
                organization_id=organization_id
            )
            
            transaction = Transaction(**transaction_create.dict())
            session.add(transaction)
            await session.commit()
            await session.refresh(transaction)
            
            return transaction
    
    async def get_transaction(
        self,
        transaction_id: UUID,
        user_id: UUID,
        organization_id: UUID
    ) -> Optional[Transaction]:
        """Get a transaction by ID"""
        
        async with get_session() as session:
            statement = select(Transaction).where(
                Transaction.id == transaction_id,
                Transaction.organization_id == organization_id,
                Transaction.deleted_at.is_(None)
            )
            result = await session.exec(statement)
            transaction = result.first()
            
            if not transaction:
                return None
            
            return transaction
    
    async def get_transactions(
        self,
        organization_id: UUID,
        user_id: Optional[UUID] = None,
        account_id: Optional[UUID] = None,
        category_id: Optional[UUID] = None,
        transaction_type: Optional[TransactionType] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "date",
        order_direction: str = "desc"
    ) -> List[Transaction]:
        """Get transactions with filtering and pagination"""
        
        async with get_session() as session:
            # Build base query
            conditions = [
                Transaction.organization_id == organization_id,
                Transaction.deleted_at.is_(None)
            ]
            
            if user_id:
                conditions.append(Transaction.user_id == user_id)
            
            if account_id:
                conditions.append(Transaction.account_id == account_id)
            
            if category_id:
                conditions.append(Transaction.category_id == category_id)
            
            if transaction_type:
                conditions.append(Transaction.transaction_type == transaction_type)
            
            if start_date:
                conditions.append(Transaction.date >= start_date)
            
            if end_date:
                conditions.append(Transaction.date <= end_date)
            
            if search:
                search_condition = or_(
                    Transaction.description.ilike(f"%{search}%"),
                    Transaction.notes.ilike(f"%{search}%"),
                    Transaction.reference.ilike(f"%{search}%")
                )
                conditions.append(search_condition)
            
            # Build statement
            statement = select(Transaction).where(and_(*conditions))
            
            # Add ordering
            if order_by == "date":
                if order_direction == "desc":
                    statement = statement.order_by(Transaction.date.desc())
                else:
                    statement = statement.order_by(Transaction.date.asc())
            elif order_by == "amount":
                if order_direction == "desc":
                    statement = statement.order_by(Transaction.amount.desc())
                else:
                    statement = statement.order_by(Transaction.amount.asc())
            elif order_by == "created_at":
                if order_direction == "desc":
                    statement = statement.order_by(Transaction.created_at.desc())
                else:
                    statement = statement.order_by(Transaction.created_at.asc())
            
            # Add pagination
            statement = statement.offset(skip).limit(limit)
            
            result = await session.exec(statement)
            transactions = result.all()
            
            return transactions
    
    async def update_transaction(
        self,
        transaction_id: UUID,
        transaction_update: TransactionUpdate,
        user_id: UUID,
        organization_id: UUID
    ) -> Optional[Transaction]:
        """Update a transaction"""
        
        async with get_session() as session:
            # Get existing transaction
            statement = select(Transaction).where(
                Transaction.id == transaction_id,
                Transaction.organization_id == organization_id,
                Transaction.deleted_at.is_(None)
            )
            result = await session.exec(statement)
            transaction = result.first()
            
            if not transaction:
                return None
            
            # Update fields
            update_data = transaction_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(transaction, field, value)
            
            transaction.updated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(transaction)
            
            return transaction
    
    async def delete_transaction(
        self,
        transaction_id: UUID,
        user_id: UUID,
        organization_id: UUID,
        hard_delete: bool = False
    ) -> bool:
        """Delete a transaction (soft delete by default)"""
        
        async with get_session() as session:
            statement = select(Transaction).where(
                Transaction.id == transaction_id,
                Transaction.organization_id == organization_id,
                Transaction.deleted_at.is_(None)
            )
            result = await session.exec(statement)
            transaction = result.first()
            
            if not transaction:
                return False
            
            if hard_delete:
                await session.delete(transaction)
            else:
                transaction.deleted_at = datetime.utcnow()
                transaction.is_active = False
            
            await session.commit()
            return True
    
    async def get_transaction_summary(
        self,
        organization_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        account_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get transaction summary statistics"""
        
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
            
            if account_id:
                conditions.append(Transaction.account_id == account_id)
            
            if user_id:
                conditions.append(Transaction.user_id == user_id)
            
            # Get total income
            income_statement = select(func.sum(Transaction.amount)).where(
                and_(*conditions, Transaction.amount > 0)
            )
            income_result = await session.exec(income_statement)
            total_income = income_result.first() or Decimal('0.00')
            
            # Get total expenses
            expense_statement = select(func.sum(Transaction.amount)).where(
                and_(*conditions, Transaction.amount < 0)
            )
            expense_result = await session.exec(expense_statement)
            total_expenses = abs(expense_result.first() or Decimal('0.00'))
            
            # Get transaction count
            count_statement = select(func.count(Transaction.id)).where(and_(*conditions))
            count_result = await session.exec(count_statement)
            transaction_count = count_result.first() or 0
            
            # Get average transaction amount
            avg_statement = select(func.avg(Transaction.amount)).where(and_(*conditions))
            avg_result = await session.exec(avg_statement)
            avg_amount = avg_result.first() or Decimal('0.00')
            
            # Calculate net income
            net_income = total_income - total_expenses
            
            # Calculate savings rate
            savings_rate = Decimal('0.00')
            if total_income > 0:
                savings_rate = (net_income / total_income) * 100
            
            return {
                "total_income": float(total_income),
                "total_expenses": float(total_expenses),
                "net_income": float(net_income),
                "transaction_count": transaction_count,
                "average_amount": float(avg_amount),
                "savings_rate": float(savings_rate),
                "period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                }
            }
    
    async def get_category_breakdown(
        self,
        organization_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        account_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get spending breakdown by category"""
        
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
            
            if account_id:
                conditions.append(Transaction.account_id == account_id)
            
            if user_id:
                conditions.append(Transaction.user_id == user_id)
            
            # Get category breakdown
            statement = select(
                Category.name,
                Category.color,
                func.sum(Transaction.amount).label("total_amount"),
                func.count(Transaction.id).label("transaction_count")
            ).join(
                Category, Transaction.category_id == Category.id
            ).where(
                and_(*conditions)
            ).group_by(
                Category.id, Category.name, Category.color
            ).order_by(
                func.sum(Transaction.amount).asc()  # Most expensive first
            )
            
            result = await session.exec(statement)
            breakdown = []
            
            for row in result:
                breakdown.append({
                    "category_name": row.name,
                    "category_color": row.color,
                    "total_amount": abs(float(row.total_amount)),
                    "transaction_count": row.transaction_count
                })
            
            return breakdown
    
    async def get_monthly_trends(
        self,
        organization_id: UUID,
        months: int = 12,
        account_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get monthly spending and income trends"""
        
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)
        
        trends = []
        current_date = start_date
        
        while current_date <= end_date:
            month_start = current_date.replace(day=1)
            if current_date.month == 12:
                month_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
            
            # Get month summary
            month_summary = await self.get_transaction_summary(
                organization_id=organization_id,
                start_date=month_start,
                end_date=month_end,
                account_id=account_id,
                user_id=user_id
            )
            
            trends.append({
                "month": month_start.strftime("%Y-%m"),
                "total_income": month_summary["total_income"],
                "total_expenses": month_summary["total_expenses"],
                "net_income": month_summary["net_income"],
                "transaction_count": month_summary["transaction_count"]
            })
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return trends
    
    async def get_recurring_transactions(
        self,
        organization_id: UUID,
        user_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Identify potential recurring transactions"""
        
        async with get_session() as session:
            # Get transactions from last 6 months
            six_months_ago = date.today() - timedelta(days=180)
            
            conditions = [
                Transaction.organization_id == organization_id,
                Transaction.deleted_at.is_(None),
                Transaction.date >= six_months_ago
            ]
            
            if user_id:
                conditions.append(Transaction.user_id == user_id)
            
            statement = select(Transaction).where(and_(*conditions))
            result = await session.exec(statement)
            transactions = result.all()
            
            # Group by description and analyze patterns
            patterns = {}
            for tx in transactions:
                key = tx.description.lower().strip()
                if key not in patterns:
                    patterns[key] = []
                patterns[key].append(tx)
            
            # Find recurring patterns
            recurring = []
            for description, txs in patterns.items():
                if len(txs) >= 2:
                    # Sort by date
                    txs.sort(key=lambda x: x.date)
                    
                    # Calculate average amount
                    total_amount = sum(tx.amount for tx in txs)
                    avg_amount = total_amount / len(txs)
                    
                    # Check if amounts are similar (within 10%)
                    amount_variance = all(
                        abs(tx.amount - avg_amount) / abs(avg_amount) < 0.1
                        for tx in txs
                    )
                    
                    if amount_variance:
                        # Calculate frequency
                        if len(txs) >= 3:
                            # Calculate average days between transactions
                            intervals = []
                            for i in range(1, len(txs)):
                                days = (txs[i].date - txs[i-1].date).days
                                intervals.append(days)
                            
                            avg_interval = sum(intervals) / len(intervals)
                            
                            recurring.append({
                                "description": description,
                                "average_amount": float(avg_amount),
                                "frequency_days": round(avg_interval),
                                "transaction_count": len(txs),
                                "last_transaction": txs[-1].date.isoformat(),
                                "category_id": txs[-1].category_id,
                                "account_id": txs[-1].account_id
                            })
            
            return recurring
    
    async def bulk_update_transactions(
        self,
        transaction_ids: List[UUID],
        updates: Dict[str, Any],
        user_id: UUID,
        organization_id: UUID
    ) -> Dict[str, Any]:
        """Bulk update multiple transactions"""
        
        async with get_session() as session:
            # Verify all transactions belong to organization
            statement = select(Transaction).where(
                Transaction.id.in_(transaction_ids),
                Transaction.organization_id == organization_id,
                Transaction.deleted_at.is_(None)
            )
            result = await session.exec(statement)
            transactions = result.all()
            
            if len(transactions) != len(transaction_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Some transaction IDs are invalid or don't belong to organization"
                )
            
            # Update transactions
            updated_count = 0
            for transaction in transactions:
                for field, value in updates.items():
                    if hasattr(transaction, field):
                        setattr(transaction, field, value)
                
                transaction.updated_at = datetime.utcnow()
                updated_count += 1
            
            await session.commit()
            
            return {
                "success": True,
                "message": f"Updated {updated_count} transactions",
                "updated_count": updated_count
            }
    
    async def export_transactions(
        self,
        organization_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        format: str = "csv"
    ) -> str:
        """Export transactions to specified format"""
        
        # Get transactions
        transactions = await self.get_transactions(
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date,
            limit=10000  # Large limit for export
        )
        
        if format.lower() == "csv":
            return self._export_to_csv(transactions)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported export format"
            )
    
    def _export_to_csv(self, transactions: List[Transaction]) -> str:
        """Export transactions to CSV format"""
        
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Date", "Description", "Amount", "Type", "Category", "Account", "Reference", "Notes"
        ])
        
        # Write data
        for tx in transactions:
            writer.writerow([
                tx.date.strftime("%Y-%m-%d"),
                tx.description,
                f"{tx.amount:.2f}",
                tx.transaction_type.value,
                tx.category.name if tx.category else "",
                tx.account.name if tx.account else "",
                tx.reference or "",
                tx.notes or ""
            ])
        
        return output.getvalue()


# Global transaction service instance
transaction_service = TransactionService()


# Export functions and classes
__all__ = [
    "TransactionService",
    "transaction_service"
]