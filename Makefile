# Financial Analytics Platform Makefile
# Comprehensive automation for development, testing, and deployment

.PHONY: help setup dev test ci clean build up down logs restart status health

# =============================================================================
# VARIABLES
# =============================================================================
COMPOSE_FILE := docker-compose.yml
ENV_FILE := .env
PYTHON := python3
PIP := pip3

# =============================================================================
# HELP
# =============================================================================
help:
	@echo "🚀 Financial Analytics Platform - Available Commands"
	@echo "=================================================="
	@echo ""
	@echo "📋 Setup & Configuration:"
	@echo "  make setup          - Set up development environment"
	@echo "  make env            - Create environment file from template"
	@echo "  make build          - Build all Docker images"
	@echo ""
	@echo "🐳 Docker Operations:"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View service logs"
	@echo "  make status         - Show service status"
	@echo "  make health         - Check service health"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  make test           - Run test suite"
	@echo "  make test-unit      - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-e2e       - Run end-to-end tests only"
	@echo "  make lint           - Run code linting"
	@echo "  make format         - Format code with black"
	@echo "  make ci             - Run complete CI pipeline"
	@echo ""
	@echo "🔧 Development:"
	@echo "  make dev            - Start development environment"
	@echo "  make shell          - Open shell in backend container"
	@echo "  make db-shell       - Open PostgreSQL shell"
	@echo "  make migrate        - Run database migrations"
	@echo "  make seed           - Seed database with sample data"
	@echo ""
	@echo "📊 Monitoring:"
	@echo "  make prometheus     - Open Prometheus UI"
	@echo "  make grafana        - Open Grafana UI"
	@echo "  make alertmanager   - Open Alertmanager UI"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  make clean          - Clean up containers and volumes"
	@echo "  make prune          - Remove unused Docker resources"
	@echo "  make backup         - Backup database"
	@echo "  make restore        - Restore database from backup"
	@echo ""

# =============================================================================
# SETUP & CONFIGURATION
# =============================================================================
setup: env build
	@echo "🚀 Setting up Financial Analytics Platform..."
	@echo "✅ Environment configured"
	@echo "✅ Docker images built"
	@echo "✅ Ready to start services with 'make up'"

env:
	@echo "🔧 Creating environment file..."
	@if [ ! -f $(ENV_FILE) ]; then \
		cp .env.example $(ENV_FILE); \
		echo "✅ Environment file created from template"; \
		echo "⚠️  Please edit $(ENV_FILE) with your configuration"; \
	else \
		echo "✅ Environment file already exists"; \
	fi

build:
	@echo "🏗️ Building Docker images..."
	docker compose -f $(COMPOSE_FILE) build --no-cache
	@echo "✅ All images built successfully"

# =============================================================================
# DOCKER OPERATIONS
# =============================================================================
up:
	@echo "🚀 Starting Financial Analytics Platform..."
	docker compose -f $(COMPOSE_FILE) up -d
	@echo "✅ Services started"
	@echo "🌐 Access points:"
	@echo "   - API: http://localhost:8000"
	@echo "   - UI: http://localhost:8080"
	@echo "   - Database: localhost:5432"
	@echo "   - SMTP: http://localhost:1080"
	@echo "   - Prometheus: http://localhost:9090"
	@echo "   - Grafana: http://localhost:3000"

down:
	@echo "🛑 Stopping services..."
	docker compose -f $(COMPOSE_FILE) down
	@echo "✅ Services stopped"

restart:
	@echo "🔄 Restarting services..."
	docker compose -f $(COMPOSE_FILE) restart
	@echo "✅ Services restarted"

logs:
	@echo "📋 Viewing service logs..."
	docker compose -f $(COMPOSE_FILE) logs -f

status:
	@echo "📊 Service status:"
	docker compose -f $(COMPOSE_FILE) ps

health:
	@echo "🏥 Checking service health..."
	@echo "API Health:"
	@curl -f http://localhost:8000/health || echo "❌ API not healthy"
	@echo "UI Health:"
	@curl -f http://localhost:8080/health || echo "❌ UI not healthy"
	@echo "Database Health:"
	@docker compose -f $(COMPOSE_FILE) exec -T db pg_isready -U finance || echo "❌ Database not healthy"

# =============================================================================
# TESTING & QUALITY
# =============================================================================
test: test-unit test-integration
	@echo "✅ All tests completed"

test-unit:
	@echo "🧪 Running unit tests..."
	docker compose -f $(COMPOSE_FILE) exec -T api pytest tests/unit/ -v --cov=src --cov-report=term-missing

test-integration:
	@echo "🔗 Running integration tests..."
	docker compose -f $(COMPOSE_FILE) exec -T api pytest tests/integration/ -v --cov=src --cov-report=term-missing

test-e2e:
	@echo "🌐 Running end-to-end tests..."
	docker compose -f $(COMPOSE_FILE) exec -T api pytest tests/e2e/ -v --cov=src --cov-report=term-missing

lint:
	@echo "🔍 Running code linting..."
	docker compose -f $(COMPOSE_FILE) exec -T api ruff check src/ tests/
	@echo "✅ Linting completed"

format:
	@echo "🎨 Formatting code..."
	docker compose -f $(COMPOSE_FILE) exec -T api black src/ tests/
	docker compose -f $(COMPOSE_FILE) exec -T api isort src/ tests/
	@echo "✅ Code formatting completed"

ci: lint test
	@echo "🔍 Running security scan..."
	docker compose -f $(COMPOSE_FILE) exec -T api bandit -r src/
	@echo "🔒 Running dependency check..."
	docker compose -f $(COMPOSE_FILE) exec -T api safety check
	@echo "✅ CI pipeline completed"

