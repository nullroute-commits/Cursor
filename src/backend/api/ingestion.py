"""
Ingestion API router for Financial Analytics Platform
Handles CSV file uploads and data ingestion
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy import select, func

from src.backend.services.auth_service import get_current_user, get_current_active_user
from src.backend.services.ingestion_service import ingestion_service
from src.backend.services.transaction_service import transaction_service
from src.backend.models.database import User, Transaction
from src.common.models.base import BaseResponse
from src.backend.database import get_session

router = APIRouter()


@router.post("/csv", response_model=dict)
async def upload_csv_file(
    file: UploadFile = File(..., description="CSV file to upload"),
    account_id: UUID = Form(..., description="Account ID to associate transactions with"),
    category_id: Optional[UUID] = Form(None, description="Default category ID for transactions"),
    auto_categorize: bool = Form(True, description="Enable automatic categorization"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload and process CSV file for transaction ingestion
    
    Supports multiple bank formats:
    - Chase Bank
    - Discover Card
    - Capital One
    - Generic CSV
    """
    
    try:
        result = await ingestion_service.process_csv_file(
            file=file,
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            account_id=account_id,
            category_id=category_id,
            auto_categorize=auto_categorize
        )
        
        return {
            "success": True,
            "message": "CSV file processed successfully",
            "data": result["data"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process CSV file: {str(e)}"
        )


@router.get("/history", response_model=dict)
async def get_import_history(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_active_user)
):
    """Get import history for the current user's organization"""
    
    try:
        history = await ingestion_service.get_import_history(
            organization_id=current_user.organization_id,
            skip=skip,
            limit=limit
        )
        
        return {
            "success": True,
            "message": "Import history retrieved successfully",
            "data": {
                "imports": history,
                "total_count": len(history),
                "pagination": {
                    "skip": skip,
                    "limit": limit
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve import history: {str(e)}"
        )


@router.get("/formats", response_model=dict)
async def get_supported_formats():
    """Get list of supported bank CSV formats"""
    
    formats = [
        {
            "id": "chase",
            "name": "Chase Bank",
            "description": "Chase Bank CSV export format",
            "columns": ["Details", "Posting Date", "Description", "Amount", "Type", "Balance", "Check or Slip #"],
            "example": "Details,Posting Date,Description,Amount,Type,Balance,Check or Slip #"
        },
        {
            "id": "discover",
            "name": "Discover Card",
            "description": "Discover Card CSV export format",
            "columns": ["Trans Date", "Post Date", "Description", "Category", "Amount"],
            "example": "Trans Date,Post Date,Description,Category,Amount"
        },
        {
            "id": "capitalone",
            "name": "Capital One",
            "description": "Capital One CSV export format",
            "columns": ["Transaction Date", "Posted Date", "Card No.", "Description", "Category", "Debit", "Credit"],
            "example": "Transaction Date,Posted Date,Card No.,Description,Category,Debit,Credit"
        },
        {
            "id": "generic",
            "name": "Generic CSV",
            "description": "Generic CSV with date, amount, and description columns",
            "columns": ["Date", "Amount", "Description"],
            "example": "Date,Amount,Description"
        }
    ]
    
    return {
        "success": True,
        "message": "Supported formats retrieved successfully",
        "data": {
            "formats": formats,
            "total_count": len(formats)
        }
    }


@router.get("/template/{format_id}", response_model=dict)
async def download_csv_template(format_id: str):
    """Download CSV template for a specific bank format"""
    
    templates = {
        "chase": {
            "filename": "chase_template.csv",
            "content": "Details,Posting Date,Description,Amount,Type,Balance,Check or Slip #\nSample Transaction,01/15/2024,Sample Description,-50.00,DEBIT,1000.00,12345"
        },
        "discover": {
            "filename": "discover_template.csv",
            "content": "Trans Date,Post Date,Description,Category,Amount\n01/15/2024,01/16/2024,Sample Transaction,Shopping,-50.00"
        },
        "capitalone": {
            "filename": "capitalone_template.csv",
            "content": "Transaction Date,Posted Date,Card No.,Description,Category,Debit,Credit\n01/15/2024,01/16/2024,1234****5678,Sample Transaction,Shopping,50.00,"
        },
        "generic": {
            "filename": "generic_template.csv",
            "content": "Date,Amount,Description,Category\n01/15/2024,-50.00,Sample Transaction,Shopping"
        }
    }
    
    if format_id not in templates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template not found for format: {format_id}"
        )
    
    template = templates[format_id]
    
    return {
        "success": True,
        "message": f"Template for {format_id} format",
        "data": {
            "format_id": format_id,
            "filename": template["filename"],
            "content": template["content"],
            "columns": template["content"].split('\n')[0].split(',')
        }
    }


@router.post("/validate", response_model=dict)
async def validate_csv_format(
    file: UploadFile = File(..., description="CSV file to validate"),
    current_user: User = Depends(get_current_active_user)
):
    """Validate CSV file format without importing data"""
    
    try:
        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Detect format
        format_detected = ingestion_service.csv_parser.detect_format(csv_content)
        
        # Parse without saving to get transaction count
        if format_detected == "chase":
            transactions_data = ingestion_service.csv_parser.parse_chase_csv(csv_content)
        elif format_detected == "discover":
            transactions_data = ingestion_service.csv_parser.parse_discover_csv(csv_content)
        elif format_detected == "capitalone":
            transactions_data = ingestion_service.csv_parser.parse_capitalone_csv(csv_content)
        else:
            transactions_data = ingestion_service.csv_parser.parse_generic_csv(csv_content)
        
        # Analyze data
        total_amount = sum(abs(tx['amount']) for tx in transactions_data)
        income_count = len([tx for tx in transactions_data if tx['amount'] > 0])
        expense_count = len([tx for tx in transactions_data if tx['amount'] < 0])
        
        return {
            "success": True,
            "message": "CSV file validated successfully",
            "data": {
                "format_detected": format_detected,
                "total_transactions": len(transactions_data),
                "total_amount": float(total_amount),
                "income_transactions": income_count,
                "expense_transactions": expense_count,
                "sample_transactions": transactions_data[:5] if transactions_data else [],
                "validation": {
                    "is_valid": len(transactions_data) > 0,
                    "errors": [],
                    "warnings": []
                }
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": "CSV validation failed",
            "data": {
                "format_detected": "unknown",
                "total_transactions": 0,
                "total_amount": 0.0,
                "income_transactions": 0,
                "expense_transactions": 0,
                "sample_transactions": [],
                "validation": {
                    "is_valid": False,
                    "errors": [str(e)],
                    "warnings": []
                }
            }
        }


@router.get("/stats", response_model=dict)
async def get_ingestion_stats(
    current_user: User = Depends(get_current_active_user)
):
    """Get ingestion statistics for the organization"""
    
    try:
        # Get import history
        history = await ingestion_service.get_import_history(
            organization_id=current_user.organization_id,
            limit=1000  # Get all history for stats
        )
        
        # Calculate statistics
        total_imports = len(history)
        total_transactions = sum(imp['transaction_count'] for imp in history)
        total_amount = sum(imp['total_amount'] for imp in history)
        
        # Format breakdown
        format_breakdown = {}
        for imp in history:
            format_name = imp['bank_format']
            if format_name not in format_breakdown:
                format_breakdown[format_name] = {
                    'import_count': 0,
                    'transaction_count': 0,
                    'total_amount': 0.0
                }
            
            format_breakdown[format_name]['import_count'] += 1
            format_breakdown[format_name]['transaction_count'] += imp['transaction_count']
            format_breakdown[format_name]['total_amount'] += imp['total_amount']
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        recent_imports = [imp for imp in history if datetime.fromisoformat(imp['import_date']).date() >= thirty_days_ago]
        recent_transactions = sum(imp['transaction_count'] for imp in recent_imports)
        
        return {
            "success": True,
            "message": "Ingestion statistics retrieved successfully",
            "data": {
                "overview": {
                    "total_imports": total_imports,
                    "total_transactions": total_transactions,
                    "total_amount": total_amount,
                    "recent_imports_30d": len(recent_imports),
                    "recent_transactions_30d": recent_transactions
                },
                "format_breakdown": format_breakdown,
                "recent_activity": {
                    "last_import": history[0]['import_date'] if history else None,
                    "last_import_format": history[0]['bank_format'] if history else None,
                    "last_import_count": history[0]['transaction_count'] if history else None
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve ingestion statistics: {str(e)}"
        )


@router.delete("/history/{import_id}", response_model=dict)
async def delete_import_session(
    import_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete all transactions from a specific import session"""
    
    try:
        # Parse import_id (format: bank_format_YYYY-MM-DD)
        if '_' not in import_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid import ID format"
            )
        
        bank_format, date_str = import_id.split('_', 1)
        
        # Get transactions from this import session
        async with get_session() as session:
            statement = select(Transaction).where(
                Transaction.organization_id == current_user.organization_id,
                Transaction.metadata.contains({"bank_format": bank_format}),
                func.date(Transaction.created_at) == date_str,
                Transaction.deleted_at.is_(None)
            )
            
            result = await session.exec(statement)
            transactions = result.all()
            
            if not transactions:
                return {
                    "success": True,
                    "message": "No transactions found for this import session",
                    "data": {"deleted_count": 0}
                }
            
            # Soft delete transactions
            deleted_count = 0
            for transaction in transactions:
                transaction.deleted_at = datetime.utcnow()
                transaction.is_active = False
                deleted_count += 1
            
            await session.commit()
            
            return {
                "success": True,
                "message": f"Import session deleted successfully",
                "data": {
                    "import_id": import_id,
                    "deleted_count": deleted_count,
                    "bank_format": bank_format,
                    "import_date": date_str
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete import session: {str(e)}"
        )


@router.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint for ingestion service"""
    
    return {
        "success": True,
        "message": "Ingestion service is healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "ingestion",
        "status": "operational"
    }