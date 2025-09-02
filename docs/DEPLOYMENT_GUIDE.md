# Django 5 Financial Management Application - Deployment Guide

This guide provides comprehensive documentation for deploying and using the Django 5 Multi-Architecture CI/CD Pipeline with RBAC and Audit Logging application.

## 🚀 Application Overview

This is a comprehensive financial management application built with Django 5, featuring:

- **Django 5.0.2** with Python 3.12.5
- **PostgreSQL 17.2** database with optimized configuration
- **SQLAlchemy 1.4.49** for advanced ORM capabilities
- **Memcached 1.6.22** for high-performance caching
- **RabbitMQ 3.12.8** for message queuing and async processing
- **RBAC System** for fine-grained access control
- **Audit Logging** for comprehensive activity tracking
- **Multi-architecture Docker support** (linux/amd64, linux/arm64)

## 📋 Prerequisites

- Docker 24.0.7+ with Docker Compose v2
- Git
- At least 4GB RAM and 10GB disk space

## 🔧 Quick Deployment

### 1. Clone and Setup

```bash
git clone https://github.com/nullroute-commits/Cursor.git
cd Cursor
```

### 2. Environment Configuration

The application uses multiple environment files for different configurations:

```bash
# Copy environment files from examples
cp .env.example .env
cp .env.app.example .env.app
cp .env.db.example .env.db
cp .env.cache.example .env.cache
cp .env.queue.example .env.queue
cp .env.security.example .env.security
cp .env.logging.example .env.logging
```

### 3. Start Infrastructure Services

Start the core infrastructure services first:

```bash
# Start PostgreSQL, Memcached, and RabbitMQ
docker compose -f docker-compose.base.yml up -d db memcached rabbitmq

# Start database admin tool
docker run -d --name adminer --network cursor_default \
  -e ADMINER_DEFAULT_SERVER=cursor-db-1 \
  -p 8080:8080 adminer:4.8.1

# Start email testing tool
docker run -d --name mailhog --network cursor_default \
  -p 1025:1025 -p 8025:8025 mailhog/mailhog:v1.0.1
```

### 4. Verify Services

Check that all services are running:

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Expected output:
```
NAMES                STATUS                     PORTS
mailhog              Up X minutes               0.0.0.0:1025->1025/tcp, 0.0.0.0:8025->8025/tcp
adminer              Up X minutes               0.0.0.0:8080->8080/tcp
cursor-rabbitmq-1    Up X minutes (healthy)     0.0.0.0:15672->15672/tcp
cursor-memcached-1   Up X minutes (healthy)     11211/tcp
cursor-db-1          Up X minutes (healthy)     5432/tcp
```

## 🌐 Available Services

Once deployed, the following services are available:

### 1. Database Administration (Adminer)
- **URL**: http://localhost:8080
- **Purpose**: PostgreSQL database management interface
- **Credentials**: 
  - System: PostgreSQL
  - Server: cursor-db-1 (or container IP: 172.18.0.3)
  - Username: postgres
  - Password: postgres
  - Database: django_app_dev

