"""
Ingestion service for Financial Analytics Platform
Handles CSV data ingestion from various bank formats
"""

import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
import logging
from uuid import UUID

from fastapi import HTTPException, status, UploadFile
from sqlmodel import select

from src.backend.models.database import Transaction, TransactionCreate, Category, Account
from src.backend.database import get_session
from src.common.models.enums import TransactionType

logger = logging.getLogger(__name__)


class BankFormat:
    """Supported bank formats"""
    CHASE = "chase"
    DISCOVER = "discover"
    CAPITALONE = "capitalone"
    GENERIC = "generic"


class CSVParser:
    """CSV parser for different bank formats"""
    
    def __init__(self):
        self.supported_formats = [
            BankFormat.CHASE,
            BankFormat.DISCOVER,
            BankFormat.CAPITALONE,
            BankFormat.GENERIC
        ]
    
    def detect_format(self, csv_content: str) -> str:
        """Detect bank format from CSV content"""
        lines = csv_content.strip().split('\n')
        if not lines:
            return BankFormat.GENERIC
        
        header = lines[0].lower()
        
        if 'details' in header and 'posting date' in header:
            return BankFormat.CHASE
        elif 'trans date' in header and 'post date' in header:
            return BankFormat.DISCOVER
        elif 'transaction date' in header and 'posted date' in header:
            return BankFormat.CAPITALONE
        else:
            return BankFormat.GENERIC
    
    def parse_chase_csv(self, csv_content: str) -> List[Dict[str, Any]]:
        """Parse Chase bank CSV format"""
        transactions = []
        
        # Skip header lines and find data start
        lines = csv_content.strip().split('\n')
        data_start = 0
        
        for i, line in enumerate(lines):
            if 'Details' in line and 'Posting Date' in line:
                data_start = i + 1
                break
        
        # Parse data rows
        for line in lines[data_start:]:
            if not line.strip():
                continue
                
            try:
                # Chase format: Details, Posting Date, Description, Amount, Type, Balance, Check or Slip #
                parts = [part.strip() for part in line.split(',')]
                
                if len(parts) >= 6:
                    details = parts[0]
                    posting_date_str = parts[1]
                    description = parts[2]
                    amount_str = parts[3]
                    transaction_type = parts[4]
                    balance_str = parts[5]
                    check_number = parts[6] if len(parts) > 6 else None
                    
                    # Parse date
                    try:
                        posting_date = datetime.strptime(posting_date_str, '%m/%d/%Y')
                    except ValueError:
                        posting_date = datetime.utcnow()
                    
                    # Parse amount
                    try:
                        amount = Decimal(amount_str.replace('$', '').replace(',', ''))
                    except (ValueError, TypeError):
                        amount = Decimal('0.00')
                    
                    # Determine transaction type
                    if amount > 0:
                        tx_type = TransactionType.INCOME
                    else:
                        tx_type = TransactionType.EXPENSE
                    
                    transactions.append({
                        'date': posting_date,
                        'description': description or details,
                        'amount': amount,
                        'transaction_type': tx_type,
                        'reference': check_number,
                        'notes': f"Original type: {transaction_type}",
                        'metadata': {
                            'bank_format': BankFormat.CHASE,
                            'original_details': details,
                            'original_type': transaction_type,
                            'balance': balance_str
                        }
                    })
            except Exception as e:
                logger.warning(f"Failed to parse Chase CSV line: {line}, error: {e}")
                continue
        
        return transactions
    
    def parse_discover_csv(self, csv_content: str) -> List[Dict[str, Any]]:
        """Parse Discover bank CSV format"""
        transactions = []
        
        lines = csv_content.strip().split('\n')
        data_start = 0
        
        for i, line in enumerate(lines):
            if 'Trans Date' in line and 'Post Date' in line:
                data_start = i + 1
                break
        
        for line in lines[data_start:]:
            if not line.strip():
                continue
                
            try:
                # Discover format: Trans Date, Post Date, Description, Category, Amount
                parts = [part.strip() for part in line.split(',')]
                
                if len(parts) >= 5:
                    trans_date_str = parts[0]
                    post_date_str = parts[1]
                    description = parts[2]
                    category = parts[3]
                    amount_str = parts[4]
                    
                    # Parse dates
                    try:
                        trans_date = datetime.strptime(trans_date_str, '%m/%d/%Y')
                        post_date = datetime.strptime(post_date_str, '%m/%d/%Y')
                    except ValueError:
                        trans_date = post_date = datetime.utcnow()
                    
                    # Parse amount
                    try:
                        amount = Decimal(amount_str.replace('$', '').replace(',', ''))
                    except (ValueError, TypeError):
                        amount = Decimal('0.00')
                    
                    # Determine transaction type
                    if amount > 0:
                        tx_type = TransactionType.INCOME
                    else:
                        tx_type = TransactionType.EXPENSE
                    
                    transactions.append({
                        'date': trans_date,
                        'description': description,
                        'amount': amount,
                        'transaction_type': tx_type,
                        'notes': f"Category: {category}",
                        'metadata': {
                            'bank_format': BankFormat.DISCOVER,
                            'category': category,
                            'post_date': post_date.isoformat()
                        }
                    })
            except Exception as e:
                logger.warning(f"Failed to parse Discover CSV line: {line}, error: {e}")
                continue
        
        return transactions
    
    def parse_capitalone_csv(self, csv_content: str) -> List[Dict[str, Any]]:
        """Parse Capital One bank CSV format"""
        transactions = []
        
        lines = csv_content.strip().split('\n')
        data_start = 0
        
        for i, line in enumerate(lines):
            if 'Transaction Date' in line and 'Posted Date' in line:
                data_start = i + 1
                break
        
        for line in lines[data_start:]:
            if not line.strip():
                continue
                
            try:
                # Capital One format: Transaction Date, Posted Date, Card No., Description, Category, Debit, Credit
                parts = [part.strip() for part in line.split(',')]
                
                if len(parts) >= 7:
                    trans_date_str = parts[0]
                    posted_date_str = parts[1]
                    card_no = parts[2]
                    description = parts[3]
                    category = parts[4]
                    debit_str = parts[5]
                    credit_str = parts[6]
                    
                    # Parse dates
                    try:
                        trans_date = datetime.strptime(trans_date_str, '%m/%d/%Y')
                        posted_date = datetime.strptime(posted_date_str, '%m/%d/%Y')
                    except ValueError:
                        trans_date = posted_date = datetime.utcnow()
                    
                    # Determine amount and type
                    amount = Decimal('0.00')
                    if debit_str and debit_str.strip():
                        try:
                            amount = -Decimal(debit_str.replace('$', '').replace(',', ''))
                        except (ValueError, TypeError):
                            pass
                    elif credit_str and credit_str.strip():
                        try:
                            amount = Decimal(credit_str.replace('$', '').replace(',', ''))
                        except (ValueError, TypeError):
                            pass
                    
                    # Determine transaction type
                    if amount > 0:
                        tx_type = TransactionType.INCOME
                    else:
                        tx_type = TransactionType.EXPENSE
                    
                    transactions.append({
                        'date': trans_date,
                        'description': description,
                        'amount': amount,
                        'transaction_type': tx_type,
                        'reference': card_no,
                        'notes': f"Category: {category}",
                        'metadata': {
                            'bank_format': BankFormat.CAPITALONE,
                            'category': category,
                            'posted_date': posted_date.isoformat()
                        }
                    })
            except Exception as e:
                logger.warning(f"Failed to parse Capital One CSV line: {line}, error: {e}")
                continue
        
        return transactions
    
    def parse_generic_csv(self, csv_content: str) -> List[Dict[str, Any]]:
        """Parse generic CSV format"""
        transactions = []
        
        try:
            csv_file = io.StringIO(csv_content)
            reader = csv.DictReader(csv_file)
            
            for row in reader:
                try:
                    # Try to find common column names
                    date_col = None
                    amount_col = None
                    description_col = None
                    
                    for col in row.keys():
                        col_lower = col.lower()
                        if 'date' in col_lower:
                            date_col = col
                        elif 'amount' in col_lower or 'debit' in col_lower or 'credit' in col_lower:
                            amount_col = col
                        elif 'description' in col_lower or 'memo' in col_lower or 'note' in col_lower:
                            description_col = col
                    
                    if not all([date_col, amount_col, description_col]):
                        continue
                    
                    # Parse date
                    try:
                        date_str = row[date_col]
                        # Try common date formats
                        for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m/%d/%y', '%d/%m/%Y']:
                            try:
                                date = datetime.strptime(date_str, fmt)
                                break
                            except ValueError:
                                continue
                        else:
                            date = datetime.utcnow()
                    except (ValueError, TypeError):
                        date = datetime.utcnow()
                    
                    # Parse amount
                    try:
                        amount_str = row[amount_col]
                        amount = Decimal(str(amount_str).replace('$', '').replace(',', ''))
                    except (ValueError, TypeError):
                        amount = Decimal('0.00')
                    
                    # Determine transaction type
                    if amount > 0:
                        tx_type = TransactionType.INCOME
                    else:
                        tx_type = TransactionType.EXPENSE
                    
                    transactions.append({
                        'date': date,
                        'description': row[description_col] or 'Unknown',
                        'amount': amount,
                        'transaction_type': tx_type,
                        'notes': f"Generic CSV import",
                        'metadata': {
                            'bank_format': BankFormat.GENERIC,
                            'original_row': row
                        }
                    })
                except Exception as e:
                    logger.warning(f"Failed to parse generic CSV row: {row}, error: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to parse generic CSV: {e}")
        
        return transactions


