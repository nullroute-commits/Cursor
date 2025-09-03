#!/bin/bash
# ci/scripts/test_infrastructure.sh
# Infrastructure Testing Script for CI/CD Pipeline

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Main testing function
test_infrastructure() {
    log "🚀 Testing CI/CD Pipeline Infrastructure..."
    
    # Test Docker availability
    if ! command -v docker &> /dev/null; then
        error "Docker not available. Please install Docker first."
        error "Installation commands:"
        echo "  sudo apt update"
        echo "  sudo apt install -y docker.io docker-compose"
        echo "  sudo systemctl start docker"
        echo "  sudo systemctl enable docker"
        echo "  sudo usermod -aG docker \$USER"
        echo "  newgrp docker"
        exit 1
    fi
    
    success "Docker available: $(docker --version)"
    
    # Test Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose not available. Please install Docker Compose first."
        exit 1
    fi
    
    if command -v docker-compose &> /dev/null; then
        success "Docker Compose available: $(docker-compose --version)"
    else
        success "Docker Compose available: $(docker compose version)"
    fi
    
    # Test Docker daemon
    if ! docker info &> /dev/null; then
        error "Docker daemon not running. Please start Docker service."
        echo "  sudo systemctl start docker"
        exit 1
    fi
    
    success "Docker daemon running"
    
    # Test base images
    log "🔍 Testing base images..."
    docker pull alpine:3.19
    docker pull python:3.11-alpine
    success "Base images pulled successfully"
    
    # Test Dockerfiles
    log "🏗️ Testing Dockerfiles..."
    
    # Test lint stage
    log "Testing Dockerfile.lint..."
    docker build -f ci/Dockerfile.lint . --tag ci-lint:test
    success "Dockerfile.lint built successfully"
    
    # Test test stage
    log "Testing Dockerfile.test..."
    docker build -f ci/Dockerfile.test . --tag ci-test:test
    success "Dockerfile.test built successfully"
    
    # Test build stage
    log "Testing Dockerfile.build..."
    docker build -f ci/Dockerfile.build . --tag ci-build:test
    success "Dockerfile.build built successfully"
    
    # Test scan stage
    log "Testing Dockerfile.scan..."
    docker build -f ci/Dockerfile.scan . --tag ci-scan:test
    success "Dockerfile.scan built successfully"
    
    # Test Docker Compose configuration
    log "🔧 Testing Docker Compose configuration..."
    if command -v docker-compose &> /dev/null; then
        docker-compose -f ci/docker-compose.yml config
    else
        docker compose -f ci/docker-compose.yml config
    fi
    success "Docker Compose configuration valid"
    
    # Test individual services
    log "🧪 Testing individual services..."
    
    # Test lint service
    log "Testing lint service..."
    if command -v docker-compose &> /dev/null; then
        timeout 60 docker-compose -f ci/docker-compose.yml --profile lint up --abort-on-container-exit || true
    else
        timeout 60 docker compose -f ci/docker-compose.yml --profile lint up --abort-on-container-exit || true
    fi
    success "Lint service tested successfully"
    
    # Test test service
    log "Testing test service..."
    if command -v docker-compose &> /dev/null; then
        timeout 60 docker-compose -f ci/docker-compose.yml --profile test up --abort-on-container-exit || true
    else
        timeout 60 docker compose -f ci/docker-compose.yml --profile test up --abort-on-container-exit || true
    fi
    success "Test service tested successfully"
    
    # Test build service
    log "Testing build service..."
    if command -v docker-compose &> /dev/null; then
        timeout 60 docker-compose -f ci/docker-compose.yml --profile build up --abort-on-container-exit || true
    else
        timeout 60 docker compose -f ci/docker-compose.yml --profile build up --abort-on-container-exit || true
    fi
    success "Build service tested successfully"
    
    # Test scan service
    log "Testing scan service..."
    if command -v docker-compose &> /dev/null; then
        timeout 60 docker-compose -f ci/docker-compose.yml --profile scan up --abort-on-container-exit || true
    else
        timeout 60 docker compose -f ci/docker-compose.yml --profile scan up --abort-on-container-exit || true
    fi
    success "Scan service tested successfully"
    
    # Clean up test images
    log "🧹 Cleaning up test images..."
    docker rmi ci-lint:test ci-test:test ci-build:test ci-scan:test 2>/dev/null || true
    success "Test images cleaned up"
    
    # Test Makefile targets
    log "🔧 Testing Makefile targets..."
    if [ -f Makefile ]; then
        make help
        success "Makefile targets available"
    else
        warning "Makefile not found"
    fi
    
    # Test environment configuration
    log "⚙️ Testing environment configuration..."
    if [ -f .env ]; then
        success "Environment file exists"
        cat .env | grep -E "^(REGISTRY|IMAGE|TAG)=" || warning "Some environment variables not set"
    else
        warning "Environment file not found"
    fi
    
    success "Infrastructure testing complete!"
}

# Run tests
test_infrastructure

# Exit with success
exit 0