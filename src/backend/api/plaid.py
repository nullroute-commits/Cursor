"""
Plaid API router for Financial Analytics Platform
Handles Plaid integration for automated bank data fetching
"""

from datetime import datetime, date
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body

import logging
from sqlmodel import select, func, and_
from src.backend.services.auth_service import get_current_user, get_current_active_user
from src.backend.services.plaid_service import plaid_service
from src.backend.models.database import User, Account, Transaction
from src.backend.database import get_session
from src.common.models.base import BaseResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/link-token", response_model=dict)
async def create_link_token(
    current_user: User = Depends(get_current_active_user)
):
    """Create a Plaid Link token for connecting bank accounts"""
    
    try:
        result = await plaid_service.create_link_token(current_user.id)
        
        if result["success"]:
            return {
                "success": True,
                "message": "Plaid link token created successfully",
                "data": result["data"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Plaid link token: {str(e)}"
        )


@router.post("/connect", response_model=dict)
async def connect_accounts(
    public_token: str = Body(..., embed=True, description="Plaid public token from Link"),
    current_user: User = Depends(get_current_active_user)
):
    """Connect Plaid accounts to the platform"""
    
    try:
        result = await plaid_service.connect_accounts(
            public_token=public_token,
            user_id=current_user.id,
            organization_id=current_user.organization_id
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": "Accounts connected successfully",
                "data": result["data"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect accounts: {str(e)}"
        )


@router.post("/sync", response_model=dict)
async def sync_transactions(
    days_back: int = Body(30, ge=1, le=365, description="Number of days to sync"),
    current_user: User = Depends(get_current_active_user)
):
    """Sync transactions from Plaid for all connected accounts"""
    
    try:
        result = await plaid_service.sync_transactions(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            days_back=days_back
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": "Transactions synced successfully",
                "data": result["data"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync transactions: {str(e)}"
        )


@router.get("/status", response_model=dict)
async def get_sync_status(
    current_user: User = Depends(get_current_active_user)
):
    """Get sync status for all Plaid-connected accounts"""
    
    try:
        result = await plaid_service.get_sync_status(
            organization_id=current_user.organization_id
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": "Sync status retrieved successfully",
                "data": result["data"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync status: {str(e)}"
        )


@router.post("/webhook", response_model=dict)
async def handle_webhook(
    webhook_data: dict = Body(..., description="Plaid webhook payload")
):
    """Handle Plaid webhooks for real-time updates"""
    
    try:
        webhook_type = webhook_data.get("webhook_type")
        webhook_code = webhook_data.get("webhook_code")
        item_id = webhook_data.get("item_id")
        
        logger.info(f"Received Plaid webhook: {webhook_type} - {webhook_code} for item {item_id}")
        
        # Handle different webhook types
        if webhook_type == "TRANSACTIONS":
            if webhook_code == "INITIAL_UPDATE":
                # Initial transaction sync completed
                logger.info(f"Initial transaction sync completed for item {item_id}")
            elif webhook_code == "HISTORICAL_UPDATE":
                # Historical transaction sync completed
                logger.info(f"Historical transaction sync completed for item {item_id}")
            elif webhook_code == "DEFAULT_UPDATE":
                # New transactions available
                logger.info(f"New transactions available for item {item_id}")
            elif webhook_code == "TRANSACTIONS_REMOVED":
                # Transactions removed
                logger.info(f"Transactions removed for item {item_id}")
        
        elif webhook_type == "ITEM":
            if webhook_code == "ERROR":
                error = webhook_data.get("error", {})
                logger.error(f"Plaid item error for {item_id}: {error}")
            elif webhook_code == "PENDING_EXPIRATION":
                logger.warning(f"Plaid item {item_id} will expire soon")
            elif webhook_code == "USER_PERMISSION_REVOKED":
                logger.warning(f"User permission revoked for Plaid item {item_id}")
        
        elif webhook_type == "ACCOUNTS":
            if webhook_code == "ACCOUNT_UPDATED":
                logger.info(f"Account updated for Plaid item {item_id}")
        
        return {
            "success": True,
            "message": "Webhook processed successfully",
            "data": {
                "webhook_type": webhook_type,
                "webhook_code": webhook_code,
                "item_id": item_id,
                "processed_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to process Plaid webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )


@router.get("/accounts", response_model=dict)
async def get_plaid_accounts(
    current_user: User = Depends(get_current_active_user)
):
    """Get all Plaid-connected accounts for the current user"""
    
    try:
        # Get accounts from database that have Plaid integration
        async with get_session() as session:
            statement = select(Account).where(
                Account.organization_id == current_user.organization_id,
                Account.plaid_account_id.is_not(None),
                Account.is_active == True
            )
            result = await session.exec(statement)
            accounts = result.all()
        
        account_list = []
        for account in accounts:
            metadata = account.metadata or {}
            plaid_data = metadata.get("plaid_account_data", {})
            
            account_list.append({
                "id": str(account.id),
                "name": account.name,
                "account_type": account.account_type.value,
                "balance": float(account.balance),
                "available_balance": float(account.available_balance),
                "credit_limit": float(account.credit_limit) if account.credit_limit else None,
                "institution": account.institution_name,
                "plaid_account_id": account.plaid_account_id,
                "plaid_item_id": account.plaid_item_id,
                "last_sync": metadata.get("plaid_last_sync"),
                "plaid_subtype": plaid_data.get("subtype"),
                "plaid_mask": plaid_data.get("mask")
            })
        
        return {
            "success": True,
            "message": "Plaid accounts retrieved successfully",
            "data": {
                "accounts": account_list,
                "total_count": len(account_list)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve Plaid accounts: {str(e)}"
        )


@router.delete("/accounts/{account_id}", response_model=dict)
async def disconnect_plaid_account(
    account_id: UUID,
    current_user: User = Depends(get_current_active_user)
):
    """Disconnect a Plaid account from the platform"""
    
    try:
        async with get_session() as session:
            # Get account and verify ownership
            statement = select(Account).where(
                Account.id == account_id,
                Account.organization_id == current_user.organization_id,
                Account.plaid_account_id.is_not(None)
            )
            result = await session.exec(statement)
            account = result.first()
            
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Plaid account not found"
                )
            
            # Remove Plaid integration data
            account.plaid_account_id = None
            account.plaid_item_id = None
            account.plaid_access_token = None
            account.updated_at = datetime.utcnow()
            
            # Update metadata
            metadata = account.metadata or {}
            metadata["plaid_disconnected_at"] = datetime.utcnow().isoformat()
            metadata["plaid_disconnected_by"] = str(current_user.id)
            account.metadata = metadata
            
            await session.commit()
            
            return {
                "success": True,
                "message": "Plaid account disconnected successfully",
                "data": {
                    "account_id": str(account_id),
                    "account_name": account.name,
                    "disconnected_at": metadata["plaid_disconnected_at"]
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect Plaid account: {str(e)}"
        )


@router.get("/institutions", response_model=dict)
async def get_plaid_institutions(
    current_user: User = Depends(get_current_active_user)
):
    """Get information about Plaid institutions for connected accounts"""
    
    try:
        # Get unique institutions from connected accounts
        async with get_session() as session:
            statement = select(Account.institution_name).where(
                Account.organization_id == current_user.organization_id,
                Account.plaid_account_id.is_not(None),
                Account.is_active == True
            ).distinct()
            result = await session.exec(statement)
            institutions = result.all()
        
        institution_list = []
        for institution_name in institutions:
            if institution_name:
                # Get account count for this institution
                count_statement = select(func.count(Account.id)).where(
                    Account.organization_id == current_user.organization_id,
                    Account.institution_name == institution_name,
                    Account.plaid_account_id.is_not(None),
                    Account.is_active == True
                )
                count_result = await session.exec(count_statement)
                account_count = count_result.first() or 0
                
                # Get sample account for metadata
                sample_statement = select(Account).where(
                    Account.organization_id == current_user.organization_id,
                    Account.institution_name == institution_name,
                    Account.plaid_account_id.is_not(None),
                    Account.is_active == True
                ).limit(1)
                sample_result = await session.exec(sample_statement)
                sample_account = sample_result.first()
                
                metadata = sample_account.metadata or {} if sample_account else {}
                plaid_institution_data = metadata.get("plaid_institution_data", {})
                
                institution_list.append({
                    "name": institution_name,
                    "account_count": account_count,
                    "plaid_institution_id": plaid_institution_data.get("institution_id"),
                    "url": plaid_institution_data.get("url"),
                    "primary_color": plaid_institution_data.get("primary_color"),
                    "logo": plaid_institution_data.get("logo"),
                    "products": plaid_institution_data.get("products", []),
                    "country_codes": plaid_institution_data.get("country_codes", [])
                })
        
        return {
            "success": True,
            "message": "Plaid institutions retrieved successfully",
            "data": {
                "institutions": institution_list,
                "total_count": len(institution_list)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve Plaid institutions: {str(e)}"
        )


@router.get("/transactions", response_model=dict)
async def get_plaid_transactions(
    account_id: Optional[UUID] = Query(None, description="Filter by account ID"),
    start_date: Optional[date] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_active_user)
):
    """Get Plaid-synced transactions with filtering"""
    
    try:
        async with get_session() as session:
            # Build base query for Plaid transactions
            conditions = [
                Transaction.organization_id == current_user.organization_id,
                Transaction.plaid_transaction_id.is_not(None),
                Transaction.deleted_at.is_(None)
            ]
            
            if account_id:
                conditions.append(Transaction.account_id == account_id)
            
            if start_date:
                conditions.append(Transaction.date >= start_date)
            
            if end_date:
                conditions.append(Transaction.date <= end_date)
            
            # Get transactions
            statement = select(Transaction).where(and_(*conditions)).order_by(
                Transaction.date.desc()
            ).offset(skip).limit(limit)
            
            result = await session.exec(statement)
            transactions = result.all()
            
            # Convert to response format
            transaction_list = []
            for tx in transactions:
                metadata = tx.metadata or {}
                plaid_data = metadata.get("plaid_transaction_data", {})
                
                transaction_list.append({
                    "id": str(tx.id),
                    "description": tx.description,
                    "amount": float(tx.amount),
                    "transaction_type": tx.transaction_type.value,
                    "date": tx.date.isoformat(),
                    "merchant_name": tx.merchant_name,
                    "reference": tx.reference,
                    "notes": tx.notes,
                    "plaid_transaction_id": tx.plaid_transaction_id,
                    "plaid_category_id": tx.plaid_category_id,
                    "plaid_categories": plaid_data.get("category", []),
                    "plaid_payment_channel": plaid_data.get("payment_channel"),
                    "plaid_pending": plaid_data.get("pending", False),
                    "account": {
                        "id": str(tx.account.id),
                        "name": tx.account.name,
                        "institution": tx.account.institution_name
                    } if tx.account else None,
                    "category": {
                        "id": str(tx.category.id),
                        "name": tx.category.name,
                        "color": tx.category.color
                    } if tx.category else None,
                    "last_sync": metadata.get("plaid_last_sync"),
                    "created_at": tx.created_at.isoformat()
                })
            
            return {
                "success": True,
                "message": "Plaid transactions retrieved successfully",
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
            detail=f"Failed to retrieve Plaid transactions: {str(e)}"
        )


@router.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint for Plaid service"""
    
    return {
        "success": True,
        "message": "Plaid service is healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "plaid",
        "status": "operational",
        "plaid_available": plaid_service.client.plaid_available
    }