# =============================================================================
# DEVELOPMENT
# =============================================================================
dev: up
	@echo "🔧 Development environment started"
	@echo "📝 Services are running with hot reload enabled"
	@echo "🔄 Code changes will automatically restart services"

shell:
	@echo "🐚 Opening shell in backend container..."
	docker compose -f $(COMPOSE_FILE) exec api /bin/bash

db-shell:
	@echo "🗄️ Opening PostgreSQL shell..."
	docker compose -f $(COMPOSE_FILE) exec db psql -U finance -d finance

migrate:
	@echo "🔄 Running database migrations..."
	docker compose -f $(COMPOSE_FILE) exec -T api alembic upgrade head
	@echo "✅ Migrations completed"

seed:
	@echo "🌱 Seeding database with sample data..."
	docker compose -f $(COMPOSE_FILE) exec -T api python -m scripts.seed_data
	@echo "✅ Database seeded"

# =============================================================================
# MONITORING
# =============================================================================
prometheus:
	@echo "📊 Opening Prometheus UI..."
	@if command -v xdg-open > /dev/null; then \
		xdg-open http://localhost:9090; \
	elif command -v open > /dev/null; then \
		open http://localhost:9090; \
	else \
		echo "🌐 Prometheus UI: http://localhost:9090"; \
	fi

grafana:
	@echo "📈 Opening Grafana UI..."
	@if command -v xdg-open > /dev/null; then \
		xdg-open http://localhost:3000; \
	elif command -v open > /dev/null; then \
		open http://localhost:3000; \
	else \
		echo "🌐 Grafana UI: http://localhost:3000"; \
	fi

alertmanager:
	@echo "🚨 Opening Alertmanager UI..."
	@if command -v xdg-open > /dev/null; then \
		xdg-open http://localhost:9093; \
	elif command -v open > /dev/null; then \
		open http://localhost:9093; \
	else \
		echo "🌐 Alertmanager UI: http://localhost:9093"; \
	fi

# =============================================================================
# MAINTENANCE
# =============================================================================
clean:
	@echo "🧹 Cleaning up containers and volumes..."
	docker compose -f $(COMPOSE_FILE) down -v
	docker system prune -f
	@echo "✅ Cleanup completed"

prune:
	@echo "🗑️ Removing unused Docker resources..."
	docker system prune -a -f
	@echo "✅ Pruning completed"

backup:
	@echo "💾 Creating database backup..."
	@mkdir -p backups
	docker compose -f $(COMPOSE_FILE) exec -T db pg_dump -U finance finance > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup created in backups/ directory"

restore:
	@echo "📥 Restoring database from backup..."
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "❌ Please specify backup file: make restore BACKUP_FILE=backups/backup_YYYYMMDD_HHMMSS.sql"; \
		exit 1; \
	fi
	docker compose -f $(COMPOSE_FILE) exec -T db psql -U finance -d finance < $(BACKUP_FILE)
	@echo "✅ Database restored from $(BACKUP_FILE)"

# =============================================================================
# UTILITIES
# =============================================================================
check-deps:
	@echo "🔍 Checking system dependencies..."
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed"; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed"; exit 1; }
	@echo "✅ All dependencies are available"

version:
	@echo "📋 Financial Analytics Platform Information:"
	@echo "   - Docker: $(shell docker --version)"
	@echo "   - Docker Compose: $(shell docker-compose --version)"
	@echo "   - Python: $(shell python3 --version)"
	@echo "   - Platform: $(shell uname -s) $(shell uname -m)"

# =============================================================================
# SPRINT-SPECIFIC COMMANDS
# =============================================================================
sprint1: setup
	@echo "🚀 Sprint 1: Multitenancy & RBAC"
	@echo "📋 Goals: Setup multitenancy schema, implement RBAC middleware"
	@echo "✅ Foundation ready for Sprint 1 development"

sprint2: up
	@echo "🚀 Sprint 2: Ingestion Adapters"
	@echo "📋 Goals: Build ingestion adapters for CHASE/DISCOVER/CAPITALONE"
	@echo "✅ Services ready for Sprint 2 development"

sprint3: up
	@echo "🚀 Sprint 3: Plaid Integration"
	@echo "📋 Goals: Integrate Plaid webhook (FOSS client)"
	@echo "✅ Services ready for Sprint 3 development"

sprint4: up
	@echo "🚀 Sprint 4: Analytics Engine"
	@echo "📋 Goals: Develop analytics engine"
	@echo "✅ Services ready for Sprint 4 development"

sprint5: up
	@echo "🚀 Sprint 5: Monitoring & Alerts"
	@echo "📋 Goals: Add monitoring & email alerts"
	@echo "✅ Services ready for Sprint 5 development"

sprint6: up
	@echo "🚀 Sprint 6: Frontend Dashboard"
	@echo "📋 Goals: Front-end dashboard"
	@echo "✅ Services ready for Sprint 6 development"

# =============================================================================
# PRODUCTION COMMANDS
# =============================================================================
prod-build:
	@echo "🏗️ Building production images..."
	docker compose -f $(COMPOSE_FILE) build --target production
	@echo "✅ Production images built"

prod-up:
	@echo "🚀 Starting production services..."
	ENVIRONMENT=production docker compose -f $(COMPOSE_FILE) up -d
	@echo "✅ Production services started"

prod-down:
	@echo "🛑 Stopping production services..."
	ENVIRONMENT=production docker compose -f $(COMPOSE_FILE) down
	@echo "✅ Production services stopped"

# =============================================================================
# DEFAULT TARGET
# =============================================================================
.DEFAULT_GOAL := help