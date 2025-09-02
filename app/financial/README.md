# Financial Management Application

A comprehensive financial management system built on Django 5 with advanced features for personal and business financial tracking, analysis, and reporting.

## 🚀 Features

### Core Financial Management
- **Account Management**: Multiple account types (checking, savings, credit cards, investments)
- **Transaction Tracking**: Comprehensive transaction management with categorization and tagging
- **Budget Planning**: Multi-period budget planning and variance analysis
- **Category Management**: Hierarchical category system with custom colors and icons
- **Tag System**: Flexible tagging system for transaction organization

### Data Import & Processing
- **Multi-Format Support**: CSV, Excel (XLSX/XLS), and PDF file processing
- **Intelligent Parsing**: Automatic column mapping and data validation
- **Background Processing**: Asynchronous file processing with progress tracking
- **Data Enrichment**: AI-powered transaction categorization and smart suggestions
- **Duplicate Detection**: Automatic duplicate transaction identification

### Analytics & Reporting
- **Financial Metrics**: Income, expenses, savings rate, expense ratios
- **Trend Analysis**: Monthly trends, category analysis, spending patterns
- **Cash Flow Analysis**: Operating, investing, and financing activities
- **Budget Performance**: Variance analysis and threshold alerts
- **Forecasting**: Expense forecasting based on historical data

### Advanced Features
- **Webhook System**: Event-driven external integrations
- **Role-Based Access Control**: Granular permissions for financial data
- **Audit Logging**: Comprehensive activity tracking and compliance
- **Configuration Management**: Web-based system configuration
- **Multi-Currency Support**: International currency handling

### Security & Compliance
- **LDAP/RADIUS Integration**: Enterprise authentication support
- **Data Encryption**: Secure storage and transmission
- **Access Controls**: User-level data isolation
- **Audit Trails**: Complete change history and compliance reporting

## 🏗️ Architecture

### System Components
```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Presentation Layer                            │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │   Dashboard │  │  Analytics  │  │   Reports   │  │  Settings   │   │
│  │   Views     │  │   Views     │  │    Views    │  │    Views    │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────┐
│                         Application Layer                               │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ Financial   │  │   File      │  │  Analytics  │  │  Webhook    │   │
│  │   Models    │  │ Processor   │  │   Engine    │  │  Service    │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────┐
│                            Data Layer                                  │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ PostgreSQL  │  │  Memcached  │  │  RabbitMQ   │  │   Redis     │   │
│  │  Database   │  │    Cache    │  │   Queue     │  │   Cache     │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Models
- **Account**: Financial accounts with balances and metadata
- **Transaction**: Individual financial transactions with categorization
- **Category**: Hierarchical transaction categories
- **Tag**: Custom transaction tags
- **Budget**: Budget planning and tracking
- **ImportHistory**: File import tracking and status
- **Webhook**: External integration configuration

### Services
- **FileProcessor**: Handles CSV, Excel, and PDF file processing
- **AnalyticsEngine**: Financial calculations and trend analysis
- **WebhookService**: Event publishing and delivery management
- **ConfigurationManager**: System configuration management

## 🛠️ Installation

### Prerequisites
- Python 3.12+
- Django 5.0+
- PostgreSQL 17+
- Redis (for background processing)
- RabbitMQ (for message queuing)

### Setup
1. **Install Dependencies**
   ```bash
   pip install -r requirements/financial.txt
   ```

2. **Add to Django Settings**
   ```python
   INSTALLED_APPS = [
       # ... other apps
       'app.financial',
   ]
   ```

3. **Run Migrations**
   ```bash
   python manage.py makemigrations financial
   python manage.py migrate
   ```

4. **Create Permissions**
   ```python
   python manage.py shell
   >>> from app.financial.permissions import FinancialPermissionManager
   >>> FinancialPermissionManager.create_financial_permissions()
   >>> FinancialPermissionManager.create_financial_roles()
   ```

## 📊 Usage

### Dashboard
Access the main dashboard at `/financial/` to view:
- Account balances and summaries
- Recent transactions
- Budget performance
- Financial metrics

### Account Management
- **Create Accounts**: `/financial/accounts/create/`
- **View Accounts**: `/financial/accounts/`
- **Manage Transactions**: `/financial/accounts/{id}/transactions/`

### Data Import
1. **Upload Files**: `/financial/import/upload/`
2. **Supported Formats**: CSV, Excel (XLSX/XLS), PDF
3. **Column Mapping**: Automatic or manual column mapping
4. **Processing**: Background processing with progress tracking

### Analytics
- **Overview**: `/financial/analytics/`
- **Trends**: `/financial/analytics/trends/`
- **Cash Flow**: `/financial/analytics/cash-flow/`
- **Budget Analysis**: `/financial/analytics/budget-analysis/`

### Configuration
- **System Settings**: `/financial/config/`
- **Security**: `/financial/config/security/`
- **Financial**: `/financial/config/financial/`
- **Import**: `/financial/config/import/`

## 🔧 Configuration

### Environment Variables
```bash
# File Processing
MAX_FILE_SIZE=52428800  # 50MB in bytes
ALLOWED_FILE_TYPES=csv,xlsx,xls,pdf

