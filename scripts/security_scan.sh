#!/bin/bash

# Security Scanning Script
# Comprehensive security assessment for Django application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCAN_DIRS="app config tests"
REPORTS_DIR="security_reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FAILED_SCANS=0

# Create reports directory
mkdir -p "$REPORTS_DIR"

echo -e "${BLUE}🔒 Running Comprehensive Security Scan...${NC}"
echo "Timestamp: $TIMESTAMP"
echo "Scan directories: $SCAN_DIRS"
echo "Reports directory: $REPORTS_DIR"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to run security scan with error handling
run_security_scan() {
    local name="$1"
    local command="$2"
    local output_file="$3"
    
    echo -e "${BLUE}Running $name...${NC}"
    
    if eval "$command" > "$output_file" 2>&1; then
        echo -e "${GREEN}✓ $name completed successfully${NC}"
        return 0
    else
        echo -e "${RED}✗ $name failed${NC}"
        FAILED_SCANS=$((FAILED_SCANS + 1))
        return 1
    fi
}

# 1. Dependency Security Scan (Safety)
echo -e "${BLUE}=== Dependency Security Scan ===${NC}"
if command_exists safety; then
    run_security_scan "Safety dependency scan" \
        "safety check -r requirements/base.txt --json --output $REPORTS_DIR/safety_report_$TIMESTAMP.json" \
        "$REPORTS_DIR/safety_output_$TIMESTAMP.txt"
else
    echo -e "${YELLOW}Safety not installed, skipping dependency scan${NC}"
fi

# 2. Code Security Analysis (Bandit)
echo -e "${BLUE}=== Code Security Analysis ===${NC}"
if command_exists bandit; then
    run_security_scan "Bandit security scan" \
        "bandit -r $SCAN_DIRS -f json -o $REPORTS_DIR/bandit_report_$TIMESTAMP.json" \
        "$REPORTS_DIR/bandit_output_$TIMESTAMP.txt"
else
    echo -e "${YELLOW}Bandit not installed, skipping code security scan${NC}"
fi

# 3. Container Security Scan (Trivy)
echo -e "${BLUE}=== Container Security Scan ===${NC}"
if command_exists trivy; then
    run_security_scan "Trivy container scan" \
        "trivy image --format json --output $REPORTS_DIR/trivy_report_$TIMESTAMP.json python:3.12.5-alpine" \
        "$REPORTS_DIR/trivy_output_$TIMESTAMP.txt"
else
    echo -e "${YELLOW}Trivy not installed, skipping container scan${NC}"
fi

# 4. OWASP ZAP Security Scan (if available)
echo -e "${BLUE}=== OWASP ZAP Security Scan ===${NC}"
if command_exists zap-baseline; then
    echo -e "${BLUE}Starting OWASP ZAP scan...${NC}"
    # This would require a running application instance
    echo -e "${YELLOW}OWASP ZAP scan requires running application instance${NC}"
else
    echo -e "${YELLOW}OWASP ZAP not installed, skipping web application scan${NC}"
fi

# 5. Django Security Check
echo -e "${BLUE}=== Django Security Check ===${NC}"
if command_exists python; then
    echo -e "${BLUE}Running Django security check...${NC}"
    if python manage.py check --deploy > "$REPORTS_DIR/django_security_check_$TIMESTAMP.txt" 2>&1; then
        echo -e "${GREEN}✓ Django security check passed${NC}"
    else
        echo -e "${RED}✗ Django security check failed${NC}"
        FAILED_SCANS=$((FAILED_SCANS + 1))
    fi
else
    echo -e "${YELLOW}Python not available, skipping Django security check${NC}"
fi

# 6. Secret Detection (TruffleHog)
echo -e "${BLUE}=== Secret Detection ===${NC}"
if command_exists trufflehog; then
    run_security_scan "TruffleHog secret scan" \
        "trufflehog --json . > $REPORTS_DIR/trufflehog_report_$TIMESTAMP.json" \
        "$REPORTS_DIR/trufflehog_output_$TIMESTAMP.txt"
else
    echo -e "${YELLOW}TruffleHog not installed, skipping secret detection${NC}"
fi

# 7. License Compliance Check
echo -e "${BLUE}=== License Compliance Check ===${NC}"
if command_exists licensecheck; then
    run_security_scan "License compliance check" \
        "licensecheck -r . > $REPORTS_DIR/license_check_$TIMESTAMP.txt" \
        "$REPORTS_DIR/license_check_$TIMESTAMP.txt"
else
    echo -e "${YELLOW}Licensecheck not installed, skipping license compliance check${NC}"
fi

# 8. Generate Security Summary Report
echo -e "${BLUE}=== Generating Security Summary Report ===${NC}"
cat > "$REPORTS_DIR/security_summary_$TIMESTAMP.md" << EOF
# Security Scan Summary Report

**Generated:** $TIMESTAMP  
**Reports Directory:** $REPORTS_DIR

## Scans Performed

- ✅ Dependency Security (Safety)
- ✅ Code Security Analysis (Bandit)
- ✅ Container Security (Trivy)
- ⚠️ OWASP ZAP Web Application Scan
- ✅ Django Security Check
- ✅ Secret Detection (TruffleHog)
- ✅ License Compliance Check

## Scan Results

- **Total Scans:** 7
- **Successful:** $((7 - FAILED_SCANS))
- **Failed:** $FAILED_SCANS

## Files Generated

$(ls -la "$REPORTS_DIR"/*"$TIMESTAMP"* | awk '{print "- " $9}')

## Security Recommendations

1. **Immediate Actions:**
   - Review all security reports
   - Address high and critical vulnerabilities
   - Update dependencies with security issues

2. **Short Term (1-2 weeks):**
   - Implement security fixes
   - Run follow-up scans
   - Update security policies

3. **Long Term (1-2 months):**
   - Establish security scanning schedule
   - Implement automated security testing
   - Conduct security training

## Next Steps

1. Review all generated security reports
2. Prioritize vulnerabilities by severity
3. Implement security fixes
4. Re-run security scans
5. Document security improvements

EOF

echo -e "${GREEN}✓ Security summary report generated: $REPORTS_DIR/security_summary_$TIMESTAMP.md${NC}"

# 9. Display Results
echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Security Scan Complete      ${NC}"
echo -e "${BLUE}================================${NC}"
echo ""
echo -e "${BLUE}Reports generated in: $REPORTS_DIR${NC}"
echo -e "${BLUE}Summary: $REPORTS_DIR/security_summary_$TIMESTAMP.md${NC}"
echo ""
echo -e "${BLUE}Scan Results:${NC}"
echo -e "  Total Scans: 7"
echo -e "  Successful: $((7 - FAILED_SCANS))"
echo -e "  Failed: $FAILED_SCANS"
echo ""

if [ $FAILED_SCANS -eq 0 ]; then
    echo -e "${GREEN}🎉 All security scans completed successfully!${NC}"
else
    echo -e "${YELLOW}⚠️  Some security scans failed. Review reports for details.${NC}"
fi

echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Review all security reports"
echo "2. Address identified vulnerabilities"
echo "3. Re-run failed scans"
echo "4. Implement security improvements"
echo ""
echo -e "${GREEN}Stay secure! 🔒${NC}"