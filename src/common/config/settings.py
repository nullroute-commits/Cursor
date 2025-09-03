"""
Settings configuration for Financial Analytics Platform
Environment-based configuration with validation
"""

import os
from typing import List, Optional, Union
from pydantic import BaseSettings, Field, validator
from pydantic_settings import BaseSettings as PydanticBaseSettings


class Settings(PydanticBaseSettings):
    """Application settings with environment variable support"""
    
    # =============================================================================
    # APPLICATION CONFIGURATION
    # =============================================================================
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # =============================================================================
    # DATABASE CONFIGURATION
    # =============================================================================
    postgres_user: str = Field(default="finance", env="POSTGRES_USER")
    postgres_password: str = Field(default="password", env="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="finance", env="POSTGRES_DB")
    postgres_host: str = Field(default="db", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    @validator("database_url", pre=True, always=True)
    def build_database_url(cls, v, values):
        if v is not None:
            return v
        return f"postgresql://{values['postgres_user']}:{values['postgres_password']}@{values['postgres_host']}:{values['postgres_port']}/{values['postgres_db']}"
    
    # =============================================================================
    # REDIS CONFIGURATION
    # =============================================================================
    redis_host: str = Field(default="redis", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    
    @validator("redis_url", pre=True, always=True)
    def build_redis_url(cls, v, values):
        if v is not None:
            return v
        if values.get("redis_password"):
            return f"redis://:{values['redis_password']}@{values['redis_host']}:{values['redis_port']}/{values['redis_db']}"
        return f"redis://{values['redis_host']}:{values['redis_port']}/{values['redis_db']}"
    
    # =============================================================================
    # SMTP CONFIGURATION
    # =============================================================================
    smtp_host: str = Field(default="smtp", env="SMTP_HOST")
    smtp_port: int = Field(default=1025, env="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, env="SMTP_USER")
    smtp_pass: Optional[str] = Field(default=None, env="SMTP_PASS")
    smtp_tls: bool = Field(default=False, env="SMTP_TLS")
    smtp_from: str = Field(default="noreply@financialplatform.local", env="SMTP_FROM")
    
    # =============================================================================
    # JWT CONFIGURATION
    # =============================================================================
    jwt_secret: str = Field(default="your_super_secret_jwt_key_here_change_in_production", env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=7, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    # =============================================================================
    # POST-QUANTUM CRYPTOGRAPHY
    # =============================================================================
    post_quantum: bool = Field(default=False, env="POST_QUANTUM")
    pq_library: str = Field(default="pqcrypto", env="PQ_LIBRARY")
    pq_encryption_level: int = Field(default=128, env="PQ_ENCRYPTION_LEVEL")
    
    # =============================================================================
    # API CONFIGURATION
    # =============================================================================
    api_url: str = Field(default="http://localhost:8000", env="API_URL")
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=4, env="API_WORKERS")
    api_reload: bool = Field(default=True, env="API_RELOAD")
    
    # =============================================================================
    # FRONTEND CONFIGURATION
    # =============================================================================
    ui_host: str = Field(default="0.0.0.0", env="UI_HOST")
    ui_port: int = Field(default=8080, env="UI_PORT")
    ui_reload: bool = Field(default=True, env="UI_RELOAD")
    
    # =============================================================================
    # MONITORING CONFIGURATION
    # =============================================================================
    grafana_password: str = Field(default="admin123", env="GRAFANA_PASSWORD")
    prometheus_retention_days: int = Field(default=7, env="PROMETHEUS_RETENTION_DAYS")
    alertmanager_smtp_host: str = Field(default="smtp", env="ALERTMANAGER_SMTP_HOST")
    alertmanager_smtp_port: int = Field(default=1025, env="ALERTMANAGER_SMTP_PORT")
    alertmanager_smtp_from: str = Field(default="alerts@financialplatform.local", env="ALERTMANAGER_SMTP_FROM")
    
    # =============================================================================
    # SECURITY CONFIGURATION
    # =============================================================================
    cors_origins: List[str] = Field(default=["http://localhost:8080", "http://localhost:3000"], env="CORS_ORIGINS")
    secret_key: str = Field(default="your_super_secret_key_here_change_in_production", env="SECRET_KEY")
    bcrypt_rounds: int = Field(default=12, env="BCRYPT_ROUNDS")
    session_timeout_minutes: int = Field(default=60, env="SESSION_TIMEOUT_MINUTES")
    
    # =============================================================================
    # ANALYTICS CONFIGURATION
    # =============================================================================
    analytics_batch_size: int = Field(default=1000, env="ANALYTICS_BATCH_SIZE")
    analytics_worker_pool_size: int = Field(default=4, env="ANALYTICS_WORKER_POOL_SIZE")
    analytics_cache_ttl_hours: int = Field(default=24, env="ANALYTICS_CACHE_TTL_HOURS")
    analytics_model_update_interval_hours: int = Field(default=6, env="ANALYTICS_MODEL_UPDATE_INTERVAL_HOURS")
    
    # =============================================================================
    # INGESTION CONFIGURATION
    # =============================================================================
    ingestion_chunk_size: int = Field(default=100, env="INGESTION_CHUNK_SIZE")
    ingestion_max_retries: int = Field(default=3, env="INGESTION_MAX_RETRIES")
    ingestion_retry_delay_seconds: int = Field(default=60, env="INGESTION_RETRY_DELAY_SECONDS")
    ingestion_batch_timeout_seconds: int = Field(default=300, env="INGESTION_BATCH_TIMEOUT_SECONDS")
    
    # =============================================================================
    # PLAID CONFIGURATION (Optional)
    # =============================================================================
    plaid_client_id: Optional[str] = Field(default=None, env="PLAID_CLIENT_ID")
    plaid_secret: Optional[str] = Field(default=None, env="PLAID_SECRET")
    plaid_env: str = Field(default="sandbox", env="PLAID_ENV")
    plaid_webhook_verification: Optional[str] = Field(default=None, env="PLAID_WEBHOOK_VERIFICATION")
    
    # =============================================================================
    # BANK CSV CONFIGURATION
    # =============================================================================
    bank_csv_encoding: str = Field(default="utf-8", env="BANK_CSV_ENCODING")
    bank_csv_delimiter: str = Field(default=",", env="BANK_CSV_DELIMITER")
    bank_csv_date_format: str = Field(default="%m/%d/%Y", env="BANK_CSV_DATE_FORMAT")
    bank_csv_amount_column: str = Field(default="Amount", env="BANK_CSV_AMOUNT_COLUMN")
    bank_csv_date_column: str = Field(default="Date", env="BANK_CSV_DATE_COLUMN")
    bank_csv_description_column: str = Field(default="Description", env="BANK_CSV_DESCRIPTION_COLUMN")
    
    # =============================================================================
    # FEATURE FLAGS
    # =============================================================================
    enable_rbac: bool = Field(default=True, env="ENABLE_RBAC")
    enable_multitenancy: bool = Field(default=True, env="ENABLE_MULTITENANCY")
    enable_analytics: bool = Field(default=True, env="ENABLE_ANALYTICS")
    enable_monitoring: bool = Field(default=True, env="ENABLE_MONITORING")
    enable_alerting: bool = Field(default=True, env="ENABLE_ALERTING")
    enable_plaid_integration: bool = Field(default=False, env="ENABLE_PLAID_INTEGRATION")
    enable_bank_csv_ingestion: bool = Field(default=True, env="ENABLE_BANK_CSV_INGESTION")
    enable_post_quantum_crypto: bool = Field(default=False, env="ENABLE_POST_QUANTUM_CRYPTO")
    
    # =============================================================================
    # DEVELOPMENT CONFIGURATION
    # =============================================================================
    development_mode: bool = Field(default=True, env="DEVELOPMENT_MODE")
    auto_reload: bool = Field(default=True, env="AUTO_RELOAD")
    debug_toolbar: bool = Field(default=False, env="DEBUG_TOOLBAR")
    profiling: bool = Field(default=False, env="PROFILING")
    testing: bool = Field(default=False, env="TESTING")
    
    # =============================================================================
    # LOGGING CONFIGURATION
    # =============================================================================
    log_format: str = Field(default="json", env="LOG_FORMAT")
    log_file_path: str = Field(default="./logs/app.log", env="LOG_FILE_PATH")
    log_max_size_mb: int = Field(default=100, env="LOG_MAX_SIZE_MB")
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    log_level_root: str = Field(default="INFO", env="LOG_LEVEL_ROOT")
    log_level_app: str = Field(default="DEBUG", env="LOG_LEVEL_APP")
    
    # =============================================================================
    # PERFORMANCE CONFIGURATION
    # =============================================================================
    worker_processes: int = Field(default=4, env="WORKER_PROCESSES")
    worker_threads: int = Field(default=2, env="WORKER_THREADS")
    max_connections: int = Field(default=100, env="MAX_CONNECTIONS")
    connection_timeout: int = Field(default=30, env="CONNECTION_TIMEOUT")
    request_timeout: int = Field(default=60, env="REQUEST_TIMEOUT")
    keepalive_timeout: int = Field(default=5, env="KEEPALIVE_TIMEOUT")
    
    # =============================================================================
    # BACKUP CONFIGURATION
    # =============================================================================
    backup_enabled: bool = Field(default=True, env="BACKUP_ENABLED")
    backup_schedule: str = Field(default="0 2 * * *", env="BACKUP_SCHEDULE")
    backup_retention_days: int = Field(default=30, env="BACKUP_RETENTION_DAYS")
    backup_path: str = Field(default="./backups", env="BACKUP_PATH")
    backup_compression: bool = Field(default=True, env="BACKUP_COMPRESSION")
    
    # =============================================================================
    # NOTIFICATION CONFIGURATION
    # =============================================================================
    email_notifications_enabled: bool = Field(default=True, env="EMAIL_NOTIFICATIONS_ENABLED")
    slack_webhook_url: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")
    telegram_bot_token: Optional[str] = Field(default=None, env="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: Optional[str] = Field(default=None, env="TELEGRAM_CHAT_ID")
    
    # =============================================================================
    # THIRD-PARTY INTEGRATIONS
    # =============================================================================
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    new_relic_license_key: Optional[str] = Field(default=None, env="NEW_RELIC_LICENSE_KEY")
    datadog_api_key: Optional[str] = Field(default=None, env="DATADOG_API_KEY")
    cloudwatch_access_key: Optional[str] = Field(default=None, env="CLOUDWATCH_ACCESS_KEY")
    cloudwatch_secret_key: Optional[str] = Field(default=None, env="CLOUDWATCH_SECRET_KEY")
    cloudwatch_region: str = Field(default="us-east-1", env="CLOUDWATCH_REGION")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Convenience function for getting specific settings
def get_database_url() -> str:
    """Get database connection URL"""
    return get_settings().database_url


def get_redis_url() -> str:
    """Get Redis connection URL"""
    return get_settings().redis_url


def is_production() -> bool:
    """Check if running in production environment"""
    return get_settings().environment.lower() == "production"


def is_development() -> bool:
    """Check if running in development environment"""
    return get_settings().environment.lower() == "development"


def is_testing() -> bool:
    """Check if running in testing environment"""
    return get_settings().environment.lower() == "testing"