# Webhook Settings
WEBHOOK_TIMEOUT=30
MAX_RETRY_ATTEMPTS=3

# Analytics
CACHE_TTL=3600
QUERY_OPTIMIZATION=true
```

### Django Settings
```python
# Financial App Settings
FINANCIAL_SETTINGS = {
    'DEFAULT_CURRENCY': 'USD',
    'AUTO_CATEGORIZATION': True,
    'BUDGET_ALERT_THRESHOLD': 80,
    'RETENTION_PERIOD_MONTHS': 84,
}

# File Upload Settings
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
MAX_FILE_SIZE = 52428800  # 50MB

# Cache Settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

## 🔐 Security

### Authentication
- **Local Accounts**: Django's built-in user authentication
- **LDAP Integration**: Enterprise directory integration
- **RADIUS Support**: Network authentication
- **Two-Factor Authentication**: Optional 2FA requirement

### Permissions
- **Role-Based Access Control**: Predefined financial roles
- **Data Isolation**: User-level data separation
- **Audit Logging**: Complete activity tracking
- **Permission Decorators**: Easy permission enforcement

### Data Protection
- **Input Validation**: Comprehensive data validation
- **SQL Injection Protection**: Django ORM security
- **XSS Prevention**: Template auto-escaping
- **CSRF Protection**: Cross-site request forgery prevention

## 📈 Analytics & Reporting

### Financial Metrics
- **Income Analysis**: Total income, monthly averages, growth rates
- **Expense Tracking**: Category breakdown, spending patterns, trends
- **Savings Rate**: Net income percentage, savings goals
- **Budget Variance**: Planned vs. actual spending analysis

### Trend Analysis
- **Monthly Trends**: Income and expense patterns over time
- **Category Analysis**: Spending by category with trends
- **Seasonal Patterns**: Identify recurring spending patterns
- **Forecasting**: Predict future expenses based on history

### Cash Flow
- **Operating Activities**: Income and expenses
- **Investing Activities**: Asset purchases and sales
- **Financing Activities**: Loans and transfers
- **Liquidity Ratios**: Current ratio, quick ratio

## 🔗 API Integration

### RESTful Endpoints
```python
# Accounts
GET    /financial/api/accounts/
POST   /financial/api/accounts/
GET    /financial/api/accounts/{id}/
PUT    /financial/api/accounts/{id}/
DELETE /financial/api/accounts/{id}/

# Transactions
GET    /financial/api/transactions/
POST   /financial/api/transactions/
GET    /financial/api/transactions/{id}/
PUT    /financial/api/transactions/{id}/
DELETE /financial/api/transactions/{id}/

# Analytics
GET    /financial/api/analytics/
GET    /financial/api/analytics/trends/
GET    /financial/api/analytics/cash-flow/
```

### Webhook Events
- `transaction.created` - New transaction created
- `transaction.updated` - Transaction modified
- `transaction.deleted` - Transaction removed
- `account.balance_changed` - Account balance updated
- `budget.threshold_exceeded` - Budget limit exceeded
- `import.completed` - File import finished

## 🧪 Testing

### Test Coverage
```bash
# Run all tests
python manage.py test app.financial

# Run specific test modules
python manage.py test app.financial.tests.test_models
python manage.py test app.financial.tests.test_views
python manage.py test app.financial.tests.test_services

# Coverage report
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Test Data
```python
# Create test data
python manage.py shell
>>> from app.financial.tests.factories import *
>>> user = UserFactory()
>>> account = AccountFactory(user=user)
>>> transaction = TransactionFactory(account=account)
```

## 🚀 Deployment

### Production Checklist
- [ ] Set `DEBUG = False`
- [ ] Configure production database
- [ ] Set secure `SECRET_KEY`
- [ ] Configure static file serving
- [ ] Set up SSL/TLS certificates
- [ ] Configure backup procedures
- [ ] Set up monitoring and logging
- [ ] Configure caching layers

### Docker Deployment
```bash
# Build image
docker build -t financial-app .

# Run container
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e REDIS_URL=redis://host:6379/0 \
  financial-app
```

### Performance Optimization
- **Database Indexing**: Optimized queries with proper indexes
- **Caching Strategy**: Multi-layer caching (Redis, Memcached)
- **Background Processing**: Async task processing with Celery
- **Connection Pooling**: Database connection optimization
- **CDN Integration**: Static asset delivery optimization

## 📚 Documentation

### Additional Resources
- [API Documentation](api.md)
- [User Guide](user-guide.md)
- [Developer Guide](developer-guide.md)
- [Deployment Guide](deployment.md)
- [Troubleshooting](troubleshooting.md)

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## 🆘 Support

### Getting Help
- **Documentation**: Check the docs first
- **Issues**: Report bugs on GitHub
- **Discussions**: Ask questions in GitHub Discussions
- **Email**: Contact the development team

### Common Issues
- **Import Failures**: Check file format and column mapping
- **Performance Issues**: Verify database indexes and caching
- **Authentication Problems**: Check LDAP/RADIUS configuration
- **Webhook Failures**: Verify endpoint URLs and authentication

---

**Last updated**: 2025-01-27
**Version**: 1.0.0
**Django Version**: 5.0+
**Python Version**: 3.12+