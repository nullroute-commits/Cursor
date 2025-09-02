"""
File Processing Service

Handles file upload, parsing, and data extraction for financial data imports.
Supports CSV, Excel, and PDF file formats.
"""

import os
import csv
import logging
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from io import StringIO, BytesIO
import pandas as pd
import PyPDF2
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from ..models import ImportHistory, Transaction, Account, Category, Tag
from app.core.audit import audit_logger

logger = logging.getLogger(__name__)


class FileProcessorError(Exception):
    """Custom exception for file processing errors"""
    pass


class BaseFileProcessor:
    """Base class for file processors"""
    
    def __init__(self, import_history: ImportHistory):
        self.import_history = import_history
        self.file_path = import_history.file_path if hasattr(import_history, 'file_path') else None
        self.processed_data = []
        self.errors = []
        
    def process(self) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Process the file and return processed data and errors"""
        raise NotImplementedError("Subclasses must implement process method")
    
    def validate_file(self) -> bool:
        """Validate the uploaded file"""
        if not self.file_path or not default_storage.exists(self.file_path):
            raise FileProcessorError("File not found")
        
        file_size = default_storage.size(self.file_path)
        if file_size > settings.MAX_FILE_SIZE:
            raise FileProcessorError(f"File size {file_size} exceeds maximum allowed size")
        
        return True
    
    def log_processing_start(self):
        """Log the start of file processing"""
        self.import_history.status = 'processing'
        self.import_history.started_at = timezone.now()
        self.import_history.save()
        
        audit_logger.info(
            f"Started processing file: {self.import_history.filename}",
            extra={
                'user_id': self.import_history.user.id,
                'import_id': str(self.import_history.id),
                'file_size': self.import_history.file_size,
                'file_type': self.import_history.file_type
            }
        )
    
    def log_processing_complete(self, success: bool):
        """Log the completion of file processing"""
        self.import_history.completed_at = timezone.now()
        self.import_history.status = 'completed' if success else 'failed'
        self.import_history.processed_records = len(self.processed_data)
        self.import_history.failed_records = len(self.errors)
        if self.errors:
            self.import_history.error_log = '\n'.join(self.errors[:1000])  # Limit error log size
        self.import_history.save()
        
        audit_logger.info(
            f"Completed processing file: {self.import_history.filename}",
            extra={
                'user_id': self.import_history.user.id,
                'import_id': str(self.import_history.id),
                'success': success,
                'processed_records': len(self.processed_data),
                'failed_records': len(self.errors)
            }
        )


class CSVFileProcessor(BaseFileProcessor):
    """Process CSV files for financial data import"""
    
    def process(self) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Process CSV file and extract financial data"""
        try:
            self.log_processing_start()
            self.validate_file()
            
            # Read CSV file
            with default_storage.open(self.file_path, 'r') as file:
                content = file.read().decode('utf-8')
            
            # Parse CSV content
            csv_data = csv.DictReader(StringIO(content))
            
            # Process each row
            for row_num, row in enumerate(csv_data, start=2):  # Start at 2 to account for header
                try:
                    processed_row = self._process_row(row, row_num)
                    if processed_row:
                        self.processed_data.append(processed_row)
                except Exception as e:
                    error_msg = f"Row {row_num}: {str(e)}"
                    self.errors.append(error_msg)
                    logger.error(f"Error processing CSV row {row_num}: {e}")
            
            success = len(self.errors) == 0 or len(self.processed_data) > 0
            self.log_processing_complete(success)
            
            return self.processed_data, self.errors
            
        except Exception as e:
            error_msg = f"CSV processing failed: {str(e)}"
            self.errors.append(error_msg)
            logger.error(f"CSV processing error: {e}")
            self.log_processing_complete(False)
            raise FileProcessorError(error_msg)
    
    def _process_row(self, row: Dict[str, str], row_num: int) -> Optional[Dict[str, Any]]:
        """Process a single CSV row"""
        # Extract and validate required fields
        description = row.get('description', '').strip()
        amount_str = row.get('amount', '').strip()
        date_str = row.get('date', '').strip()
        
        if not description:
            raise ValueError("Description is required")
        
        if not amount_str:
            raise ValueError("Amount is required")
        
        if not date_str:
            raise ValueError("Date is required")
        
        # Parse amount
        try:
            amount = Decimal(amount_str.replace('$', '').replace(',', ''))
        except InvalidOperation:
            raise ValueError(f"Invalid amount format: {amount_str}")
        
        # Parse date
        try:
            # Try multiple date formats
            for date_format in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
                try:
                    transaction_date = datetime.strptime(date_str, date_format).date()
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Invalid date format: {date_str}")
        except Exception:
            raise ValueError(f"Invalid date format: {date_str}")
        
        # Build processed row
        processed_row = {
            'description': description,
            'amount': amount,
            'transaction_date': transaction_date,
            'posted_date': transaction_date,  # Default to transaction date
            'reference_number': row.get('reference', '').strip(),
            'check_number': row.get('check_number', '').strip(),
            'notes': row.get('notes', '').strip(),
            'category_name': row.get('category', '').strip(),
            'tags': [tag.strip() for tag in row.get('tags', '').split(',') if tag.strip()],
            'raw_data': row  # Keep original row data for reference
        }
        
        return processed_row


