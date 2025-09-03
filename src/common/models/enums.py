"""
Enums for Financial Analytics Platform
Common enumerations used across the platform
"""

from enum import Enum


class Role(str, Enum):
    """User roles for RBAC"""
    
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class TransactionType(str, Enum):
    """Transaction types"""
    
    DEBIT = "debit"
    CREDIT = "credit"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    REFUND = "refund"
    FEE = "fee"
    INTEREST = "interest"
    DIVIDEND = "dividend"
    PURCHASE = "purchase"
    SALE = "sale"


class AccountType(str, Enum):
    """Account types"""
    
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT = "credit"
    INVESTMENT = "investment"
    LOAN = "loan"
    MORTGAGE = "mortgage"
    INSURANCE = "insurance"
    RETIREMENT = "retirement"
    BUSINESS = "business"
    STUDENT = "student"


class InstitutionType(str, Enum):
    """Financial institution types"""
    
    BANK = "bank"
    CREDIT_UNION = "credit_union"
    CREDIT_CARD = "credit_card"
    INVESTMENT = "investment"
    INSURANCE = "insurance"
    LOAN = "loan"
    PAYMENT_PROCESSOR = "payment_processor"
    CRYPTOCURRENCY = "cryptocurrency"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnalyticsRunStatus(str, Enum):
    """Analytics run status"""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingStatus(str, Enum):
    """Transaction processing status"""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReportFormat(str, Enum):
    """Report export formats"""
    
    JSON = "json"
    HTML = "html"
    PDF = "pdf"
    XLSX = "xlsx"
    CSV = "csv"


class NotificationType(str, Enum):
    """Notification types"""
    
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    SLACK = "slack"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"


class Currency(str, Enum):
    """Supported currencies"""
    
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CAD = "CAD"
    AUD = "AUD"
    CHF = "CHF"
    CNY = "CNY"
    INR = "INR"
    BRL = "BRL"


class AnalyticsType(str, Enum):
    """Analytics types"""
    
    CATEGORIZATION = "categorization"
    CLUSTERING = "clustering"
    FORECASTING = "forecasting"
    ANOMALY_DETECTION = "anomaly_detection"
    PATTERN_RECOGNITION = "pattern_recognition"
    TREND_ANALYSIS = "trend_analysis"
    CORRELATION_ANALYSIS = "correlation_analysis"


class AlertRuleType(str, Enum):
    """Alert rule types"""
    
    THRESHOLD = "threshold"
    ANOMALY = "anomaly"
    SCHEDULE = "schedule"
    PATTERN = "pattern"
    TREND = "trend"


class DataSource(str, Enum):
    """Data source types"""
    
    CHASE = "CHASE"
    DISCOVER_CARD = "DISCOVER_CARD"
    CAPITALONE = "CAPITALONE"
    PLAID = "PLAID"
    MANUAL = "MANUAL"
    CSV_IMPORT = "CSV_IMPORT"
    API = "API"
    WEBHOOK = "WEBHOOK"


class Permission(str, Enum):
    """User permissions"""
    
    # Admin permissions
    ALL = "*"
    
    # User management
    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    
    # Organization management
    CREATE_ORG = "create_org"
    READ_ORG = "read_org"
    UPDATE_ORG = "update_org"
    DELETE_ORG = "delete_org"
    
    # Transaction permissions
    READ_TRANSACTIONS = "read_transactions"
    CREATE_TRANSACTIONS = "create_transactions"
    UPDATE_TRANSACTIONS = "update_transactions"
    DELETE_TRANSACTIONS = "delete_transactions"
    
    # Analytics permissions
    RUN_ANALYTICS = "run_analytics"
    READ_REPORTS = "read_reports"
    WRITE_REPORTS = "write_reports"
    EXPORT_DATA = "export_data"
    
    # Monitoring permissions
    VIEW_MONITORING = "view_monitoring"
    MANAGE_ALERTS = "manage_alerts"
    VIEW_LOGS = "view_logs"
    
    # System permissions
    VIEW_SYSTEM = "view_system"
    MANAGE_SYSTEM = "manage_system"
    VIEW_AUDIT = "view_audit"


class LogLevel(str, Enum):
    """Log levels"""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Environment(str, Enum):
    """Environment types"""
    
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"