#!/bin/bash
set -euo pipefail

# CI/CD Pipeline Entrypoint Script
# Dispatches to appropriate stage based on CI_STAGE environment variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Validate required environment variables
validate_env() {
    local required_vars=("CI_STAGE")
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    # Validate CI_STAGE value
    local valid_stages=("lint" "test" "build" "scan")
    local stage_valid=false
    
    for stage in "${valid_stages[@]}"; do
        if [[ "$CI_STAGE" == "$stage" ]]; then
            stage_valid=true
            break
        fi
    done
    
    if [[ "$stage_valid" == false ]]; then
        error "Invalid CI_STAGE: $CI_STAGE. Valid stages: ${valid_stages[*]}"
        exit 1
    fi
}

# Create reports directory
setup_reports() {
    mkdir -p reports
    log "Reports directory ready"
}

# Lint stage execution
run_lint() {
    log "Starting Lint Stage..."
    
    # Run Hadolint on Dockerfiles
    log "Running Hadolint on Dockerfiles..."
    if find . -name "Dockerfile*" -type f | grep -q .; then
        find . -name "Dockerfile*" -type f -exec hadolint {} \;
        success "Hadolint completed successfully"
    else
        warn "No Dockerfiles found for Hadolint"
    fi
    
    # Run Ruff on Python files
    log "Running Ruff on Python files..."
    if find . -name "*.py" -type f | grep -q .; then
        ruff check . --output-format=text
        success "Ruff completed successfully"
    else
        warn "No Python files found for Ruff"
    fi
    
    # Run ShellCheck on shell scripts
    log "Running ShellCheck on shell scripts..."
    if find . -name "*.sh" -type f | grep -q .; then
        find . -name "*.sh" -type f -exec shellcheck {} \;
        success "ShellCheck completed successfully"
    else
        warn "No shell scripts found for ShellCheck"
    fi
    
    success "Lint Stage completed successfully"
}

# Test stage execution
run_test() {
    log "Starting Test Stage..."
    
    # Run pytest with coverage
    log "Running pytest with coverage..."
    python -m pytest --junitxml=reports/junit.xml \
                     --cov=. \
                     --cov-report=html:reports/coverage \
                     --cov-report=term \
                     --cov-fail-under=80 \
                     -v
    
    success "Test Stage completed successfully"
}

# Build stage execution
run_build() {
    log "Starting Build Stage..."
    
    # Validate required build environment variables
    local build_vars=("REGISTRY" "IMAGE" "TAG")
    for var in "${build_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error "Build requires environment variable: $var"
            exit 1
        fi
    done
    
    # Create multi-arch build
    log "Building multi-architecture image..."
    docker buildx create --use --name ci-builder || true
    
    # Build and push multi-arch image
    docker buildx build \
        --platform linux/amd64,linux/arm64,linux/arm/v7 \
        --tag "${REGISTRY}/${IMAGE}:${TAG}" \
        --tag "${REGISTRY}/${IMAGE}:latest" \
        --push \
        .
    
    success "Build Stage completed successfully"
    log "Image pushed: ${REGISTRY}/${IMAGE}:${TAG}"
}

# Scan stage execution
run_scan() {
    log "Starting Scan Stage..."
    
    # Validate required scan environment variables
    local scan_vars=("REGISTRY" "IMAGE" "TAG")
    for var in "${scan_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error "Scan requires environment variable: $var"
            exit 1
        fi
    done
    
    # Run Docker Scout vulnerability scan
    log "Running Docker Scout vulnerability scan..."
    scout cves "${REGISTRY}/${IMAGE}:${TAG}" --format json > reports/vulnerabilities.json
    
    # Check for high-severity CVEs
    local high_cves=$(jq -r '.vulnerabilities[] | select(.severity == "high" or .severity == "critical") | .id' reports/vulnerabilities.json 2>/dev/null || echo "")
    
    if [[ -n "$high_cves" ]]; then
        error "High-severity vulnerabilities found:"
        echo "$high_cves"
        exit 1
    fi
    
    # Generate SBOM
    log "Generating Software Bill of Materials..."
    docker sbom "${REGISTRY}/${IMAGE}:${TAG}" --format json > reports/sbom.json
    
    success "Scan Stage completed successfully"
    log "Vulnerability scan and SBOM generation completed"
}

# Main execution
main() {
    log "CI/CD Pipeline Entrypoint Starting..."
    log "Stage: $CI_STAGE"
    
    # Validate environment
    validate_env
    
    # Setup reports directory
    setup_reports
    
    # Execute appropriate stage
    case "$CI_STAGE" in
        "lint")
            run_lint
            ;;
        "test")
            run_test
            ;;
        "build")
            run_build
            ;;
        "scan")
            run_scan
            ;;
        *)
            error "Unknown CI stage: $CI_STAGE"
            exit 1
            ;;
    esac
    
    success "CI/CD Pipeline Stage completed successfully"
}

# Handle signals
trap 'error "Pipeline interrupted"; exit 130' INT TERM

# Execute main function
main "$@"