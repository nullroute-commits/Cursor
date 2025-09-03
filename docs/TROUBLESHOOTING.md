# 🚨 Troubleshooting Guide: CI/CD Pipeline Issues

## 📋 Overview

This troubleshooting guide provides solutions for common issues encountered when using the Lightweight Alpine-Based CI/CD Pipeline. Each section includes problem descriptions, diagnostic steps, and resolution procedures.

## 🔍 Quick Diagnostic Commands

### 🚀 Pipeline Status Check
```bash
# Check pipeline status
make status

# Check Docker services
docker compose -f ci/docker-compose.yml ps

# Check environment configuration
cat .env

# Check file permissions
ls -la ci/
```

### 📊 Log Analysis
```bash
# View recent logs
docker compose -f ci/docker-compose.yml logs --tail=100

# View specific service logs
docker compose -f ci/docker-compose.yml logs lint
docker compose -f ci/docker-compose.yml logs test
docker compose -f ci/docker-compose.yml logs build
docker compose -f ci/docker-compose.yml logs scan

# Follow logs in real-time
docker compose -f ci/docker-compose.yml logs -f
```

## 🚨 Common Issues & Solutions

### 1. 🔴 Docker Not Running

#### Problem
```bash
❌ Error: Cannot connect to the Docker daemon
❌ Error: docker: command not found
```

#### Diagnosis
```bash
# Check Docker status
docker --version
docker compose version
systemctl status docker

# Check Docker daemon
ps aux | grep docker
```

#### Solutions
```bash
# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Start Docker Desktop (macOS/Windows)
# Open Docker Desktop application

# Verify Docker is running
docker run hello-world
```

#### Prevention
- Ensure Docker starts automatically on boot
- Check Docker Desktop is running before pipeline execution
- Verify Docker daemon has proper permissions

---

### 2. 🔴 Permission Denied Errors

#### Problem
```bash
❌ Error: permission denied
❌ Error: cannot create directory
❌ Error: cannot write to file
```

#### Diagnosis
```bash
# Check file permissions
ls -la ci/
ls -la ci/entrypoint.sh

# Check user permissions
whoami
id

# Check directory ownership
ls -ld ci/
```

#### Solutions
```bash
# Fix file permissions
chmod +x ci/entrypoint.sh
chmod +x Makefile

# Fix directory permissions
chmod 755 ci/
chmod 755 reports/

# Fix ownership (if needed)
sudo chown -R $USER:$USER ci/
sudo chown -R $USER:$USER reports/
```

#### Prevention
- Ensure proper file permissions are set
- Use consistent user accounts
- Check file ownership after git operations

---

### 3. 🔴 Environment Variables Missing

#### Problem
```bash
❌ Error: Build requires environment variable: REGISTRY
❌ Error: Required environment variable CI_STAGE is not set
```

#### Diagnosis
```bash
# Check environment file
ls -la .env
cat .env

# Check environment variables
echo $REGISTRY
echo $IMAGE
echo $TAG
echo $CI_STAGE

# Validate environment
make validate
```

#### Solutions
```bash
# Create environment file
cp .env.example .env

# Edit environment file
nano .env
# or
vim .env

# Set environment variables
export REGISTRY=ghcr.io/your-org
export IMAGE=your-app
export TAG=latest

# Verify environment
make validate
```

#### Prevention
- Always copy `.env.example` to `.env`
- Validate environment before running pipeline
- Use consistent environment variable names

---

### 4. 🔴 Docker Build Failures

#### Problem
```bash
❌ Error: failed to build Docker image
❌ Error: base image not found
❌ Error: build context not found
```

#### Diagnosis
```bash
# Check Dockerfile syntax
docker build -f ci/Dockerfile.lint . --no-cache

# Check base images
docker pull alpine:3.19
docker pull python:3.11-alpine

# Check build context
ls -la
pwd
```

#### Solutions
```bash
# Pull base images manually
docker pull alpine:3.19
docker pull python:3.11-alpine

# Clean Docker cache
docker system prune -a

# Rebuild with no cache
docker build -f ci/Dockerfile.lint . --no-cache

# Check Dockerfile syntax
bash -n ci/entrypoint.sh
```

#### Prevention
- Ensure base images are available
- Use specific image tags
- Clean Docker cache regularly
- Validate Dockerfile syntax

---

### 5. 🔴 Docker Compose Issues

#### Problem
```bash
❌ Error: service not found
❌ Error: profile not found
❌ Error: volume mount failed
```

