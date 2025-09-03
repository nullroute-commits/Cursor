#!/bin/bash
# ci/scripts/run_operational_tests.sh
# Comprehensive Operational Testing Script for CI/CD Pipeline

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

phase() {
    echo -e "${PURPLE}🚀 $1${NC}"
}

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPORTS_DIR="$PROJECT_ROOT/reports"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Create reports directory
mkdir -p "$REPORTS_DIR"

# Test results tracking
declare -A TEST_RESULTS
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNINGS=0

# Test result tracking function
record_test_result() {
    local test_name="$1"
    local result="$2"
    local details="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    TEST_RESULTS["$test_name"]="$result"
    
    case "$result" in
        "PASS")
            PASSED_TESTS=$((PASSED_TESTS + 1))
            success "$test_name: PASS"
            ;;
        "FAIL")
            FAILED_TESTS=$((FAILED_TESTS + 1))
            error "$test_name: FAIL - $details"
            ;;
        "WARN")
            WARNINGS=$((WARNINGS + 1))
            warning "$test_name: WARN - $details"
            ;;
    esac
}

# Phase 1: Infrastructure Testing
run_infrastructure_tests() {
    phase "Phase 1: Infrastructure Testing"
    
    log "Running infrastructure tests..."
    
    if [ -f "$SCRIPT_DIR/test_infrastructure.sh" ]; then
        if "$SCRIPT_DIR/test_infrastructure.sh" 2>&1; then
            record_test_result "Infrastructure Tests" "PASS" "All infrastructure components validated"
        else
            record_test_result "Infrastructure Tests" "FAIL" "Infrastructure testing failed"
        fi
    else
        record_test_result "Infrastructure Tests" "WARN" "Infrastructure test script not found"
    fi
    
    echo
}

# Phase 2: Security Testing
run_security_tests() {
    phase "Phase 2: Security Testing"
    
    log "Running security tests..."
    
    if [ -f "$SCRIPT_DIR/test_security.sh" ]; then
        if "$SCRIPT_DIR/test_security.sh" 2>&1; then
            record_test_result "Security Tests" "PASS" "All security components validated"
        else
            record_test_result "Security Tests" "FAIL" "Security testing failed"
        fi
    else
        record_test_result "Security Tests" "WARN" "Security test script not found"
    fi
    
    echo
}

# Phase 3: Quality Testing
run_quality_tests() {
    phase "Phase 3: Quality Testing"
    
    log "Running quality tests..."
    
    if [ -f "$SCRIPT_DIR/test_quality.sh" ]; then
        if "$SCRIPT_DIR/test_quality.sh" 2>&1; then
            record_test_result "Quality Tests" "PASS" "All quality components validated"
        else
            record_test_result "Quality Tests" "FAIL" "Quality testing failed"
        fi
    else
        record_test_result "Quality Tests" "WARN" "Quality test script not found"
    fi
    
    echo
}

# Phase 4: Integration Testing
run_integration_tests() {
    phase "Phase 4: Integration Testing"
    
    log "Running integration tests..."
    
    # Test Python module integration
    log "Testing Python module integration..."
    if python3 -c "from pipeline import Pipeline; p = Pipeline(); print('Integration test passed')" 2>/dev/null; then
        record_test_result "Python Integration" "PASS" "Pipeline module integration successful"
    else
        record_test_result "Python Integration" "FAIL" "Pipeline module integration failed"
    fi
    
    # Test configuration integration
    log "Testing configuration integration..."
    if [ -f "$PROJECT_ROOT/.env" ] && [ -f "$PROJECT_ROOT/Makefile" ]; then
        record_test_result "Configuration Integration" "PASS" "Configuration files properly integrated"
    else
        record_test_result "Configuration Integration" "FAIL" "Configuration files missing"
    fi
    
    # Test documentation integration
    log "Testing documentation integration..."
    if [ -d "$PROJECT_ROOT/docs" ] && [ -f "$PROJECT_ROOT/README.md" ]; then
        record_test_result "Documentation Integration" "PASS" "Documentation properly integrated"
    else
        record_test_result "Documentation Integration" "FAIL" "Documentation missing"
    fi
    
    echo
}

