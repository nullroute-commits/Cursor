"""
Transactions API router for Financial Analytics Platform
Handles transaction CRUD operations and financial analysis
"""

from datetime import datetime, date
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.responses import StreamingResponse

from src.backend.services.auth_service import get_current_user, get_current_active_user
from src.backend.services.transaction_service import transaction_service
from src.backend.models.database import User, TransactionCreate, TransactionUpdate
from src.common.models.base import BaseResponse
from src.common.models.enums import TransactionType

router = APIRouter()


@router.post("/", response_model=dict)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new transaction"""
    
    try:
        transaction = await transaction_service.create_transaction(
            transaction_data=transaction_data.dict(),
            user_id=current_user.id,
            organization_id=current_user.organization_id
        )
        
        return {
            "success": True,
            "message": "Transaction created successfully",
            "data": {
                "transaction_id": str(transaction.id),
                "description": transaction.description,
                "amount": float(transaction.amount),
                "date": transaction.date.isoformat(),
                "created_at": transaction.created_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create transaction: {str(e)}"
        )


@router.get("/", response_model=dict)
async def get_transactions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    account_id: Optional[UUID] = Query(None, description="Filter by account ID"),
    category_id: Optional[UUID] = Query(None, description="Filter by category ID"),
    transaction_type: Optional[TransactionType] = Query(None, description="Filter by transaction type"),
    start_date: Optional[date] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Search in description, notes, or reference"),
    order_by: str = Query("date", description="Order by field (date, amount, created_at)"),
    order_direction: str = Query("desc", description="Order direction (asc, desc)"),
    current_user: User = Depends(get_current_active_user)
):
    """Get transactions with filtering and pagination"""
    
    try:
        transactions = await transaction_service.get_transactions(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            account_id=account_id,
            category_id=category_id,
            transaction_type=transaction_type,
            start_date=start_date,
            end_date=end_date,
            search=search,
            skip=skip,
            limit=limit,
            order_by=order_by,
            order_direction=order_direction
        )
        
        # Convert to response format
        transaction_list = []
        for tx in transactions:
            transaction_list.append({
                "id": str(tx.id),
                "description": tx.description,
                "amount": float(tx.amount),
                "transaction_type": tx.transaction_type.value,
                "date": tx.date.isoformat(),
                "reference": tx.reference,
                "notes": tx.notes,
                "is_recurring": tx.is_recurring,
                "category": {
                    "id": str(tx.category.id),
                    "name": tx.category.name,
                    "color": tx.category.color
                } if tx.category else None,
                "account": {
                    "id": str(tx.account.id),
                    "name": tx.account.name,
                    "account_type": tx.account.account_type.value
                } if tx.account else None,
                "created_at": tx.created_at.isoformat(),
                "updated_at": tx.updated_at.isoformat()
            })
        
        return {
            "success": True,
            "message": "Transactions retrieved successfully",
            "data": {
                "transactions": transaction_list,
                "total_count": len(transaction_list),
                "pagination": {
                    "skip": skip,
                    "limit": limit,
                    "has_more": len(transaction_list) == limit
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve transactions: {str(e)}"
        )


@router.get("/{transaction_id}", response_model=dict)
async def get_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific transaction by ID"""
    
    try:
        transaction = await transaction_service.get_transaction(
            transaction_id=transaction_id,
            user_id=current_user.id,
            organization_id=current_user.organization_id
        )
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        return {
            "success": True,
            "message": "Transaction retrieved successfully",
            "data": {
                "id": str(transaction.id),
                "description": transaction.description,
                "amount": float(transaction.amount),
                "transaction_type": transaction.transaction_type.value,
                "date": transaction.date.isoformat(),
                "reference": transaction.reference,
                "notes": transaction.notes,
                "is_recurring": transaction.is_recurring,
                "category": {
                    "id": str(transaction.category.id),
                    "name": transaction.category.name,
                    "color": transaction.category.color
                } if transaction.category else None,
                "account": {
                    "id": str(transaction.account.id),
                    "name": transaction.account.name,
                    "account_type": transaction.account.account_type.value
                } if transaction.account else None,
                "metadata": transaction.metadata,
                "created_at": transaction.created_at.isoformat(),
                "updated_at": transaction.updated_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve transaction: {str(e)}"
        )


@router.put("/{transaction_id}", response_model=dict)
async def update_transaction(
    transaction_id: UUID,
    transaction_update: TransactionUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update a transaction"""
    
    try:
        transaction = await transaction_service.update_transaction(
            transaction_id=transaction_id,
            transaction_update=transaction_update,
            user_id=current_user.id,
            organization_id=current_user.organization_id
        )
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        return {
            "success": True,
            "message": "Transaction updated successfully",
            "data": {
                "id": str(transaction.id),
                "description": transaction.description,
                "amount": float(transaction.amount),
                "transaction_type": transaction.transaction_type.value,
                "date": transaction.date.isoformat(),
                "updated_at": transaction.updated_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update transaction: {str(e)}"
        )


@router.delete("/{transaction_id}", response_model=dict)
async def delete_transaction(
    transaction_id: UUID,
    hard_delete: bool = Query(False, description="Perform hard delete instead of soft delete"),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a transaction"""
    
    try:
        success = await transaction_service.delete_transaction(
            transaction_id=transaction_id,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            hard_delete=hard_delete
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        delete_type = "hard delete" if hard_delete else "soft delete"
        return {
            "success": True,
            "message": f"Transaction {delete_type} completed successfully",
            "data": {
                "transaction_id": str(transaction_id),
                "delete_type": delete_type
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete transaction: {str(e)}"
        )


@router.get("/summary/overview", response_model=dict)
async def get_transaction_summary(
    start_date: Optional[date] = Query(None, description="Start date for summary (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for summary (YYYY-MM-DD)"),
    account_id: Optional[UUID] = Query(None, description="Filter by account ID"),
    current_user: User = Depends(get_current_active_user)
):
    """Get transaction summary statistics"""
    
    try:
        summary = await transaction_service.get_transaction_summary(
            organization_id=current_user.organization_id,
            start_date=start_date,
            end_date=end_date,
            account_id=account_id,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "message": "Transaction summary retrieved successfully",
            "data": summary
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve transaction summary: {str(e)}"
        )


@router.get("/summary/categories", response_model=dict)
async def get_category_breakdown(
    start_date: Optional[date] = Query(None, description="Start date for breakdown (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for breakdown (YYYY-MM-DD)"),
    account_id: Optional[UUID] = Query(None, description="Filter by account ID"),
    current_user: User = Depends(get_current_active_user)
):
    """Get spending breakdown by category"""
    
    try:
        breakdown = await transaction_service.get_category_breakdown(
            organization_id=current_user.organization_id,
            start_date=start_date,
            end_date=end_date,
            account_id=account_id,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "message": "Category breakdown retrieved successfully",
            "data": {
                "categories": breakdown,
                "total_categories": len(breakdown),
                "total_spending": sum(cat["total_amount"] for cat in breakdown)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve category breakdown: {str(e)}"
        )


@router.get("/trends/monthly", response_model=dict)
async def get_monthly_trends(
    months: int = Query(12, ge=1, le=60, description="Number of months to analyze"),
    account_id: Optional[UUID] = Query(None, description="Filter by account ID"),
    current_user: User = Depends(get_current_active_user)
):
    """Get monthly spending and income trends"""
    
    try:
        trends = await transaction_service.get_monthly_trends(
            organization_id=current_user.organization_id,
            months=months,
            account_id=account_id,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "message": "Monthly trends retrieved successfully",
            "data": {
                "trends": trends,
                "months_analyzed": months,
                "total_months": len(trends)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve monthly trends: {str(e)}"
        )


@router.get("/recurring", response_model=dict)
async def get_recurring_transactions(
    current_user: User = Depends(get_current_active_user)
):
    """Identify potential recurring transactions"""
    
    try:
        recurring = await transaction_service.get_recurring_transactions(
            organization_id=current_user.organization_id,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "message": "Recurring transactions identified successfully",
            "data": {
                "recurring_transactions": recurring,
                "total_recurring": len(recurring)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to identify recurring transactions: {str(e)}"
        )


@router.put("/bulk/update", response_model=dict)
async def bulk_update_transactions(
    transaction_ids: List[UUID] = Body(..., description="List of transaction IDs to update"),
    updates: dict = Body(..., description="Fields to update for all transactions"),
    current_user: User = Depends(get_current_active_user)
):
    """Bulk update multiple transactions"""
    
    try:
        result = await transaction_service.bulk_update_transactions(
            transaction_ids=transaction_ids,
            updates=updates,
            user_id=current_user.id,
            organization_id=current_user.organization_id
        )
        
        return {
            "success": True,
            "message": "Bulk update completed successfully",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk update: {str(e)}"
        )


@router.get("/export/csv", response_model=StreamingResponse)
async def export_transactions_csv(
    start_date: Optional[date] = Query(None, description="Start date for export (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for export (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user)
):
    """Export transactions to CSV format"""
    
    try:
        csv_content = await transaction_service.export_transactions(
            organization_id=current_user.organization_id,
            start_date=start_date,
            end_date=end_date,
            format="csv"
        )
        
        # Create filename with date range
        filename = f"transactions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        if start_date and end_date:
            filename = f"transactions_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv"
        
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export transactions: {str(e)}"
        )


@router.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint for transactions service"""
    
    return {
        "success": True,
        "message": "Transactions service is healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "transactions",
        "status": "operational"
    }