![Adminer Login Interface](https://github.com/user-attachments/assets/35345c9c-11ae-44b0-a5f1-ea72f15fcc84)

### 2. Message Queue Management (RabbitMQ)
- **URL**: http://localhost:15672
- **Purpose**: RabbitMQ management interface for monitoring queues and messages
- **Credentials**: guest/guest

![RabbitMQ Management Interface](https://github.com/user-attachments/assets/071773c5-2430-4d36-827f-a7ffda156b80)

### 3. Email Testing (Mailhog)
- **URL**: http://localhost:8025
- **Purpose**: Email testing and debugging tool
- **SMTP**: localhost:1025 for application email testing

### 4. Django Application (When Built)
- **URL**: http://localhost:8000
- **Purpose**: Main financial management application
- **Admin Panel**: http://localhost:8000/admin

## 🏗️ Financial Application Features

This application provides comprehensive financial management capabilities:

### Core Modules

#### 📊 Dashboard and Analytics
- Real-time financial overview
- Trends analysis and visualization
- Cash flow monitoring
- Budget performance tracking

#### 💰 Account Management
- Multiple account types support
- Account creation, editing, and deletion
- Transaction history per account
- Account balance tracking

#### 💸 Transaction Management
- Transaction creation and categorization
- Bulk transaction editing
- Transaction reconciliation
- Advanced search and filtering

#### 🏷️ Category and Tag System
- Hierarchical category structure
- Custom tagging system
- Category-based reporting
- Tag-based analytics

#### 📈 Budget Management
- Budget creation and monitoring
- Budget performance analysis
- Variance tracking
- Alert system for budget overruns

#### 📊 Reporting and Analytics
- Customizable reports
- Scheduled report generation
- Export capabilities (CSV, PDF)
- Advanced analytics dashboard

#### 🔗 Data Import/Export
- CSV file import
- Template download
- Bulk data processing
- Import validation and error handling

#### 🔐 Security and RBAC
- Role-based access control
- User permission management
- Audit logging for all activities
- Session management

### API Endpoints

The application provides RESTful API endpoints for:
- `/financial/api/accounts/` - Account management
- `/financial/api/transactions/` - Transaction operations
- `/financial/api/categories/` - Category management
- `/financial/api/budgets/` - Budget operations
- `/financial/api/analytics/` - Analytics data
- `/financial/api/webhooks/` - Webhook management

## 🔧 Configuration Management

### Environment Variables

The application uses multiple environment files for different aspects:

- **.env.app**: Application-specific settings
- **.env.db**: Database configuration
- **.env.cache**: Memcached settings
- **.env.queue**: RabbitMQ configuration
- **.env.security**: Security-related settings
- **.env.logging**: Logging configuration

### Database Configuration

PostgreSQL is optimized with the following settings:
- Max connections: 100
- Shared buffers: 256MB
- Work memory: 4MB
- Effective cache size: 1GB

### Caching Strategy

Memcached configuration:
- Memory allocation: 64MB
- Max connections: 1024
- Worker threads: 4

### Message Queue Setup

RabbitMQ configuration:
- Default exchange: app.topic
- Default queue: app.tasks
- Max priority: 10
- Prefetch count: 10

## 📊 Monitoring and Health Checks

### Health Check Endpoints

- Database: PostgreSQL health check every 30s
- Cache: Memcached status monitoring
- Queue: RabbitMQ management monitoring
- Application: Django health endpoint at `/health/`

### Logging

Comprehensive logging system:
- Application logs: `/app/logs/django.log`
- Error logs: `/app/logs/error.log`
- Audit logs: `/app/logs/audit.log`
- Log rotation: 5 files, 10MB each

## 🔐 Security Features

### Authentication and Authorization
- Django's built-in authentication system
- Role-based access control (RBAC)
- Session management
- Password policies

### Security Headers
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Content-Security-Policy configuration
- CSRF protection

### Audit Logging
- All user actions logged
- Model change tracking
- Request/response logging
- Sensitive data sanitization

## 🛠️ Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Check database status
   docker logs cursor-db-1
   
   # Test connection from adminer using container IP
   docker inspect cursor-db-1 | grep IPAddress
   ```

2. **Service Discovery Issues**
   ```bash
   # Check Docker network
   docker network ls
   docker network inspect cursor_default
   ```

3. **Port Conflicts**
   ```bash
   # Check port usage
   netstat -tulpn | grep :8080
   netstat -tulpn | grep :15672
   ```

### Logs and Debugging

```bash
# View all service logs
docker compose -f docker-compose.base.yml logs -f

# View specific service logs
docker logs cursor-db-1
docker logs cursor-rabbitmq-1
docker logs cursor-memcached-1
```

## 📚 Additional Resources

### Development

For development setup:
```bash
./scripts/start-dev.sh
```

### Testing

For running tests:
```bash
./scripts/start-test.sh
```

### Production Deployment

For production deployment:
```bash
./scripts/start-prod.sh
```

## 🤝 Support and Contributing

- **Documentation**: See the `docs/` directory for detailed documentation
- **Issues**: Report issues on GitHub
- **Contributing**: Follow the development workflow in CONTRIBUTING.md

---

**Last updated**: 2025-01-27 by deployment automation
**Version**: 1.0.0
**Environment**: Development/Staging