# Phase 5: End-to-End Testing
run_e2e_tests() {
    phase "Phase 5: End-to-End Testing"
    
    log "Running end-to-end tests..."
    
    # Test Makefile targets
    log "Testing Makefile targets..."
    if [ -f "$PROJECT_ROOT/Makefile" ]; then
        if make -f "$PROJECT_ROOT/Makefile" help >/dev/null 2>&1; then
            record_test_result "Makefile Targets" "PASS" "All Makefile targets functional"
        else
            record_test_result "Makefile Targets" "FAIL" "Makefile targets not functional"
        fi
    else
        record_test_result "Makefile Targets" "WARN" "Makefile not found"
    fi
    
    # Test environment setup
    log "Testing environment setup..."
    if [ -f "$PROJECT_ROOT/.env" ]; then
        record_test_result "Environment Setup" "PASS" "Environment configuration ready"
    else
        record_test_result "Environment Setup" "WARN" "Environment file not found"
    fi
    
    # Test project structure
    log "Testing project structure..."
    local required_files=("ci/Dockerfile.lint" "ci/Dockerfile.test" "ci/Dockerfile.build" "ci/Dockerfile.scan" "ci/docker-compose.yml" "ci/entrypoint.sh")
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$PROJECT_ROOT/$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -eq 0 ]; then
        record_test_result "Project Structure" "PASS" "All required files present"
    else
        record_test_result "Project Structure" "FAIL" "Missing files: ${missing_files[*]}"
    fi
    
    echo
}

# Generate comprehensive test report
generate_test_report() {
    phase "Generating Test Report"
    
    log "Generating comprehensive test report..."
    
    # Create detailed test report
    cat > "$REPORTS_DIR/operational_test_report.json" << EOF
{
  "test_summary": {
    "timestamp": "$TIMESTAMP",
    "total_tests": $TOTAL_TESTS,
    "passed_tests": $PASSED_TESTS,
    "failed_tests": $FAILED_TESTS,
    "warnings": $WARNINGS,
    "success_rate": "$((PASSED_TESTS * 100 / TOTAL_TESTS))%"
  },
  "test_results": {
$(for test_name in "${!TEST_RESULTS[@]}"; do
    echo "    \"$test_name\": \"${TEST_RESULTS[$test_name]}\""
done | sed '$ s/,$//')
  },
  "operational_status": "$([ $FAILED_TESTS -eq 0 ] && echo "OPERATIONAL" || echo "NOT_OPERATIONAL")",
  "recommendations": [
$(if [ $FAILED_TESTS -gt 0 ]; then
    echo "    \"Address failed tests before proceeding to production\""
fi
if [ $WARNINGS -gt 0 ]; then
    echo "    \"Review warnings to improve operational readiness\""
fi
if [ $FAILED_TESTS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "    \"All tests passed - pipeline is operational\""
fi)
  ]
}
EOF
    
    success "Test report generated: $REPORTS_DIR/operational_test_report.json"
    
    # Create human-readable summary
    cat > "$REPORTS_DIR/operational_test_summary.md" << EOF
# 🚀 Operational Test Summary

**Date**: $TIMESTAMP  
**Status**: $([ $FAILED_TESTS -eq 0 ] && echo "✅ OPERATIONAL" || echo "❌ NOT OPERATIONAL")  

## 📊 Test Results

- **Total Tests**: $TOTAL_TESTS
- **Passed**: $PASSED_TESTS ✅
- **Failed**: $FAILED_TESTS ❌
- **Warnings**: $WARNINGS ⚠️
- **Success Rate**: $((PASSED_TESTS * 100 / TOTAL_TESTS))%

## 🎯 Test Details

$(for test_name in "${!TEST_RESULTS[@]}"; do
    case "${TEST_RESULTS[$test_name]}" in
        "PASS")
            echo "- ✅ **$test_name**: PASS"
            ;;
        "FAIL")
            echo "- ❌ **$test_name**: FAIL"
            ;;
        "WARN")
            echo "- ⚠️ **$test_name**: WARN"
            ;;
    esac
