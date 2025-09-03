"""
Unit tests for Sprint 4: Analytics Engine Implementation
Tests for analytics service, ML service, and related functionality
"""

import pytest
from datetime import datetime, date, timedelta
from uuid import UUID, uuid4
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np
import pandas as pd

from src.backend.services.analytics_service import AnalyticsService, analytics_service
from src.backend.services.ml_service import MLService, ml_service


class TestAnalyticsService:
    """Test AnalyticsService functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.analytics_service = AnalyticsService()
        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.start_date = date.today() - timedelta(days=30)
        self.end_date = date.today()

    @pytest.mark.asyncio
    async def test_get_financial_overview_success(self):
        """Test successful financial overview generation"""
        with patch('src.backend.services.analytics_service.get_session') as mock_session:
            # Mock session context manager
            mock_session.return_value.__aenter__ = AsyncMock()
            mock_session.return_value.__aexit__ = AsyncMock()
            
            # Mock session methods
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.exec = AsyncMock()
            
            # Mock transaction summary data
            mock_summary = {
                "total_income": 5000.0,
                "total_expenses": 3000.0,
                "net_income": 2000.0,
                "transaction_count": 50,
                "savings_rate": 40.0
            }
            
            # Mock the private method calls
            with patch.object(self.analytics_service, '_get_transaction_summary', return_value=mock_summary), \
                 patch.object(self.analytics_service, '_get_spending_patterns', return_value={}), \
                 patch.object(self.analytics_service, '_get_income_analysis', return_value={}), \
                 patch.object(self.analytics_service, '_get_cash_flow_analysis', return_value={}), \
                 patch.object(self.analytics_service, '_get_budget_performance', return_value={}), \
                 patch.object(self.analytics_service, '_get_financial_health_indicators', return_value={}):
                
                result = await self.analytics_service.get_financial_overview(
                    organization_id=self.organization_id,
                    start_date=self.start_date,
                    end_date=self.end_date,
                    user_id=self.user_id
                )
                
                assert result["success"] is True
                assert "summary" in result["data"]
                assert result["data"]["summary"]["total_income"] == 5000.0
                assert result["data"]["summary"]["savings_rate"] == 40.0

    @pytest.mark.asyncio
    async def test_get_spending_analysis_success(self):
        """Test successful spending analysis generation"""
        with patch('src.backend.services.analytics_service.get_session') as mock_session:
            # Mock session context manager
            mock_session.return_value.__aenter__ = AsyncMock()
            mock_session.return_value.__aexit__ = AsyncMock()
            
            # Mock session methods
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.exec = AsyncMock()
            
            # Mock category spending data
            mock_category_result = [
                MagicMock(
                    name="Food",
                    color="#FF0000",
                    total_spent=Decimal("-1000.00"),
                    transaction_count=20,
                    average_amount=Decimal("-50.00")
                ),
                MagicMock(
                    name="Transportation",
                    color="#00FF00",
                    total_spent=Decimal("-500.00"),
                    transaction_count=10,
                    average_amount=Decimal("-50.00")
                )
            ]
            
            # Mock day spending data
            mock_day_result = [
                MagicMock(
                    day_of_week=0,
                    total_spent=Decimal("-200.00"),
                    transaction_count=5
                )
            ]
            
            # Mock month spending data
            mock_month_result = [
                MagicMock(
                    month=1,
                    year=2024,
                    total_spent=Decimal("-1500.00"),
                    transaction_count=30
                )
            ]
            
            # Mock merchant data
            mock_merchant_result = [
                MagicMock(
                    merchant_name="Walmart",
                    total_spent=Decimal("-300.00"),
                    transaction_count=8
                )
            ]
            
            # Configure mock returns
            mock_session_instance.exec.side_effect = [
                mock_category_result,
                mock_day_result,
                mock_month_result,
                mock_merchant_result
            ]
            
            result = await self.analytics_service.get_spending_analysis(
                organization_id=self.organization_id,
                start_date=self.start_date,
                end_date=self.end_date,
                user_id=self.user_id
            )
            
            assert result["success"] is True
            assert "category_breakdown" in result["data"]
            assert len(result["data"]["category_breakdown"]) == 2
            assert result["data"]["total_spent"] == 1500.0

    @pytest.mark.asyncio
    async def test_get_income_analysis_success(self):
        """Test successful income analysis generation"""
        with patch('src.backend.services.analytics_service.get_session') as mock_session:
            # Mock session context manager
            mock_session.return_value.__aenter__ = AsyncMock()
            mock_session.return_value.__aexit__ = AsyncMock()
            
            # Mock session methods
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.exec = AsyncMock()
            
            # Mock category income data
            mock_category_result = [
                MagicMock(
                    name="Salary",
                    color="#0000FF",
                    total_income=Decimal("4000.00"),
                    transaction_count=4,
                    average_amount=Decimal("1000.00")
                )
            ]
            
            # Mock month income data
            mock_month_result = [
                MagicMock(
                    month=1,
                    year=2024,
                    total_income=Decimal("4000.00"),
                    transaction_count=4
                )
            ]
            
            # Mock source data
            mock_source_result = [
                MagicMock(
                    merchant_name="Company Inc",
                    total_income=Decimal("4000.00"),
                    transaction_count=4
                )
            ]
            
            # Configure mock returns
            mock_session_instance.exec.side_effect = [
                mock_category_result,
                mock_month_result,
                mock_source_result
            ]
            
            result = await self.analytics_service.get_income_analysis(
                organization_id=self.organization_id,
                start_date=self.start_date,
                end_date=self.end_date,
                user_id=self.user_id
            )
            
            assert result["success"] is True
            assert "category_breakdown" in result["data"]
            assert result["data"]["total_income"] == 4000.0

    @pytest.mark.asyncio
    async def test_get_cash_flow_forecast_success(self):
        """Test successful cash flow forecast generation"""
        with patch('src.backend.services.analytics_service.get_session') as mock_session:
            # Mock session context manager
            mock_session.return_value.__aenter__ = AsyncMock()
            mock_session.return_value.__aexit__ = AsyncMock()
            
            # Mock session methods
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.exec = AsyncMock()
            
            # Mock monthly data
            mock_monthly_result = [
                MagicMock(
                    month=1,
                    year=2024,
                    income=Decimal("4000.00"),
                    expenses=Decimal("3000.00")
                ),
                MagicMock(
                    month=2,
                    year=2024,
                    income=Decimal("4000.00"),
                    expenses=Decimal("3000.00")
                )
            ]
            
            mock_session_instance.exec.return_value = mock_monthly_result
            
            result = await self.analytics_service.get_cash_flow_forecast(
                organization_id=self.organization_id,
                months_ahead=3,
                user_id=self.user_id
            )
            
            assert result["success"] is True
            assert "forecast" in result["data"]
            assert len(result["data"]["forecast"]) == 3

    @pytest.mark.asyncio
    async def test_get_anomaly_detection_success(self):
        """Test successful anomaly detection"""
        with patch('src.backend.services.analytics_service.get_session') as mock_session:
            # Mock session context manager
            mock_session.return_value.__aenter__ = AsyncMock()
            mock_session.return_value.__aexit__ = AsyncMock()
            
            # Mock session methods
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.exec = AsyncMock()
            
            # Mock transaction data
            mock_transactions = [
                MagicMock(
                    id=uuid4(),
                    amount=Decimal("-100.00"),
                    date=date.today(),
                    category_id=uuid4(),
                    merchant_name="Test Merchant",
                    description="Test Transaction"
                )
            ]
            
            mock_session_instance.exec.return_value = mock_transactions
            
            result = await self.analytics_service.get_anomaly_detection(
                organization_id=self.organization_id,
                start_date=self.start_date,
                end_date=self.end_date,
                user_id=self.user_id
            )
            
            assert result["success"] is True
            assert "anomalies" in result["data"]

    @pytest.mark.asyncio
    async def test_get_budget_analysis_success(self):
        """Test successful budget analysis generation"""
        with patch('src.backend.services.analytics_service.get_session') as mock_session:
            # Mock session context manager
            mock_session.return_value.__aenter__ = AsyncMock()
            mock_session.return_value.__aexit__ = AsyncMock()
            
            # Mock session methods
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.exec = AsyncMock()
            
            # Mock budget data
            mock_budgets = [
                MagicMock(
                    id=uuid4(),
                    name="Food Budget",
                    amount=Decimal("500.00"),
                    start_date=date.today() - timedelta(days=30),
                    end_date=date.today(),
                    category=MagicMock(
                        id=uuid4(),
                        name="Food",
                        color="#FF0000"
                    )
                )
            ]
            
            # Mock spending data
            mock_spending_result = [Decimal("300.00")]
            
            # Configure mock returns
            mock_session_instance.exec.side_effect = [
                mock_budgets,
                mock_spending_result
            ]
            
            result = await self.analytics_service.get_budget_analysis(
                organization_id=self.organization_id,
                start_date=self.start_date,
                end_date=self.end_date,
                user_id=self.user_id
            )
            
            assert result["success"] is True
            assert "budgets" in result["data"]
            assert len(result["data"]["budgets"]) == 1

    def test_calculate_trend(self):
        """Test trend calculation helper method"""
        values = [100, 110, 120, 130, 140]
        trend = self.analytics_service._calculate_trend(values)
        
        # Should be positive trend
        assert trend > 0
        
        # Test with decreasing values
        decreasing_values = [140, 130, 120, 110, 100]
        decreasing_trend = self.analytics_service._calculate_trend(decreasing_values)
        assert decreasing_trend < 0

    def test_get_month_name(self):
        """Test month name helper method"""
        assert self.analytics_service._get_month_name(1) == "January"
        assert self.analytics_service._get_month_name(12) == "December"
        assert self.analytics_service._get_month_name(13) == "Unknown"


class TestMLService:
    """Test MLService functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.ml_service = MLService()
        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.start_date = date.today() - timedelta(days=90)
        self.end_date = date.today()

    @pytest.mark.asyncio
    async def test_predict_spending_success(self):
        """Test successful spending prediction"""
        with patch('src.backend.services.ml_service.get_session') as mock_session:
            # Mock session context manager
            mock_session.return_value.__aenter__ = AsyncMock()
            mock_session.return_value.__aexit__ = AsyncMock()
            
            # Mock session methods
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.exec = AsyncMock()
            
            # Mock monthly spending data
            mock_monthly_result = [
                MagicMock(
                    month=1,
                    year=2024,
                    total_spending=Decimal("1000.00")
                ),
                MagicMock(
                    month=2,
                    year=2024,
                    total_spending=Decimal("1100.00")
                ),
                MagicMock(
                    month=3,
                    year=2024,
                    total_spending=Decimal("1200.00")
                ),
                MagicMock(
                    month=4,
                    year=2024,
                    total_spending=Decimal("1300.00")
                ),
                MagicMock(
                    month=5,
                    year=2024,
                    total_spending=Decimal("1400.00")
                ),
                MagicMock(
                    month=6,
                    year=2024,
                    total_spending=Decimal("1500.00")
                )
            ]
            
            mock_session_instance.exec.return_value = mock_monthly_result
            
            result = await self.ml_service.predict_spending(
                organization_id=self.organization_id,
                months_ahead=3,
                user_id=self.user_id
            )
            
            assert result["success"] is True
            assert "predictions" in result["data"]
            assert len(result["data"]["predictions"]) == 3

    @pytest.mark.asyncio
    async def test_predict_spending_insufficient_data(self):
        """Test spending prediction with insufficient data"""
        with patch('src.backend.services.ml_service.get_session') as mock_session:
            # Mock session context manager
            mock_session.return_value.__aenter__ = AsyncMock()
            mock_session.return_value.__aexit__ = AsyncMock()
            
            # Mock session methods
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.exec = AsyncMock()
            
            # Mock insufficient data
            mock_monthly_result = [
                MagicMock(
                    month=1,
                    year=2024,
                    total_spending=Decimal("1000.00")
                )
            ]
            
            mock_session_instance.exec.return_value = mock_monthly_result
            
            result = await self.ml_service.predict_spending(
                organization_id=self.organization_id,
                months_ahead=3,
                user_id=self.user_id
            )
            
            assert result["success"] is False
            assert "Insufficient historical data" in result["message"]

    @pytest.mark.asyncio
    async def test_detect_advanced_anomalies_success(self):
        """Test successful advanced anomaly detection"""
        with patch('src.backend.services.ml_service.get_session') as mock_session:
            # Mock session context manager
            mock_session.return_value.__aenter__ = AsyncMock()
            mock_session.return_value.__aexit__ = AsyncMock()
            
            # Mock session methods
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.exec = AsyncMock()
            
            # Mock transaction data
            mock_transactions = [
                MagicMock(
                    id=uuid4(),
                    amount=Decimal("-100.00"),
                    date=date.today(),
                    category_id=uuid4(),
                    merchant_name="Test Merchant",
                    description="Test Transaction"
                )
            ]
            
            mock_session_instance.exec.return_value = mock_transactions
            
            result = await self.ml_service.detect_advanced_anomalies(
                organization_id=self.organization_id,
                start_date=self.start_date,
                end_date=self.end_date,
                user_id=self.user_id
            )
            
            assert result["success"] is True
            assert "anomalies" in result["data"]

    @pytest.mark.asyncio
    async def test_predict_cash_flow_success(self):
        """Test successful cash flow prediction"""
        with patch('src.backend.services.ml_service.get_session') as mock_session:
            # Mock session context manager
            mock_session.return_value.__aenter__ = AsyncMock()
            mock_session.return_value.__aexit__ = AsyncMock()
            
            # Mock session methods
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.exec = AsyncMock()
            
            # Mock monthly data
            mock_monthly_result = [
                MagicMock(
                    month=1,
                    year=2024,
                    income=Decimal("4000.00"),
                    expenses=Decimal("3000.00")
                ),
                MagicMock(
                    month=2,
                    year=2024,
                    income=Decimal("4000.00"),
                    expenses=Decimal("3000.00")
                ),
                MagicMock(
                    month=3,
                    year=2024,
                    income=Decimal("4000.00"),
                    expenses=Decimal("3000.00")
                ),
                MagicMock(
                    month=4,
                    year=2024,
                    income=Decimal("4000.00"),
                    expenses=Decimal("3000.00")
                ),
                MagicMock(
                    month=5,
                    year=2024,
                    income=Decimal("4000.00"),
                    expenses=Decimal("3000.00")
                ),
                MagicMock(
                    month=6,
                    year=2024,
                    income=Decimal("4000.00"),
                    expenses=Decimal("3000.00")
                ),
                MagicMock(
                    month=7,
                    year=2024,
                    income=Decimal("4000.00"),
                    expenses=Decimal("3000.00")
                ),
                MagicMock(
                    month=8,
                    year=2024,
                    income=Decimal("4000.00"),
                    expenses=Decimal("3000.00")
                ),
                MagicMock(
                    month=9,
                    year=2024,
                    income=Decimal("4000.00"),
                    expenses=Decimal("3000.00")
                ),
                MagicMock(
                    month=10,
                    year=2024,
                    income=Decimal("4000.00"),
                    expenses=Decimal("3000.00")
                ),
                MagicMock(
                    month=11,
                    year=2024,
                    income=Decimal("4000.00"),
                    expenses=Decimal("3000.00")
                ),
                MagicMock(
                    month=12,
                    year=2024,
                    income=Decimal("4000.00"),
                    expenses=Decimal("3000.00")
                )
            ]
            
            mock_session_instance.exec.return_value = mock_monthly_result
            
            result = await self.ml_service.predict_cash_flow(
                organization_id=self.organization_id,
                months_ahead=6,
                user_id=self.user_id
            )
            
            assert result["success"] is True
            assert "forecast" in result["data"]
            assert len(result["data"]["forecast"]) == 6

    @pytest.mark.asyncio
    async def test_cluster_spending_patterns_success(self):
        """Test successful spending pattern clustering"""
        with patch('src.backend.services.ml_service.get_session') as mock_session:
            # Mock session context manager
            mock_session.return_value.__aenter__ = AsyncMock()
            mock_session.return_value.__aexit__ = AsyncMock()
            
            # Mock session methods
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.exec = AsyncMock()
            
            # Mock transaction data
            mock_transactions = [
                MagicMock(
                    id=uuid4(),
                    amount=Decimal("-100.00"),
                    date=date.today(),
                    category_id=uuid4(),
                    merchant_name="Test Merchant"
                )
            ]
            
            mock_session_instance.exec.return_value = mock_transactions
            
            result = await self.ml_service.cluster_spending_patterns(
                organization_id=self.organization_id,
                start_date=self.start_date,
                end_date=self.end_date,
                user_id=self.user_id,
                n_clusters=3
            )
            
            assert result["success"] is True
            assert "clusters" in result["data"]

    @pytest.mark.asyncio
    async def test_get_model_performance_success(self):
        """Test successful model performance retrieval"""
        # Mock that models are loaded
        self.ml_service.spending_predictor = MagicMock()
        self.ml_service.anomaly_detector = MagicMock()
        self.ml_service.cash_flow_predictor = MagicMock()
        
        result = await self.ml_service.get_model_performance("all")
        
        assert result["success"] is True
        assert "models" in result["data"]
        assert len(result["data"]["models"]) == 3

    def test_get_month_name(self):
        """Test month name helper method"""
        assert self.ml_service._get_month_name(1) == "January"
        assert self.ml_service._get_month_name(12) == "December"
        assert self.ml_service._get_month_name(13) == "Unknown"


class TestAnalyticsIntegration:
    """Test integration between analytics and ML services"""

    @pytest.mark.asyncio
    async def test_analytics_with_ml_predictions(self):
        """Test analytics service using ML predictions"""
        # This would test the integration between analytics and ML services
        # For now, just verify both services can be instantiated
        analytics = AnalyticsService()
        ml = MLService()
        
        assert analytics is not None
        assert ml is not None
        assert hasattr(analytics, 'get_financial_overview')
        assert hasattr(ml, 'predict_spending')


if __name__ == "__main__":
    pytest.main([__file__])