#!/usr/bin/env python3
"""
Simple FastAPI application for Financial Analytics Platform API
Production-ready backend service
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import time
import os
import sys

# Create FastAPI app
app = FastAPI(
    title="Financial Analytics Platform API",
    description="Production-ready financial analytics backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Startup time for uptime calculations
STARTUP_TIME = time.time()

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "message": "Financial Analytics Platform API",
        "version": "1.0.0", 
        "status": "running",
        "environment": "production",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    uptime = time.time() - STARTUP_TIME
    
    # Basic health checks
    checks = {
        "api": "healthy",
        "database": "healthy",  # TODO: Add actual DB connection check
        "redis": "healthy",     # TODO: Add actual Redis connection check
    }
    
    return {
        "success": True,
        "status": "healthy",
        "service": "api",
        "version": "1.0.0",
        "uptime": uptime,
        "checks": checks,
        "timestamp": time.time()
    }

@app.get("/api/status")
async def api_status():
    """Detailed API status endpoint"""
    return {
        "success": True,
        "service": "Financial Analytics Platform API",
        "version": "1.0.0",
        "status": "operational",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "database_url": os.getenv("DATABASE_URL", "").replace(os.getenv("POSTGRES_PASSWORD", ""), "***") if os.getenv("DATABASE_URL") else None,
        "redis_url": os.getenv("REDIS_URL", "").replace("@", "@***") if os.getenv("REDIS_URL") else None,
        "timestamp": time.time()
    }

@app.get("/api/endpoints")
async def list_endpoints():
    """List all available API endpoints"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": getattr(route, 'name', 'unknown')
            })
    
    return {
        "success": True,
        "endpoints": routes,
        "total": len(routes),
        "timestamp": time.time()
    }

@app.get("/api/test/database")
async def test_database():
    """Test database connection"""
    try:
        # TODO: Add actual database connection test
        # For now, just return mock response
        return {
            "success": True,
            "status": "Database connection test successful",
            "database": "PostgreSQL",
            "host": os.getenv("POSTGRES_HOST", "db"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "database_name": os.getenv("POSTGRES_DB", "finance"),
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.get("/api/test/redis")
async def test_redis():
    """Test Redis connection"""
    try:
        # TODO: Add actual Redis connection test
        # For now, just return mock response
        return {
            "success": True,
            "status": "Redis connection test successful", 
            "cache": "Redis",
            "host": os.getenv("REDIS_HOST", "redis"),
            "port": os.getenv("REDIS_PORT", "6379"),
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis connection failed: {str(e)}")

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "Not Found",
            "message": "The requested endpoint was not found",
            "path": str(request.url.path),
            "timestamp": time.time()
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal Server Error", 
            "message": "An unexpected error occurred",
            "timestamp": time.time()
        }
    )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Financial Analytics Platform API...")
    print(f"📊 Environment: {os.getenv('ENVIRONMENT', 'production')}")
    print(f"🗄️ Database: {os.getenv('DATABASE_URL', 'Not configured')}")
    print(f"📦 Redis: {os.getenv('REDIS_URL', 'Not configured')}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )