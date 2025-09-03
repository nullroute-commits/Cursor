# Simple Dockerfile for CI/CD Pipeline testing
FROM alpine:3.19

# Install Python and pip
RUN apk add --no-cache \
    python3 \
    py3-pip \
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 1000 app && \
    adduser -D -s /bin/bash -u 1000 -G app app

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY pipeline/ ./pipeline/
COPY tests/ ./tests/

# Switch to non-root user
USER app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python3", "-m", "pytest", "tests/", "-v"]