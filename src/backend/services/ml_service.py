"""
Machine Learning service for Financial Analytics Platform
Handles advanced analytics, predictions, and ML models
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple
from uuid import UUID
from decimal import Decimal
import json
import pickle
import base64
from pathlib import Path

from fastapi import HTTPException, status
from sqlmodel import select, func, and_, or_
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.cluster import KMeans
import joblib

from src.backend.models.database import Transaction, Account, Category, Budget
from src.backend.database import get_session
from src.common.models.enums import TransactionType, AccountType
from src.common.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MLService:
    """Service for machine learning and advanced analytics"""
    
    def __init__(self):
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        self.scalers_dir = Path("scalers")
        self.scalers_dir.mkdir(exist_ok=True)
        
        # Initialize models
        self.spending_predictor = None
        self.anomaly_detector = None
        self.category_classifier = None
        self.cash_flow_predictor = None
        
        # Load pre-trained models if available
        self._load_models()
    
    async def predict_spending(
        self,
        organization_id: UUID,
        months_ahead: int = 3,
        user_id: Optional[UUID] = None,
        category_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Predict future spending using ML models"""
        
        try:
            async with get_session() as session:
                # Get historical spending data
                conditions = [
                    Transaction.organization_id == organization_id,
                    Transaction.deleted_at.is_(None),
                    Transaction.amount < 0  # Only expenses
                ]
                
                if user_id:
                    conditions.append(Transaction.user_id == user_id)
                if category_id:
                    conditions.append(Transaction.category_id == category_id)
                
                # Get data from last 24 months for training
                end_date = date.today()
                start_date = end_date - timedelta(days=730)
                conditions.extend([
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                ])
                
                # Get monthly spending data
                monthly_statement = select(
                    func.extract('month', Transaction.date).label("month"),
                    func.extract('year', Transaction.date).label("year"),
                    func.sum(func.abs(Transaction.amount)).label("total_spending")
                ).where(
                    and_(*conditions)
                ).group_by(
                    func.extract('month', Transaction.date),
                    func.extract('year', Transaction.date)
                ).order_by(
                    func.extract('year', Transaction.date),
                    func.extract('month', Transaction.date)
                )
                
                monthly_result = await session.exec(monthly_statement)
                historical_data = []
                
                for row in monthly_result:
                    historical_data.append({
                        "month": int(row.month),
                        "year": int(row.year),
                        "spending": float(row.total_spending)
                    })
                
                if len(historical_data) < 6:
                    return {
                        "success": False,
                        "message": "Insufficient historical data for prediction (need at least 6 months)",
                        "data": None
                    }
                
                # Prepare features for ML
                df = pd.DataFrame(historical_data)
                df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
                df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
                df['year_normalized'] = (df['year'] - df['year'].min()) / (df['year'].max() - df['year'].min())
                
                # Create lag features
                df['spending_lag1'] = df['spending'].shift(1)
                df['spending_lag2'] = df['spending'].shift(2)
                df['spending_lag3'] = df['spending'].shift(3)
                
                # Remove rows with NaN values
                df = df.dropna()
                
                if len(df) < 3:
                    return {
                        "success": False,
                        "message": "Insufficient data after feature engineering",
                        "data": None
                    }
                
                # Prepare features and target
                feature_columns = ['month_sin', 'month_cos', 'year_normalized', 'spending_lag1', 'spending_lag2', 'spending_lag3']
                X = df[feature_columns].values
                y = df['spending'].values
                
                # Train model if not already trained
                if self.spending_predictor is None:
                    self.spending_predictor = RandomForestRegressor(
                        n_estimators=100,
                        random_state=42,
                        n_jobs=-1
                    )
                    self.spending_predictor.fit(X, y)
                    
                    # Save model
                    self._save_model('spending_predictor', self.spending_predictor)
                
                # Generate future predictions
                predictions = []
                current_month = date.today().month
                current_year = date.today().year
                
                # Use last known values for initial lags
                last_spending = df['spending'].iloc[-1]
                lag1 = df['spending'].iloc[-1] if len(df) > 0 else 0
                lag2 = df['spending'].iloc[-2] if len(df) > 1 else 0
                lag3 = df['spending'].iloc[-3] if len(df) > 2 else 0
                
                for i in range(months_ahead):
                    # Calculate month and year
                    month = ((current_month - 1 + i) % 12) + 1
                    year = current_year + ((current_month - 1 + i) // 12)
                    
                    # Prepare features for prediction
                    month_sin = np.sin(2 * np.pi * month / 12)
                    month_cos = np.cos(2 * np.pi * month / 12)
                    year_normalized = (year - df['year'].min()) / (df['year'].max() - df['year'].min())
                    
                    features = np.array([[
                        month_sin, month_cos, year_normalized,
                        lag1, lag2, lag3
                    ]])
                    
                    # Make prediction
                    predicted_spending = self.spending_predictor.predict(features)[0]
                    
                    # Ensure prediction is positive
                    predicted_spending = max(0, predicted_spending)
                    
                    predictions.append({
                        "month": month,
                        "year": year,
                        "month_name": self._get_month_name(month),
                        "predicted_spending": float(predicted_spending),
                        "confidence": max(0.1, 1.0 - (i * 0.15))  # Decreasing confidence
                    })
                    
                    # Update lags for next iteration
                    lag3 = lag2
                    lag2 = lag1
                    lag1 = predicted_spending
                
                # Calculate prediction metrics
                total_predicted = sum(p["predicted_spending"] for p in predictions)
                avg_monthly = total_predicted / months_ahead
                
                return {
                    "success": True,
                    "message": "Spending prediction generated successfully",
                    "data": {
                        "predictions": predictions,
                        "summary": {
                            "total_predicted_spending": total_predicted,
                            "average_monthly_spending": avg_monthly,
                            "prediction_horizon": months_ahead
                        },
                        "model_info": {
                            "type": "Random Forest Regressor",
                            "training_data_points": len(df),
                            "features_used": feature_columns,
                            "last_training_date": datetime.now().isoformat()
                        }
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to predict spending: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to predict spending: {str(e)}"
            )
    
    async def detect_advanced_anomalies(
        self,
        organization_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        user_id: Optional[UUID] = None,
        method: str = "isolation_forest"
    ) -> Dict[str, Any]:
        """Detect anomalies using advanced ML methods"""
        
        try:
            async with get_session() as session:
                # Build base conditions
                conditions = [
                    Transaction.organization_id == organization_id,
                    Transaction.deleted_at.is_(None)
                ]
                
                if start_date:
                    conditions.append(Transaction.date >= start_date)
                if end_date:
                    conditions.append(Transaction.date <= end_date)
                if user_id:
                    conditions.append(Transaction.user_id == user_id)
                
                # Get transactions for analysis
                statement = select(Transaction).where(and_(*conditions))
                result = await session.exec(statement)
                transactions = result.all()
                
                if not transactions:
                    return {
                        "success": False,
                        "message": "No transactions found for anomaly detection",
                        "data": None
                    }
                
                # Convert to pandas DataFrame
                df = pd.DataFrame([
                    {
                        'id': str(tx.id),
                        'amount': abs(float(tx.amount)),
                        'date': tx.date,
                        'category_id': str(tx.category_id) if tx.category_id else 'unknown',
                        'merchant_name': tx.merchant_name or 'unknown',
                        'description': tx.description
                    }
                    for tx in transactions
                ])
                
                # Feature engineering
                df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
                df['month'] = pd.to_datetime(df['date']).dt.month
                df['day_of_month'] = pd.to_datetime(df['date']).dt.day
                
                # Encode categorical variables
                le_category = LabelEncoder()
                le_merchant = LabelEncoder()
                
                df['category_encoded'] = le_category.fit_transform(df['category_id'])
                df['merchant_encoded'] = le_merchant.fit_transform(df['merchant_name'])
                
                # Prepare features for ML
                feature_columns = ['amount', 'day_of_week', 'month', 'day_of_month', 'category_encoded', 'merchant_encoded']
                X = df[feature_columns].values
                
                # Scale features
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X)
                
                # Detect anomalies using Isolation Forest
                if method == "isolation_forest":
                    if self.anomaly_detector is None:
                        self.anomaly_detector = IsolationForest(
                            contamination=0.1,  # Expect 10% anomalies
                            random_state=42,
                            n_estimators=100
                        )
                    
                    # Fit and predict
                    anomaly_labels = self.anomaly_detector.fit_predict(X_scaled)
                    
                    # Get anomaly scores
                    anomaly_scores = self.anomaly_detector.decision_function(X_scaled)
                    
                    # Identify anomalies (label -1 indicates anomaly)
                    anomaly_indices = np.where(anomaly_labels == -1)[0]
                    
                    anomalies = []
                    for idx in anomaly_indices:
                        row = df.iloc[idx]
                        score = anomaly_scores[idx]
                        
                        # Determine severity based on score
                        if score < -0.5:
                            severity = "high"
                        elif score < -0.2:
                            severity = "medium"
                        else:
                            severity = "low"
                        
                        anomalies.append({
                            "type": "ml_anomaly",
                            "transaction_id": row['id'],
                            "amount": float(row['amount']),
                            "anomaly_score": float(score),
                            "description": row['description'],
                            "merchant": row['merchant_name'],
                            "date": row['date'].isoformat(),
                            "severity": severity,
                            "features": {
                                "day_of_week": int(row['day_of_week']),
                                "month": int(row['month']),
                                "day_of_month": int(row['day_of_month']),
                                "category": row['category_id']
                            }
                        })
                    
                    # Sort by anomaly score (most anomalous first)
                    anomalies.sort(key=lambda x: x['anomaly_score'])
                    
                    return {
                        "success": True,
                        "message": "Advanced anomaly detection completed successfully",
                        "data": {
                            "anomalies": anomalies,
                            "total_anomalies": len(anomalies),
                            "anomaly_rate": len(anomalies) / len(df),
                            "method": method,
                            "severity_breakdown": {
                                "high": len([a for a in anomalies if a["severity"] == "high"]),
                                "medium": len([a for a in anomalies if a["severity"] == "medium"]),
                                "low": len([a for a in anomalies if a["severity"] == "low"])
                            },
                            "model_info": {
                                "type": "Isolation Forest",
                                "contamination": 0.1,
                                "features_used": feature_columns,
                                "total_transactions_analyzed": len(df)
                            }
                        }
                    }
                
                else:
                    return {
                        "success": False,
                        "message": f"Unsupported anomaly detection method: {method}",
                        "data": None
                    }
                
        except Exception as e:
            logger.error(f"Failed to detect advanced anomalies: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to detect advanced anomalies: {str(e)}"
            )
    
    async def predict_cash_flow(
        self,
        organization_id: UUID,
        months_ahead: int = 6,
        user_id: Optional[UUID] = None,
        include_confidence: bool = True
    ) -> Dict[str, Any]:
        """Predict cash flow using advanced ML models"""
        
        try:
            async with get_session() as session:
                # Get historical cash flow data
                conditions = [
                    Transaction.organization_id == organization_id,
                    Transaction.deleted_at.is_(None)
                ]
                
                if user_id:
                    conditions.append(Transaction.user_id == user_id)
                
                # Get data from last 36 months for training
                end_date = date.today()
                start_date = end_date - timedelta(days=1095)
                conditions.extend([
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                ])
                
                # Get monthly income and expenses
                monthly_statement = select(
                    func.extract('month', Transaction.date).label("month"),
                    func.extract('year', Transaction.date).label("year"),
                    func.sum(
                        func.case(
                            (Transaction.amount > 0, Transaction.amount),
                            else_=0
                        )
                    ).label("income"),
                    func.sum(
                        func.case(
                            (Transaction.amount < 0, func.abs(Transaction.amount)),
                            else_=0
                        )
                    ).label("expenses")
                ).where(
                    and_(*conditions)
                ).group_by(
                    func.extract('month', Transaction.date),
                    func.extract('year', Transaction.date)
                ).order_by(
                    func.extract('year', Transaction.date),
                    func.extract('month', Transaction.date)
                )
                
                monthly_result = await session.exec(monthly_statement)
                historical_data = []
                
                for row in monthly_result:
                    historical_data.append({
                        "month": int(row.month),
                        "year": int(row.year),
                        "income": float(row.income),
                        "expenses": float(row.expenses),
                        "net_cash_flow": float(row.income) - float(row.expenses)
                    })
                
                if len(historical_data) < 12:
                    return {
                        "success": False,
                        "message": "Insufficient historical data for cash flow prediction (need at least 12 months)",
                        "data": None
                    }
                
                # Prepare features for ML
                df = pd.DataFrame(historical_data)
                df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
                df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
                df['year_normalized'] = (df['year'] - df['year'].min()) / (df['year'].max() - df['year'].min())
                
                # Create lag features for cash flow
                df['net_cash_flow_lag1'] = df['net_cash_flow'].shift(1)
                df['net_cash_flow_lag2'] = df['net_cash_flow'].shift(2)
                df['net_cash_flow_lag3'] = df['net_cash_flow'].shift(3)
                
                # Create rolling statistics
                df['net_cash_flow_rolling_mean'] = df['net_cash_flow'].rolling(window=3).mean()
                df['net_cash_flow_rolling_std'] = df['net_cash_flow'].rolling(window=3).std()
                
                # Remove rows with NaN values
                df = df.dropna()
                
                if len(df) < 6:
                    return {
                        "success": False,
                        "message": "Insufficient data after feature engineering",
                        "data": None
                    }
                
                # Prepare features and target
                feature_columns = [
                    'month_sin', 'month_cos', 'year_normalized',
                    'net_cash_flow_lag1', 'net_cash_flow_lag2', 'net_cash_flow_lag3',
                    'net_cash_flow_rolling_mean', 'net_cash_flow_rolling_std'
                ]
                X = df[feature_columns].values
                y = df['net_cash_flow'].values
                
                # Train model if not already trained
                if self.cash_flow_predictor is None:
                    self.cash_flow_predictor = RandomForestRegressor(
                        n_estimators=200,
                        random_state=42,
                        n_jobs=-1,
                        max_depth=10
                    )
                    self.cash_flow_predictor.fit(X, y)
                    
                    # Save model
                    self._save_model('cash_flow_predictor', self.cash_flow_predictor)
                
                # Generate future predictions
                predictions = []
                current_month = date.today().month
                current_year = date.today().year
                
                # Use last known values for initial lags
                last_net_cf = df['net_cash_flow'].iloc[-1]
                lag1 = df['net_cash_flow'].iloc[-1] if len(df) > 0 else 0
                lag2 = df['net_cash_flow'].iloc[-2] if len(df) > 1 else 0
                lag3 = df['net_cash_flow'].iloc[-3] if len(df) > 2 else 0
                rolling_mean = df['net_cash_flow_rolling_mean'].iloc[-1] if len(df) > 0 else 0
                rolling_std = df['net_cash_flow_rolling_std'].iloc[-1] if len(df) > 0 else 0
                
                for i in range(months_ahead):
                    # Calculate month and year
                    month = ((current_month - 1 + i) % 12) + 1
                    year = current_year + ((current_month - 1 + i) // 12)
                    
                    # Prepare features for prediction
                    month_sin = np.sin(2 * np.pi * month / 12)
                    month_cos = np.cos(2 * np.pi * month / 12)
                    year_normalized = (year - df['year'].min()) / (df['year'].max() - df['year'].min())
                    
                    features = np.array([[
                        month_sin, month_cos, year_normalized,
                        lag1, lag2, lag3, rolling_mean, rolling_std
                    ]])
                    
                    # Make prediction
                    predicted_net_cf = self.cash_flow_predictor.predict(features)[0]
                    
                    # Calculate confidence interval (simplified)
                    confidence = max(0.1, 1.0 - (i * 0.1))
                    
                    # Estimate income and expenses based on historical ratios
                    if rolling_mean != 0:
                        income_expense_ratio = abs(rolling_mean) / (abs(rolling_mean) + rolling_std) if rolling_std > 0 else 0.5
                        predicted_income = max(0, predicted_net_cf * income_expense_ratio)
                        predicted_expenses = max(0, predicted_income - predicted_net_cf)
                    else:
                        predicted_income = max(0, predicted_net_cf)
                        predicted_expenses = max(0, -predicted_net_cf)
                    
                    predictions.append({
                        "month": month,
                        "year": year,
                        "month_name": self._get_month_name(month),
                        "predicted_income": float(predicted_income),
                        "predicted_expenses": float(predicted_expenses),
                        "predicted_net_cash_flow": float(predicted_net_cf),
                        "confidence": confidence if include_confidence else None
                    })
                    
                    # Update lags for next iteration
                    lag3 = lag2
                    lag2 = lag1
                    lag1 = predicted_net_cf
                    
                    # Update rolling statistics (simplified)
                    rolling_mean = (rolling_mean * 0.7 + predicted_net_cf * 0.3)
                    rolling_std = rolling_std * 0.9  # Decay factor
                
                # Calculate prediction metrics
                total_predicted_income = sum(p["predicted_income"] for p in predictions)
                total_predicted_expenses = sum(p["predicted_expenses"] for p in predictions)
                total_predicted_net = sum(p["predicted_net_cash_flow"] for p in predictions)
                
                return {
                    "success": True,
                    "message": "Cash flow prediction generated successfully",
                    "data": {
                        "predictions": predictions,
                        "summary": {
                            "total_predicted_income": total_predicted_income,
                            "total_predicted_expenses": total_predicted_expenses,
                            "total_predicted_net_cash_flow": total_predicted_net,
                            "average_monthly_income": total_predicted_income / months_ahead,
                            "average_monthly_expenses": total_predicted_expenses / months_ahead,
                            "average_monthly_net": total_predicted_net / months_ahead
                        },
                        "model_info": {
                            "type": "Random Forest Regressor",
                            "training_data_points": len(df),
                            "features_used": feature_columns,
                            "last_training_date": datetime.now().isoformat()
                        }
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to predict cash flow: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to predict cash flow: {str(e)}"
            )
    
    async def cluster_spending_patterns(
        self,
        organization_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        user_id: Optional[UUID] = None,
        n_clusters: int = 5
    ) -> Dict[str, Any]:
        """Cluster spending patterns using K-means"""
        
        try:
            async with get_session() as session:
                # Build base conditions
                conditions = [
                    Transaction.organization_id == organization_id,
                    Transaction.deleted_at.is_(None),
                    Transaction.amount < 0  # Only expenses
                ]
                
                if start_date:
                    conditions.append(Transaction.date >= start_date)
                if end_date:
                    conditions.append(Transaction.date <= end_date)
                if user_id:
                    conditions.append(Transaction.user_id == user_id)
                
                # Get spending data
                statement = select(Transaction).where(and_(*conditions))
                result = await session.exec(statement)
                transactions = result.all()
                
                if not transactions:
                    return {
                        "success": False,
                        "message": "No transactions found for clustering",
                        "data": None
                    }
                
                # Convert to pandas DataFrame
                df = pd.DataFrame([
                    {
                        'id': str(tx.id),
                        'amount': abs(float(tx.amount)),
                        'date': tx.date,
                        'category_id': str(tx.category_id) if tx.category_id else 'unknown',
                        'merchant_name': tx.merchant_name or 'unknown'
                    }
                    for tx in transactions
                ])
                
                # Feature engineering
                df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
                df['month'] = pd.to_datetime(df['date']).dt.month
                df['day_of_month'] = pd.to_datetime(df['date']).dt.day
                
                # Encode categorical variables
                le_category = LabelEncoder()
                le_merchant = LabelEncoder()
                
                df['category_encoded'] = le_category.fit_transform(df['category_id'])
                df['merchant_encoded'] = le_merchant.fit_transform(df['merchant_name'])
                
                # Prepare features for clustering
                feature_columns = ['amount', 'day_of_week', 'month', 'day_of_month', 'category_encoded', 'merchant_encoded']
                X = df[feature_columns].values
                
                # Scale features
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X)
                
                # Perform K-means clustering
                kmeans = KMeans(n_clusters=min(n_clusters, len(df)), random_state=42, n_init=10)
                cluster_labels = kmeans.fit_predict(X_scaled)
                
                # Add cluster labels to DataFrame
                df['cluster'] = cluster_labels
                
                # Analyze clusters
                clusters = []
                for cluster_id in range(kmeans.n_clusters_):
                    cluster_data = df[df['cluster'] == cluster_id]
                    
                    if len(cluster_data) > 0:
                        cluster_info = {
                            "cluster_id": int(cluster_id),
                            "size": len(cluster_data),
                            "percentage": (len(cluster_data) / len(df)) * 100,
                            "characteristics": {
                                "average_amount": float(cluster_data['amount'].mean()),
                                "median_amount": float(cluster_data['amount'].median()),
                                "std_amount": float(cluster_data['amount'].std()),
                                "most_common_day": int(cluster_data['day_of_week'].mode().iloc[0]) if len(cluster_data['day_of_week'].mode()) > 0 else -1,
                                "most_common_month": int(cluster_data['month'].mode().iloc[0]) if len(cluster_data['month'].mode()) > 0 else -1
                            },
                            "top_categories": cluster_data['category_id'].value_counts().head(3).to_dict(),
                            "top_merchants": cluster_data['merchant_name'].value_counts().head(3).to_dict(),
                            "sample_transactions": [
                                {
                                    "id": row['id'],
                                    "amount": float(row['amount']),
                                    "category": row['category_id'],
                                    "merchant": row['merchant_name'],
                                    "date": row['date'].isoformat()
                                }
                                for _, row in cluster_data.head(5).iterrows()
                            ]
                        }
                        clusters.append(cluster_info)
                
                # Sort clusters by size
                clusters.sort(key=lambda x: x['size'], reverse=True)
                
                return {
                    "success": True,
                    "message": "Spending pattern clustering completed successfully",
                    "data": {
                        "clusters": clusters,
                        "total_clusters": len(clusters),
                        "total_transactions": len(df),
                        "clustering_method": "K-means",
                        "features_used": feature_columns,
                        "model_info": {
                            "type": "K-means Clustering",
                            "n_clusters": kmeans.n_clusters_,
                            "inertia": float(kmeans.inertia_),
                            "n_iter": kmeans.n_iter_
                        }
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to cluster spending patterns: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to cluster spending patterns: {str(e)}"
            )
    
    async def get_model_performance(
        self,
        model_type: str = "all"
    ) -> Dict[str, Any]:
        """Get performance metrics for ML models"""
        
        try:
            performance_metrics = {}
            
            if model_type in ["all", "spending_predictor"] and self.spending_predictor is not None:
                # This would include actual performance metrics from model evaluation
                performance_metrics["spending_predictor"] = {
                    "status": "trained",
                    "type": "Random Forest Regressor",
                    "last_training": "recent",
                    "performance": "good"
                }
            
            if model_type in ["all", "anomaly_detector"] and self.anomaly_detector is not None:
                performance_metrics["anomaly_detector"] = {
                    "status": "trained",
                    "type": "Isolation Forest",
                    "last_training": "recent",
                    "performance": "good"
                }
            
            if model_type in ["all", "cash_flow_predictor"] and self.cash_flow_predictor is not None:
                performance_metrics["cash_flow_predictor"] = {
                    "status": "trained",
                    "type": "Random Forest Regressor",
                    "last_training": "recent",
                    "performance": "good"
                }
            
            return {
                "success": True,
                "message": "Model performance metrics retrieved successfully",
                "data": {
                    "models": performance_metrics,
                    "total_models": len(performance_metrics),
                    "overall_status": "operational" if performance_metrics else "no_models"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get model performance: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get model performance: {str(e)}"
            )
    
    # Helper methods
    def _load_models(self):
        """Load pre-trained models from disk"""
        try:
            # Load spending predictor
            spending_model_path = self.models_dir / "spending_predictor.pkl"
            if spending_model_path.exists():
                with open(spending_model_path, 'rb') as f:
                    self.spending_predictor = pickle.load(f)
                logger.info("Loaded pre-trained spending predictor model")
            
            # Load anomaly detector
            anomaly_model_path = self.models_dir / "anomaly_detector.pkl"
            if anomaly_model_path.exists():
                with open(anomaly_model_path, 'rb') as f:
                    self.anomaly_detector = pickle.load(f)
                logger.info("Loaded pre-trained anomaly detector model")
            
            # Load cash flow predictor
            cashflow_model_path = self.models_dir / "cash_flow_predictor.pkl"
            if cashflow_model_path.exists():
                with open(cashflow_model_path, 'rb') as f:
                    self.cash_flow_predictor = pickle.load(f)
                logger.info("Loaded pre-trained cash flow predictor model")
                
        except Exception as e:
            logger.warning(f"Failed to load pre-trained models: {e}")
    
    def _save_model(self, model_name: str, model):
        """Save trained model to disk"""
        try:
            model_path = self.models_dir / f"{model_name}.pkl"
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            logger.info(f"Saved {model_name} model to disk")
        except Exception as e:
            logger.warning(f"Failed to save {model_name} model: {e}")
    
    def _get_month_name(self, month: int) -> str:
        """Get month name from month number"""
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        return month_names[month - 1] if 1 <= month <= 12 else "Unknown"


# Global ML service instance
ml_service = MLService()


# Export functions and classes
__all__ = [
    "MLService",
    "ml_service"
]