class IngestionService:
    """Service for ingesting financial data from various sources"""
    
    def __init__(self):
        self.csv_parser = CSVParser()
    
    async def process_csv_file(
        self,
        file: UploadFile,
        organization_id: UUID,
        user_id: UUID,
        account_id: UUID,
        category_id: Optional[UUID] = None,
        auto_categorize: bool = True
    ) -> Dict[str, Any]:
        """Process uploaded CSV file and import transactions"""
        
        # Validate file
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a CSV file"
            )
        
        # Read file content
        try:
            content = await file.read()
            csv_content = content.decode('utf-8')
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to read file: {str(e)}"
            )
        
        # Detect format and parse
        format_detected = self.csv_parser.detect_format(csv_content)
        
        if format_detected == BankFormat.CHASE:
            transactions_data = self.csv_parser.parse_chase_csv(csv_content)
        elif format_detected == BankFormat.DISCOVER:
            transactions_data = self.csv_parser.parse_discover_csv(csv_content)
        elif format_detected == BankFormat.CAPITALONE:
            transactions_data = self.csv_parser.parse_capitalone_csv(csv_content)
        else:
            transactions_data = self.csv_parser.parse_generic_csv(csv_content)
        
        if not transactions_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid transactions found in CSV file"
            )
        
        # Auto-categorize if enabled
        if auto_categorize:
            transactions_data = await self._auto_categorize_transactions(
                transactions_data, organization_id
            )
        
        # Import transactions
        imported_count = 0
        failed_count = 0
        errors = []
        
        async with get_session() as session:
            for tx_data in transactions_data:
                try:
                    # Create transaction
                    transaction_create = TransactionCreate(
                        amount=tx_data['amount'],
                        description=tx_data['description'],
                        transaction_type=tx_data['transaction_type'],
                        date=tx_data['date'],
                        reference=tx_data.get('reference'),
                        notes=tx_data.get('notes'),
                        is_recurring=False,
                        organization_id=organization_id,
                        user_id=user_id,
                        account_id=account_id,
                        category_id=tx_data.get('category_id') or category_id,
                        metadata=tx_data.get('metadata', {})
                    )
                    
                    transaction = Transaction(**transaction_create.dict())
                    session.add(transaction)
                    imported_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    errors.append(f"Row {imported_count + failed_count}: {str(e)}")
                    logger.error(f"Failed to import transaction: {e}")
            
            # Commit all transactions
            try:
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to save transactions: {str(e)}"
                )
        
        return {
            "success": True,
            "message": f"CSV import completed",
            "data": {
                "format_detected": format_detected,
                "total_parsed": len(transactions_data),
                "imported_count": imported_count,
                "failed_count": failed_count,
                "errors": errors
            }
        }
    
    async def _auto_categorize_transactions(
        self,
        transactions_data: List[Dict[str, Any]],
        organization_id: UUID
    ) -> List[Dict[str, Any]]:
        """Auto-categorize transactions based on description patterns"""
        
        # Get existing categories for the organization
        async with get_session() as session:
            statement = select(Category).where(
                Category.organization_id == organization_id,
                Category.is_active == True
            )
            result = await session.exec(statement)
            categories = result.all()
        
        # Create category mapping patterns
        category_patterns = {}
        for category in categories:
            if category.name.lower() in ['food', 'dining', 'restaurant', 'groceries']:
                category_patterns['food'] = category.id
            elif category.name.lower() in ['gas', 'fuel', 'transportation', 'uber', 'lyft']:
                category_patterns['transportation'] = category.id
            elif category.name.lower() in ['shopping', 'amazon', 'walmart', 'target']:
                category_patterns['shopping'] = category.id
            elif category.name.lower() in ['utilities', 'electric', 'water', 'internet']:
                category_patterns['utilities'] = category.id
            elif category.name.lower() in ['healthcare', 'medical', 'doctor', 'pharmacy']:
                category_patterns['healthcare'] = category.id
            elif category.name.lower() in ['entertainment', 'netflix', 'spotify', 'movie']:
                category_patterns['entertainment'] = category.id
        
        # Apply categorization
        for tx_data in transactions_data:
            description_lower = tx_data['description'].lower()
            
            # Food patterns
            if any(word in description_lower for word in ['restaurant', 'cafe', 'pizza', 'burger', 'chipotle', 'starbucks']):
                tx_data['category_id'] = category_patterns.get('food')
            
            # Transportation patterns
            elif any(word in description_lower for word in ['gas', 'fuel', 'uber', 'lyft', 'taxi', 'parking']):
                tx_data['category_id'] = category_patterns.get('transportation')
            
            # Shopping patterns
            elif any(word in description_lower for word in ['amazon', 'walmart', 'target', 'costco', 'macy']):
                tx_data['category_id'] = category_patterns.get('shopping')
            
            # Utilities patterns
            elif any(word in description_lower for word in ['electric', 'water', 'gas bill', 'internet', 'phone']):
                tx_data['category_id'] = category_patterns.get('utilities')
            
            # Healthcare patterns
            elif any(word in description_lower for word in ['doctor', 'pharmacy', 'medical', 'hospital', 'dental']):
                tx_data['category_id'] = category_patterns.get('healthcare')
            
            # Entertainment patterns
            elif any(word in description_lower for word in ['netflix', 'spotify', 'movie', 'theater', 'concert']):
                tx_data['category_id'] = category_patterns.get('entertainment')
        
        return transactions_data
    
    async def get_import_history(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get import history for an organization"""
        
        async with get_session() as session:
            # Get transactions with import metadata
            statement = select(Transaction).where(
                Transaction.organization_id == organization_id,
                Transaction.metadata.contains({"bank_format": True}),
                Transaction.deleted_at.is_(None)
            ).order_by(Transaction.created_at.desc()).offset(skip).limit(limit)
            
            result = await session.exec(statement)
            transactions = result.all()
        
        # Group by import session
        import_sessions = {}
        for tx in transactions:
            metadata = tx.metadata or {}
            bank_format = metadata.get('bank_format', 'unknown')
            import_key = f"{bank_format}_{tx.created_at.date().isoformat()}"
            
            if import_key not in import_sessions:
                import_sessions[import_key] = {
                    'bank_format': bank_format,
                    'import_date': tx.created_at.date().isoformat(),
                    'transaction_count': 0,
                    'total_amount': Decimal('0.00'),
                    'categories': set()
                }
            
            import_sessions[import_key]['transaction_count'] += 1
            import_sessions[import_key]['total_amount'] += tx.amount
            
            if tx.category_id:
                import_sessions[import_key]['categories'].add(str(tx.category_id))
        
        # Convert to list format
        history = []
        for session_data in import_sessions.values():
            history.append({
                'bank_format': session_data['bank_format'],
                'import_date': session_data['import_date'],
                'transaction_count': session_data['transaction_count'],
                'total_amount': float(session_data['total_amount']),
                'category_count': len(session_data['categories'])
            })
        
        return history


# Global ingestion service instance
ingestion_service = IngestionService()


# Export functions and classes
__all__ = [
    "IngestionService",
    "CSVParser",
    "BankFormat",
    "ingestion_service"
]