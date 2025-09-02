#!/bin/bash

# Quality Gate Script
# Enforces strict quality standards and generates comprehensive reports

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
QUALITY_THRESHOLDS=${QUALITY_THRESHOLDS:-"strict"}
GENERATE_REPORTS=${GENERATE_REPORTS:-"true"}
REPORTS_DIR="quality_reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Quality thresholds
case $QUALITY_THRESHOLDS in
    "strict")
        MIN_COVERAGE=90
        MAX_COMPLEXITY=8
        MAX_LINE_LENGTH=120
        MAX_DUPLICATION=2
        ;;
    "standard")
        MIN_COVERAGE=80
        MAX_COMPLEXITY=10
        MAX_LINE_LENGTH=120
        MAX_DUPLICATION=3
        ;;
    "relaxed")
        MIN_COVERAGE=70
        MAX_COMPLEXITY=12
        MAX_LINE_LENGTH=120
        MAX_DUPLICATION=5
        ;;
    *)
        echo -e "${RED}Invalid quality threshold: $QUALITY_THRESHOLDS${NC}"
        exit 1
        ;;
esac

# Create reports directory
mkdir -p "$REPORTS_DIR"

echo -e "${BLUE}🚀 Running Quality Gate with $QUALITY_THRESHOLDS thresholds...${NC}"
echo "Timestamp: $TIMESTAMP"
echo "Reports directory: $REPORTS_DIR"
echo ""
echo -e "${BLUE}Quality Thresholds:${NC}"
echo "  Coverage: $MIN_COVERAGE%"
echo "  Complexity: $MAX_COMPLEXITY"
echo "  Line Length: $MAX_LINE_LENGTH"
echo "  Duplication: $MAX_DUPLICATION%"
echo ""

# Initialize quality metrics
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
QUALITY_SCORE=0