#### Diagnosis
```bash
# Check Docker Compose file
docker compose -f ci/docker-compose.yml config

# Check service profiles
docker compose -f ci/docker-compose.yml --help

# Check volume mounts
docker volume ls
```

#### Solutions
```bash
# Use correct profile
docker compose -f ci/docker-compose.yml --profile lint up
docker compose -f ci/docker-compose.yml --profile all up

# Create missing directories
mkdir -p ci/reports
mkdir -p reports

# Fix volume permissions
sudo chown -R $USER:$USER reports/
```

#### Prevention
- Use correct service profiles
- Ensure directories exist before mounting
- Check Docker Compose syntax
- Validate volume permissions

---

### 6. 🔴 Network Connectivity Issues

#### Problem
```bash
❌ Error: connection refused
❌ Error: network unreachable
❌ Error: timeout exceeded
```

#### Diagnosis
```bash
# Check network configuration
docker network ls
docker network inspect ci_default

# Check service connectivity
docker compose -f ci/docker-compose.yml exec lint ping test
docker compose -f ci/docker-compose.yml exec test ping build

# Check external connectivity
ping 8.8.8.8
curl -I https://google.com
```

#### Solutions
```bash
# Restart Docker network
docker network prune
docker compose -f ci/docker-compose.yml down
docker compose -f ci/docker-compose.yml up -d

# Check firewall settings
sudo ufw status
sudo iptables -L

# Restart Docker service
sudo systemctl restart docker
```

#### Prevention
- Use consistent network configuration
- Check firewall rules
- Monitor network connectivity
- Use network debugging tools

---

### 7. 🔴 Resource Exhaustion

#### Problem
```bash
❌ Error: no space left on device
❌ Error: memory limit exceeded
❌ Error: CPU limit exceeded
```

#### Diagnosis
```bash
# Check disk space
df -h
du -sh ci/
du -sh reports/

# Check memory usage
free -h
docker stats

# Check Docker system usage
docker system df
```

#### Solutions
```bash
# Clean Docker system
docker system prune -a
docker volume prune
docker image prune -a

# Clean reports directory
rm -rf ci/reports/*
rm -rf reports/*

# Restart Docker service
sudo systemctl restart docker

# Check disk space
df -h
```

#### Prevention
- Monitor disk space regularly
- Clean old images and containers
- Set resource limits in Docker Compose
- Use multi-stage builds to reduce image size

---

### 8. 🔴 Security Scanning Failures

#### Problem
```bash
❌ Error: Docker Scout not found
❌ Error: vulnerability scan failed
❌ Error: SBOM generation failed
```

#### Diagnosis
```bash
# Check Docker Scout installation
which scout
scout --version

# Check Docker SBOM
docker sbom --help

# Check security tools
ls -la ci/Dockerfile.scan
```

#### Solutions
```bash
# Install Docker Scout manually
curl -L https://github.com/docker/scout-cli/releases/download/v1.4.0/scout_1.4.0_linux_amd64.tar.gz | \
    tar -xz -C /usr/local/bin/ scout

# Verify installation
scout --version

# Test SBOM generation
docker sbom --help

# Rebuild scan stage
docker build -f ci/Dockerfile.scan . --no-cache
```

#### Prevention
- Ensure security tools are properly installed
- Verify tool compatibility with Alpine Linux
- Test security scanning independently
- Keep security tools updated

---

### 9. 🔴 Test Execution Failures

#### Problem
```bash
❌ Error: pytest not found
❌ Error: coverage report failed
❌ Error: JUnit XML generation failed
```

#### Diagnosis
```bash
# Check Python environment
python3 --version
pip3 list | grep pytest

# Check test files
ls -la tests/
python3 -c "import pytest; print('pytest available')"

# Check coverage tools
python3 -c "import coverage; print('coverage available')"
```

#### Solutions
```bash
# Install Python dependencies
pip3 install pytest pytest-cov coverage junitparser

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test Python module
python3 -c "from pipeline import Pipeline; print('Module works')"

# Run tests manually
python3 -m pytest tests/ -v
```

#### Prevention
- Use virtual environments for Python development
- Install all required dependencies
- Test Python functionality independently
- Validate test configuration

---

### 10. 🔴 Registry Authentication Issues

#### Problem
```bash
❌ Error: authentication required
❌ Error: unauthorized access
❌ Error: push access denied
```

