"""
Unit tests for Sprint 5: Advanced Reporting & Dashboards
Tests the reporting service, dashboard service, and related functionality
"""

import pytest
from datetime import datetime, date, timedelta
from uuid import UUID, uuid4
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from src.backend.services.reporting_service import ReportingService, reporting_service
from src.backend.services.dashboard_service import DashboardService, dashboard_service
from src.backend.services.analytics_service import analytics_service
from src.backend.services.ml_service import ml_service
from src.backend.models.database import User, Organization


class TestReportingService:
    """Test ReportingService functionality"""

    @pytest.fixture
    def reporting_service_instance(self):
        """Create a fresh reporting service instance for testing"""
        return ReportingService()

    @pytest.fixture
    def mock_organization_id(self):
        """Mock organization ID"""
        return uuid4()

    @pytest.fixture
    def mock_user_id(self):
        """Mock user ID"""
        return uuid4()

    @pytest.fixture
    def sample_report_data(self):
        """Sample report data for testing"""
        return {
            "overview": {
                "summary": {
                    "total_income": 10000.00,
                    "total_expenses": 7000.00,
                    "net_income": 3000.00,
                    "savings_rate": 30.0
                }
            },
            "spending": {
                "category_breakdown": [
                    {"category": "Food", "amount": 2000.00},
                    {"category": "Transport", "amount": 1500.00}
                ]
            },
            "income": {
                "source_breakdown": [
                    {"source": "Salary", "amount": 8000.00},
                    {"source": "Freelance", "amount": 2000.00}
                ]
            },
            "budgets": {
                "budget_performance": [
                    {"budget": "Food", "planned": 2500.00, "actual": 2000.00}
                ]
            }
        }

    def test_reporting_service_initialization(self, reporting_service_instance):
        """Test reporting service initialization"""
        assert reporting_service_instance.templates_dir.exists()
        assert reporting_service_instance.reports_dir.exists()
        assert reporting_service_instance.jinja_env is not None

    @pytest.mark.asyncio
    async def test_generate_comprehensive_report_monthly(self, reporting_service_instance, mock_organization_id, mock_user_id, sample_report_data):
        """Test monthly report generation"""
        with patch.object(analytics_service, 'get_financial_overview', return_value={"data": sample_report_data["overview"]}), \
             patch.object(analytics_service, 'get_spending_analysis', return_value={"data": sample_report_data["spending"]}), \
             patch.object(analytics_service, 'get_income_analysis', return_value={"data": sample_report_data["income"]}), \
             patch.object(analytics_service, 'get_budget_analysis', return_value={"data": sample_report_data["budgets"]}), \
             patch.object(ml_service, 'predict_spending', return_value={"success": True, "data": {"predictions": [1000, 1100, 1200]}}), \
             patch.object(ml_service, 'predict_cash_flow', return_value={"success": True, "data": {"predictions": [500, 600, 700]}}):
            
            result = await reporting_service_instance.generate_comprehensive_report(
                organization_id=mock_organization_id,
                report_type="monthly",
                user_id=mock_user_id,
                format="pdf"
            )
            
            assert result["success"] is True
            assert "monthly" in result["message"].lower()
            assert result["data"]["report_type"] == "monthly"
            assert result["data"]["format"] == "pdf"

    @pytest.mark.asyncio
    async def test_generate_comprehensive_report_quarterly(self, reporting_service_instance, mock_organization_id, mock_user_id, sample_report_data):
        """Test quarterly report generation"""
        with patch.object(analytics_service, 'get_financial_overview', return_value={"data": sample_report_data["overview"]}), \
             patch.object(analytics_service, 'get_spending_analysis', return_value={"data": sample_report_data["spending"]}), \
             patch.object(analytics_service, 'get_income_analysis', return_value={"data": sample_report_data["income"]}), \
             patch.object(analytics_service, 'get_budget_analysis', return_value={"data": sample_report_data["budgets"]}):
            
            result = await reporting_service_instance.generate_comprehensive_report(
                organization_id=mock_organization_id,
                report_type="quarterly",
                user_id=mock_user_id,
                format="html"
            )
            
            assert result["success"] is True
            assert "quarterly" in result["message"].lower()
            assert result["data"]["report_type"] == "quarterly"
            assert result["data"]["format"] == "html"

    @pytest.mark.asyncio
    async def test_generate_comprehensive_report_yearly(self, reporting_service_instance, mock_organization_id, mock_user_id, sample_report_data):
        """Test yearly report generation"""
        with patch.object(analytics_service, 'get_financial_overview', return_value={"data": sample_report_data["overview"]}), \
             patch.object(analytics_service, 'get_spending_analysis', return_value={"data": sample_report_data["spending"]}), \
             patch.object(analytics_service, 'get_income_analysis', return_value={"data": sample_report_data["income"]}), \
             patch.object(analytics_service, 'get_budget_analysis', return_value={"data": sample_report_data["budgets"]}):
            
            result = await reporting_service_instance.generate_comprehensive_report(
                organization_id=mock_organization_id,
                report_type="yearly",
                user_id=mock_user_id,
                format="csv"
            )
            
            assert result["success"] is True
            assert "yearly" in result["message"].lower()
            assert result["data"]["report_type"] == "yearly"
            assert result["data"]["format"] == "csv"

    @pytest.mark.asyncio
    async def test_generate_dashboard_data(self, reporting_service_instance, mock_organization_id, mock_user_id):
        """Test dashboard data generation"""
        with patch.object(analytics_service, 'get_financial_overview', return_value={"data": {"summary": {"total_income": 10000}}}), \
             patch.object(analytics_service, 'get_spending_analysis', return_value={"data": {"category_breakdown": []}}), \
             patch.object(analytics_service, 'get_income_analysis', return_value={"data": {"source_breakdown": []}}), \
             patch.object(analytics_service, 'get_budget_analysis', return_value={"data": {"budget_performance": []}}), \
             patch.object(analytics_service, 'get_anomaly_detection', return_value={"data": {"detected_anomalies": []}}):
            
            result = await reporting_service_instance.generate_dashboard_data(
                organization_id=mock_organization_id,
                dashboard_type="executive",
                user_id=mock_user_id
            )
            
            assert result["success"] is True
            assert "executive" in result["message"].lower()
            assert result["data"]["dashboard_type"] == "executive"

    @pytest.mark.asyncio
    async def test_create_scheduled_report(self, reporting_service_instance, mock_organization_id, mock_user_id):
        """Test scheduled report creation"""
        report_config = {
            "name": "Monthly Executive Summary",
            "type": "monthly",
            "frequency": "monthly",
            "recipients": ["exec@company.com"],
            "format": "pdf"
        }
        
        result = await reporting_service_instance.create_scheduled_report(
            organization_id=mock_organization_id,
            report_config=report_config,
            user_id=mock_user_id
        )
        
        assert result["success"] is True
        assert "created successfully" in result["message"]
        assert "report_id" in result["data"]
        assert result["data"]["config"]["name"] == "Monthly Executive Summary"

    def test_get_report_templates(self, reporting_service_instance):
        """Test report template retrieval"""
        # Test all templates
        result = reporting_service_instance.get_report_templates()
        assert result["success"] is True
        assert result["data"]["total_count"] == 5  # monthly, quarterly, annual, executive, custom
        
        # Test specific template
        monthly_result = reporting_service_instance.get_report_templates("monthly")
        assert monthly_result["success"] is True
        assert monthly_result["data"]["total_count"] == 1
        assert "monthly" in monthly_result["data"]["templates"]

    @pytest.mark.asyncio
    async def test_export_report_data_transactions(self, reporting_service_instance, mock_organization_id, mock_user_id):
        """Test transaction data export"""
        with patch.object(reporting_service_instance, '_export_transactions_data', return_value=[
            {"id": "1", "date": "2024-01-01", "amount": 100.00, "description": "Test"}
        ]):
            result = await reporting_service_instance.export_report_data(
                organization_id=mock_organization_id,
                export_type="transactions",
                format="csv"
            )
            
            assert result["success"] is True
            assert result["data"]["export_type"] == "transactions"
            assert result["data"]["format"] == "csv"

    @pytest.mark.asyncio
    async def test_export_report_data_analytics(self, reporting_service_instance, mock_organization_id, mock_user_id):
        """Test analytics data export"""
        with patch.object(analytics_service, 'get_financial_overview', return_value={"data": {"summary": {}}}), \
             patch.object(analytics_service, 'get_spending_analysis', return_value={"data": {}}), \
             patch.object(analytics_service, 'get_income_analysis', return_value={"data": {}}):
            
            result = await reporting_service_instance.export_report_data(
                organization_id=mock_organization_id,
                export_type="analytics",
                format="json"
            )
            
            assert result["success"] is True
            assert result["data"]["export_type"] == "analytics"
            assert result["data"]["format"] == "json"

    def test_format_csv_export(self, reporting_service_instance):
        """Test CSV export formatting"""
        # Test list data (transactions)
        list_data = [
            {"id": "1", "name": "Test1", "amount": 100},
            {"id": "2", "name": "Test2", "amount": 200}
        ]
        
        csv_result = reporting_service_instance._format_csv_export(list_data, "transactions")
        assert "id,name,amount" in csv_result
        assert "1,Test1,100" in csv_result
        
        # Test dict data (analytics)
        dict_data = {"metric1": "value1", "metric2": "value2"}
        csv_result = reporting_service_instance._format_csv_export(dict_data, "analytics")
        assert "metric1,value1" in csv_result
        assert "metric2,value2" in csv_result