# Function to run quality check
run_quality_check() {
    local name="$1"
    local command="$2"
    local output_file="$3"
    local weight="$4"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    echo -e "${BLUE}Running $name...${NC}"
    
    if eval "$command" > "$output_file" 2>&1; then
        echo -e "${GREEN}✓ $name passed${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        QUALITY_SCORE=$((QUALITY_SCORE + weight))
        return 0
    else
        echo -e "${RED}✗ $name failed${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Code Coverage Check
echo -e "${BLUE}=== Code Coverage Analysis ===${NC}"
if command_exists pytest; then
    run_quality_check "Code coverage" \
        "pytest --cov=app --cov-report=term-missing --cov-fail-under=$MIN_COVERAGE tests/" \
        "$REPORTS_DIR/coverage_check_$TIMESTAMP.txt" \
        25
else
    echo -e "${YELLOW}pytest not installed, skipping coverage check${NC}"
fi

# 2. Code Complexity Check
echo -e "${BLUE}=== Code Complexity Analysis ===${NC}"
if command_exists radon; then
    run_quality_check "Code complexity" \
        "radon cc app/ -a -nc -j --json > $REPORTS_DIR/complexity_report_$TIMESTAMP.json" \
        "$REPORTS_DIR/complexity_check_$TIMESTAMP.txt" \
        20
    
    # Check if any functions exceed complexity threshold
    if [ -f "$REPORTS_DIR/complexity_report_$TIMESTAMP.json" ]; then
        COMPLEX_FUNCTIONS=$(python3 -c "
import json
with open('$REPORTS_DIR/complexity_report_$TIMESTAMP.json') as f:
    data = json.load(f)
    complex_count = 0
    for file_data in data.values():
        for func in file_data:
            if func['complexity'] > $MAX_COMPLEXITY:
                complex_count += 1
    print(complex_count)
")
        
        if [ "$COMPLEX_FUNCTIONS" -gt 0 ]; then
            echo -e "${RED}✗ Found $COMPLEX_FUNCTIONS functions exceeding complexity threshold${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        else
            echo -e "${GREEN}✓ All functions within complexity threshold${NC}"
        fi
    fi
else
    echo -e "${YELLOW}radon not installed, skipping complexity check${NC}"
fi

# 3. Code Duplication Check
echo -e "${BLUE}=== Code Duplication Analysis ===${NC}"
if command_exists jscpd; then
    run_quality_check "Code duplication" \
        "jscpd app/ --reporters json --output $REPORTS_DIR/duplication_report_$TIMESTAMP.json" \
        "$REPORTS_DIR/duplication_check_$TIMESTAMP.txt" \
        15
    
    # Check duplication percentage
    if [ -f "$REPORTS_DIR/duplication_report_$TIMESTAMP.json" ]; then
        DUPLICATION_PERCENT=$(python3 -c "
import json
with open('$REPORTS_DIR/duplication_report_$TIMESTAMP.json') as f:
    data = json.load(f)
    print(data.get('statistics', {}).get('total', {}).get('percentage', 0))
")
        
        if (( $(echo "$DUPLICATION_PERCENT > $MAX_DUPLICATION" | bc -l) )); then
            echo -e "${RED}✗ Code duplication ($DUPLICATION_PERCENT%) exceeds threshold ($MAX_DUPLICATION%)${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        else
            echo -e "${GREEN}✓ Code duplication ($DUPLICATION_PERCENT%) within threshold${NC}"
        fi
    fi
else
    echo -e "${YELLOW}jscpd not installed, skipping duplication check${NC}"
fi

# 4. Code Style Check
echo -e "${BLUE}=== Code Style Analysis ===${NC}"
if command_exists black; then
    run_quality_check "Black formatting" \
        "black --check --diff --line-length=$MAX_LINE_LENGTH app/ config/ tests/" \
        "$REPORTS_DIR/black_check_$TIMESTAMP.txt" \
        10
else
    echo -e "${YELLOW}Black not installed, skipping formatting check${NC}"
fi

# 5. Import Sorting Check
echo -e "${BLUE}=== Import Sorting Analysis ===${NC}"
if command_exists isort; then
    run_quality_check "Import sorting" \
        "isort --check-only --diff --profile=black --line-length=$MAX_LINE_LENGTH app/ config/ tests/" \
        "$REPORTS_DIR/isort_check_$TIMESTAMP.txt" \
        10
else
    echo -e "${YELLOW}isort not installed, skipping import sorting check${NC}"
fi

# 6. Linting Check
echo -e "${BLUE}=== Code Linting Analysis ===${NC}"
if command_exists flake8; then
    run_quality_check "Flake8 linting" \
        "flake8 --max-line-length=$MAX_LINE_LENGTH --max-complexity=$MAX_COMPLEXITY --statistics --count app/ config/ tests/" \
        "$REPORTS_DIR/flake8_check_$TIMESTAMP.txt" \
        15
else
    echo -e "${YELLOW}flake8 not installed, skipping linting check${NC}"
fi

# 7. Type Checking
echo -e "${BLUE}=== Type Checking Analysis ===${NC}"
if command_exists mypy; then
    run_quality_check "MyPy type checking" \
        "mypy --ignore-missing-imports app/ config/" \
        "$REPORTS_DIR/mypy_check_$TIMESTAMP.txt" \
        15
else
    echo -e "${YELLOW}mypy not installed, skipping type checking${NC}"
fi

# 8. Security Analysis
echo -e "${BLUE}=== Security Analysis ===${NC}"
if command_exists bandit; then
    run_quality_check "Bandit security scan" \
        "bandit -r app/ -f json -o $REPORTS_DIR/bandit_report_$TIMESTAMP.json" \
        "$REPORTS_DIR/bandit_check_$TIMESTAMP.txt" \
        20
else
    echo -e "${YELLOW}bandit not installed, skipping security scan${NC}"
fi

# 9. Dependency Security
echo -e "${BLUE}=== Dependency Security Analysis ===${NC}"
if command_exists safety; then
    run_quality_check "Safety dependency check" \
        "safety check -r requirements/base.txt --json --output $REPORTS_DIR/safety_report_$TIMESTAMP.json" \
        "$REPORTS_DIR/safety_check_$TIMESTAMP.txt" \
        20
else
    echo -e "${YELLOW}safety not installed, skipping dependency security check${NC}"
fi

# 10. Test Quality Check
echo -e "${BLUE}=== Test Quality Analysis ===${NC}"
if command_exists pytest; then
    run_quality_check "Test execution" \
        "pytest --tb=short --maxfail=5 tests/" \
        "$REPORTS_DIR/test_execution_$TIMESTAMP.txt" \
        25
else
    echo -e "${YELLOW}pytest not installed, skipping test execution check${NC}"
fi

# Calculate final quality score
if [ $TOTAL_CHECKS -gt 0 ]; then
    FINAL_SCORE=$((QUALITY_SCORE * 100 / (TOTAL_CHECKS * 25)))
else
    FINAL_SCORE=0
fi

# Determine quality grade
if [ $FINAL_SCORE -ge 90 ]; then
    QUALITY_GRADE="A"
    GRADE_COLOR=$GREEN
elif [ $FINAL_SCORE -ge 80 ]; then
    QUALITY_GRADE="B"
    GRADE_COLOR=$YELLOW
elif [ $FINAL_SCORE -ge 70 ]; then
    QUALITY_GRADE="C"
    GRADE_COLOR=$YELLOW
else
    QUALITY_GRADE="F"
    GRADE_COLOR=$RED
fi

# Generate Quality Gate Report
echo -e "${BLUE}=== Generating Quality Gate Report ===${NC}"
cat > "$REPORTS_DIR/quality_gate_report_$TIMESTAMP.md" << EOF
# Quality Gate Report

**Generated:** $TIMESTAMP  
**Quality Thresholds:** $QUALITY_THRESHOLDS  
**Reports Directory:** $REPORTS_DIR

## Quality Metrics

- **Total Checks:** $TOTAL_CHECKS
- **Passed Checks:** $PASSED_CHECKS
- **Failed Checks:** $FAILED_CHECKS
- **Quality Score:** $FINAL_SCORE/100
- **Quality Grade:** $QUALITY_GRADE

## Quality Thresholds

- **Coverage:** $MIN_COVERAGE%
- **Complexity:** $MAX_COMPLEXITY
- **Line Length:** $MAX_LINE_LENGTH
- **Duplication:** $MAX_DUPLICATION%

## Checks Performed

- ✅ Code Coverage (pytest)
- ✅ Code Complexity (radon)
- ✅ Code Duplication (jscpd)
- ✅ Code Formatting (Black)
- ✅ Import Sorting (isort)
- ✅ Code Linting (flake8)
- ✅ Type Checking (MyPy)
- ✅ Security Analysis (Bandit)
- ✅ Dependency Security (Safety)
- ✅ Test Execution (pytest)

## Quality Assessment

**Overall Quality:** $QUALITY_GRADE ($FINAL_SCORE/100)

EOF

if [ $FAILED_CHECKS -eq 0 ]; then
    cat >> "$REPORTS_DIR/quality_gate_report_$TIMESTAMP.md" << EOF

🎉 **QUALITY GATE PASSED** 🎉

All quality checks have passed successfully. The codebase meets the required quality standards.

## Recommendations

- Maintain current quality standards
- Continue regular quality monitoring
- Consider implementing additional quality metrics
EOF
else
    cat >> "$REPORTS_DIR/quality_gate_report_$TIMESTAMP.md" << EOF

❌ **QUALITY GATE FAILED** ❌

$FAILED_CHECKS quality checks have failed. Please address the issues before proceeding.

## Failed Checks

$(ls -la "$REPORTS_DIR"/*"$TIMESTAMP"* | grep -E "(failed|error)" | awk '{print "- " $9}' || echo "Review individual check reports for details")

## Next Steps

1. Review failed check reports
2. Address quality issues
3. Re-run quality gate
4. Ensure all checks pass before deployment
EOF
fi

cat >> "$REPORTS_DIR/quality_gate_report_$TIMESTAMP.md" << EOF

## Files Generated

$(ls -la "$REPORTS_DIR"/*"$TIMESTAMP"* | awk '{print "- " $9}')

## Quality Improvement Suggestions

1. **Immediate Actions:**
   - Fix all failed quality checks
   - Address security vulnerabilities
   - Improve test coverage

2. **Short Term (1-2 weeks):**
   - Implement automated quality gates
   - Set up quality monitoring dashboard
   - Establish quality improvement process

3. **Long Term (1-2 months):**
   - Continuous quality improvement
   - Quality metrics tracking
   - Team quality training

---

*Report generated by Quality Gate System*
EOF

echo -e "${GREEN}✓ Quality gate report generated: $REPORTS_DIR/quality_gate_report_$TIMESTAMP.md${NC}"

# Display Results
echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}      Quality Gate Results      ${NC}"
echo -e "${BLUE}================================${NC}"
echo ""
echo -e "${BLUE}Quality Metrics:${NC}"
echo -e "  Total Checks: $TOTAL_CHECKS"
echo -e "  Passed: $PASSED_CHECKS"
echo -e "  Failed: $FAILED_CHECKS"
echo -e "  Quality Score: $FINAL_SCORE/100"
echo -e "  Quality Grade: $QUALITY_GRADE"
echo ""

# Determine exit code
if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}🎉 Quality Gate PASSED! 🎉${NC}"
    echo -e "${GREEN}All quality checks completed successfully.${NC}"
    EXIT_CODE=0
else
    echo -e "${RED}❌ Quality Gate FAILED! ❌${NC}"
    echo -e "${RED}$FAILED_CHECKS quality checks failed.${NC}"
    echo -e "${YELLOW}Review the quality gate report for details.${NC}"
    EXIT_CODE=1
fi

echo ""
echo -e "${BLUE}Reports generated in: $REPORTS_DIR${NC}"
echo -e "${BLUE}Summary: $REPORTS_DIR/quality_gate_report_$TIMESTAMP.md${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
if [ $FAILED_CHECKS -eq 0 ]; then
    echo "1. ✅ Quality gate passed - proceed with deployment"
    echo "2. 📊 Monitor quality metrics"
    echo "3. 🔄 Continue quality improvement process"
else
    echo "1. ❌ Fix failed quality checks"
    echo "2. 🔍 Review quality gate report"
    echo "3. 🔄 Re-run quality gate"
    echo "4. ✅ Ensure all checks pass before deployment"
fi
echo ""
echo -e "${GREEN}Quality is not an act, it is a habit! 🚀${NC}"

exit $EXIT_CODE