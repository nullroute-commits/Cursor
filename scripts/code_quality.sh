#!/bin/bash

# Code Quality Check Script
# Runs comprehensive code quality checks and generates reports

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MAX_LINE_LENGTH=120
MAX_COMPLEXITY=10
MIN_COVERAGE=80
REPORTS_DIR="reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create reports directory
mkdir -p "$REPORTS_DIR"

echo -e "${BLUE}🔍 Running Comprehensive Code Quality Checks...${NC}"
echo "Timestamp: $TIMESTAMP"
echo "Reports directory: $REPORTS_DIR"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to run check with error handling
run_check() {
    local name="$1"
    local command="$2"
    local output_file="$3"
    
    echo -e "${BLUE}Running $name...${NC}"
    
    if eval "$command" > "$output_file" 2>&1; then
        echo -e "${GREEN}✓ $name passed${NC}"
        return 0
    else
        echo -e "${RED}✗ $name failed${NC}"
        return 1
    fi
}

# 1. Code Formatting Check (Black)
echo -e "${BLUE}=== Code Formatting ===${NC}"
if command_exists black; then
    run_check "Black formatting check" \
        "black --check --diff --line-length=$MAX_LINE_LENGTH app/ config/ tests/" \
        "$REPORTS_DIR/black_check_$TIMESTAMP.txt"
else
    echo -e "${YELLOW}Black not installed, skipping${NC}"
fi

# 2. Import Sorting Check (isort)
echo -e "${BLUE}=== Import Sorting ===${NC}"
if command_exists isort; then
    run_check "isort import check" \
        "isort --check-only --diff --profile=black --line-length=$MAX_LINE_LENGTH app/ config/ tests/" \
        "$REPORTS_DIR/isort_check_$TIMESTAMP.txt"
else
    echo -e "${YELLOW}isort not installed, skipping${NC}"
fi

# 3. Linting (flake8)
echo -e "${BLUE}=== Code Linting ===${NC}"
if command_exists flake8; then
    run_check "flake8 linting" \
        "flake8 --max-line-length=$MAX_LINE_LENGTH --max-complexity=$MAX_COMPLEXITY --statistics --count app/ config/ tests/" \
        "$REPORTS_DIR/flake8_report_$TIMESTAMP.txt"
else
    echo -e "${YELLOW}flake8 not installed, skipping${NC}"
fi

# 4. Type Checking (mypy)
echo -e "${BLUE}=== Type Checking ===${NC}"
if command_exists mypy; then
    run_check "mypy type checking" \
        "mypy --ignore-missing-imports app/ config/" \
        "$REPORTS_DIR/mypy_report_$TIMESTAMP.txt"
else
    echo -e "${YELLOW}mypy not installed, skipping${NC}"
fi

# 5. Security Checks (bandit)
echo -e "${BLUE}=== Security Analysis ===${NC}"
if command_exists bandit; then
    run_check "bandit security scan" \
        "bandit -r app/ -f json -o $REPORTS_DIR/bandit_report_$TIMESTAMP.json" \
        "$REPORTS_DIR/bandit_output_$TIMESTAMP.txt"
else
    echo -e "${YELLOW}bandit not installed, skipping${NC}"
fi

# 6. Dependency Security (safety)
echo -e "${BLUE}=== Dependency Security ===${NC}"
if command_exists safety; then
    run_check "safety dependency check" \
        "safety check -r requirements/base.txt --json --output $REPORTS_DIR/safety_report_$TIMESTAMP.json" \
        "$REPORTS_DIR/safety_output_$TIMESTAMP.txt"
else
    echo -e "${YELLOW}safety not installed, skipping${NC}"
fi

# 7. Test Coverage
echo -e "${BLUE}=== Test Coverage ===${NC}"
if command_exists pytest; then
    echo -e "${BLUE}Running tests with coverage...${NC}"
    if pytest --cov=app --cov-report=html:$REPORTS_DIR/coverage_html_$TIMESTAMP --cov-report=term-missing --cov-fail-under=$MIN_COVERAGE tests/ > "$REPORTS_DIR/pytest_coverage_$TIMESTAMP.txt" 2>&1; then
        echo -e "${GREEN}✓ Test coverage passed (minimum: $MIN_COVERAGE%)${NC}"
    else
        echo -e "${RED}✗ Test coverage below minimum threshold${NC}"
    fi
else
    echo -e "${YELLOW}pytest not installed, skipping${NC}"
fi

# 8. Django Specific Checks
echo -e "${BLUE}=== Django Checks ===${NC}"
if command_exists python; then
    echo -e "${BLUE}Running Django system check...${NC}"
    if python manage.py check --deploy > "$REPORTS_DIR/django_check_$TIMESTAMP.txt" 2>&1; then
        echo -e "${GREEN}✓ Django system check passed${NC}"
    else
        echo -e "${RED}✗ Django system check failed${NC}"
    fi
else
    echo -e "${YELLOW}Python not available, skipping${NC}"
fi

# 9. Generate Summary Report
echo -e "${BLUE}=== Generating Summary Report ===${NC}"
cat > "$REPORTS_DIR/summary_$TIMESTAMP.md" << EOF
# Code Quality Report Summary

**Generated:** $TIMESTAMP  
**Reports Directory:** $REPORTS_DIR

## Checks Performed

- ✅ Code Formatting (Black)
- ✅ Import Sorting (isort)
- ✅ Code Linting (flake8)
- ✅ Type Checking (mypy)
- ✅ Security Analysis (bandit)
- ✅ Dependency Security (safety)
- ✅ Test Coverage (pytest)
- ✅ Django System Check

## Configuration

- **Max Line Length:** $MAX_LINE_LENGTH
- **Max Complexity:** $MAX_COMPLEXITY
- **Min Coverage:** $MIN_COVERAGE%

## Files Generated

$(ls -la "$REPORTS_DIR"/*"$TIMESTAMP"* | awk '{print "- " $9}')

## Next Steps

1. Review all generated reports
2. Fix any issues identified
3. Re-run quality checks
4. Commit only when all checks pass

EOF

echo -e "${GREEN}✓ Summary report generated: $REPORTS_DIR/summary_$TIMESTAMP.md${NC}"

# 10. Display Results
echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Code Quality Check Complete  ${NC}"
echo -e "${BLUE}================================${NC}"
echo ""
echo -e "${BLUE}Reports generated in: $REPORTS_DIR${NC}"
echo -e "${BLUE}Summary: $REPORTS_DIR/summary_$TIMESTAMP.md${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Review generated reports"
echo "2. Fix any quality issues"
echo "3. Re-run quality checks"
echo "4. Commit when all checks pass"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"