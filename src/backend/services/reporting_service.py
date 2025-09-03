"""
Reporting service for Financial Analytics Platform
Handles advanced reporting, dashboard generation, and scheduled reports
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple
from uuid import UUID, uuid4
from decimal import Decimal
import json
import csv
import io
from pathlib import Path
import jinja2
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from fastapi import HTTPException, status
from sqlmodel import select, func, and_, or_

from src.backend.services.analytics_service import analytics_service
from src.backend.services.ml_service import ml_service
from src.backend.models.database import Transaction, Account, Category, Budget, User, Organization
from src.backend.database import get_session
from src.common.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ReportingService:
    """Service for advanced financial reporting and dashboard generation"""
    
    def __init__(self):
        self.templates_dir = Path("templates/reports")
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        
        # Initialize Jinja2 environment
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.templates_dir)),
            autoescape=True
        )
    
    async def generate_comprehensive_report(
        self,
        organization_id: UUID,
        report_type: str = "monthly",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        user_id: Optional[UUID] = None,
        format: str = "pdf",
        include_charts: bool = True,
        include_predictions: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive financial report"""
        
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = date.today()
            if not start_date:
                if report_type == "monthly":
                    start_date = end_date.replace(day=1)
                elif report_type == "quarterly":
                    quarter_start = ((end_date.month - 1) // 3) * 3 + 1
                    start_date = end_date.replace(month=quarter_start, day=1)
                elif report_type == "yearly":
                    start_date = end_date.replace(month=1, day=1)
                else:
                    start_date = end_date - timedelta(days=30)
            
            # Gather all report data
            report_data = await self._gather_report_data(
                organization_id, start_date, end_date, user_id, include_predictions
            )
            
            # Generate report based on format
            if format.lower() == "pdf":
                report_file = await self._generate_pdf_report(report_data, report_type)
            elif format.lower() == "html":
                report_file = await self._generate_html_report(report_data, report_type)
            elif format.lower() == "csv":
                report_file = await self._generate_csv_report(report_data, report_type)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported format: {format}"
                )
            
            return {
                "success": True,
                "message": f"{report_type.title()} report generated successfully",
                "data": {
                    "report_type": report_type,
                    "format": format,
                    "file_path": str(report_file),
                    "file_size": report_file.stat().st_size if report_file.exists() else 0,
                    "generation_timestamp": datetime.now().isoformat(),
                    "date_range": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "days": (end_date - start_date).days
                    },
                    "summary": report_data.get("summary", {})
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate comprehensive report: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate report: {str(e)}"
            )
    
    async def generate_dashboard_data(
        self,
        organization_id: UUID,
        dashboard_type: str = "executive",
        user_id: Optional[UUID] = None,
        refresh_cache: bool = False
    ) -> Dict[str, Any]:
        """Generate dashboard data for frontend visualization"""
        
        try:
            # Get current date range
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            # Gather dashboard data
            dashboard_data = await self._gather_dashboard_data(
                organization_id, start_date, end_date, user_id, dashboard_type
            )
            
            return {
                "success": True,
                "message": f"{dashboard_type.title()} dashboard data generated successfully",
                "data": {
                    "dashboard_type": dashboard_type,
                    "refresh_timestamp": datetime.now().isoformat(),
                    "date_range": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    },
                    "widgets": dashboard_data
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate dashboard data: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate dashboard data: {str(e)}"
            )
    
    async def create_scheduled_report(
        self,
        organization_id: UUID,
        report_config: Dict[str, Any],
        user_id: UUID
    ) -> Dict[str, Any]:
        """Create a scheduled report configuration"""
        
        try:
            # Validate report configuration
            required_fields = ["name", "type", "frequency", "recipients", "format"]
            for field in required_fields:
                if field not in report_config:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Missing required field: {field}"
                    )
            
            # Save report configuration (in a real implementation, this would go to database)
            report_id = str(uuid4())
            report_config["id"] = report_id
            report_config["organization_id"] = str(organization_id)
            report_config["created_by"] = str(user_id)
            report_config["created_at"] = datetime.now().isoformat()
            report_config["status"] = "active"
            
            return {
                "success": True,
                "message": "Scheduled report created successfully",
                "data": {
                    "report_id": report_id,
                    "config": report_config
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create scheduled report: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create scheduled report: {str(e)}"
            )
    
    async def get_report_templates(
        self,
        template_type: str = "all"
    ) -> Dict[str, Any]:
        """Get available report templates"""
        
        templates = {
            "monthly": {
                "id": "monthly",
                "name": "Monthly Financial Report",
                "description": "Comprehensive monthly financial overview with charts and analysis",
                "sections": ["summary", "spending", "income", "budgets", "trends", "predictions"],
                "charts": ["spending_by_category", "income_trends", "budget_variance"],
                "format": ["pdf", "html", "csv"]
            },
            "quarterly": {
                "id": "quarterly",
                "name": "Quarterly Business Review",
                "description": "Quarterly financial performance with year-over-year comparisons",
                "sections": ["summary", "performance", "trends", "forecasting", "recommendations"],
                "charts": ["quarterly_comparison", "trend_analysis", "forecast_charts"],
                "format": ["pdf", "html"]
            },
            "annual": {
                "id": "annual",
                "name": "Annual Financial Report",
                "description": "Comprehensive annual financial analysis and planning",
                "sections": ["executive_summary", "financial_statements", "analysis", "forecasting", "strategy"],
                "charts": ["annual_summary", "long_term_trends", "scenario_analysis"],
                "format": ["pdf", "html"]
            },
            "executive": {
                "id": "executive",
                "name": "Executive Dashboard",
                "description": "High-level executive summary with key metrics and insights",
                "sections": ["kpis", "summary", "alerts", "trends"],
                "charts": ["kpi_dashboard", "trend_summary", "alert_summary"],
                "format": ["html", "pdf"]
            },
            "custom": {
                "id": "custom",
                "name": "Custom Report Builder",
                "description": "Build custom reports with selected sections and charts",
                "sections": ["configurable"],
                "charts": ["configurable"],
                "format": ["pdf", "html", "csv"]
            }
        }
        
        if template_type != "all":
            filtered_templates = {template_type: templates.get(template_type, {})}
        else:
            filtered_templates = templates
        
        return {
            "success": True,
            "message": "Report templates retrieved successfully",
            "data": {
                "templates": filtered_templates,
                "total_count": len(filtered_templates)
            }
        }
    
    async def export_report_data(
        self,
        organization_id: UUID,
        export_type: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        user_id: Optional[UUID] = None,
        format: str = "csv"
    ) -> Dict[str, Any]:
        """Export report data in various formats"""
        
        try:
            # Set default date range
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Get data based on export type
            if export_type == "transactions":
                data = await self._export_transactions_data(
                    organization_id, start_date, end_date, user_id
                )
            elif export_type == "analytics":
                data = await self._export_analytics_data(
                    organization_id, start_date, end_date, user_id
                )
            elif export_type == "budgets":
                data = await self._export_budgets_data(
                    organization_id, start_date, end_date, user_id
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported export type: {export_type}"
                )
            
            # Format export based on requested format
            if format.lower() == "csv":
                export_content = self._format_csv_export(data, export_type)
                file_extension = "csv"
            elif format.lower() == "json":
                export_content = json.dumps(data, indent=2, default=str)
                file_extension = "json"
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported export format: {format}"
                )
            
            # Generate filename
            filename = f"{export_type}_export_{start_date.isoformat()}_{end_date.isoformat()}.{file_extension}"
            
            return {
                "success": True,
                "message": f"{export_type.title()} data exported successfully",
                "data": {
                    "export_type": export_type,
                    "format": format,
                    "filename": filename,
                    "content": export_content,
                    "date_range": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    }
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to export report data: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to export data: {str(e)}"
            )
    
    # Helper methods
    async def _gather_report_data(
        self,
        organization_id: UUID,
        start_date: date,
        end_date: date,
        user_id: Optional[UUID],
        include_predictions: bool
    ) -> Dict[str, Any]:
        """Gather all data needed for comprehensive report"""
        
        # Get analytics data
        overview = await analytics_service.get_financial_overview(
            organization_id, start_date, end_date, user_id
        )
        
        spending_analysis = await analytics_service.get_spending_analysis(
            organization_id, start_date, end_date, user_id
        )
        
        income_analysis = await analytics_service.get_income_analysis(
            organization_id, start_date, end_date, user_id
        )
        
        budget_analysis = await analytics_service.get_budget_analysis(
            organization_id, start_date, end_date, user_id
        )
        
        # Get ML predictions if requested
        predictions = {}
        if include_predictions:
            try:
                spending_prediction = await ml_service.predict_spending(
                    organization_id, 3, user_id
                )
                if spending_prediction["success"]:
                    predictions["spending"] = spending_prediction["data"]
                
                cash_flow_prediction = await ml_service.predict_cash_flow(
                    organization_id, 6, user_id
                )
                if cash_flow_prediction["success"]:
                    predictions["cash_flow"] = cash_flow_prediction["data"]
            except Exception as e:
                logger.warning(f"Failed to get predictions: {e}")
                predictions = {"error": str(e)}
        
        return {
            "overview": overview.get("data", {}),
            "spending": spending_analysis.get("data", {}),
            "income": income_analysis.get("data", {}),
            "budgets": budget_analysis.get("data", {}),
            "predictions": predictions,
            "summary": {
                "period": f"{start_date.strftime('%B %Y')} - {end_date.strftime('%B %Y')}",
                "total_days": (end_date - start_date).days,
                "generated_at": datetime.now().isoformat()
            }
        }
    
    async def _gather_dashboard_data(
        self,
        organization_id: UUID,
        start_date: date,
        end_date: date,
        user_id: Optional[UUID],
        dashboard_type: str
    ) -> Dict[str, Any]:
        """Gather data for dashboard widgets"""
        
        # Get basic analytics data
        overview = await analytics_service.get_financial_overview(
            organization_id, start_date, end_date, user_id
        )
        
        # Get spending analysis for charts
        spending = await analytics_service.get_spending_analysis(
            organization_id, start_date, end_date, user_id
        )
        
        # Get income analysis
        income = await analytics_service.get_income_analysis(
            organization_id, start_date, end_date, user_id
        )
        
        # Get budget performance
        budgets = await analytics_service.get_budget_analysis(
            organization_id, start_date, end_date, user_id
        )
        
        # Get recent anomalies
        anomalies = await analytics_service.get_anomaly_detection(
            organization_id, start_date, end_date, user_id
        )
        
        return {
            "overview": overview.get("data", {}),
            "spending": spending.get("data", {}),
            "income": income.get("data", {}),
            "budgets": budgets.get("data", {}),
            "anomalies": anomalies.get("data", {}),
            "dashboard_type": dashboard_type
        }
    
    async def _generate_pdf_report(
        self,
        report_data: Dict[str, Any],
        report_type: str
    ) -> Path:
        """Generate PDF report using ReportLab"""
        
        filename = f"financial_report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = self.reports_dir / filename
        
        doc = SimpleDocTemplate(str(filepath), pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center
        )
        story.append(Paragraph(f"{report_type.title()} Financial Report", title_style))
        story.append(Spacer(1, 20))
        
        # Summary section
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        summary_data = report_data.get("summary", {})
        if summary_data:
            summary_table_data = [
                ["Period", summary_data.get("period", "N/A")],
                ["Total Days", str(summary_data.get("total_days", "N/A"))],
                ["Generated At", summary_data.get("generated_at", "N/A")]
            ]
            
            summary_table = Table(summary_table_data)
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(summary_table)
        
        story.append(Spacer(1, 20))
        
        # Financial overview
        overview = report_data.get("overview", {})
        if overview:
            story.append(Paragraph("Financial Overview", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            overview_data = overview.get("summary", {})
            if overview_data:
                overview_table_data = [
                    ["Metric", "Value"],
                    ["Total Income", f"${overview_data.get('total_income', 0):,.2f}"],
                    ["Total Expenses", f"${overview_data.get('total_expenses', 0):,.2f}"],
                    ["Net Income", f"${overview_data.get('net_income', 0):,.2f}"],
                    ["Savings Rate", f"{overview_data.get('savings_rate', 0):.1f}%"]
                ]
                
                overview_table = Table(overview_table_data)
                overview_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(overview_table)
        
        # Build PDF
        doc.build(story)
        return filepath
    
    async def _generate_html_report(
        self,
        report_data: Dict[str, Any],
        report_type: str
    ) -> Path:
        """Generate HTML report using Jinja2 templates"""
        
        filename = f"financial_report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = self.reports_dir / filename
        
        # Create default template if none exists
        template_content = self._get_default_html_template()
        
        # Render template
        template = self.jinja_env.from_string(template_content)
        html_content = template.render(
            report_data=report_data,
            report_type=report_type,
            generated_at=datetime.now().isoformat()
        )
        
        # Write HTML file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath
    
    async def _generate_csv_report(
        self,
        report_data: Dict[str, Any],
        report_type: str
    ) -> Path:
        """Generate CSV report"""
        
        filename = f"financial_report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([f"{report_type.title()} Financial Report"])
            writer.writerow([f"Generated: {datetime.now().isoformat()}"])
            writer.writerow([])
            
            # Write overview data
            overview = report_data.get("overview", {})
            if overview:
                writer.writerow(["Financial Overview"])
                summary = overview.get("summary", {})
                if summary:
                    writer.writerow(["Total Income", f"${summary.get('total_income', 0):,.2f}"])
                    writer.writerow(["Total Expenses", f"${summary.get('total_expenses', 0):,.2f}"])
                    writer.writerow(["Net Income", f"${summary.get('net_income', 0):,.2f}"])
                    writer.writerow(["Savings Rate", f"{summary.get('savings_rate', 0):.1f}%"])
                writer.writerow([])
        
        return filepath
    
    def _get_default_html_template(self) -> str:
        """Get default HTML template for reports"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ report_type.title() }} Financial Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .section { margin-bottom: 30px; }
        .section h2 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 5px; }
        .metric { display: inline-block; margin: 10px; padding: 15px; background: #f8f9fa; border-radius: 5px; }
        .metric-value { font-size: 24px; font-weight: bold; color: #007bff; }
        .metric-label { font-size: 14px; color: #666; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #007bff; color: white; }
        .footer { text-align: center; margin-top: 50px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ report_type.title() }} Financial Report</h1>
        <p>Generated on {{ generated_at }}</p>
    </div>
    
    <div class="section">
        <h2>Executive Summary</h2>
        <div class="metric">
            <div class="metric-value">${{ "%.2f"|format(report_data.overview.summary.total_income|default(0)) }}</div>
            <div class="metric-label">Total Income</div>
        </div>
        <div class="metric">
            <div class="metric-value">${{ "%.2f"|format(report_data.overview.summary.total_expenses|default(0)) }}</div>
            <div class="metric-label">Total Expenses</div>
        </div>
        <div class="metric">
            <div class="metric-value">${{ "%.2f"|format(report_data.overview.summary.net_income|default(0)) }}</div>
            <div class="metric-label">Net Income</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ "%.1f"|format(report_data.overview.summary.savings_rate|default(0)) }}%</div>
            <div class="metric-label">Savings Rate</div>
        </div>
    </div>
    
    <div class="footer">
        <p>Financial Analytics Platform - {{ report_type.title() }} Report</p>
    </div>
</body>
</html>
        """
    
    async def _export_transactions_data(
        self,
        organization_id: UUID,
        start_date: date,
        end_date: date,
        user_id: Optional[UUID]
    ) -> List[Dict[str, Any]]:
        """Export transactions data"""
        
        async with get_session() as session:
            conditions = [
                Transaction.organization_id == organization_id,
                Transaction.deleted_at.is_(None),
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ]
            
            if user_id:
                conditions.append(Transaction.user_id == user_id)
            
            statement = select(Transaction).where(and_(*conditions))
            result = await session.exec(statement)
            transactions = result.all()
            
            return [
                {
                    "id": str(tx.id),
                    "date": tx.date.isoformat(),
                    "amount": float(tx.amount),
                    "description": tx.description,
                    "category": tx.category.name if tx.category else None,
                    "merchant": tx.merchant_name,
                    "reference": tx.reference,
                    "notes": tx.notes
                }
                for tx in transactions
            ]
    
    async def _export_analytics_data(
        self,
        organization_id: UUID,
        start_date: date,
        end_date: date,
        user_id: Optional[UUID]
    ) -> Dict[str, Any]:
        """Export analytics data"""
        
        overview = await analytics_service.get_financial_overview(
            organization_id, start_date, end_date, user_id
        )
        
        spending = await analytics_service.get_spending_analysis(
            organization_id, start_date, end_date, user_id
        )
        
        income = await analytics_service.get_income_analysis(
            organization_id, start_date, end_date, user_id
        )
        
        return {
            "overview": overview.get("data", {}),
            "spending": spending.get("data", {}),
            "income": income.get("data", {})
        }
    
    async def _export_budgets_data(
        self,
        organization_id: UUID,
        start_date: date,
        end_date: date,
        user_id: Optional[UUID]
    ) -> List[Dict[str, Any]]:
        """Export budgets data"""
        
        async with get_session() as session:
            conditions = [
                Budget.organization_id == organization_id,
                Budget.is_active == True
            ]
            
            if user_id:
                conditions.append(Budget.user_id == user_id)
            
            statement = select(Budget).where(and_(*conditions))
            result = await session.exec(statement)
            budgets = result.all()
            
            return [
                {
                    "id": str(budget.id),
                    "name": budget.name,
                    "amount": float(budget.amount),
                    "start_date": budget.start_date.isoformat(),
                    "end_date": budget.end_date.isoformat(),
                    "category": budget.category.name if budget.category else None
                }
                for budget in budgets
            ]
    
    def _format_csv_export(
        self,
        data: Union[List[Dict[str, Any]], Dict[str, Any]],
        export_type: str
    ) -> str:
        """Format data as CSV string"""
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        if export_type == "transactions" and isinstance(data, list):
            if data:
                # Write header
                writer.writerow(data[0].keys())
                # Write data
                for row in data:
                    writer.writerow(row.values())
        else:
            # For other types, write as key-value pairs
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        writer.writerow([key, str(value)])
                    else:
                        writer.writerow([key, value])
        
        return output.getvalue()


# Global reporting service instance
reporting_service = ReportingService()


# Export functions and classes
__all__ = [
    "ReportingService",
    "reporting_service"
]