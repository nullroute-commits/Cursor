# CI/CD Pipeline Test Deployment

This document describes the test deployment of the CI/CD pipeline for the Cursor project.

## Overview

The pipeline implements a complete CI/CD workflow with the following stages:
- **Lint**: Code quality checks using Hadolint, Ruff, and ShellCheck
- **Test**: Python tests with pytest and coverage reporting
- **Build**: Multi-architecture Docker image builds with BuildX
- **Scan**: Security vulnerability scanning with Trivy
- **Deploy**: Container deployment testing

## Deployment Architecture

### Local Testing
```bash
# Validate deployment readiness
./validate-deployment.sh

# Test pipeline locally
./test-pipeline-local.sh

# Run individual stages
make lint    # Linting
make test    # Testing
make build   # Building
make scan    # Security scanning
make ci      # Full pipeline
```

### GitHub Actions Workflow

The pipeline automatically runs on:
- Push to `main` or `develop` branches
- Pull requests to `main`
- Manual workflow dispatch

#### Workflow Stages

1. **Lint Stage** (`lint` job)
   - Runs code quality checks
   - Uploads lint reports as artifacts

2. **Test Stage** (`test` job)
   - Executes Python tests with coverage
   - Generates JUnit XML reports
   - Publishes test results

3. **Build Stage** (`build` job)
   - Builds multi-arch Docker images (amd64, arm64)
   - Pushes to GitHub Container Registry
   - Generates build metadata

4. **Scan Stage** (`scan` job)
   - Performs security vulnerability scanning
   - Uploads SARIF results to GitHub Security tab
   - Generates security reports

5. **Deploy Test** (`deploy-test` job)
   - Tests container deployment
   - Validates image functionality
   - Runs on `main` branch only

6. **Summary** (`summary` job)
   - Aggregates all pipeline results
   - Downloads all artifacts
   - Generates comprehensive report

## Container Registry

Images are published to GitHub Container Registry:
- **Registry**: `ghcr.io`
- **Repository**: `nullroute-commits/cursor`
- **Tags**: 
  - `latest` (main branch)
  - `<branch-name>` (feature branches)
  - `<branch>-<sha>` (commit-specific)

## Configuration

### Environment Variables (.env)
```bash
REGISTRY=ghcr.io/nullroute-commits
IMAGE=cursor
TAG=latest
DOCKER_BUILDKIT=1
COVERAGE_THRESHOLD=80
```

### Docker Compose Profiles
- `lint`: Linting stage only
- `test`: Testing stage only
- `build`: Build stage only
- `scan`: Security scanning only
- `reports`: Reports server (port 8080)
- `all`: Complete pipeline

## Monitoring and Reporting

### GitHub Actions
- View workflow runs in the Actions tab
- Monitor build status and artifacts
- Review security scan results

### Artifacts Generated
- **Lint Reports**: Code quality analysis
- **Test Reports**: JUnit XML and coverage HTML
- **Build Reports**: Image metadata and tags
- **Security Reports**: Vulnerability scan results
- **Deployment Reports**: Container deployment status

### Reports Server
```bash
# Start local reports server
make reports

# Access at http://localhost:8080
# View coverage, test results, and scan reports
```

## Security Features

- **Multi-stage Docker builds** with non-root users
- **Vulnerability scanning** with Trivy
- **SARIF integration** with GitHub Security tab
- **Secrets management** via GitHub Secrets
- **Container image signing** (planned)

## Troubleshooting

### Local Issues
```bash
# Check environment
make validate

# Clean up containers
make clean

# Reset environment
make setup
```

### GitHub Actions Issues
- Check workflow logs in Actions tab
- Verify secrets are configured
- Ensure repository permissions allow package publishing

## Manual Deployment

For manual testing, use workflow dispatch:
1. Go to Actions tab in GitHub
2. Select "CI/CD Pipeline Test Deployment"
3. Click "Run workflow"
4. Choose stage: `all`, `lint`, `test`, `build`, or `scan`

## Success Criteria

The deployment is considered successful when:
- [x] All pipeline stages complete without errors
- [x] Container images are published to registry
- [x] Security scans pass vulnerability thresholds
- [x] Test coverage meets minimum requirements (80%)
- [x] Deployment test validates container functionality

## Next Steps

1. **Production Deployment**: Extend for production environments
2. **Staging Integration**: Add staging environment deployment
3. **Monitoring**: Integrate with monitoring and alerting systems
4. **Performance**: Optimize build times and caching
5. **Security**: Add image signing and attestation