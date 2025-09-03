"""
Analytics API router for Financial Analytics Platform
Handles financial analysis and reporting endpoints
"""

from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse

from src.backend.services.auth_service import get_current_user, get_current_active_user
from src.backend.services.analytics_service import analytics_service
from src.backend.models.database import User
from src.common.models.base import BaseResponse

router = APIRouter()


@router.get("/overview", response_model=dict)
async def get_financial_overview(
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    user_id: Optional[UUID] = Query(None, description="User ID to filter by"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get comprehensive financial overview
    
    Provides summary statistics, spending patterns, income analysis,
    cash flow analysis, budget performance, and financial health indicators.
    """
    
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        result = await analytics_service.get_financial_overview(
            organization_id=current_user.organization_id,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate financial overview: {str(e)}"
        )


@router.get("/spending", response_model=dict)
async def get_spending_analysis(
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    user_id: Optional[UUID] = Query(None, description="User ID to filter by"),
    category_id: Optional[UUID] = Query(None, description="Category ID to filter by"),
    account_id: Optional[UUID] = Query(None, description="Account ID to filter by"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed spending analysis
    
    Provides spending breakdown by category, day of week, month,
    and top merchants with percentage analysis.
    """
    
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        result = await analytics_service.get_spending_analysis(
            organization_id=current_user.organization_id,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            category_id=category_id,
            account_id=account_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate spending analysis: {str(e)}"
        )


@router.get("/income", response_model=dict)
async def get_income_analysis(
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    user_id: Optional[UUID] = Query(None, description="User ID to filter by"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed income analysis
    
    Provides income breakdown by category, month, and income sources
    with trend analysis and stability metrics.
    """
    
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        result = await analytics_service.get_income_analysis(
            organization_id=current_user.organization_id,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate income analysis: {str(e)}"
        )


@router.get("/cash-flow/forecast", response_model=dict)
async def get_cash_flow_forecast(
    months_ahead: int = Query(6, ge=1, le=24, description="Number of months to forecast"),
    user_id: Optional[UUID] = Query(None, description="User ID to filter by"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get cash flow forecast
    
    Provides cash flow projections based on historical data with
    trend analysis and confidence levels for future months.
    """
    
    try:
        result = await analytics_service.get_cash_flow_forecast(
            organization_id=current_user.organization_id,
            months_ahead=months_ahead,
            user_id=user_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate cash flow forecast: {str(e)}"
        )


@router.get("/anomalies", response_model=dict)
async def get_anomaly_detection(
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    user_id: Optional[UUID] = Query(None, description="User ID to filter by"),
    threshold: float = Query(2.0, ge=1.0, le=5.0, description="Z-score threshold for anomaly detection"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Detect financial anomalies
    
    Identifies unusual transactions and spending patterns using
    statistical analysis (Z-scores) across multiple dimensions:
    - Amount-based anomalies
    - Category-based anomalies
    - Time-based anomalies
    - Merchant-based anomalies
    """
    
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=90)  # Longer period for anomaly detection
        
        result = await analytics_service.get_anomaly_detection(
            organization_id=current_user.organization_id,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            threshold=threshold
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform anomaly detection: {str(e)}"
        )


@router.get("/budgets", response_model=dict)
async def get_budget_analysis(
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    user_id: Optional[UUID] = Query(None, description="User ID to filter by"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get budget vs actual analysis
    
    Compares budgeted amounts with actual spending to provide
    performance metrics and variance analysis.
    """
    
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        result = await analytics_service.get_budget_analysis(
            organization_id=current_user.organization_id,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate budget analysis: {str(e)}"
        )


@router.get("/trends", response_model=dict)
async def get_financial_trends(
    months: int = Query(12, ge=3, le=60, description="Number of months to analyze"),
    user_id: Optional[UUID] = Query(None, description="User ID to filter by"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get financial trends analysis
    
    Analyzes spending and income trends over time with
    seasonal patterns and growth rate calculations.
    """
    
    try:
        # This would call a trends analysis method
        # For now, return a placeholder response
        return {
            "success": True,
            "message": "Trends analysis endpoint - implementation in progress",
            "data": {
                "period_months": months,
                "trends": [],
                "seasonal_patterns": [],
                "growth_rates": {}
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate trends analysis: {str(e)}"
        )


@router.get("/reports", response_model=dict)
async def get_available_reports(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get available analytics reports
    
    Lists all available report types and their descriptions
    for the analytics system.
    """
    
    reports = [
        {
            "id": "financial_overview",
            "name": "Financial Overview",
            "description": "Comprehensive financial summary with key metrics",
            "endpoint": "/api/analytics/overview",
            "parameters": ["start_date", "end_date", "user_id"],
            "refresh_rate": "real_time"
        },
        {
            "id": "spending_analysis",
            "name": "Spending Analysis",
            "description": "Detailed spending breakdown by category and time",
            "endpoint": "/api/analytics/spending",
            "parameters": ["start_date", "end_date", "user_id", "category_id", "account_id"],
            "refresh_rate": "real_time"
        },
        {
            "id": "income_analysis",
            "name": "Income Analysis",
            "description": "Income breakdown and source analysis",
            "endpoint": "/api/analytics/income",
            "parameters": ["start_date", "end_date", "user_id"],
            "refresh_rate": "real_time"
        },
        {
            "id": "cash_flow_forecast",
            "name": "Cash Flow Forecast",
            "description": "Future cash flow projections based on historical data",
            "endpoint": "/api/analytics/cash-flow/forecast",
            "parameters": ["months_ahead", "user_id"],
            "refresh_rate": "daily"
        },
        {
            "id": "anomaly_detection",
            "name": "Anomaly Detection",
            "description": "Statistical analysis to identify unusual transactions",
            "endpoint": "/api/analytics/anomalies",
            "parameters": ["start_date", "end_date", "user_id", "threshold"],
            "refresh_rate": "daily"
        },
        {
            "id": "budget_analysis",
            "name": "Budget Analysis",
            "description": "Budget vs actual spending comparison",
            "endpoint": "/api/analytics/budgets",
            "parameters": ["start_date", "end_date", "user_id"],
            "refresh_rate": "real_time"
        },
        {
            "id": "financial_trends",
            "name": "Financial Trends",
            "description": "Long-term spending and income trend analysis",
            "endpoint": "/api/analytics/trends",
            "parameters": ["months", "user_id"],
            "refresh_rate": "weekly"
        }
    ]
    
    return {
        "success": True,
        "message": "Available reports retrieved successfully",
        "data": {
            "reports": reports,
            "total_count": len(reports),
            "categories": {
                "real_time": len([r for r in reports if r["refresh_rate"] == "real_time"]),
                "daily": len([r for r in reports if r["refresh_rate"] == "daily"]),
                "weekly": len([r for r in reports if r["refresh_rate"] == "weekly"])
            }
        }
    }


@router.get("/export/{report_type}", response_model=dict)
async def export_analytics_report(
    report_type: str,
    format: str = Query("csv", regex="^(csv|json|pdf)$", description="Export format"),
    start_date: Optional[date] = Query(None, description="Start date for report"),
    end_date: Optional[date] = Query(None, description="End date for report"),
    user_id: Optional[UUID] = Query(None, description="User ID to filter by"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export analytics report
    
    Exports analytics data in various formats (CSV, JSON, PDF)
    for external analysis and reporting.
    """
    
    try:
        # Validate report type
        valid_reports = ["overview", "spending", "income", "cash-flow", "anomalies", "budgets", "trends"]
        if report_type not in valid_reports:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid report type. Must be one of: {', '.join(valid_reports)}"
            )
        
        # Set default date range if not provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Generate report based on type
        if report_type == "overview":
            data = await analytics_service.get_financial_overview(
                organization_id=current_user.organization_id,
                start_date=start_date,
                end_date=end_date,
                user_id=user_id
            )
        elif report_type == "spending":
            data = await analytics_service.get_spending_analysis(
                organization_id=current_user.organization_id,
                start_date=start_date,
                end_date=end_date,
                user_id=user_id
            )
        elif report_type == "income":
            data = await analytics_service.get_income_analysis(
                organization_id=current_user.organization_id,
                start_date=start_date,
                end_date=end_date,
                user_id=user_id
            )
        elif report_type == "cash-flow":
            data = await analytics_service.get_cash_flow_forecast(
                organization_id=current_user.organization_id,
                months_ahead=6,
                user_id=user_id
            )
        elif report_type == "anomalies":
            data = await analytics_service.get_anomaly_detection(
                organization_id=current_user.organization_id,
                start_date=start_date,
                end_date=end_date,
                user_id=user_id
            )
        elif report_type == "budgets":
            data = await analytics_service.get_budget_analysis(
                organization_id=current_user.organization_id,
                start_date=start_date,
                end_date=end_date,
                user_id=user_id
            )
        else:
            data = {"message": "Report type not yet implemented"}
        
        # Format export based on requested format
        if format == "json":
            return {
                "success": True,
                "message": f"{report_type} report exported successfully",
                "data": {
                    "format": format,
                    "report_type": report_type,
                    "export_date": date.today().isoformat(),
                    "content": data
                }
            }
        elif format == "csv":
            # Convert to CSV format (simplified)
            csv_content = f"Report Type,{report_type}\n"
            csv_content += f"Export Date,{date.today().isoformat()}\n"
            csv_content += f"Start Date,{start_date.isoformat() if start_date else 'N/A'}\n"
            csv_content += f"End Date,{end_date.isoformat() if end_date else 'N/A'}\n"
            
            return {
                "success": True,
                "message": f"{report_type} report exported successfully",
                "data": {
                    "format": format,
                    "report_type": report_type,
                    "export_date": date.today().isoformat(),
                    "content": csv_content,
                    "filename": f"{report_type}_report_{date.today().isoformat()}.csv"
                }
            }
        else:
            return {
                "success": True,
                "message": f"{report_type} report exported successfully",
                "data": {
                    "format": format,
                    "report_type": report_type,
                    "export_date": date.today().isoformat(),
                    "content": f"PDF export for {report_type} report - implementation in progress"
                }
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export {report_type} report: {str(e)}"
        )


@router.get("/health", response_model=dict)
async def analytics_health_check():
    """Health check for analytics service"""
    
    return {
        "success": True,
        "message": "Analytics service is healthy",
        "timestamp": date.today().isoformat(),
        "service": "analytics",
        "status": "operational"
    }