class ExcelFileProcessor(BaseFileProcessor):
    """Process Excel files for financial data import"""
    
    def process(self) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Process Excel file and extract financial data"""
        try:
            self.log_processing_start()
            self.validate_file()
            
            # Read Excel file
            with default_storage.open(self.file_path, 'rb') as file:
                df = pd.read_excel(file, engine='openpyxl')
            
            # Convert DataFrame to list of dictionaries
            excel_data = df.to_dict('records')
            
            # Process each row
            for row_num, row in enumerate(excel_data, start=2):
                try:
                    processed_row = self._process_row(row, row_num)
                    if processed_row:
                        self.processed_data.append(processed_row)
                except Exception as e:
                    error_msg = f"Row {row_num}: {str(e)}"
                    self.errors.append(error_msg)
                    logger.error(f"Error processing Excel row {row_num}: {e}")
            
            success = len(self.errors) == 0 or len(self.processed_data) > 0
            self.log_processing_complete(success)
            
            return self.processed_data, self.errors
            
        except Exception as e:
            error_msg = f"Excel processing failed: {str(e)}"
            self.errors.append(error_msg)
            logger.error(f"Excel processing error: {e}")
            self.log_processing_complete(False)
            raise FileProcessorError(error_msg)
    
    def _process_row(self, row: Dict[str, Any], row_num: int) -> Optional[Dict[str, Any]]:
        """Process a single Excel row"""
        # Extract and validate required fields
        description = str(row.get('description', '')).strip()
        amount_val = row.get('amount')
        date_val = row.get('date')
        
        if not description or description == 'nan':
            raise ValueError("Description is required")
        
        if amount_val is None or pd.isna(amount_val):
            raise ValueError("Amount is required")
        
        if date_val is None or pd.isna(date_val):
            raise ValueError("Date is required")
        
        # Parse amount
        try:
            if isinstance(amount_val, str):
                amount = Decimal(amount_val.replace('$', '').replace(',', ''))
            else:
                amount = Decimal(str(amount_val))
        except InvalidOperation:
            raise ValueError(f"Invalid amount format: {amount_val}")
        
        # Parse date
        try:
            if isinstance(date_val, str):
                # Try multiple date formats
                for date_format in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
                    try:
                        transaction_date = datetime.strptime(date_val, date_format).date()
                        break
                    except ValueError:
                        continue
                else:
                    raise ValueError(f"Invalid date format: {date_val}")
            elif isinstance(date_val, datetime):
                transaction_date = date_val.date()
            elif isinstance(date_val, date):
                transaction_date = date_val
            else:
                raise ValueError(f"Invalid date format: {date_val}")
        except Exception:
            raise ValueError(f"Invalid date format: {date_val}")
        
        # Build processed row
        processed_row = {
            'description': description,
            'amount': amount,
            'transaction_date': transaction_date,
            'posted_date': transaction_date,
            'reference_number': str(row.get('reference', '')).strip() if row.get('reference') else '',
            'check_number': str(row.get('check_number', '')).strip() if row.get('check_number') else '',
            'notes': str(row.get('notes', '')).strip() if row.get('notes') else '',
            'category_name': str(row.get('category', '')).strip() if row.get('category') else '',
            'tags': [str(tag).strip() for tag in str(row.get('tags', '')).split(',') if row.get('tags') else []],
            'raw_data': row
        }
        
        return processed_row


class PDFFileProcessor(BaseFileProcessor):
    """Process PDF files for financial data import"""
    
    def process(self) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Process PDF file and extract financial data"""
        try:
            self.log_processing_start()
            self.validate_file()
            
            # Read PDF file
            with default_storage.open(self.file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract text from all pages
                text_content = ""
                for page in pdf_reader.pages:
                    text_content += page.extract_text()
            
            # Parse extracted text
            processed_data = self._parse_pdf_text(text_content)
            self.processed_data = processed_data
            
            success = len(self.errors) == 0 or len(self.processed_data) > 0
            self.log_processing_complete(success)
            
            return self.processed_data, self.errors
            
        except Exception as e:
            error_msg = f"PDF processing failed: {str(e)}"
            self.errors.append(error_msg)
            logger.error(f"PDF processing error: {e}")
            self.log_processing_complete(False)
            raise FileProcessorError(error_msg)
    
    def _parse_pdf_text(self, text_content: str) -> List[Dict[str, Any]]:
        """Parse extracted PDF text to find financial data"""
        processed_data = []
        
        # Split text into lines
        lines = text_content.split('\n')
        
        # Look for patterns that might indicate financial transactions
        for line_num, line in enumerate(lines, 1):
            try:
                # Look for amount patterns (e.g., $123.45, -$123.45, 123.45)
                import re
                amount_pattern = r'[\$]?[-]?[\d,]+\.\d{2}'
                amounts = re.findall(amount_pattern, line)
                
                if amounts:
                    # Try to extract transaction information from this line
                    processed_row = self._extract_transaction_from_line(line, amounts[0], line_num)
                    if processed_row:
                        processed_data.append(processed_row)
                        
            except Exception as e:
                error_msg = f"Line {line_num}: Error parsing PDF text: {str(e)}"
                self.errors.append(error_msg)
                logger.warning(f"Error parsing PDF line {line_num}: {e}")
        
        return processed_data
    
    def _extract_transaction_from_line(self, line: str, amount_str: str, line_num: int) -> Optional[Dict[str, Any]]:
        """Extract transaction information from a PDF text line"""
        try:
            # Parse amount
            amount = Decimal(amount_str.replace('$', '').replace(',', ''))
            
            # Try to extract description (everything before the amount)
            amount_index = line.find(amount_str)
            if amount_index > 0:
                description = line[:amount_index].strip()
            else:
                description = line.strip()
            
            # Skip if description is too short or looks like a header
            if len(description) < 3 or description.upper() in ['DATE', 'DESCRIPTION', 'AMOUNT', 'BALANCE']:
                return None
            
            # Try to extract date from the line or use current date
            transaction_date = self._extract_date_from_line(line) or date.today()
            
            processed_row = {
                'description': description,
                'amount': amount,
                'transaction_date': transaction_date,
                'posted_date': transaction_date,
                'reference_number': '',
                'check_number': '',
                'notes': f"Extracted from PDF line {line_num}",
                'category_name': '',
                'tags': ['pdf-import'],
                'raw_data': {'line': line, 'line_number': line_num}
            }
            
            return processed_row
            
        except Exception as e:
            error_msg = f"Line {line_num}: Error extracting transaction: {str(e)}"
            self.errors.append(error_msg)
            return None
    
    def _extract_date_from_line(self, line: str) -> Optional[date]:
        """Extract date from a text line"""
        import re
        
        # Common date patterns
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY or DD/MM/YYYY
            r'\d{4}-\d{1,2}-\d{1,2}',  # YYYY-MM-DD
            r'\d{1,2}-\d{1,2}-\d{4}',  # MM-DD-YYYY or DD-MM-YYYY
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, line)
            if matches:
                date_str = matches[0]
                try:
                    # Try multiple date formats
                    for date_format in ['%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d', '%m-%d-%Y', '%d-%m-%Y']:
                        try:
                            return datetime.strptime(date_str, date_format).date()
                        except ValueError:
                            continue
                except Exception:
                    continue
        
        return None


