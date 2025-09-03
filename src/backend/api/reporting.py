"""
Reporting API router for Financial Analytics Platform
Handles advanced financial reporting and dashboard endpoints
"""

from datetime import date, timedelta, datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.responses import HTMLResponse

from src.backend.services.auth_service import get_current_user, get_current_active_user
from src.backend.services.reporting_service import reporting_service
from src.backend.models.database import User
from src.common.models.base import BaseResponse

router = APIRouter()


@router.post("/generate", response_model=dict)
async def generate_comprehensive_report(
    report_type: str = Body("monthly", description="Type of report to generate"),
    start_date: Optional[date] = Body(None, description="Start date for report"),
    end_date: Optional[date] = Body(None, description="End date for report"),
    user_id: Optional[UUID] = Body(None, description="User ID to filter by"),
    format: str = Body("pdf", description="Report format (pdf, html, csv)"),
    include_charts: bool = Body(True, description="Include charts in report"),
    include_predictions: bool = Body(True, description="Include ML predictions"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate comprehensive financial report
    
    Creates detailed financial reports in various formats with
    analytics, charts, and machine learning predictions.
    """
    
    try:
        result = await reporting_service.generate_comprehensive_report(
            organization_id=current_user.organization_id,
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            format=format,
            include_charts=include_charts,
            include_predictions=include_predictions
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )


@router.get("/dashboard/{dashboard_type}", response_model=dict)
async def get_dashboard_data(
    dashboard_type: str,
    refresh_cache: bool = Query(False, description="Force refresh dashboard data"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get dashboard data for frontend visualization
    
    Provides real-time dashboard data for various dashboard types:
    - executive: High-level executive summary
    - analyst: Detailed analytical dashboard
    - manager: Management-focused metrics
    - custom: User-customized dashboard
    """
    
    try:
        result = await reporting_service.generate_dashboard_data(
            organization_id=current_user.organization_id,
            dashboard_type=dashboard_type,
            user_id=current_user.id,
            refresh_cache=refresh_cache
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dashboard data: {str(e)}"
        )


@router.post("/schedule", response_model=dict)
async def create_scheduled_report(
    report_config: Dict[str, Any] = Body(..., description="Report configuration"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a scheduled report configuration
    
    Sets up automated report generation with configurable:
    - Frequency (daily, weekly, monthly, quarterly)
    - Recipients (email addresses)
    - Format (pdf, html, csv)
    - Delivery method
    """
    
    try:
        result = await reporting_service.create_scheduled_report(
            organization_id=current_user.organization_id,
            report_config=report_config,
            user_id=current_user.id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create scheduled report: {str(e)}"
        )


@router.get("/templates", response_model=dict)
async def get_report_templates(
    template_type: str = Query("all", description="Type of templates to retrieve"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get available report templates
    
    Lists all available report templates with their:
    - Sections and content structure
    - Chart types and visualizations
    - Supported output formats
    - Customization options
    """
    
    try:
        result = await reporting_service.get_report_templates(template_type=template_type)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve report templates: {str(e)}"
        )


@router.get("/export/{export_type}", response_model=dict)
async def export_report_data(
    export_type: str,
    format: str = Query("csv", regex="^(csv|json)$", description="Export format"),
    start_date: Optional[date] = Query(None, description="Start date for export"),
    end_date: Optional[date] = Query(None, description="End date for export"),
    user_id: Optional[UUID] = Query(None, description="User ID to filter by"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export report data in various formats
    
    Exports financial data for external analysis:
    - transactions: Transaction history and details
    - analytics: Financial analytics and metrics
    - budgets: Budget information and performance
    """
    
    try:
        result = await reporting_service.export_report_data(
            organization_id=current_user.organization_id,
            export_type=export_type,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            format=format
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export data: {str(e)}"
        )


@router.get("/download/{report_id}", response_model=dict)
async def download_generated_report(
    report_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Download a previously generated report
    
    Provides access to stored reports with:
    - File download functionality
    - Report metadata and information
    - Access control and permissions
    """
    
    try:
        # This would typically look up the report in a database
        # For now, return a placeholder response
        return {
            "success": True,
            "message": "Report download initiated",
            "data": {
                "report_id": report_id,
                "download_url": f"/api/reporting/download/{report_id}/file",
                "status": "ready"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download report: {str(e)}"
        )


@router.get("/download/{report_id}/file")
async def download_report_file(
    report_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Download the actual report file
    
    Streams the report file to the client with proper
    content type and filename headers.
    """
    
    try:
        # This would typically look up the file path in a database
        # For now, return a placeholder file response
        file_path = f"reports/placeholder_{report_id}.pdf"
        
        # Create placeholder file if it doesn't exist
        from pathlib import Path
        placeholder_file = Path(file_path)
        placeholder_file.parent.mkdir(exist_ok=True)
        
        if not placeholder_file.exists():
            with open(placeholder_file, 'w') as f:
                f.write(f"Placeholder report for {report_id}")
        
        return FileResponse(
            path=file_path,
            filename=f"financial_report_{report_id}.pdf",
            media_type="application/pdf"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download report file: {str(e)}"
        )


@router.get("/scheduled", response_model=dict)
async def get_scheduled_reports(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all scheduled reports for the organization
    
    Lists all configured scheduled reports with their:
    - Configuration details
    - Execution status
    - Next run times
    - Recipient lists
    """
    
    try:
        # This would typically query the database for scheduled reports
        # For now, return a placeholder response
        scheduled_reports = [
            {
                "id": "monthly_exec_summary",
                "name": "Monthly Executive Summary",
                "type": "monthly",
                "frequency": "monthly",
                "recipients": ["executives@company.com"],
                "format": "pdf",
                "status": "active",
                "next_run": "2024-02-01T00:00:00Z",
                "last_run": "2024-01-01T00:00:00Z"
            },
            {
                "id": "weekly_analytics",
                "name": "Weekly Analytics Report",
                "type": "weekly",
                "frequency": "weekly",
                "recipients": ["analysts@company.com"],
                "format": "html",
                "status": "active",
                "next_run": "2024-01-22T00:00:00Z",
                "last_run": "2024-01-15T00:00:00Z"
            }
        ]
        
        return {
            "success": True,
            "message": "Scheduled reports retrieved successfully",
            "data": {
                "scheduled_reports": scheduled_reports,
                "total_count": len(scheduled_reports)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve scheduled reports: {str(e)}"
        )


@router.put("/scheduled/{report_id}", response_model=dict)
async def update_scheduled_report(
    report_id: str,
    updates: Dict[str, Any] = Body(..., description="Report updates"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a scheduled report configuration
    
    Modifies existing scheduled report settings:
    - Frequency and timing
    - Recipients and delivery
    - Report content and format
    - Status (active/inactive)
    """
    
    try:
        # This would typically update the database
        # For now, return a placeholder response
        return {
            "success": True,
            "message": f"Scheduled report {report_id} updated successfully",
            "data": {
                "report_id": report_id,
                "updates": updates,
                "updated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update scheduled report: {str(e)}"
        )


@router.delete("/scheduled/{report_id}", response_model=dict)
async def delete_scheduled_report(
    report_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a scheduled report configuration
    
    Removes scheduled report and stops future executions.
    """
    
    try:
        # This would typically delete from the database
        # For now, return a placeholder response
        return {
            "success": True,
            "message": f"Scheduled report {report_id} deleted successfully",
            "data": {
                "report_id": report_id,
                "deleted_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete scheduled report: {str(e)}"
        )


@router.post("/scheduled/{report_id}/execute", response_model=dict)
async def execute_scheduled_report(
    report_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Manually execute a scheduled report
    
    Triggers immediate execution of a scheduled report
    regardless of its normal schedule.
    """
    
    try:
        # This would typically trigger report generation
        # For now, return a placeholder response
        return {
            "success": True,
            "message": f"Scheduled report {report_id} execution initiated",
            "data": {
                "report_id": report_id,
                "execution_id": f"exec_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "status": "queued",
                "estimated_completion": "5 minutes"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute scheduled report: {str(e)}"
        )


@router.get("/preview/{template_id}", response_class=HTMLResponse)
async def preview_report_template(
    template_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Preview a report template
    
    Shows a live preview of how a report template will look
    with sample data for customization purposes.
    """
    
    try:
        # This would typically render the template with sample data
        # For now, return a placeholder HTML response
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Report Template Preview - {template_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .preview {{ border: 2px dashed #ccc; padding: 20px; text-align: center; }}
                .template-info {{ background: #f5f5f5; padding: 15px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>Report Template Preview</h1>
            <div class="template-info">
                <h2>Template: {template_id}</h2>
                <p>This is a preview of how the {template_id} report template will look.</p>
                <p>Use this preview to customize the template before generating the actual report.</p>
            </div>
            <div class="preview">
                <h3>Sample Report Content</h3>
                <p>Financial Overview</p>
                <p>Spending Analysis</p>
                <p>Income Breakdown</p>
                <p>Budget Performance</p>
                <p>Trends and Predictions</p>
            </div>
            <p><em>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview template: {str(e)}"
        )


@router.get("/health", response_model=dict)
async def reporting_health_check():
    """Health check for reporting service"""
    
    return {
        "success": True,
        "message": "Reporting service is healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "reporting",
        "status": "operational"
    }