#### Diagnosis
```bash
# Check registry login
docker login ghcr.io
docker login docker.io

# Check credentials
echo $REGISTRY_USERNAME
echo $REGISTRY_PASSWORD

# Test registry access
docker pull hello-world
docker push hello-world:latest
```

#### Solutions
```bash
# Login to registry
docker login ghcr.io
docker login docker.io

# Set credentials in environment
export REGISTRY_USERNAME=your-username
export REGISTRY_PASSWORD=your-token

# Add to .env file
echo "REGISTRY_USERNAME=your-username" >> .env
echo "REGISTRY_PASSWORD=your-token" >> .env

# Test authentication
docker pull hello-world
```

#### Prevention
- Use proper registry authentication
- Store credentials securely
- Use service accounts with minimal permissions
- Monitor authentication attempts

---

## 🛠️ Advanced Troubleshooting

### 🔍 Debug Mode
```bash
# Enable verbose output
docker compose -f ci/docker-compose.yml --profile lint up -v

# Enable debug logging
export DEBUG=1
make lint

# Check container internals
docker compose -f ci/docker-compose.yml exec lint sh
docker compose -f ci/docker-compose.yml exec lint env
```

### 📊 Performance Analysis
```bash
# Monitor resource usage
docker stats

# Profile pipeline execution
time make ci

# Check build performance
docker build -f ci/Dockerfile.lint . --progress=plain

# Analyze image layers
docker history ci-lint:latest
```

### 🔧 Configuration Validation
```bash
# Validate Docker Compose
docker compose -f ci/docker-compose.yml config

# Validate environment
make validate

# Check file syntax
bash -n ci/entrypoint.sh
python3 -m py_compile pipeline/__init__.py

# Validate Dockerfiles
docker build -f ci/Dockerfile.lint . --dry-run
```

## 📋 Troubleshooting Checklist

### 🔍 Pre-Troubleshooting Steps
- [ ] Check pipeline status with `make status`
- [ ] Verify environment configuration with `make validate`
- [ ] Check Docker service status
- [ ] Review recent changes and commits
- [ ] Check system resources (disk, memory, CPU)

### 🚨 Issue Identification
- [ ] Read error messages carefully
- [ ] Check pipeline logs for context
- [ ] Identify which stage is failing
- [ ] Determine if issue is local or systemic
- [ ] Check if issue is reproducible

### 🛠️ Resolution Steps
- [ ] Apply appropriate solution from this guide
- [ ] Test resolution with minimal pipeline execution
- [ ] Verify fix resolves the original issue
- [ ] Check for any new issues introduced
- [ ] Document resolution for future reference

### 📊 Post-Resolution
- [ ] Run full pipeline to ensure stability
- [ ] Update documentation if needed
- [ ] Share solution with team
- [ ] Monitor for recurrence
- [ ] Update troubleshooting procedures

## 🚀 Getting Help

### 📞 Team Support
- **DevOps Issues**: @devops-team (Slack)
- **Security Issues**: @security-team (Slack)
- **QA Issues**: @qa-team (Slack)
- **Documentation Issues**: @tech-writing-team (Slack)
- **Code Issues**: @backend-team (Slack)

### 🆘 Emergency Escalation
- **Critical Pipeline Failure**: #ci-cd-pipeline-alerts (Slack)
- **Security Incident**: @security-officer (Slack)
- **Infrastructure Down**: @infra-lead (Slack)

### 📚 Additional Resources
- **Project Documentation**: README.md, TEAM_ASSIGNMENTS.md
- **Process Documentation**: TEAM_COLLABORATION.md
- **Security Guide**: docs/SECURITY_CONFIGURATION.md
- **User Guide**: docs/USER_GUIDE.md

---

## 🎉 Success Metrics

### 📊 Troubleshooting Performance
- **Resolution Time**: < 30 minutes for common issues
- **First-Time Fix Rate**: > 80% of issues resolved on first attempt
- **Documentation Coverage**: 100% of common issues documented
- **Team Knowledge**: All team members can resolve basic issues

### 🚀 Continuous Improvement
- **Issue Tracking**: All issues logged and categorized
- **Solution Updates**: Troubleshooting guide updated regularly
- **Team Training**: Regular troubleshooting workshops
- **Process Optimization**: Streamlined resolution procedures

---

**Status**: ✅ **Troubleshooting Guide Complete**  
**Created**: Today  
**Next Review**: After team validation  
**Success**: User support optimized! 🎯**