class FileProcessorFactory:
    """Factory for creating appropriate file processors"""
    
    @staticmethod
    def create_processor(import_history: ImportHistory) -> BaseFileProcessor:
        """Create the appropriate file processor based on file type"""
        file_type = import_history.file_type.lower()
        
        if file_type == 'csv':
            return CSVFileProcessor(import_history)
        elif file_type in ['xlsx', 'xls']:
            return ExcelFileProcessor(import_history)
        elif file_type == 'pdf':
            return PDFFileProcessor(import_history)
        else:
            raise FileProcessorError(f"Unsupported file type: {file_type}")


class DataImportService:
    """Service for importing processed financial data"""
    
    def __init__(self, import_history: ImportHistory, user):
        self.import_history = import_history
        self.user = user
        self.imported_transactions = []
        self.import_errors = []
    
    def import_data(self, processed_data: List[Dict[str, Any]]) -> Tuple[List[Transaction], List[str]]:
        """Import processed data into the database"""
        try:
            for row in processed_data:
                try:
                    transaction = self._create_transaction(row)
                    if transaction:
                        self.imported_transactions.append(transaction)
                except Exception as e:
                    error_msg = f"Import error for row: {str(e)}"
                    self.import_errors.append(error_msg)
                    logger.error(f"Error importing row: {e}")
            
            return self.imported_transactions, self.import_errors
            
        except Exception as e:
            error_msg = f"Data import failed: {str(e)}"
            self.import_errors.append(error_msg)
            logger.error(f"Data import error: {e}")
            raise FileProcessorError(error_msg)
    
    def _create_transaction(self, row: Dict[str, Any]) -> Optional[Transaction]:
        """Create a transaction from processed data"""
        try:
            # Get or create default account for the user
            account = self._get_default_account()
            
            # Get or create category
            category = None
            if row.get('category_name'):
                category = self._get_or_create_category(row['category_name'])
            
            # Get or create tags
            tags = []
            for tag_name in row.get('tags', []):
                tag = self._get_or_create_tag(tag_name)
                if tag:
                    tags.append(tag)
            
            # Create transaction
            transaction = Transaction.objects.create(
                account=account,
                description=row['description'],
                amount=row['amount'],
                transaction_type='expense' if row['amount'] < 0 else 'income',
                category=category,
                transaction_date=row['transaction_date'],
                posted_date=row.get('posted_date', row['transaction_date']),
                reference_number=row.get('reference_number', ''),
                check_number=row.get('check_number', ''),
                notes=row.get('notes', ''),
                is_reconciled=False
            )
            
            # Add tags
            if tags:
                transaction.tags.set(tags)
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            raise
    
    def _get_default_account(self) -> Account:
        """Get or create a default account for the user"""
        account, created = Account.objects.get_or_create(
            user=self.user,
            name="Default Account",
            defaults={
                'account_type': 'checking',
                'balance': Decimal('0.00'),
                'currency': 'USD'
            }
        )
        return account
    
    def _get_or_create_category(self, category_name: str) -> Optional[Category]:
        """Get or create a category"""
        if not category_name:
            return None
        
        category, created = Category.objects.get_or_create(
            name=category_name,
            defaults={
                'color': '#3B82F6',
                'is_active': True
            }
        )
        return category
    
    def _get_or_create_tag(self, tag_name: str) -> Optional[Tag]:
        """Get or create a tag"""
        if not tag_name:
            return None
        
        tag, created = Tag.objects.get_or_create(
            name=tag_name,
            defaults={
                'color': '#6B7280',
                'is_active': True,
                'created_by': self.user
            }
        )
        return tag