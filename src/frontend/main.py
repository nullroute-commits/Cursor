"""
Main FastAPI application for Financial Analytics Platform Frontend
Frontend UI service with Jinja2 templates and static file serving
"""

import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from src.common.config import get_settings

# Global startup time for health checks
STARTUP_TIME = time.time()

# Template and static file paths
TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"

# Ensure directories exist
TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# Create templates instance
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🎨 Starting Financial Analytics Platform Frontend...")
    yield
    # Shutdown
    print("🛑 Shutting down Financial Analytics Platform Frontend...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="Financial Analytics Platform Frontend",
        description="Frontend UI for financial analytics platform",
        version="1.0.0",
        docs_url=None,  # No API docs for frontend
        redoc_url=None,
        openapi_url=None,
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
    
    # Mount static files
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), "static"
    
    return app


# Create application instance
app = create_app()


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - Dashboard"""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "title": "Financial Analytics Dashboard",
            "user": {"name": "Demo User", "role": "admin"},
            "organization": {"name": "Demo Organization"}
        }
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    uptime = time.time() - STARTUP_TIME
    
    return {
        "success": True,
        "status": "healthy",
        "service": "frontend",
        "version": "1.0.0",
        "uptime": uptime,
        "timestamp": time.time()
    }


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "title": "Login - Financial Analytics Platform"
        }
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard page"""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "title": "Dashboard - Financial Analytics Platform",
            "user": {"name": "Demo User", "role": "admin"},
            "organization": {"name": "Demo Organization"}
        }
    )


@app.get("/transactions", response_class=HTMLResponse)
async def transactions_page(request: Request):
    """Transactions page"""
    return templates.TemplateResponse(
        "transactions.html",
        {
            "request": request,
            "title": "Transactions - Financial Analytics Platform",
            "user": {"name": "Demo User", "role": "analyst"}
        }
    )


@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """Analytics page"""
    return templates.TemplateResponse(
        "analytics.html",
        {
            "request": request,
            "title": "Analytics - Financial Analytics Platform",
            "user": {"name": "Demo User", "role": "analyst"}
        }
    )


@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    """Reports page"""
    return templates.TemplateResponse(
        "reports.html",
        {
            "request": request,
            "title": "Reports - Financial Analytics Platform",
            "user": {"name": "Demo User", "role": "viewer"}
        }
    )


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page"""
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "title": "Settings - Financial Analytics Platform",
            "user": {"name": "Demo User", "role": "admin"}
        }
    )


@app.get("/api/status")
async def api_status():
    """API status endpoint"""
    return {
        "success": True,
        "service": "frontend",
        "version": "1.0.0",
        "status": "running",
        "timestamp": time.time()
    }


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    
    uvicorn.run(
        "src.frontend.main:app",
        host=settings.ui_host,
        port=settings.ui_port,
        reload=settings.ui_reload
    )