class TestDashboardService:
    """Test DashboardService functionality"""

    @pytest.fixture
    def dashboard_service_instance(self):
        """Create a fresh dashboard service instance for testing"""
        return DashboardService()

    @pytest.fixture
    def mock_organization_id(self):
        """Mock organization ID"""
        return uuid4()

    @pytest.fixture
    def mock_user_id(self):
        """Mock user ID"""
        return uuid4()

    def test_dashboard_service_initialization(self, dashboard_service_instance):
        """Test dashboard service initialization"""
        assert dashboard_service_instance.widget_cache == {}
        assert dashboard_service_instance.cache_ttl == 300
        assert len(dashboard_service_instance.dashboard_templates) == 4  # executive, analyst, manager, custom

    def test_dashboard_templates_structure(self, dashboard_service_instance):
        """Test dashboard templates structure"""
        executive_template = dashboard_service_instance.dashboard_templates["executive"]
        assert executive_template["name"] == "Executive Dashboard"
        assert "kpi_summary" in executive_template["widgets"]
        assert executive_template["layout"] == "grid_2x2"
        assert executive_template["refresh_interval"] == 300

    @pytest.mark.asyncio
    async def test_generate_dashboard_executive(self, dashboard_service_instance, mock_organization_id, mock_user_id):
        """Test executive dashboard generation"""
        with patch.object(analytics_service, 'get_financial_overview', return_value={"data": {"summary": {"total_income": 10000}}}), \
             patch.object(analytics_service, 'get_spending_analysis', return_value={"data": {"category_breakdown": []}}), \
             patch.object(analytics_service, 'get_income_analysis', return_value={"data": {"source_breakdown": []}}), \
             patch.object(analytics_service, 'get_budget_analysis', return_value={"data": {"budget_performance": []}}), \
             patch.object(analytics_service, 'get_anomaly_detection', return_value={"data": {"detected_anomalies": []}}):
            
            result = await dashboard_service_instance.generate_dashboard(
                organization_id=mock_organization_id,
                dashboard_type="executive",
                user_id=mock_user_id
            )
            
            assert result["success"] is True
            assert "executive" in result["message"].lower()
            assert result["data"]["metadata"]["dashboard_type"] == "executive"
            assert result["data"]["metadata"]["widget_count"] > 0

    @pytest.mark.asyncio
    async def test_generate_dashboard_analyst(self, dashboard_service_instance, mock_organization_id, mock_user_id):
        """Test analyst dashboard generation"""
        with patch.object(analytics_service, 'get_financial_overview', return_value={"data": {"summary": {"total_income": 10000}}}), \
             patch.object(analytics_service, 'get_spending_analysis', return_value={"data": {"category_breakdown": []}}), \
             patch.object(analytics_service, 'get_income_analysis', return_value={"data": {"source_breakdown": []}}), \
             patch.object(analytics_service, 'get_budget_analysis', return_value={"data": {"budget_performance": []}}), \
             patch.object(analytics_service, 'get_anomaly_detection', return_value={"data": {"detected_anomalies": []}}):
            
            result = await dashboard_service_instance.generate_dashboard(
                organization_id=mock_organization_id,
                dashboard_type="analyst",
                user_id=mock_user_id
            )
            
            assert result["success"] is True
            assert "analyst" in result["message"].lower()
            assert result["data"]["metadata"]["dashboard_type"] == "analyst"

    @pytest.mark.asyncio
    async def test_generate_dashboard_manager(self, dashboard_service_instance, mock_organization_id, mock_user_id):
        """Test manager dashboard generation"""
        with patch.object(analytics_service, 'get_financial_overview', return_value={"data": {"summary": {"total_income": 10000}}}), \
             patch.object(analytics_service, 'get_spending_analysis', return_value={"data": {"category_breakdown": []}}), \
             patch.object(analytics_service, 'get_income_analysis', return_value={"data": {"source_breakdown": []}}), \
             patch.object(analytics_service, 'get_budget_analysis', return_value={"data": {"budget_performance": []}}), \
             patch.object(analytics_service, 'get_anomaly_detection', return_value={"data": {"detected_anomalies": []}}):
            
            result = await dashboard_service_instance.generate_dashboard(
                organization_id=mock_organization_id,
                dashboard_type="manager",
                user_id=mock_user_id
            )
            
            assert result["success"] is True
            assert "manager" in result["message"].lower()
            assert result["data"]["metadata"]["dashboard_type"] == "manager"

    @pytest.mark.asyncio
    async def test_generate_dashboard_custom_widgets(self, dashboard_service_instance, mock_organization_id, mock_user_id):
        """Test dashboard generation with custom widgets"""
        custom_widgets = ["kpi_summary", "financial_overview"]
        
        with patch.object(analytics_service, 'get_financial_overview', return_value={"data": {"summary": {"total_income": 10000}}}), \
             patch.object(analytics_service, 'get_spending_analysis', return_value={"data": {"category_breakdown": []}}), \
             patch.object(analytics_service, 'get_income_analysis', return_value={"data": {"source_breakdown": []}}), \
             patch.object(analytics_service, 'get_budget_analysis', return_value={"data": {"budget_performance": []}}), \
             patch.object(analytics_service, 'get_anomaly_detection', return_value={"data": {"detected_anomalies": []}}):
            
            result = await dashboard_service_instance.generate_dashboard(
                organization_id=mock_organization_id,
                dashboard_type="executive",
                user_id=mock_user_id,
                custom_widgets=custom_widgets
            )
            
            assert result["success"] is True
            assert result["data"]["metadata"]["widget_count"] == 2
            assert "kpi_summary" in result["data"]
            assert "financial_overview" in result["data"]

    @pytest.mark.asyncio
    async def test_get_widget_data(self, dashboard_service_instance, mock_organization_id, mock_user_id):
        """Test individual widget data retrieval"""
        with patch.object(analytics_service, 'get_financial_overview', return_value={"data": {"summary": {"total_income": 10000}}}):
            result = await dashboard_service_instance.get_widget_data(
                widget_name="kpi_summary",
                organization_id=mock_organization_id,
                user_id=mock_user_id
            )
            
            assert result["success"] is True
            assert "kpi_summary" in result["message"].lower()
            assert result["data"]["widget_type"] == "kpi_summary"

    def test_get_available_widgets(self, dashboard_service_instance):
        """Test available widgets retrieval"""
        # Test all widgets
        result = dashboard_service_instance.get_available_widgets()
        assert result["success"] is True
        assert result["data"]["total_count"] > 0
        
        # Test executive dashboard widgets
        executive_widgets = dashboard_service_instance.get_available_widgets("executive")
        assert executive_widgets["success"] is True
        assert executive_widgets["data"]["total_count"] > 0
        
        # Verify specific widgets exist
        all_widgets = result["data"]["widgets"]
        assert "kpi_summary" in all_widgets
        assert "financial_overview" in all_widgets
        assert "trend_chart" in all_widgets

    @pytest.mark.asyncio
    async def test_create_custom_dashboard(self, dashboard_service_instance, mock_organization_id, mock_user_id):
        """Test custom dashboard creation"""
        dashboard_config = {
            "name": "My Custom Dashboard",
            "description": "Personalized dashboard for my needs",
            "widgets": ["kpi_summary", "financial_overview"],
            "layout": "grid_2x2"
        }
        
        result = await dashboard_service_instance.create_custom_dashboard(
            organization_id=mock_organization_id,
            user_id=mock_user_id,
            dashboard_config=dashboard_config
        )
        
        assert result["success"] is True
        assert "created successfully" in result["message"]
        assert result["data"]["dashboard"]["name"] == "My Custom Dashboard"
        assert result["data"]["dashboard"]["widgets"] == ["kpi_summary", "financial_overview"]

    def test_get_dashboard_templates(self, dashboard_service_instance):
        """Test dashboard template retrieval"""
        # Test all templates
        result = dashboard_service_instance.get_dashboard_templates()
        assert result["success"] is True
        assert result["data"]["total_count"] == 4
        
        # Test specific template
        executive_result = dashboard_service_instance.get_dashboard_templates("executive")
        assert executive_result["success"] is True
        assert executive_result["data"]["total_count"] == 1
        assert "executive" in executive_result["data"]["templates"]

    @pytest.mark.asyncio
    async def test_widget_caching(self, dashboard_service_instance, mock_organization_id, mock_user_id):
        """Test widget data caching functionality"""
        with patch.object(analytics_service, 'get_financial_overview', return_value={"data": {"summary": {"total_income": 10000}}}):
            # First call - should cache data
            result1 = await dashboard_service_instance.get_widget_data(
                widget_name="kpi_summary",
                organization_id=mock_organization_id,
                user_id=mock_user_id
            )
            
            # Second call - should use cached data
            result2 = await dashboard_service_instance.get_widget_data(
                widget_name="kpi_summary",
                organization_id=mock_organization_id,
                user_id=mock_user_id
            )
            
            assert result1["success"] is True
            assert result2["success"] is True
            
            # Verify cache key exists
            cache_key = f"kpi_summary_{mock_organization_id}_{mock_user_id}"
            assert cache_key in dashboard_service_instance.widget_cache

    @pytest.mark.asyncio
    async def test_widget_cache_refresh(self, dashboard_service_instance, mock_organization_id, mock_user_id):
        """Test widget cache refresh functionality"""
        with patch.object(analytics_service, 'get_financial_overview', return_value={"data": {"summary": {"total_income": 10000}}}):
            # First call - cache data
            await dashboard_service_instance.get_widget_data(
                widget_name="kpi_summary",
                organization_id=mock_organization_id,
                user_id=mock_user_id
            )
            
            # Refresh cache
            result = await dashboard_service_instance.get_widget_data(
                widget_name="kpi_summary",
                organization_id=mock_organization_id,
                user_id=mock_user_id,
                refresh_cache=True
            )
            
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_kpi_summary_widget_generation(self, dashboard_service_instance, mock_organization_id, mock_user_id):
        """Test KPI summary widget generation"""
        with patch.object(analytics_service, 'get_financial_overview', return_value={
            "data": {
                "summary": {
                    "total_income": 10000.00,
                    "total_expenses": 7000.00,
                    "net_income": 3000.00,
                    "savings_rate": 30.0,
                    "income_change": 500.00,
                    "expense_change": -200.00,
                    "net_income_change": 700.00,
                    "savings_rate_change": 2.0
                }
            }
        }):
            widget_data = await dashboard_service_instance._generate_kpi_summary(
                organization_id=mock_organization_id,
                user_id=mock_user_id,
                parameters={"date_range": "30d"}
            )
            
            assert widget_data["widget_type"] == "kpi_summary"
            assert widget_data["title"] == "Key Performance Indicators"
            assert "total_income" in widget_data["kpis"]
            assert "total_expenses" in widget_data["kpis"]
            assert "net_income" in widget_data["kpis"]
            assert "savings_rate" in widget_data["kpis"]

    @pytest.mark.asyncio
    async def test_financial_overview_widget_generation(self, dashboard_service_instance, mock_organization_id, mock_user_id):
        """Test financial overview widget generation"""
        with patch.object(analytics_service, 'get_financial_overview', return_value={
            "data": {
                "summary": {"total_income": 10000.00},
                "patterns": {"seasonal": True},
                "health": {"score": 85}
            }
        }):
            widget_data = await dashboard_service_instance._generate_financial_overview(
                organization_id=mock_organization_id,
                user_id=mock_user_id,
                parameters={"date_range": "30d"}
            )
            
            assert widget_data["widget_type"] == "financial_overview"
            assert widget_data["title"] == "Financial Overview"
            assert "summary" in widget_data
            assert "patterns" in widget_data
            assert "health" in widget_data

    @pytest.mark.asyncio
    async def test_trend_chart_widget_generation(self, dashboard_service_instance, mock_organization_id, mock_user_id):
        """Test trend chart widget generation"""
        with patch.object(analytics_service, 'get_financial_trends', return_value={
            "data": {"trends": [{"month": "2024-01", "value": 1000}]}
        }):
            widget_data = await dashboard_service_instance._generate_trend_chart(
                organization_id=mock_organization_id,
                user_id=mock_user_id,
                parameters={"metric": "net_income", "period": "monthly", "date_range": "12m"}
            )
            
            assert widget_data["widget_type"] == "trend_chart"
            assert "net_income" in widget_data["title"]
            assert widget_data["metric"] == "net_income"
            assert widget_data["period"] == "monthly"

    @pytest.mark.asyncio
    async def test_alerts_summary_widget_generation(self, dashboard_service_instance, mock_organization_id, mock_user_id):
        """Test alerts summary widget generation"""
        with patch.object(analytics_service, 'get_anomaly_detection', return_value={
            "data": {
                "detected_anomalies": [
                    {"severity": "high", "description": "Unusual spending"},
                    {"severity": "medium", "description": "Income fluctuation"}
                ]
            }
        }):
            widget_data = await dashboard_service_instance._generate_alerts_summary(
                organization_id=mock_organization_id,
                user_id=mock_user_id
            )
            
            assert widget_data["widget_type"] == "alerts_summary"
            assert widget_data["title"] == "Alerts & Anomalies"
            assert widget_data["alert_counts"]["total"] == 2
            assert widget_data["alert_counts"]["high"] == 1
            assert widget_data["alert_counts"]["medium"] == 1

    @pytest.mark.asyncio
    async def test_ml_insights_widget_generation(self, dashboard_service_instance, mock_organization_id, mock_user_id):
        """Test ML insights widget generation"""
        with patch.object(ml_service, 'predict_spending', return_value={
            "success": True,
            "data": {"predictions": [1000, 1100, 1200]}
        }):
            widget_data = await dashboard_service_instance._generate_ml_insights(
                organization_id=mock_organization_id,
                user_id=mock_user_id,
                parameters={"prediction_type": "spending", "horizon": 3}
            )
            
            assert widget_data["widget_type"] == "ml_insights"
            assert "Machine Learning Insights" in widget_data["title"]
            assert widget_data["prediction_type"] == "spending"
            assert widget_data["horizon"] == 3
            assert "spending_prediction" in widget_data["data"]


