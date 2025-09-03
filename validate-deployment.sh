#!/bin/bash
set -euo pipefail

# Pipeline Deployment Validation
# Validates that all required files and configurations are ready for CI/CD deployment

echo "🔍 Validating CI/CD Pipeline Deployment Readiness"
echo "================================================"

validate_file() {
    local file="$1"
    local description="$2"
    
    if [ -f "$file" ]; then
        echo "✅ $description: $file"
        return 0
    else
        echo "❌ Missing $description: $file"
        return 1
    fi
}

validate_directory() {
    local dir="$1"
    local description="$2"
    
    if [ -d "$dir" ]; then
        echo "✅ $description: $dir"
        return 0
    else
        echo "❌ Missing $description: $dir"
        return 1
    fi
}

validation_errors=0

echo "📋 Core Configuration Files:"
validate_file ".env" "Environment configuration" || ((validation_errors++))
validate_file "Makefile" "Pipeline automation" || ((validation_errors++))
validate_file "Dockerfile" "Main container definition" || ((validation_errors++))
validate_file "pyproject.toml" "Python project configuration" || ((validation_errors++))
validate_file "requirements.txt" "Python dependencies" || ((validation_errors++))

echo ""
echo "📋 CI/CD Infrastructure:"
validate_directory "ci" "CI/CD configuration directory" || ((validation_errors++))
validate_file "ci/docker-compose.yml" "Docker Compose configuration" || ((validation_errors++))
validate_file "ci/entrypoint.sh" "Pipeline entrypoint script" || ((validation_errors++))
validate_file "ci/Dockerfile.lint" "Lint stage Dockerfile" || ((validation_errors++))
validate_file "ci/Dockerfile.test" "Test stage Dockerfile" || ((validation_errors++))
validate_file "ci/Dockerfile.build" "Build stage Dockerfile" || ((validation_errors++))
validate_file "ci/Dockerfile.scan" "Scan stage Dockerfile" || ((validation_errors++))

echo ""
echo "📋 GitHub Actions:"
validate_directory ".github/workflows" "GitHub Actions directory" || ((validation_errors++))
validate_file ".github/workflows/ci-cd-test.yml" "CI/CD workflow definition" || ((validation_errors++))

echo ""
echo "📋 Application Code:"
validate_directory "pipeline" "Pipeline module directory" || ((validation_errors++))
validate_file "pipeline/__init__.py" "Pipeline module" || ((validation_errors++))
validate_directory "tests" "Tests directory" || ((validation_errors++))
validate_file "tests/test_pipeline.py" "Pipeline tests" || ((validation_errors++))

echo ""
echo "📋 Deployment Configuration:"
if grep -q "REGISTRY=ghcr.io" .env; then
    echo "✅ Container registry configured"
else
    echo "❌ Container registry not properly configured"
    ((validation_errors++))
fi

if grep -q "IMAGE=" .env; then
    echo "✅ Image name configured"
else
    echo "❌ Image name not configured"
    ((validation_errors++))
fi

echo ""
echo "📋 Pipeline Execution Test:"
if [ -x "test-pipeline-local.sh" ]; then
    echo "✅ Local test script available and executable"
else
    echo "❌ Local test script not executable"
    ((validation_errors++))
fi

echo ""
echo "================================================"

if [ $validation_errors -eq 0 ]; then
    echo "🎉 All validations passed! Pipeline is ready for deployment."
    echo ""
    echo "Next steps:"
    echo "1. Commit changes to repository"
    echo "2. Push to GitHub to trigger CI/CD pipeline"
    echo "3. Monitor GitHub Actions for pipeline execution"
    echo "4. Check GitHub Container Registry for published images"
    echo ""
    exit 0
else
    echo "❌ Found $validation_errors validation error(s). Please fix before deployment."
    echo ""
    exit 1
fi