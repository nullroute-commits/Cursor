"""
Main FastAPI application for Financial Analytics Platform
Backend API with authentication, RBAC, and analytics capabilities
"""

import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.common.config import get_settings
from src.backend.api import auth_router, users_router, organizations_router, ingestion_router, transactions_router, plaid_router, analytics_router, ml_router, reporting_router, dashboard_router
from src.backend.middleware.auth import AuthMiddleware
from src.backend.middleware.rbac import RBACMiddleware
from src.backend.middleware.audit import AuditMiddleware
from src.backend.middleware.metrics import MetricsMiddleware

# Global startup time for health checks
STARTUP_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Starting Financial Analytics Platform Backend...")
    yield
    # Shutdown
    print("🛑 Shutting down Financial Analytics Platform Backend...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="Financial Analytics Platform API",
        description="Comprehensive financial analytics platform with multitenancy and RBAC",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan
    )
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
    app.add_middleware(AuthMiddleware)
    app.add_middleware(RBACMiddleware)
    app.add_middleware(AuditMiddleware)
    app.add_middleware(MetricsMiddleware)
    
    # Include routers
    app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(users_router, prefix="/api/users", tags=["Users"])
    app.include_router(organizations_router, prefix="/api/organizations", tags=["Organizations"])
    app.include_router(ingestion_router, prefix="/api/ingestion", tags=["Data Ingestion"])
    app.include_router(transactions_router, prefix="/api/transactions", tags=["Transactions"])
    app.include_router(plaid_router, prefix="/api/plaid", tags=["Plaid Integration"])
    app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
    app.include_router(ml_router, prefix="/api/ml", tags=["Machine Learning"])
    app.include_router(reporting_router, prefix="/api/reporting", tags=["Reporting"])
    app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboards"])
    
    # Global exception handlers
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.detail,
                "error_code": f"HTTP_{exc.status_code}",
                "timestamp": time.time()
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": "Validation error",
                "error_code": "VALIDATION_ERROR",
                "error_details": exc.errors(),
                "timestamp": time.time()
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error",
                "error_code": "INTERNAL_ERROR",
                "timestamp": time.time()
            }
        )
    
    return app


# Create application instance
app = create_app()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Financial Analytics Platform API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    settings = get_settings()
    uptime = time.time() - STARTUP_TIME
    
    # Basic health checks
    checks = {
        "api": "healthy",
        "database": "healthy",  # TODO: Add actual DB health check
        "redis": "healthy",     # TODO: Add actual Redis health check
        "environment": settings.environment,
        "debug": settings.debug
    }
    
    return {
        "success": True,
        "status": "healthy",
        "version": "1.0.0",
        "uptime": uptime,
        "checks": checks,
        "timestamp": time.time()
    }


@app.get("/info")
async def info():
    """System information endpoint"""
    settings = get_settings()
    
    return {
        "success": True,
        "platform": "Financial Analytics Platform",
        "version": "1.0.0",
        "environment": settings.environment,
        "features": {
            "rbac": settings.enable_rbac,
            "multitenancy": settings.enable_multitenancy,
            "analytics": settings.enable_analytics,
            "monitoring": settings.enable_monitoring,
            "alerting": settings.enable_alerting,
            "plaid_integration": settings.enable_plaid_integration,
            "post_quantum_crypto": settings.enable_post_quantum_crypto
        },
        "timestamp": time.time()
    }


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    
    uvicorn.run(
        "src.backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        workers=settings.api_workers
    )