class TestDashboardWidgets:
    """Test individual dashboard widgets"""

    @pytest.fixture
    def dashboard_service_instance(self):
        """Create a fresh dashboard service instance for testing"""
        return DashboardService()

    @pytest.fixture
    def mock_organization_id(self):
        """Mock organization ID"""
        return uuid4()

    @pytest.fixture
    def mock_user_id(self):
        """Mock user ID"""
        return uuid4()

    @pytest.mark.asyncio
    async def test_spending_breakdown_widget(self, dashboard_service_instance, mock_organization_id, mock_user_id):
        """Test spending breakdown widget"""
        with patch.object(analytics_service, 'get_spending_analysis', return_value={
            "data": {
                "category_breakdown": [
                    {"category_name": "Food", "total_amount": 2000.00, "transaction_count": 25},
                    {"category_name": "Transport", "total_amount": 1500.00, "transaction_count": 15}
                ],
                "total_spending": 3500.00
            }
        }):
            widget_data = await dashboard_service_instance._generate_spending_breakdown(
                organization_id=mock_organization_id,
                user_id=mock_user_id,
                parameters={"date_range": "30d", "grouping": "category", "limit": 5}
            )
            
            assert widget_data["widget_type"] == "spending_breakdown"
            assert widget_data["title"] == "Spending Breakdown"
            assert len(widget_data["data"]) == 2
            assert widget_data["total_spending"] == 3500.00

    @pytest.mark.asyncio
    async def test_income_analysis_widget(self, dashboard_service_instance, mock_organization_id, mock_user_id):
        """Test income analysis widget"""
        with patch.object(analytics_service, 'get_income_analysis', return_value={
            "data": {
                "source_breakdown": [
                    {"source": "Salary", "amount": 8000.00, "percentage": 80.0},
                    {"source": "Freelance", "amount": 2000.00, "percentage": 20.0}
                ],
                "total_income": 10000.00
            }
        }):
            widget_data = await dashboard_service_instance._generate_income_analysis(
                organization_id=mock_organization_id,
                user_id=mock_user_id,
                parameters={"date_range": "30d", "grouping": "source"}
            )
            
            assert widget_data["widget_type"] == "income_analysis"
            assert widget_data["title"] == "Income Analysis"
            assert len(widget_data["data"]["source_breakdown"]) == 2
            assert widget_data["total_income"] == 10000.00

    @pytest.mark.asyncio
    async def test_budget_performance_widget(self, dashboard_service_instance, mock_organization_id, mock_user_id):
        """Test budget performance widget"""
        with patch.object(analytics_service, 'get_budget_analysis', return_value={
            "data": {
                "budget_performance": [
                    {"budget_name": "Food", "planned": 2500.00, "actual": 2000.00, "variance": -500.00},
                    {"budget_name": "Transport", "planned": 1500.00, "actual": 1500.00, "variance": 0.00}
                ]
            }
        }):
            widget_data = await dashboard_service_instance._generate_budget_performance(
                organization_id=mock_organization_id,
                user_id=mock_user_id,
                parameters={"date_range": "30d", "budget_ids": []}
            )
            
            assert widget_data["widget_type"] == "budget_performance"
            assert widget_data["title"] == "Budget Performance"
            assert len(widget_data["data"]["budget_performance"]) == 2

    @pytest.mark.asyncio
    async def test_performance_metrics_widget(self, dashboard_service_instance, mock_organization_id, mock_user_id):
        """Test performance metrics widget"""
        with patch.object(analytics_service, 'get_financial_overview', return_value={
            "data": {
                "summary": {
                    "savings_rate": 30.0,
                    "expense_ratio": 0.7,
                    "cash_flow": 3000.00,
                    "total_income": 10000.00,
                    "income_change": 500.00,
                    "expense_change": -200.00,
                    "net_income_change": 700.00
                }
            }
        }):
            widget_data = await dashboard_service_instance._generate_performance_metrics(
                organization_id=mock_organization_id,
                user_id=mock_user_id,
                parameters={"date_range": "30d", "metrics": ["efficiency", "growth", "stability"]}
            )
            
            assert widget_data["widget_type"] == "performance_metrics"
            assert widget_data["title"] == "Performance Metrics"
            assert "efficiency" in widget_data["data"]
            assert "growth" in widget_data["data"]
            assert "stability" in widget_data["data"]

    @pytest.mark.asyncio
    async def test_budget_tracking_widget(self, dashboard_service_instance, mock_organization_id, mock_user_id):
        """Test budget tracking widget"""
        with patch.object(analytics_service, 'get_budget_analysis', return_value={
            "data": {
                "budget_performance": [
                    {"budget_id": "1", "budget_name": "Food", "utilization": 0.95},
                    {"budget_id": "2", "budget_name": "Transport", "utilization": 0.75}
                ]
            }
        }):
            widget_data = await dashboard_service_instance._generate_budget_tracking(
                organization_id=mock_organization_id,
                user_id=mock_user_id,
                parameters={"budget_ids": ["1", "2"], "thresholds": {"warning": 0.8, "critical": 0.95}}
            )
            
            assert widget_data["widget_type"] == "budget_tracking"
            assert widget_data["title"] == "Budget Tracking"
            assert len(widget_data["data"]) == 2
            
            # Check alert levels
            food_budget = next(b for b in widget_data["data"] if b["budget_name"] == "Food")
            transport_budget = next(b for b in widget_data["data"] if b["budget_name"] == "Transport")
            
            assert food_budget["alert_level"] == "critical"  # 0.95 >= 0.95
            assert transport_budget["alert_level"] == "normal"  # 0.75 < 0.8

    @pytest.mark.asyncio
    async def test_team_summary_widget(self, dashboard_service_instance, mock_organization_id, mock_user_id):
        """Test team summary widget"""
        widget_data = await dashboard_service_instance._generate_team_summary(
            organization_id=mock_organization_id,
            user_id=mock_user_id,
            parameters={"team_ids": ["team1"], "date_range": "30d"}
        )
        
        assert widget_data["widget_type"] == "team_summary"
        assert widget_data["title"] == "Team Summary"
        assert widget_data["data"]["total_members"] == 12
        assert widget_data["data"]["active_members"] == 10
        assert len(widget_data["data"]["top_spenders"]) == 3

    @pytest.mark.asyncio
    async def test_forecast_summary_widget(self, dashboard_service_instance, mock_organization_id, mock_user_id):
        """Test forecast summary widget"""
        with patch.object(ml_service, 'predict_cash_flow', return_value={
            "success": True,
            "data": {"predictions": [500, 600, 700]}
        }), patch.object(ml_service, 'generate_forecast_scenarios', return_value={
            "success": True,
            "data": {"scenarios": ["optimistic", "realistic", "pessimistic"]}
        }):
            widget_data = await dashboard_service_instance._generate_forecast_summary(
                organization_id=mock_organization_id,
                user_id=mock_user_id,
                parameters={"forecast_type": "cash_flow", "horizon": 6}
            )
            
            assert widget_data["widget_type"] == "forecast_summary"
            assert "Forecast Summary" in widget_data["title"]
            assert widget_data["forecast_type"] == "cash_flow"
            assert widget_data["horizon"] == 6
            assert "cash_flow" in widget_data["data"]
            assert "scenarios" in widget_data["data"]


if __name__ == "__main__":
    pytest.main([__file__])