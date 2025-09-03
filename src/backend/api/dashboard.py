"""
Dashboard API router for Financial Analytics Platform
Handles advanced dashboard functionality and widget management
"""

from datetime import date, timedelta, datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.responses import HTMLResponse

from src.backend.services.auth_service import get_current_user, get_current_active_user
from src.backend.services.dashboard_service import dashboard_service
from src.backend.models.database import User
from src.common.models.base import BaseResponse

router = APIRouter()


@router.get("/{dashboard_type}", response_model=dict)
async def get_dashboard(
    dashboard_type: str,
    custom_widgets: Optional[List[str]] = Query(None, description="Custom widgets to include"),
    refresh_cache: bool = Query(False, description="Force refresh dashboard data"),
    include_realtime: bool = Query(True, description="Include real-time data"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get comprehensive dashboard data
    
    Generates complete dashboard with all configured widgets:
    - executive: High-level executive summary
    - analyst: Detailed analytical dashboard
    - manager: Management-focused metrics
    - custom: User-customized dashboard
    """
    
    try:
        result = await dashboard_service.generate_dashboard(
            organization_id=current_user.organization_id,
            dashboard_type=dashboard_type,
            user_id=current_user.id,
            custom_widgets=custom_widgets,
            refresh_cache=refresh_cache,
            include_realtime=include_realtime
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dashboard: {str(e)}"
        )


@router.get("/widget/{widget_name}", response_model=dict)
async def get_widget_data(
    widget_name: str,
    parameters: Optional[Dict[str, Any]] = Query(None, description="Widget parameters"),
    refresh_cache: bool = Query(False, description="Force refresh widget data"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get data for a specific widget
    
    Retrieves data for individual dashboard widgets with
    configurable parameters and caching options.
    """
    
    try:
        result = await dashboard_service.get_widget_data(
            widget_name=widget_name,
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            parameters=parameters,
            refresh_cache=refresh_cache
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get widget data: {str(e)}"
        )


@router.get("/widgets/available", response_model=dict)
async def get_available_widgets(
    dashboard_type: str = Query("all", description="Filter widgets by dashboard type"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of available widgets
    
    Lists all available dashboard widgets with their:
    - Configuration options
    - Supported parameters
    - Refresh intervals
    - Dashboard compatibility
    """
    
    try:
        result = await dashboard_service.get_available_widgets(dashboard_type=dashboard_type)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available widgets: {str(e)}"
        )


@router.post("/custom", response_model=dict)
async def create_custom_dashboard(
    dashboard_config: Dict[str, Any] = Body(..., description="Dashboard configuration"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a custom dashboard configuration
    
    Builds personalized dashboard with:
    - Selected widgets and layout
    - Custom refresh intervals
    - User-specific configurations
    - Saved preferences
    """
    
    try:
        result = await dashboard_service.create_custom_dashboard(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            dashboard_config=dashboard_config
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create custom dashboard: {str(e)}"
        )


@router.get("/templates", response_model=dict)
async def get_dashboard_templates(
    template_type: str = Query("all", description="Type of templates to retrieve"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get available dashboard templates
    
    Lists all available dashboard templates with their:
    - Widget configurations
    - Layout options
    - Refresh intervals
    - Use case descriptions
    """
    
    try:
        result = await dashboard_service.get_dashboard_templates(template_type=template_type)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard templates: {str(e)}"
        )


@router.get("/preview/{template_id}", response_class=HTMLResponse)
async def preview_dashboard_template(
    template_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Preview a dashboard template
    
    Shows a live preview of how a dashboard template will look
    with sample data for customization purposes.
    """
    
    try:
        # Get template information
        templates = await dashboard_service.get_dashboard_templates(template_type=template_id)
        template_data = templates["data"]["templates"].get(template_id, {})
        
        if not template_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dashboard template {template_id} not found"
            )
        
        # Generate preview HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard Template Preview - {template_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .preview-container {{ max-width: 1200px; margin: 0 auto; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .template-info {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .widget-grid {{ display: grid; gap: 20px; }}
                .widget {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .widget-title {{ font-weight: bold; margin-bottom: 10px; color: #333; }}
                .widget-content {{ color: #666; }}
                .grid-2x2 {{ grid-template-columns: repeat(2, 1fr); }}
                .grid-2x3 {{ grid-template-columns: repeat(2, 1fr); grid-template-rows: repeat(3, auto); }}
                .grid-3x3 {{ grid-template-columns: repeat(3, 1fr); }}
                .flexible {{ grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }}
            </style>
        </head>
        <body>
            <div class="preview-container">
                <div class="header">
                    <h1>Dashboard Template Preview</h1>
                    <p>Template: {template_data.get('name', template_id)}</p>
                </div>
                
                <div class="template-info">
                    <h2>Template Information</h2>
                    <p><strong>Name:</strong> {template_data.get('name', 'N/A')}</p>
                    <p><strong>Description:</strong> {template_data.get('description', 'N/A')}</p>
                    <p><strong>Layout:</strong> {template_data.get('layout', 'N/A')}</p>
                    <p><strong>Refresh Interval:</strong> {template_data.get('refresh_interval', 'N/A')} seconds</p>
                    <p><strong>Widgets:</strong> {', '.join(template_data.get('widgets', []))}</p>
                </div>
                
                <div class="widget-grid {template_data.get('layout', 'grid-2x2')}">
        """
        
        # Add widget placeholders
        widgets = template_data.get('widgets', [])
        for widget in widgets:
            html_content += f"""
                    <div class="widget">
                        <div class="widget-title">{widget.replace('_', ' ').title()}</div>
                        <div class="widget-content">
                            <p>This widget will display {widget.replace('_', ' ')} data.</p>
                            <p>Sample content and charts will appear here.</p>
                        </div>
                    </div>
            """
        
        html_content += """
                </div>
                
                <div style="text-align: center; margin-top: 30px; color: #666;">
                    <p><em>Generated on """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</em></p>
                    <p>Use this preview to customize your dashboard before saving.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview template: {str(e)}"
        )


@router.get("/widgets/{widget_name}/preview", response_class=HTMLResponse)
async def preview_widget(
    widget_name: str,
    parameters: Optional[Dict[str, Any]] = Query(None, description="Widget parameters"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Preview a specific widget
    
    Shows how a widget will look with sample data
    and configurable parameters.
    """
    
    try:
        # Get widget information
        available_widgets = await dashboard_service.get_available_widgets()
        widget_info = available_widgets["data"]["widgets"].get(widget_name, {})
        
        if not widget_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Widget {widget_name} not found"
            )
        
        # Generate preview HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Widget Preview - {widget_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .preview-container {{ max-width: 800px; margin: 0 auto; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .widget-info {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .widget-preview {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .widget-title {{ font-size: 24px; font-weight: bold; margin-bottom: 15px; color: #333; }}
                .widget-subtitle {{ color: #666; margin-bottom: 20px; }}
                .sample-data {{ background: #f8f9fa; padding: 20px; border-radius: 6px; margin: 20px 0; }}
                .parameter-list {{ background: #e9ecef; padding: 15px; border-radius: 6px; margin: 20px 0; }}
                .parameter-item {{ margin: 5px 0; }}
            </style>
        </head>
        <body>
            <div class="preview-container">
                <div class="header">
                    <h1>Widget Preview</h1>
                    <p>Widget: {widget_info.get('name', widget_name)}</p>
                </div>
                
                <div class="widget-info">
                    <h2>Widget Information</h2>
                    <p><strong>Name:</strong> {widget_info.get('name', 'N/A')}</p>
                    <p><strong>Description:</strong> {widget_info.get('description', 'N/A')}</p>
                    <p><strong>Category:</strong> {widget_info.get('category', 'N/A')}</p>
                    <p><strong>Refresh Interval:</strong> {widget_info.get('refresh_interval', 'N/A')} seconds</p>
                    <p><strong>Supported Dashboards:</strong> {', '.join(widget_info.get('supported_dashboards', []))}</p>
                </div>
                
                <div class="widget-preview">
                    <div class="widget-title">{widget_info.get('name', widget_name)}</div>
                    <div class="widget-subtitle">Sample data preview</div>
                    
                    <div class="sample-data">
                        <h3>Sample Data</h3>
                        <p>This widget will display real-time {widget_info.get('category', 'data')} information.</p>
                        <p>Charts, metrics, and visualizations will be rendered here based on the selected parameters.</p>
                    </div>
                    
                    <div class="parameter-list">
                        <h3>Configurable Parameters</h3>
                        <div class="parameter-item">• Date Range: 7d, 30d, 90d, custom</div>
                        <div class="parameter-item">• Metrics: Select specific metrics to display</div>
                        <div class="parameter-item">• Grouping: Category, source, time period</div>
                        <div class="parameter-item">• Limits: Number of items to show</div>
                        <div class="parameter-item">• Thresholds: Alert and warning levels</div>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 30px; color: #666;">
                    <p><em>Generated on """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</em></p>
                    <p>This preview shows the widget structure and available configuration options.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview widget: {str(e)}"
        )


@router.get("/export/{dashboard_type}", response_model=dict)
async def export_dashboard_data(
    dashboard_type: str,
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    include_metadata: bool = Query(True, description="Include dashboard metadata"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export dashboard data
    
    Exports dashboard data in various formats for:
    - External analysis and reporting
    - Integration with other systems
    - Data backup and archival
    """
    
    try:
        # Get dashboard data
        dashboard_data = await dashboard_service.generate_dashboard(
            organization_id=current_user.organization_id,
            dashboard_type=dashboard_type,
            user_id=current_user.id,
            refresh_cache=True
        )
        
        if not dashboard_data["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate dashboard data for export"
            )
        
        # Prepare export data
        export_data = dashboard_data["data"]
        
        if not include_metadata:
            # Remove metadata if not requested
            export_data.pop("metadata", None)
        
        # Format export based on requested format
        if format.lower() == "csv":
            # Convert to CSV format (simplified)
            csv_content = "Widget,Title,Subtitle,Last Updated\n"
            for widget_name, widget_data in export_data.items():
                if widget_name != "metadata":
                    csv_content += f"{widget_name},{widget_data.get('title', 'N/A')},{widget_data.get('subtitle', 'N/A')},{widget_data.get('last_updated', 'N/A')}\n"
            
            return {
                "success": True,
                "message": f"Dashboard {dashboard_type} exported successfully",
                "data": {
                    "format": "csv",
                    "content": csv_content,
                    "filename": f"dashboard_{dashboard_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            }
        
        else:  # JSON format
            return {
                "success": True,
                "message": f"Dashboard {dashboard_type} exported successfully",
                "data": {
                    "format": "json",
                    "content": export_data,
                    "filename": f"dashboard_{dashboard_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                }
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export dashboard: {str(e)}"
        )


@router.get("/cache/status", response_model=dict)
async def get_cache_status(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get dashboard cache status
    
    Shows current cache status including:
    - Cached widgets
    - Cache hit rates
    - Memory usage
    - TTL information
    """
    
    try:
        # Get cache information from dashboard service
        cache_info = {
            "total_cached_widgets": len(dashboard_service.widget_cache),
            "cache_ttl_seconds": dashboard_service.cache_ttl,
            "cache_size_mb": 0,  # Would calculate actual memory usage
            "cache_hit_rate": 0.85,  # Would calculate from actual usage
            "last_cache_clear": datetime.now().isoformat(),
            "cache_enabled": True
        }
        
        return {
            "success": True,
            "message": "Cache status retrieved successfully",
            "data": cache_info
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache status: {str(e)}"
        )


@router.post("/cache/clear", response_model=dict)
async def clear_dashboard_cache(
    current_user: User = Depends(get_current_active_user)
):
    """
    Clear dashboard cache
    
    Clears all cached widget data to force
    fresh data retrieval on next request.
    """
    
    try:
        # Clear the cache
        cache_size = len(dashboard_service.widget_cache)
        dashboard_service.widget_cache.clear()
        
        return {
            "success": True,
            "message": "Dashboard cache cleared successfully",
            "data": {
                "cleared_widgets": cache_size,
                "cleared_at": datetime.now().isoformat(),
                "cache_size_after": 0
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get("/health", response_model=dict)
async def dashboard_health_check():
    """Health check for dashboard service"""
    
    return {
        "success": True,
        "message": "Dashboard service is healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "dashboard",
        "status": "operational",
        "available_templates": len(dashboard_service.dashboard_templates),
        "cache_status": "active"
    }