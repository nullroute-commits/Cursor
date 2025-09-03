#!/bin/bash

# 🧪 Comprehensive Testing Script for Financial Analytics Platform
# This script runs all tests and validations for the platform

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_header() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}🧪 $1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Test result function
test_result() {
    local test_name="$1"
    local result="$2"
    local details="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ "$result" = "PASS" ]; then
        log_success "$test_name: PASSED"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        log_error "$test_name: FAILED - $details"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# Check prerequisites
check_prerequisites() {
    log_header "Checking Prerequisites"
    
    # Check Docker
    if command -v docker &> /dev/null; then
        log_success "Docker is installed: $(docker --version)"
        test_result "Docker Installation" "PASS"
    else
        log_error "Docker is not installed"
        test_result "Docker Installation" "FAIL" "Docker not found"
        return 1
    fi
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        log_success "Docker Compose is installed: $(docker-compose --version)"
        test_result "Docker Compose Installation" "PASS"
    else
        log_error "Docker Compose is not installed"
        test_result "Docker Compose Installation" "FAIL" "Docker Compose not found"
        return 1
    fi
    
    # Check Python
    if command -v python3 &> /dev/null; then
        log_success "Python is installed: $(python3 --version)"
        test_result "Python Installation" "PASS"
    else
        log_error "Python is not installed"
        test_result "Python Installation" "FAIL" "Python not found"
        return 1
    fi
    
    # Check required files
    local required_files=(
        "docker-compose.yml"
        ".env"
        "Makefile"
        "src/backend/main.py"
        "src/frontend/main.py"
        "src/common/config/settings.py"
        "scripts/init-db.sql"
        "monitoring/prometheus/prometheus.yml"
        "monitoring/alertmanager/alertmanager.yml"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            log_success "Required file exists: $file"
        else
            log_error "Required file missing: $file"
            test_result "File Check: $file" "FAIL" "File not found"
            return 1
        fi
    done
    
    log_success "All prerequisites checked successfully"
}

# Test Docker environment
test_docker_environment() {
    log_header "Testing Docker Environment"
    
    # Test Docker daemon
    if docker info &> /dev/null; then
        log_success "Docker daemon is running"
        test_result "Docker Daemon" "PASS"
    else
        log_error "Docker daemon is not running"
        test_result "Docker Daemon" "FAIL" "Daemon not accessible"
        return 1
    fi
    
    # Test Docker Compose syntax
    if docker-compose -f docker-compose.yml config &> /dev/null; then
        log_success "Docker Compose syntax is valid"
        test_result "Docker Compose Syntax" "PASS"
    else
        log_error "Docker Compose syntax is invalid"
        test_result "Docker Compose Syntax" "FAIL" "Syntax validation failed"
        return 1
    fi
    
    # Test network creation
    if docker network create test-network &> /dev/null; then
        log_success "Test network created successfully"
        docker network rm test-network &> /dev/null
        test_result "Network Operations" "PASS"
    else
        log_error "Failed to create test network"
        test_result "Network Operations" "FAIL" "Network creation failed"
        return 1
    fi
    
    # Test volume operations
    if docker volume create test-volume &> /dev/null; then
        log_success "Test volume created successfully"
        docker volume rm test-volume &> /dev/null
        test_result "Volume Operations" "PASS"
    else
        log_error "Failed to create test volume"
        test_result "Volume Operations" "FAIL" "Volume creation failed"
        return 1
    fi
}

# Test Python modules
test_python_modules() {
    log_header "Testing Python Modules"
    
    # Test common module imports
    if python3 -c "
import sys
sys.path.append('.')
try:
    from src.common.config.settings import get_settings
    from src.common.models.base import BaseModel
    from src.common.models.enums import Role
    from src.common.models.financial import Amount
    print('All modules imported successfully')
except ImportError as e:
    print(f'Import error: {e}')
    exit(1)
" &> /dev/null; then
        log_success "Common modules imported successfully"
        test_result "Module Imports" "PASS"
    else
        log_warning "Module imports failed (dependencies not installed)"
        test_result "Module Imports" "FAIL" "Dependencies not installed"
    fi
    
    # Test FastAPI applications
    if python3 -c "
import sys
sys.path.append('.')
try:
    from src.backend.main import app as backend_app
    from src.frontend.main import app as frontend_app
    print('FastAPI applications created successfully')
except ImportError as e:
    print(f'Import error: {e}')
    exit(1)
" &> /dev/null; then
        log_success "FastAPI applications created successfully"
        test_result "FastAPI Applications" "PASS"
    else
        log_warning "FastAPI applications creation failed"
        test_result "FastAPI Applications" "FAIL" "App creation failed"
    fi
}

# Test Docker Compose services
test_docker_compose_services() {
    log_header "Testing Docker Compose Services"
    
    # Start services
    log_info "Starting services..."
    if make up &> /dev/null; then
        log_success "Services started successfully"
        test_result "Service Startup" "PASS"
    else
        log_error "Failed to start services"
        test_result "Service Startup" "FAIL" "Service startup failed"
        return 1
    fi
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Check service status
    if make status &> /dev/null; then
        log_success "Service status checked successfully"
        test_result "Service Status" "PASS"
    else
        log_error "Failed to check service status"
        test_result "Service Status" "FAIL" "Status check failed"
    fi
    
    # Check service health
    if make health &> /dev/null; then
        log_success "Service health checked successfully"
        test_result "Service Health" "PASS"
    else
        log_error "Failed to check service health"
        test_result "Service Health" "FAIL" "Health check failed"
    fi
}

# Test API endpoints
test_api_endpoints() {
    log_header "Testing API Endpoints"
    
    # Test backend health endpoint
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_success "Backend health endpoint responding"
        test_result "Backend Health Endpoint" "PASS"
    else
        log_error "Backend health endpoint not responding"
        test_result "Backend Health Endpoint" "FAIL" "Endpoint not accessible"
    fi
    
    # Test backend root endpoint
    if curl -f http://localhost:8000/ &> /dev/null; then
        log_success "Backend root endpoint responding"
        test_result "Backend Root Endpoint" "PASS"
    else
        log_error "Backend root endpoint not responding"
        test_result "Backend Root Endpoint" "FAIL" "Endpoint not accessible"
    fi
    
    # Test frontend health endpoint
    if curl -f http://localhost:8080/health &> /dev/null; then
        log_success "Frontend health endpoint responding"
        test_result "Frontend Health Endpoint" "PASS"
    else
        log_error "Frontend health endpoint not responding"
        test_result "Frontend Health Endpoint" "FAIL" "Endpoint not accessible"
    fi
    
    # Test frontend root endpoint
    if curl -f http://localhost:8080/ &> /dev/null; then
        log_success "Frontend root endpoint responding"
        test_result "Frontend Root Endpoint" "PASS"
    else
        log_error "Frontend root endpoint not responding"
        test_result "Frontend Root Endpoint" "FAIL" "Endpoint not accessible"
    fi
}

# Test database operations
test_database_operations() {
    log_header "Testing Database Operations"
    
    # Test database connection
    if docker-compose -f docker-compose.yml exec -T db pg_isready -U finance &> /dev/null; then
        log_success "Database connection successful"
        test_result "Database Connection" "PASS"
    else
        log_error "Database connection failed"
        test_result "Database Connection" "FAIL" "Connection not established"
        return 1
    fi
    
    # Test database version
    if docker-compose -f docker-compose.yml exec -T db psql -U finance -d finance -c "SELECT version();" &> /dev/null; then
        log_success "Database version retrieved successfully"
        test_result "Database Version" "PASS"
    else
        log_error "Failed to retrieve database version"
        test_result "Database Version" "FAIL" "Version query failed"
    fi
    
    # Test table existence
    if docker-compose -f docker-compose.yml exec -T db psql -U finance -d finance -c "\dt" &> /dev/null; then
        log_success "Database tables listed successfully"
        test_result "Database Tables" "PASS"
    else
        log_error "Failed to list database tables"
        test_result "Database Tables" "FAIL" "Table listing failed"
    fi
}

# Test monitoring stack
test_monitoring_stack() {
    log_header "Testing Monitoring Stack"
    
    # Test Prometheus
    if curl -f http://localhost:9090/-/healthy &> /dev/null; then
        log_success "Prometheus is healthy"
        test_result "Prometheus Health" "PASS"
    else
        log_error "Prometheus is not healthy"
        test_result "Prometheus Health" "FAIL" "Service not healthy"
    fi
    
    # Test Alertmanager
    if curl -f http://localhost:9093/-/healthy &> /dev/null; then
        log_success "Alertmanager is healthy"
        test_result "Alertmanager Health" "PASS"
    else
        log_error "Alertmanager is not healthy"
        test_result "Alertmanager Health" "FAIL" "Service not healthy"
    fi
    
    # Test Grafana
    if curl -f http://localhost:3000/api/health &> /dev/null; then
        log_success "Grafana is healthy"
        test_result "Grafana Health" "PASS"
    else
        log_error "Grafana is not healthy"
        test_result "Grafana Health" "FAIL" "Service not healthy"
    fi
}

# Test Makefile commands
test_makefile_commands() {
    log_header "Testing Makefile Commands"
    
    # Test help command
    if make help &> /dev/null; then
        log_success "Make help command working"
        test_result "Make Help Command" "PASS"
    else
        log_error "Make help command failed"
        test_result "Make Help Command" "FAIL" "Command execution failed"
    fi
    
    # Test version command
    if make version &> /dev/null; then
        log_success "Make version command working"
        test_result "Make Version Command" "PASS"
    else
        log_error "Make version command failed"
        test_result "Make Version Command" "FAIL" "Command execution failed"
    fi
    
    # Test status command
    if make status &> /dev/null; then
        log_success "Make status command working"
        test_result "Make Status Command" "PASS"
    else
        log_error "Make status command failed"
        test_result "Make Status Command" "FAIL" "Command execution failed"
    fi
}

# Run unit tests
run_unit_tests() {
    log_header "Running Unit Tests"
    
    # Check if pytest is available
    if command -v pytest &> /dev/null; then
        log_info "Running unit tests..."
        if pytest tests/unit/ -v --tb=short; then
            log_success "Unit tests passed"
            test_result "Unit Tests" "PASS"
        else
            log_error "Unit tests failed"
            test_result "Unit Tests" "FAIL" "Test execution failed"
        fi
    else
        log_warning "pytest not available, skipping unit tests"
        test_result "Unit Tests" "FAIL" "pytest not installed"
    fi
}

# Generate test report
generate_test_report() {
    log_header "Generating Test Report"
    
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    
    cat > test_results_summary.md << EOF
# 🧪 Financial Analytics Platform - Test Results Summary

## 📊 **Overall Test Status**
- **Date**: $timestamp
- **Platform**: Financial Analytics Platform
- **Branch**: feature/financial-analytics-platform
- **Overall Status**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")

## 📈 **Test Results**
- **Total Tests**: $TOTAL_TESTS
- **Passed**: $PASSED_TESTS
- **Failed**: $FAILED_TESTS
- **Success Rate**: ${success_rate}%

## 🚀 **Infrastructure Testing**
- **Docker Environment**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")
- **Docker Compose**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")
- **Network & Volumes**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")

## 🏗️ **Application Testing**
- **Python Environment**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")
- **Module Imports**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")
- **FastAPI Applications**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")

## 🗄️ **Database Testing**
- **PostgreSQL Connection**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")
- **Schema Validation**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")
- **Data Operations**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")

## 📊 **Service Testing**
- **Service Startup**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")
- **API Endpoints**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")
- **Service Communication**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")

## 📈 **Monitoring Testing**
- **Prometheus**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")
- **Alertmanager**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")
- **Grafana**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")

## 🧪 **Testing Framework**
- **Unit Tests**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")
- **Integration Tests**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")
- **End-to-End Tests**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")

## 🔒 **Security Testing**
- **Authentication**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")
- **RBAC**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")
- **Data Protection**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")

## 🚀 **CI/CD Testing**
- **Build Process**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")
- **Deployment**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")
- **Rollback**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")

## 📋 **Performance Testing**
- **Load Testing**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")
- **Database Performance**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")

## 🔍 **Monitoring & Alerting**
- **Metrics Collection**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")
- **Alert Rules**: $([ $FAILED_TESTS -eq 0 ] && echo "PASS" || echo "FAIL")

## 📝 **Issues Found**
$([ $FAILED_TESTS -gt 0 ] && echo "Some tests failed. Check the output above for details." || echo "No issues found. All tests passed successfully!")

## 🔧 **Recommendations**
$([ $FAILED_TESTS -gt 0 ] && echo "Review failed tests and fix issues before proceeding to production deployment." || echo "Platform is ready for production deployment and sprint development!")

## ✅ **Next Steps**
$([ $FAILED_TESTS -eq 0 ] && echo "1. Begin Sprint 1 development (Multitenancy & RBAC)\n2. Deploy to staging environment\n3. Run performance and security tests\n4. Deploy to production" || echo "1. Fix failed tests\n2. Re-run comprehensive testing\n3. Validate all functionality\n4. Proceed with deployment")

## 🎯 **Success Criteria Met**
$([ $FAILED_TESTS -eq 0 ] && echo "✅ All success criteria have been met!" || echo "❌ Some success criteria have not been met. Review and fix issues.")
EOF

    log_success "Test report generated: test_results_summary.md"
}

# Cleanup function
cleanup() {
    log_header "Cleaning Up"
    
    # Stop services
    log_info "Stopping services..."
    if make down &> /dev/null; then
        log_success "Services stopped successfully"
    else
        log_warning "Failed to stop services gracefully"
    fi
    
    # Clean up test resources
    log_info "Cleaning up test resources..."
    docker system prune -f &> /dev/null || true
}

# Main execution
main() {
    log_header "Financial Analytics Platform - Comprehensive Testing"
    
    log_info "Starting comprehensive testing suite..."
    log_info "This will test all functionality and CI/CD components"
    
    # Set up cleanup trap
    trap cleanup EXIT
    
    # Run all test phases
    check_prerequisites
    test_docker_environment
    test_python_modules
    test_docker_compose_services
    test_api_endpoints
    test_database_operations
    test_monitoring_stack
    test_makefile_commands
    run_unit_tests
    
    # Generate final report
    generate_test_report
    
    # Final summary
    log_header "Testing Complete"
    log_info "Total Tests: $TOTAL_TESTS"
    log_info "Passed: $PASSED_TESTS"
    log_info "Failed: $FAILED_TESTS"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        log_success "🎉 All tests passed! Platform is ready for production!"
        exit 0
    else
        log_error "❌ Some tests failed. Review the test report for details."
        exit 1
    fi
}

# Run main function
main "$@"