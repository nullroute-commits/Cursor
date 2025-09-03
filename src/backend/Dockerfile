# Multi-stage Dockerfile for Financial Analytics Platform Backend
FROM python:3.11-alpine AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    postgresql-dev \
    curl \
    bash

# Create app directory
WORKDIR /app

# Copy requirements files
COPY requirements/ requirements/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements/base.txt

# =============================================================================
# Development Stage
# =============================================================================
FROM base AS development

# Install development dependencies
RUN pip install --no-cache-dir -r requirements/development.txt

# Copy source code
COPY src/ /app/src/
COPY scripts/ /app/scripts/

# Set development environment
ENV ENVIRONMENT=development \
    DEBUG=true \
    PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run development server
CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# =============================================================================
# Worker Stage (for Celery)
# =============================================================================
FROM base AS worker

# Install worker dependencies
RUN pip install --no-cache-dir -r requirements/worker.txt

# Copy source code
COPY src/ /app/src/
COPY scripts/ /app/scripts/

# Set worker environment
ENV ENVIRONMENT=production \
    PYTHONPATH=/app

# Create logs directory
RUN mkdir -p /app/logs

# Run Celery worker
CMD ["celery", "-A", "src.backend.worker.celery", "worker", "--loglevel=info"]

# =============================================================================
# Production Stage
# =============================================================================
FROM base AS production

# Install production dependencies
RUN pip install --no-cache-dir -r requirements/production.txt

# Copy source code
COPY src/ /app/src/
COPY scripts/ /app/scripts/

# Set production environment
ENV ENVIRONMENT=production \
    DEBUG=false \
    PYTHONPATH=/app

# Create logs directory
RUN mkdir -p /app/logs

# Create non-root user
RUN addgroup -g 1000 app && \
    adduser -u 1000 -G app -s /bin/bash -D app

# Change ownership of app directory
RUN chown -R app:app /app

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run production server
CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]