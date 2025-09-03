"""
API package for Financial Analytics Platform
FastAPI routers and endpoints
"""

from .auth import router as auth_router
from .users import router as users_router
from .organizations import router as organizations_router
from .ingestion import router as ingestion_router
from .transactions import router as transactions_router
from .plaid import router as plaid_router
from .analytics import router as analytics_router
from .ml import router as ml_router

__all__ = [
    "auth_router",
    "users_router", 
    "organizations_router",
    "ingestion_router",
    "transactions_router",
    "plaid_router",
    "analytics_router",
    "ml_router"
]