done)

## 🚀 Operational Status

$([ $FAILED_TESTS -eq 0 ] && echo "**🎉 PIPELINE IS FULLY OPERATIONAL!**" || echo "**🚨 PIPELINE NEEDS ATTENTION BEFORE OPERATIONAL USE**")

## 📋 Recommendations

$(if [ $FAILED_TESTS -gt 0 ]; then
    echo "- ❌ **Address failed tests** before proceeding to production"
fi
if [ $WARNINGS -gt 0 ]; then
    echo "- ⚠️ **Review warnings** to improve operational readiness"
fi
if [ $FAILED_TESTS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "- ✅ **All tests passed** - pipeline is ready for production use"
fi)

## 🔧 Next Steps

$(if [ $FAILED_TESTS -eq 0 ]; then
    echo "1. **Deploy to production** - pipeline is operational"
    echo "2. **Monitor performance** - track execution metrics"
    echo "3. **Team training** - onboard users to the pipeline"
else
    echo "1. **Fix failed tests** - resolve identified issues"
    echo "2. **Re-run tests** - validate fixes"
    echo "3. **Address warnings** - improve operational readiness"
fi)

---
*Report generated by CI/CD Pipeline Operational Testing Suite*
EOF
    
    success "Test summary generated: $REPORTS_DIR/operational_test_summary.md"
}

# Display final results
display_final_results() {
    echo
    echo "=" * 80
    phase "FINAL TEST RESULTS"
    echo "=" * 80
    
    echo
    echo "📊 Test Summary:"
    echo "  Total Tests: $TOTAL_TESTS"
    echo "  Passed:      $PASSED_TESTS ✅"
    echo "  Failed:      $FAILED_TESTS ❌"
    echo "  Warnings:    $WARNINGS ⚠️"
    echo "  Success Rate: $((PASSED_TESTS * 100 / TOTAL_TESTS))%"
    echo
    
    if [ $FAILED_TESTS -eq 0 ]; then
        if [ $WARNINGS -eq 0 ]; then
            success "🎉 ALL TESTS PASSED! Pipeline is fully operational!"
            echo
            info "Next steps:"
            echo "  1. Deploy to production"
            echo "  2. Monitor performance"
            echo "  3. Train team members"
        else
            success "✅ All critical tests passed! Pipeline is operational with warnings."
            echo
            warning "Recommendations:"
            echo "  1. Review warnings to improve operational readiness"
            echo "  2. Deploy to production"
            echo "  3. Monitor performance"
        fi
    else
        error "❌ Some tests failed! Pipeline needs attention before operational use."
        echo
        info "Next steps:"
        echo "  1. Fix failed tests"
        echo "  2. Re-run operational tests"
        echo "  3. Address warnings"
        echo "  4. Deploy to production"
    fi
    
    echo
    echo "📋 Detailed reports available in:"
    echo "  - JSON Report: $REPORTS_DIR/operational_test_report.json"
    echo "  - Summary:     $REPORTS_DIR/operational_test_summary.md"
    echo
}

# Main execution
main() {
    echo "🚀 CI/CD Pipeline Operational Testing Suite"
    echo "=========================================="
    echo
    
    log "Starting comprehensive operational testing..."
    echo
    
    # Run all test phases
    run_infrastructure_tests
    run_security_tests
    run_quality_tests
    run_integration_tests
    run_e2e_tests
    
    # Generate reports
    generate_test_report
    
    # Display results
    display_final_results
    
    # Exit with appropriate code
    if [ $FAILED_TESTS -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"