# CI/CD Pipeline Makefile
# Provides convenient targets for running the pipeline

.PHONY: help ci lint test build scan clean reports

# Default target
help:
	@echo "CI/CD Pipeline Commands:"
	@echo "  make ci      - Run complete pipeline (all stages)"
	@echo "  make lint    - Run linting stage only"
	@echo "  make test    - Run testing stage only"
	@echo "  make build   - Run build stage only"
	@echo "  make scan    - Run security scan stage only"
	@echo "  make reports - Start reports server on port 8080"
	@echo "  make clean   - Clean up containers and reports"
	@echo "  make help    - Show this help message"

# Run complete CI/CD pipeline
ci:
	@echo "🚀 Running complete CI/CD pipeline..."
	docker compose -f ci/docker-compose.yml --profile all up --abort-on-container-exit

# Run linting stage
lint:
	@echo "🔍 Running linting stage..."
	docker compose -f ci/docker-compose.yml --profile lint up --abort-on-container-exit

# Run testing stage
test:
	@echo "🧪 Running testing stage..."
	docker compose -f ci/docker-compose.yml --profile test up --abort-on-container-exit

# Run build stage
build:
	@echo "🏗️  Running build stage..."
	docker compose -f ci/docker-compose.yml --profile build up --abort-on-container-exit

# Run security scan stage
scan:
	@echo "🔒 Running security scan stage..."
	docker compose -f ci/docker-compose.yml --profile scan up --abort-on-container-exit

# Start reports server
reports:
	@echo "📊 Starting reports server on http://localhost:8080..."
	docker compose -f ci/docker-compose.yml --profile reports up -d

# Clean up containers and reports
clean:
	@echo "🧹 Cleaning up containers and reports..."
	docker compose -f ci/docker-compose.yml down --volumes --remove-orphans
	rm -rf ci/reports/*
	@echo "Cleanup complete!"

# Validate environment
validate:
	@echo "✅ Validating environment configuration..."
	@if [ ! -f .env ]; then \
		echo "❌ .env file not found. Please copy .env.example to .env and configure your values."; \
		exit 1; \
	fi
	@echo "✅ Environment configuration validated"

# Setup development environment
setup: validate
	@echo "🔧 Setting up development environment..."
	@if [ ! -d ci/reports ]; then mkdir -p ci/reports; fi
	@echo "✅ Development environment ready"

# Show pipeline status
status:
	@echo "📊 Pipeline Status:"
	@docker compose -f ci/docker-compose.yml ps