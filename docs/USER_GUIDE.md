# 🚀 User Guide: Lightweight Alpine-Based CI/CD Pipeline

## 📋 Overview

This guide provides step-by-step instructions for using the Lightweight Alpine-Based CI/CD Pipeline. The pipeline builds multi-arch Docker images, runs linting, testing, vulnerability scanning and SBOM generation without Docker-in-Docker.

## 🎯 Quick Start

### Prerequisites
- Docker Desktop installed and running
- Docker Compose v2+ available
- Git client configured
- Terminal/command line access

### Environment Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd <your-repo-name>

# Copy environment template
cp .env.example .env

# Edit with your registry details
REGISTRY=ghcr.io/your-org
IMAGE=your-app
TAG=latest
```

### Run Complete Pipeline
```bash
# Setup development environment
make setup

# Run complete CI/CD pipeline
make ci
```

## 🔧 Pipeline Stages

### 1. 🔍 Lint Stage
**Purpose**: Code quality checks and standards enforcement

**Tools**:
- **Hadolint**: Dockerfile linting and best practices
- **Ruff**: Python code quality and formatting
- **ShellCheck**: Shell script validation

**Run Individually**:
```bash
make lint
```

**Output**: Linting results in terminal, errors will fail the pipeline

### 2. 🧪 Test Stage
**Purpose**: Automated testing and coverage reporting

**Tools**:
- **Pytest**: Python testing framework
- **Coverage**: Code coverage analysis
- **JUnit XML**: Test results for CI systems

**Run Individually**:
```bash
make test
```

**Output**: 
- Test results in terminal
- Coverage report in `reports/coverage/`
- JUnit XML in `reports/junit.xml`

### 3. 🏗️ Build Stage
**Purpose**: Multi-architecture Docker image building

**Tools**:
- **BuildKit**: Advanced Docker build engine
- **Buildx**: Multi-platform build support
- **Registry Push**: Automated image publishing

**Run Individually**:
```bash
make build
```

**Output**: Multi-arch images pushed to configured registry

### 4. 🔒 Scan Stage
**Purpose**: Security scanning and SBOM generation

**Tools**:
- **Docker Scout**: Vulnerability scanning
- **SBOM**: Software Bill of Materials
- **Security Gates**: Configurable CVE thresholds

**Run Individually**:
```bash
make scan
```

**Output**:
- Vulnerability report in `reports/vulnerabilities.json`
- SBOM in `reports/sbom.json`

## 📊 Reports and Outputs

### View Reports
```bash
# Start reports server
make reports

# Open in browser: http://localhost:8080
```

### Report Locations
- **Coverage Reports**: `reports/coverage/`
- **Test Results**: `reports/junit.xml`
- **Security Reports**: `reports/vulnerabilities.json`
- **SBOM**: `reports/sbom.json`

## 🛠️ Advanced Usage

### Custom Environment Variables
```bash
# Set custom registry
export REGISTRY=ghcr.io/my-org

# Set custom image name
export IMAGE=my-application

# Set custom tag
export TAG=v1.0.0

# Run pipeline with custom values
make ci
```

### Individual Stage Execution
```bash
# Run only linting
make lint

# Run only testing
make test

# Run only building
make build

# Run only scanning
make scan
```

### Docker Compose Direct Usage
```bash
# Run specific stage
docker compose -f ci/docker-compose.yml --profile lint up

# Run all stages
docker compose -f ci/docker-compose.yml --profile all up

# View logs
docker compose -f ci/docker-compose.yml logs -f
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Docker Not Running
```bash
# Check Docker status
docker --version
docker compose version

# Start Docker Desktop if needed
```

#### 2. Permission Issues
```bash
# Ensure proper file permissions
chmod +x ci/entrypoint.sh
chmod +x Makefile
```

#### 3. Environment Variables Missing
```bash
# Check environment file
cat .env

# Verify required variables
echo $REGISTRY
echo $IMAGE
echo $TAG
```

#### 4. Build Failures
```bash
# Check Dockerfile syntax
docker build -f ci/Dockerfile.lint .

# Verify base images
docker pull alpine:3.19
```

#### 5. Network Issues
```bash
# Check Docker network
docker network ls

# Restart Docker if needed
sudo systemctl restart docker
```

### Debug Mode
```bash
# Run with verbose output
docker compose -f ci/docker-compose.yml --profile lint up -v

# Check container logs
docker compose -f ci/docker-compose.yml logs lint
```

## 🔒 Security Configuration

### Vulnerability Thresholds
```bash
# Set security thresholds
export SCAN_FAIL_ON_HIGH=true
export SCAN_FAIL_ON_CRITICAL=true

# Run security scan
make scan
```

### Registry Authentication
```bash
# Login to registry
docker login ghcr.io

# Set credentials in .env
REGISTRY_USERNAME=your-username
REGISTRY_PASSWORD=your-token
```

## 📈 Performance Optimization

### Build Caching
```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1

# Use build cache
docker buildx build --cache-from type=local,src=/tmp/.buildx-cache .
```

### Parallel Execution
```bash
# Run stages in parallel (if supported)
docker compose -f ci/docker-compose.yml --profile all up --parallel
```

## 🔄 Integration with CI/CD Systems

### GitHub Actions
```yaml
name: CI/CD Pipeline
on: [push, pull_request]
jobs:
  pipeline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run CI/CD Pipeline
        run: |
          make setup
          make ci
```

### GitLab CI
```yaml
stages:
  - pipeline

ci-cd-pipeline:
  stage: pipeline
  image: docker:latest
  services:
    - docker:dind
  script:
    - make setup
    - make ci
```

### Jenkins Pipeline
```groovy
pipeline {
    agent any
    stages {
        stage('CI/CD Pipeline') {
            steps {
                sh 'make setup'
                sh 'make ci'
            }
        }
    }
}
```

## 📚 Additional Resources

### Documentation
- **README.md**: Project overview and team assignments
- **TEAM_ASSIGNMENTS.md**: Detailed team responsibilities
- **SPRINT_PLANNING.md**: Task breakdowns and acceptance criteria
- **TEAM_COLLABORATION.md**: Communication and collaboration processes

### Support
- **Issues**: Create GitHub issues for bugs or feature requests
- **Discussions**: Use GitHub discussions for questions
- **Team Channels**: Contact relevant team leads for specific issues

### Contributing
- **Development**: Follow the development workflow in TEAM_ASSIGNMENTS.md
- **Code Review**: All changes require code review
- **Testing**: Ensure all tests pass before submitting

## 🎉 Success Metrics

### Pipeline Performance
- **Build Time**: < 10 minutes for full pipeline
- **Success Rate**: > 95% successful executions
- **Resource Usage**: Minimal memory and CPU footprint

### Quality Metrics
- **Code Coverage**: > 80% test coverage
- **Security**: Zero high-severity CVEs
- **Standards**: All linting rules pass

### User Experience
- **Setup Time**: < 5 minutes for new users
- **Documentation**: Clear and actionable guides
- **Error Handling**: Helpful error messages and solutions

---

**Status**: ✅ **User Guide Complete**  
**Last Updated**: Today  
**Next Review**: After team validation  
**Success**: User experience optimized! 🎯**