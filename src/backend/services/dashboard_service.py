"""
Dashboard service for Financial Analytics Platform
Handles advanced dashboard generation and widget management
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple
from uuid import UUID
from decimal import Decimal
import json
from pathlib import Path

from fastapi import HTTPException, status
from sqlmodel import select, func, and_, or_

from src.backend.services.analytics_service import analytics_service
from src.backend.services.ml_service import ml_service
from src.backend.services.reporting_service import reporting_service
from src.backend.models.database import Transaction, Account, Category, Budget, User, Organization
from src.backend.database import get_session
from src.common.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DashboardService:
    """Service for advanced dashboard generation and widget management"""
    
    def __init__(self):
        self.widget_cache = {}
        self.cache_ttl = 300  # 5 minutes cache TTL
        self.dashboard_templates = {
            "executive": {
                "name": "Executive Dashboard",
                "description": "High-level executive summary with key metrics",
                "widgets": ["kpi_summary", "financial_overview", "trend_chart", "alerts_summary"],
                "layout": "grid_2x2",
                "refresh_interval": 300
            },
            "analyst": {
                "name": "Analyst Dashboard",
                "description": "Detailed analytical dashboard with deep insights",
                "widgets": ["detailed_analytics", "spending_breakdown", "income_analysis", "budget_performance", "ml_insights"],
                "layout": "grid_3x3",
                "refresh_interval": 60
            },
            "manager": {
                "name": "Manager Dashboard",
                "description": "Management-focused metrics and performance tracking",
                "widgets": ["performance_metrics", "budget_tracking", "team_summary", "forecast_summary"],
                "layout": "grid_2x3",
                "refresh_interval": 120
            },
            "custom": {
                "name": "Custom Dashboard",
                "description": "User-customized dashboard with selected widgets",
                "widgets": ["configurable"],
                "layout": "flexible",
                "refresh_interval": 300
            }
        }
    
    async def generate_dashboard(
        self,
        organization_id: UUID,
        dashboard_type: str = "executive",
        user_id: Optional[UUID] = None,
        custom_widgets: Optional[List[str]] = None,
        refresh_cache: bool = False,
        include_realtime: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive dashboard with all widgets"""
        
        try:
            # Validate dashboard type
            if dashboard_type not in self.dashboard_templates:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid dashboard type: {dashboard_type}"
                )
            
            # Get dashboard template
            template = self.dashboard_templates[dashboard_type]
            
            # Determine widgets to generate
            if custom_widgets:
                widgets_to_generate = custom_widgets
            else:
                widgets_to_generate = template["widgets"]
            
            # Generate all widget data
            dashboard_data = {}
            for widget_name in widgets_to_generate:
                widget_data = await self._generate_widget(
                    widget_name, organization_id, user_id, refresh_cache, include_realtime
                )
                if widget_data:
                    dashboard_data[widget_name] = widget_data
            
            # Add dashboard metadata
            dashboard_data["metadata"] = {
                "dashboard_type": dashboard_type,
                "template": template,
                "generated_at": datetime.now().isoformat(),
                "user_id": str(user_id) if user_id else None,
                "organization_id": str(organization_id),
                "widget_count": len(dashboard_data) - 1,  # Exclude metadata
                "refresh_interval": template["refresh_interval"]
            }
            
            return {
                "success": True,
                "message": f"{dashboard_type.title()} dashboard generated successfully",
                "data": dashboard_data
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to generate dashboard: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate dashboard: {str(e)}"
            )
    
    async def get_widget_data(
        self,
        widget_name: str,
        organization_id: UUID,
        user_id: Optional[UUID] = None,
        parameters: Optional[Dict[str, Any]] = None,
        refresh_cache: bool = False
    ) -> Dict[str, Any]:
        """Get data for a specific widget"""
        
        try:
            widget_data = await self._generate_widget(
                widget_name, organization_id, user_id, refresh_cache, True, parameters
            )
            
            if not widget_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown widget: {widget_name}"
                )
            
            return {
                "success": True,
                "message": f"Widget {widget_name} data retrieved successfully",
                "data": widget_data
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get widget data: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get widget data: {str(e)}"
            )
    
    async def get_available_widgets(
        self,
        dashboard_type: str = "all"
    ) -> Dict[str, Any]:
        """Get list of available widgets"""
        
        try:
            all_widgets = {
                "kpi_summary": {
                    "name": "KPI Summary",
                    "description": "Key Performance Indicators overview",
                    "category": "metrics",
                    "supported_dashboards": ["executive", "manager"],
                    "parameters": ["date_range", "metrics"],
                    "refresh_interval": 300
                },
                "financial_overview": {
                    "name": "Financial Overview",
                    "description": "High-level financial summary",
                    "category": "overview",
                    "supported_dashboards": ["executive", "analyst", "manager"],
                    "parameters": ["date_range"],
                    "refresh_interval": 300
                },
                "trend_chart": {
                    "name": "Trend Chart",
                    "description": "Financial trends over time",
                    "category": "charts",
                    "supported_dashboards": ["executive", "analyst", "manager"],
                    "parameters": ["date_range", "metric", "period"],
                    "refresh_interval": 600
                },
                "alerts_summary": {
                    "name": "Alerts Summary",
                    "description": "Active alerts and notifications",
                    "category": "alerts",
                    "supported_dashboards": ["executive", "manager"],
                    "parameters": ["severity", "status"],
                    "refresh_interval": 60
                },
                "detailed_analytics": {
                    "name": "Detailed Analytics",
                    "description": "Comprehensive financial analytics",
                    "category": "analytics",
                    "supported_dashboards": ["analyst"],
                    "parameters": ["date_range", "metrics", "grouping"],
                    "refresh_interval": 300
                },
                "spending_breakdown": {
                    "name": "Spending Breakdown",
                    "description": "Detailed spending analysis by category",
                    "category": "spending",
                    "supported_dashboards": ["analyst", "manager"],
                    "parameters": ["date_range", "grouping", "limit"],
                    "refresh_interval": 300
                },
                "income_analysis": {
                    "name": "Income Analysis",
                    "description": "Income breakdown and trends",
                    "category": "income",
                    "supported_dashboards": ["analyst", "manager"],
                    "supported_dashboards": ["analyst", "manager"],
                    "parameters": ["date_range", "grouping"],
                    "refresh_interval": 300
                },
                "budget_performance": {
                    "name": "Budget Performance",
                    "description": "Budget vs actual performance",
                    "category": "budgets",
                    "supported_dashboards": ["analyst", "manager"],
                    "parameters": ["date_range", "budget_ids"],
                    "refresh_interval": 300
                },
                "ml_insights": {
                    "name": "ML Insights",
                    "description": "Machine learning predictions and insights",
                    "category": "ml",
                    "supported_dashboards": ["analyst"],
                    "parameters": ["prediction_type", "horizon"],
                    "refresh_interval": 600
                },
                "performance_metrics": {
                    "name": "Performance Metrics",
                    "description": "Key performance metrics and KPIs",
                    "category": "metrics",
                    "supported_dashboards": ["manager"],
                    "parameters": ["date_range", "metrics"],
                    "refresh_interval": 300
                },
                "budget_tracking": {
                    "name": "Budget Tracking",
                    "description": "Real-time budget tracking and alerts",
                    "category": "budgets",
                    "supported_dashboards": ["manager"],
                    "parameters": ["budget_ids", "thresholds"],
                    "refresh_interval": 120
                },
                "team_summary": {
                    "name": "Team Summary",
                    "description": "Team performance and activity summary",
                    "category": "team",
                    "supported_dashboards": ["manager"],
                    "parameters": ["team_ids", "date_range"],
                    "refresh_interval": 300
                },
                "forecast_summary": {
                    "name": "Forecast Summary",
                    "description": "Financial forecasting and projections",
                    "category": "forecasting",
                    "supported_dashboards": ["manager", "executive"],
                    "parameters": ["forecast_type", "horizon"],
                    "refresh_interval": 600
                }
            }
            
            # Filter by dashboard type if specified
            if dashboard_type != "all":
                filtered_widgets = {
                    name: widget for name, widget in all_widgets.items()
                    if dashboard_type in widget["supported_dashboards"]
                }
            else:
                filtered_widgets = all_widgets
            
            return {
                "success": True,
                "message": "Available widgets retrieved successfully",
                "data": {
                    "widgets": filtered_widgets,
                    "total_count": len(filtered_widgets),
                    "dashboard_type": dashboard_type
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get available widgets: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get available widgets: {str(e)}"
            )
    
    async def create_custom_dashboard(
        self,
        organization_id: UUID,
        user_id: UUID,
        dashboard_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a custom dashboard configuration"""
        
        try:
            # Validate dashboard configuration
            required_fields = ["name", "description", "widgets", "layout"]
            for field in required_fields:
                if field not in dashboard_config:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Missing required field: {field}"
                    )
            
            # Validate widgets exist
            available_widgets = await self.get_available_widgets()
            valid_widgets = available_widgets["data"]["widgets"].keys()
            
            invalid_widgets = [
                widget for widget in dashboard_config["widgets"]
                if widget not in valid_widgets
            ]
            
            if invalid_widgets:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid widgets: {invalid_widgets}"
                )
            
            # Create dashboard configuration
            dashboard_id = f"custom_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            custom_dashboard = {
                "id": dashboard_id,
                "name": dashboard_config["name"],
                "description": dashboard_config["description"],
                "widgets": dashboard_config["widgets"],
                "layout": dashboard_config["layout"],
                "created_by": str(user_id),
                "created_at": datetime.now().isoformat(),
                "organization_id": str(organization_id),
                "type": "custom",
                "refresh_interval": dashboard_config.get("refresh_interval", 300)
            }
            
            return {
                "success": True,
                "message": "Custom dashboard created successfully",
                "data": {
                    "dashboard_id": dashboard_id,
                    "dashboard": custom_dashboard
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create custom dashboard: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create custom dashboard: {str(e)}"
            )
    
    async def get_dashboard_templates(
        self,
        template_type: str = "all"
    ) -> Dict[str, Any]:
        """Get available dashboard templates"""
        
        try:
            if template_type != "all":
                filtered_templates = {
                    template_type: self.dashboard_templates.get(template_type, {})
                }
            else:
                filtered_templates = self.dashboard_templates
            
            return {
                "success": True,
                "message": "Dashboard templates retrieved successfully",
                "data": {
                    "templates": filtered_templates,
                    "total_count": len(filtered_templates)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard templates: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get dashboard templates: {str(e)}"
            )
    
    # Helper methods
    async def _generate_widget(
        self,
        widget_name: str,
        organization_id: UUID,
        user_id: Optional[UUID],
        refresh_cache: bool,
        include_realtime: bool,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Generate data for a specific widget"""
        
        # Check cache first
        cache_key = f"{widget_name}_{organization_id}_{user_id}"
        if not refresh_cache and cache_key in self.widget_cache:
            cached_data = self.widget_cache[cache_key]
            if datetime.now().timestamp() - cached_data["timestamp"] < self.cache_ttl:
                return cached_data["data"]
        
        # Generate widget data based on type
        widget_data = None
        
        if widget_name == "kpi_summary":
            widget_data = await self._generate_kpi_summary(organization_id, user_id, parameters)
        elif widget_name == "financial_overview":
            widget_data = await self._generate_financial_overview(organization_id, user_id, parameters)
        elif widget_name == "trend_chart":
            widget_data = await self._generate_trend_chart(organization_id, user_id, parameters)
        elif widget_name == "alerts_summary":
            widget_data = await self._generate_alerts_summary(organization_id, user_id, parameters)
        elif widget_name == "detailed_analytics":
            widget_data = await self._generate_detailed_analytics(organization_id, user_id, parameters)
        elif widget_name == "spending_breakdown":
            widget_data = await self._generate_spending_breakdown(organization_id, user_id, parameters)
        elif widget_name == "income_analysis":
            widget_data = await self._generate_income_analysis(organization_id, user_id, parameters)
        elif widget_name == "budget_performance":
            widget_data = await self._generate_budget_performance(organization_id, user_id, parameters)
        elif widget_name == "ml_insights":
            widget_data = await self._generate_ml_insights(organization_id, user_id, parameters)
        elif widget_name == "performance_metrics":
            widget_data = await self._generate_performance_metrics(organization_id, user_id, parameters)
        elif widget_name == "budget_tracking":
            widget_data = await self._generate_budget_tracking(organization_id, user_id, parameters)
        elif widget_name == "team_summary":
            widget_data = await self._generate_team_summary(organization_id, user_id, parameters)
        elif widget_name == "forecast_summary":
            widget_data = await self._generate_forecast_summary(organization_id, user_id, parameters)
        
        # Cache the result
        if widget_data:
            self.widget_cache[cache_key] = {
                "data": widget_data,
                "timestamp": datetime.now().timestamp()
            }
        
        return widget_data
    
    async def _generate_kpi_summary(
        self,
        organization_id: UUID,
        user_id: Optional[UUID],
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate KPI summary widget data"""
        
        # Get date range from parameters or use default
        date_range = parameters.get("date_range", "30d") if parameters else "30d"
        end_date = date.today()
        
        if date_range == "7d":
            start_date = end_date - timedelta(days=7)
        elif date_range == "30d":
            start_date = end_date - timedelta(days=30)
        elif date_range == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Get financial overview
        overview = await analytics_service.get_financial_overview(
            organization_id, start_date, end_date, user_id
        )
        
        overview_data = overview.get("data", {})
        summary = overview_data.get("summary", {})
        
        # Calculate KPIs
        kpis = {
            "total_income": {
                "value": summary.get("total_income", 0),
                "change": summary.get("income_change", 0),
                "trend": "up" if summary.get("income_change", 0) > 0 else "down"
            },
            "total_expenses": {
                "value": summary.get("total_expenses", 0),
                "change": summary.get("expense_change", 0),
                "trend": "down" if summary.get("expense_change", 0) < 0 else "up"
            },
            "net_income": {
                "value": summary.get("net_income", 0),
                "change": summary.get("net_income_change", 0),
                "trend": "up" if summary.get("net_income_change", 0) > 0 else "down"
            },
            "savings_rate": {
                "value": summary.get("savings_rate", 0),
                "change": summary.get("savings_rate_change", 0),
                "trend": "up" if summary.get("savings_rate_change", 0) > 0 else "down"
            }
        }
        
        return {
            "widget_type": "kpi_summary",
            "title": "Key Performance Indicators",
            "subtitle": f"Last {date_range}",
            "kpis": kpis,
            "last_updated": datetime.now().isoformat()
        }
    
    async def _generate_financial_overview(
        self,
        organization_id: UUID,
        user_id: Optional[UUID],
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate financial overview widget data"""
        
        # Get date range from parameters or use default
        date_range = parameters.get("date_range", "30d") if parameters else "30d"
        end_date = date.today()
        
        if date_range == "7d":
            start_date = end_date - timedelta(days=7)
        elif date_range == "30d":
            start_date = end_date - timedelta(days=30)
        elif date_range == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Get financial overview
        overview = await analytics_service.get_financial_overview(
            organization_id, start_date, end_date, user_id
        )
        
        overview_data = overview.get("data", {})
        summary = overview_data.get("summary", {})
        patterns = overview_data.get("patterns", {})
        health = overview_data.get("health", {})
        
        return {
            "widget_type": "financial_overview",
            "title": "Financial Overview",
            "subtitle": f"Last {date_range}",
            "summary": summary,
            "patterns": patterns,
            "health": health,
            "last_updated": datetime.now().isoformat()
        }
    
    async def _generate_trend_chart(
        self,
        organization_id: UUID,
        user_id: Optional[UUID],
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate trend chart widget data"""
        
        # Get parameters
        metric = parameters.get("metric", "net_income") if parameters else "net_income"
        period = parameters.get("period", "monthly") if parameters else "monthly"
        date_range = parameters.get("date_range", "12m") if parameters else "12m"
        
        end_date = date.today()
        
        if date_range == "6m":
            start_date = end_date - timedelta(days=180)
        elif date_range == "12m":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=365)
        
        # Get trend data
        trends = await analytics_service.get_financial_trends(
            organization_id, start_date, end_date, user_id
        )
        
        trends_data = trends.get("data", {})
        
        return {
            "widget_type": "trend_chart",
            "title": f"{metric.replace('_', ' ').title()} Trends",
            "subtitle": f"Last {date_range} - {period}",
            "metric": metric,
            "period": period,
            "data": trends_data,
            "last_updated": datetime.now().isoformat()
        }
    
    async def _generate_alerts_summary(
        self,
        organization_id: UUID,
        user_id: Optional[UUID],
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate alerts summary widget data"""
        
        # Get parameters
        severity = parameters.get("severity", "all") if parameters else "all"
        status = parameters.get("status", "active") if parameters else "active"
        
        # Get anomalies (as alerts)
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        anomalies = await analytics_service.get_anomaly_detection(
            organization_id, start_date, end_date, user_id
        )
        
        anomalies_data = anomalies.get("data", {})
        detected_anomalies = anomalies_data.get("detected_anomalies", [])
        
        # Categorize by severity
        alerts = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        
        for anomaly in detected_anomalies:
            severity_level = anomaly.get("severity", "medium")
            if severity_level in alerts:
                alerts[severity_level].append(anomaly)
        
        # Count alerts by status
        alert_counts = {
            "total": len(detected_anomalies),
            "critical": len(alerts["critical"]),
            "high": len(alerts["high"]),
            "medium": len(alerts["medium"]),
            "low": len(alerts["low"])
        }
        
        return {
            "widget_type": "alerts_summary",
            "title": "Alerts & Anomalies",
            "subtitle": "Last 30 days",
            "alert_counts": alert_counts,
            "recent_alerts": detected_anomalies[:5],  # Show last 5
            "last_updated": datetime.now().isoformat()
        }
    
    async def _generate_detailed_analytics(
        self,
        organization_id: UUID,
        user_id: Optional[UUID],
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate detailed analytics widget data"""
        
        # Get parameters
        date_range = parameters.get("date_range", "30d") if parameters else "30d"
        metrics = parameters.get("metrics", ["spending", "income", "budgets"]) if parameters else ["spending", "income", "budgets"]
        grouping = parameters.get("grouping", "category") if parameters else "category"
        
        end_date = date.today()
        
        if date_range == "7d":
            start_date = end_date - timedelta(days=7)
        elif date_range == "30d":
            start_date = end_date - timedelta(days=30)
        elif date_range == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)
        
        analytics_data = {}
        
        # Get spending analysis
        if "spending" in metrics:
            spending = await analytics_service.get_spending_analysis(
                organization_id, start_date, end_date, user_id
            )
            analytics_data["spending"] = spending.get("data", {})
        
        # Get income analysis
        if "income" in metrics:
            income = await analytics_service.get_income_analysis(
                organization_id, start_date, end_date, user_id
            )
            analytics_data["income"] = income.get("data", {})
        
        # Get budget analysis
        if "budgets" in metrics:
            budgets = await analytics_service.get_budget_analysis(
                organization_id, start_date, end_date, user_id
            )
            analytics_data["budgets"] = budgets.get("data", {})
        
        return {
            "widget_type": "detailed_analytics",
            "title": "Detailed Analytics",
            "subtitle": f"Last {date_range} - {grouping} grouping",
            "metrics": metrics,
            "grouping": grouping,
            "data": analytics_data,
            "last_updated": datetime.now().isoformat()
        }
    
    async def _generate_spending_breakdown(
        self,
        organization_id: UUID,
        user_id: Optional[UUID],
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate spending breakdown widget data"""
        
        # Get parameters
        date_range = parameters.get("date_range", "30d") if parameters else "30d"
        grouping = parameters.get("grouping", "category") if parameters else "category"
        limit = parameters.get("limit", 10) if parameters else 10
        
        end_date = date.today()
        
        if date_range == "7d":
            start_date = end_date - timedelta(days=7)
        elif date_range == "30d":
            start_date = end_date - timedelta(days=30)
        elif date_range == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Get spending analysis
        spending = await analytics_service.get_spending_analysis(
            organization_id, start_date, end_date, user_id
        )
        
        spending_data = spending.get("data", {})
        category_breakdown = spending_data.get("category_breakdown", [])
        
        # Limit results
        if limit and len(category_breakdown) > limit:
            category_breakdown = category_breakdown[:limit]
        
        return {
            "widget_type": "spending_breakdown",
            "title": "Spending Breakdown",
            "subtitle": f"Last {date_range} by {grouping}",
            "grouping": grouping,
            "data": category_breakdown,
            "total_spending": spending_data.get("total_spending", 0),
            "last_updated": datetime.now().isoformat()
        }
    
    async def _generate_income_analysis(
        self,
        organization_id: UUID,
        user_id: Optional[UUID],
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate income analysis widget data"""
        
        # Get parameters
        date_range = parameters.get("date_range", "30d") if parameters else "30d"
        grouping = parameters.get("grouping", "source") if parameters else "source"
        
        end_date = date.today()
        
        if date_range == "7d":
            start_date = end_date - timedelta(days=7)
        elif date_range == "30d":
            start_date = end_date - timedelta(days=30)
        elif date_range == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Get income analysis
        income = await analytics_service.get_income_analysis(
            organization_id, start_date, end_date, user_id
        )
        
        income_data = income.get("data", {})
        
        return {
            "widget_type": "income_analysis",
            "title": "Income Analysis",
            "subtitle": f"Last {date_range} by {grouping}",
            "grouping": grouping,
            "data": income_data,
            "total_income": income_data.get("total_income", 0),
            "last_updated": datetime.now().isoformat()
        }
    
    async def _generate_budget_performance(
        self,
        organization_id: UUID,
        user_id: Optional[UUID],
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate budget performance widget data"""
        
        # Get parameters
        date_range = parameters.get("date_range", "30d") if parameters else "30d"
        budget_ids = parameters.get("budget_ids", []) if parameters else []
        
        end_date = date.today()
        
        if date_range == "7d":
            start_date = end_date - timedelta(days=7)
        elif date_range == "30d":
            start_date = end_date - timedelta(days=30)
        elif date_range == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Get budget analysis
        budgets = await analytics_service.get_budget_analysis(
            organization_id, start_date, end_date, user_id
        )
        
        budgets_data = budgets.get("data", {})
        
        return {
            "widget_type": "budget_performance",
            "title": "Budget Performance",
            "subtitle": f"Last {date_range}",
            "data": budgets_data,
            "budget_ids": budget_ids,
            "last_updated": datetime.now().isoformat()
        }
    
    async def _generate_ml_insights(
        self,
        organization_id: UUID,
        user_id: Optional[UUID],
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate ML insights widget data"""
        
        # Get parameters
        prediction_type = parameters.get("prediction_type", "spending") if parameters else "spending"
        horizon = parameters.get("horizon", 3) if parameters else 3
        
        ml_data = {}
        
        try:
            # Get spending predictions
            if prediction_type == "spending":
                spending_prediction = await ml_service.predict_spending(
                    organization_id, horizon, user_id
                )
                if spending_prediction["success"]:
                    ml_data["spending_prediction"] = spending_prediction["data"]
            
            # Get cash flow predictions
            elif prediction_type == "cash_flow":
                cash_flow_prediction = await ml_service.predict_cash_flow(
                    organization_id, horizon, user_id
                )
                if cash_flow_prediction["success"]:
                    ml_data["cash_flow_prediction"] = cash_flow_prediction["data"]
            
            # Get anomaly detection
            elif prediction_type == "anomalies":
                anomalies = await ml_service.detect_advanced_anomalies(
                    organization_id, user_id
                )
                if anomalies["success"]:
                    ml_data["anomalies"] = anomalies["data"]
            
            # Get clustering insights
            elif prediction_type == "clustering":
                clustering = await ml_service.cluster_spending_patterns(
                    organization_id, user_id
                )
                if clustering["success"]:
                    ml_data["clustering"] = clustering["data"]
            
        except Exception as e:
            logger.warning(f"Failed to get ML insights: {e}")
            ml_data["error"] = str(e)
        
        return {
            "widget_type": "ml_insights",
            "title": "Machine Learning Insights",
            "subtitle": f"{prediction_type.replace('_', ' ').title()} - {horizon} periods ahead",
            "prediction_type": prediction_type,
            "horizon": horizon,
            "data": ml_data,
            "last_updated": datetime.now().isoformat()
        }
    
    async def _generate_performance_metrics(
        self,
        organization_id: UUID,
        user_id: Optional[UUID],
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate performance metrics widget data"""
        
        # Get parameters
        date_range = parameters.get("date_range", "30d") if parameters else "30d"
        metrics = parameters.get("metrics", ["efficiency", "growth", "stability"]) if parameters else ["efficiency", "growth", "stability"]
        
        end_date = date.today()
        
        if date_range == "7d":
            start_date = end_date - timedelta(days=7)
        elif date_range == "30d":
            start_date = end_date - timedelta(days=30)
        elif date_range == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Get financial overview for metrics
        overview = await analytics_service.get_financial_overview(
            organization_id, start_date, end_date, user_id
        )
        
        overview_data = overview.get("data", {})
        summary = overview_data.get("summary", {})
        
        # Calculate performance metrics
        performance_metrics = {}
        
        if "efficiency" in metrics:
            performance_metrics["efficiency"] = {
                "savings_rate": summary.get("savings_rate", 0),
                "expense_ratio": summary.get("expense_ratio", 0),
                "cash_flow_efficiency": summary.get("cash_flow", 0) / max(summary.get("total_income", 1), 1)
            }
        
        if "growth" in metrics:
            performance_metrics["growth"] = {
                "income_growth": summary.get("income_change", 0),
                "expense_growth": summary.get("expense_change", 0),
                "net_income_growth": summary.get("net_income_change", 0)
            }
        
        if "stability" in metrics:
            performance_metrics["stability"] = {
                "income_volatility": 0,  # Would calculate from historical data
                "expense_volatility": 0,  # Would calculate from historical data
                "cash_flow_stability": "stable" if summary.get("cash_flow", 0) > 0 else "unstable"
            }
        
        return {
            "widget_type": "performance_metrics",
            "title": "Performance Metrics",
            "subtitle": f"Last {date_range}",
            "metrics": metrics,
            "data": performance_metrics,
            "last_updated": datetime.now().isoformat()
        }
    
    async def _generate_budget_tracking(
        self,
        organization_id: UUID,
        user_id: Optional[UUID],
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate budget tracking widget data"""
        
        # Get parameters
        budget_ids = parameters.get("budget_ids", []) if parameters else []
        thresholds = parameters.get("thresholds", {"warning": 0.8, "critical": 0.95}) if parameters else {"warning": 0.8, "critical": 0.95}
        
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        # Get budget analysis
        budgets = await analytics_service.get_budget_analysis(
            organization_id, start_date, end_date, user_id
        )
        
        budgets_data = budgets.get("data", {})
        budget_performance = budgets_data.get("budget_performance", [])
        
        # Filter by budget IDs if specified
        if budget_ids:
            budget_performance = [
                budget for budget in budget_performance
                if budget.get("budget_id") in budget_ids
            ]
        
        # Add threshold alerts
        for budget in budget_performance:
            utilization = budget.get("utilization", 0)
            if utilization >= thresholds["critical"]:
                budget["alert_level"] = "critical"
            elif utilization >= thresholds["warning"]:
                budget["alert_level"] = "warning"
            else:
                budget["alert_level"] = "normal"
        
        return {
            "widget_type": "budget_tracking",
            "title": "Budget Tracking",
            "subtitle": "Real-time budget monitoring",
            "thresholds": thresholds,
            "budget_ids": budget_ids,
            "data": budget_performance,
            "last_updated": datetime.now().isoformat()
        }
    
    async def _generate_team_summary(
        self,
        organization_id: UUID,
        user_id: Optional[UUID],
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate team summary widget data"""
        
        # Get parameters
        team_ids = parameters.get("team_ids", []) if parameters else []
        date_range = parameters.get("date_range", "30d") if parameters else "30d"
        
        end_date = date.today()
        
        if date_range == "7d":
            start_date = end_date - timedelta(days=7)
        elif date_range == "30d":
            start_date = end_date - timedelta(days=30)
        elif date_range == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)
        
        # This would typically query team-specific data
        # For now, return placeholder data
        team_summary = {
            "total_members": 12,
            "active_members": 10,
            "total_spending": 45000.00,
            "average_spending": 4500.00,
            "budget_utilization": 0.75,
            "top_spenders": [
                {"user_id": "user1", "name": "John Doe", "spending": 8000.00},
                {"user_id": "user2", "name": "Jane Smith", "spending": 6500.00},
                {"user_id": "user3", "name": "Bob Johnson", "spending": 5200.00}
            ]
        }
        
        return {
            "widget_type": "team_summary",
            "title": "Team Summary",
            "subtitle": f"Last {date_range}",
            "team_ids": team_ids,
            "data": team_summary,
            "last_updated": datetime.now().isoformat()
        }
    
    async def _generate_forecast_summary(
        self,
        organization_id: UUID,
        user_id: Optional[UUID],
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate forecast summary widget data"""
        
        # Get parameters
        forecast_type = parameters.get("forecast_type", "cash_flow") if parameters else "cash_flow"
        horizon = parameters.get("horizon", 6) if parameters else 6
        
        forecast_data = {}
        
        try:
            if forecast_type == "cash_flow":
                cash_flow_prediction = await ml_service.predict_cash_flow(
                    organization_id, horizon, user_id
                )
                if cash_flow_prediction["success"]:
                    forecast_data["cash_flow"] = cash_flow_prediction["data"]
            
            elif forecast_type == "spending":
                spending_prediction = await ml_service.predict_spending(
                    organization_id, horizon, user_id
                )
                if spending_prediction["success"]:
                    forecast_data["spending"] = spending_prediction["data"]
            
            # Get scenario analysis
            scenarios = await ml_service.generate_forecast_scenarios(
                organization_id, forecast_type, horizon, user_id
            )
            if scenarios["success"]:
                forecast_data["scenarios"] = scenarios["data"]
        
        except Exception as e:
            logger.warning(f"Failed to get forecast data: {e}")
            forecast_data["error"] = str(e)
        
        return {
            "widget_type": "forecast_summary",
            "title": "Forecast Summary",
            "subtitle": f"{forecast_type.replace('_', ' ').title()} - {horizon} periods ahead",
            "forecast_type": forecast_type,
            "horizon": horizon,
            "data": forecast_data,
            "last_updated": datetime.now().isoformat()
        }


# Global dashboard service instance
dashboard_service = DashboardService()


# Export functions and classes
__all__ = [
    "DashboardService",
    "dashboard_service"
]