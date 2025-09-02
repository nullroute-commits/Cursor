"""
Configuration Management Service

Allows users to configure webapp settings through the web interface.
Manages environment-specific configurations and provides validation.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from ..models import Webhook
from app.core.audit import audit_logger

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """Manages application configuration through the web interface"""
    
    # Configuration categories
    CATEGORIES = {
        'general': {
            'name': 'General Settings',
            'description': 'Basic application configuration',
            'icon': 'settings'
        },
        'security': {
            'name': 'Security Settings',
            'description': 'Security and authentication configuration',
            'icon': 'shield'
        },
        'financial': {
            'name': 'Financial Settings',
            'description': 'Financial data and reporting configuration',
            'icon': 'dollar-sign'
        },
        'import': {
            'name': 'Import Settings',
            'description': 'Data import and processing configuration',
            'icon': 'upload'
        },
        'webhooks': {
            'name': 'Webhook Settings',
            'description': 'External integration configuration',
            'icon': 'link'
        },
        'notifications': {
            'name': 'Notification Settings',
            'description': 'Email and alert configuration',
            'icon': 'bell'
        },
        'performance': {
            'name': 'Performance Settings',
            'description': 'Performance and caching configuration',
            'icon': 'zap'
        }
    }
    
    # Configuration schema with validation rules
    CONFIG_SCHEMA = {
        'general': {
            'app_name': {
                'type': 'string',
                'default': 'Financial Management System',
                'required': True,
                'min_length': 1,
                'max_length': 100,
                'description': 'Application display name'
            },
            'timezone': {
                'type': 'string',
                'default': 'UTC',
                'required': True,
                'choices': ['UTC', 'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles', 'Europe/London', 'Europe/Paris', 'Asia/Tokyo'],
                'description': 'Default timezone for the application'
            },
            'date_format': {
                'type': 'string',
                'default': 'MM/DD/YYYY',
                'required': True,
                'choices': ['MM/DD/YYYY', 'DD/MM/YYYY', 'YYYY-MM-DD'],
                'description': 'Default date format'
            },
            'currency': {
                'type': 'string',
                'default': 'USD',
                'required': True,
                'choices': ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD'],
                'description': 'Default currency'
            },
            'language': {
                'type': 'string',
                'default': 'en',
                'required': True,
                'choices': ['en', 'es', 'fr', 'de', 'ja'],
                'description': 'Default language'
            }
        },
        'security': {
            'session_timeout': {
                'type': 'integer',
                'default': 3600,
                'required': True,
                'min_value': 300,
                'max_value': 86400,
                'description': 'Session timeout in seconds'
            },
            'max_login_attempts': {
                'type': 'integer',
                'default': 5,
                'required': True,
                'min_value': 3,
                'max_value': 10,
                'description': 'Maximum login attempts before lockout'
            },
            'lockout_duration': {
                'type': 'integer',
                'default': 900,
                'required': True,
                'min_value': 300,
                'max_value': 3600,
                'description': 'Account lockout duration in seconds'
            },
            'require_2fa': {
                'type': 'boolean',
                'default': False,
                'required': True,
                'description': 'Require two-factor authentication'
            },
            'password_min_length': {
                'type': 'integer',
                'default': 8,
                'required': True,
                'min_value': 6,
                'max_value': 20,
                'description': 'Minimum password length'
            }
        },
        'financial': {
            'default_account_type': {
                'type': 'string',
                'default': 'checking',
                'required': True,
                'choices': ['checking', 'savings', 'credit_card', 'investment', 'loan', 'other'],
                'description': 'Default account type for new accounts'
            },
            'auto_categorization': {
                'type': 'boolean',
                'default': True,
                'required': True,
                'description': 'Enable automatic transaction categorization'
            },
            'budget_alert_threshold': {
                'type': 'integer',
                'default': 80,
                'required': True,
                'min_value': 50,
                'max_value': 100,
                'description': 'Budget alert threshold percentage'
            },
            'reconciliation_reminder_days': {
                'type': 'integer',
                'default': 7,
                'required': True,
                'min_value': 1,
                'max_value': 30,
                'description': 'Days before reconciliation reminder'
            },
            'retention_period_months': {
                'type': 'integer',
                'default': 84,
                'required': True,
                'min_value': 12,
                'max_value': 120,
                'description': 'Data retention period in months'
            }
        },
        'import': {
            'max_file_size_mb': {
                'type': 'integer',
                'default': 50,
                'required': True,
                'min_value': 1,
                'max_value': 500,
                'description': 'Maximum file size for import in MB'
            },
            'allowed_file_types': {
                'type': 'array',
                'default': ['csv', 'xlsx', 'xls', 'pdf'],
                'required': True,
                'description': 'Allowed file types for import'
            },
            'auto_process_imports': {
                'type': 'boolean',
                'default': True,
                'required': True,
                'description': 'Automatically process imports in background'
            },
            'import_batch_size': {
                'type': 'integer',
                'default': 1000,
                'required': True,
                'min_value': 100,
                'max_value': 10000,
                'description': 'Number of records to process per batch'
            },
            'enable_duplicate_detection': {
                'type': 'boolean',
                'default': True,
                'required': True,
                'description': 'Enable duplicate transaction detection'
            }
        },
        'webhooks': {
            'max_webhooks_per_user': {
                'type': 'integer',
                'default': 10,
                'required': True,
                'min_value': 1,
                'max_value': 100,
                'description': 'Maximum webhooks per user'
            },
            'webhook_timeout': {
                'type': 'integer',
                'default': 30,
                'required': True,
                'min_value': 10,
                'max_value': 300,
                'description': 'Webhook delivery timeout in seconds'
            },
            'max_retry_attempts': {
                'type': 'integer',
                'default': 3,
                'required': True,
                'min_value': 1,
                'max_value': 10,
                'description': 'Maximum webhook retry attempts'
            },
            'enable_webhook_signatures': {
                'type': 'boolean',
                'default': True,
                'required': True,
                'description': 'Enable webhook payload signatures'
            }
        },
        'notifications': {
            'email_notifications': {
                'type': 'boolean',
                'default': True,
                'required': True,
                'description': 'Enable email notifications'
            },
            'budget_alerts': {
                'type': 'boolean',
                'default': True,
                'required': True,
                'description': 'Enable budget threshold alerts'
            },
            'reconciliation_reminders': {
                'type': 'boolean',
                'default': True,
                'required': True,
                'description': 'Enable reconciliation reminders'
            },
            'import_completion_notifications': {
                'type': 'boolean',
                'default': True,
                'required': True,
                'description': 'Notify on import completion'
            }
        },
        'performance': {
            'cache_enabled': {
                'type': 'boolean',
                'default': True,
                'required': True,
                'description': 'Enable application caching'
            },
            'cache_ttl': {
                'type': 'integer',
                'default': 3600,
                'required': True,
                'min_value': 300,
                'max_value': 86400,
                'description': 'Cache time-to-live in seconds'
            },
            'query_optimization': {
                'type': 'boolean',
                'default': True,
                'required': True,
                'description': 'Enable database query optimization'
            },
            'background_processing': {
                'type': 'boolean',
                'default': True,
                'required': True,
                'description': 'Enable background task processing'
            }
        }
    }
    
    def __init__(self, user=None):
        self.user = user
        self.cache_key = f"app_config_{user.id if user else 'global'}"
    
    def get_configuration(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration for a specific category or all categories"""
        # Try to get from cache first
        cached_config = cache.get(self.cache_key)
        
        if cached_config is None:
            # Load from database or use defaults
            cached_config = self._load_configuration()
            cache.set(self.cache_key, cached_config, 3600)  # Cache for 1 hour
        
        if category:
            return cached_config.get(category, {})
        
        return cached_config
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration from database or use defaults"""
        config = {}
        
        for category, schema in self.CONFIG_SCHEMA.items():
            config[category] = {}
            for key, field_schema in schema.items():
                # Try to get from database first
                db_value = self._get_db_config_value(category, key)
                
                if db_value is not None:
                    config[category][key] = db_value
                else:
                    # Use default value
                    config[category][key] = field_schema['default']
        
        return config
    
    def _get_db_config_value(self, category: str, key: str) -> Any:
        """Get configuration value from database"""
        # This would typically query a Configuration model
        # For now, return None to use defaults
        return None
    
    def update_configuration(self, category: str, updates: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Update configuration for a specific category"""
        errors = []
        
        try:
            # Validate updates
            schema = self.CONFIG_SCHEMA.get(category)
            if not schema:
                errors.append(f"Invalid configuration category: {category}")
                return False, errors
            
            validated_updates = {}
            for key, value in updates.items():
                if key not in schema:
                    errors.append(f"Invalid configuration key: {key}")
                    continue
                
                # Validate value
                validation_result = self._validate_config_value(key, value, schema[key])
                if validation_result['valid']:
                    validated_updates[key] = validation_result['value']
                else:
                    errors.append(f"{key}: {validation_result['error']}")
            
            if errors:
                return False, errors
            
            # Apply updates
            with transaction.atomic():
                for key, value in validated_updates.items():
                    self._set_db_config_value(category, key, value)
                
                # Clear cache
                cache.delete(self.cache_key)
                
                # Log changes
                audit_logger.info(
                    f"Configuration updated: {category}",
                    extra={
                        'user_id': self.user.id if self.user else None,
                        'category': category,
                        'updates': validated_updates
                    }
                )
            
            return True, []
            
        except Exception as e:
            errors.append(f"Configuration update failed: {str(e)}")
            logger.error(f"Configuration update error: {e}")
            return False, errors
    
    def _validate_config_value(self, key: str, value: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a configuration value against its schema"""
        try:
            # Type validation
            expected_type = schema['type']
            
            if expected_type == 'string':
                if not isinstance(value, str):
                    return {'valid': False, 'error': f"Expected string, got {type(value).__name__}"}
                
                # Length validation
                if 'min_length' in schema and len(value) < schema['min_length']:
                    return {'valid': False, 'error': f"Minimum length is {schema['min_length']} characters"}
                
                if 'max_length' in schema and len(value) > schema['max_length']:
                    return {'valid': False, 'error': f"Maximum length is {schema['max_length']} characters"}
                
                # Choices validation
                if 'choices' in schema and value not in schema['choices']:
                    return {'valid': False, 'error': f"Must be one of: {', '.join(schema['choices'])}"}
                
                return {'valid': True, 'value': value}
            
            elif expected_type == 'integer':
                try:
                    int_value = int(value)
                except (ValueError, TypeError):
                    return {'valid': False, 'error': f"Expected integer, got {type(value).__name__}"}
                
                # Range validation
                if 'min_value' in schema and int_value < schema['min_value']:
                    return {'valid': False, 'error': f"Minimum value is {schema['min_value']}"}
                
                if 'max_value' in schema and int_value > schema['max_value']:
                    return {'valid': False, 'error': f"Maximum value is {schema['max_value']}"}
                
                return {'valid': True, 'value': int_value}
            
            elif expected_type == 'boolean':
                if isinstance(value, bool):
                    return {'valid': True, 'value': value}
                elif isinstance(value, str):
                    if value.lower() in ['true', '1', 'yes', 'on']:
                        return {'valid': True, 'value': True}
                    elif value.lower() in ['false', '0', 'no', 'off']:
                        return {'valid': True, 'value': False}
                    else:
                        return {'valid': False, 'error': "Must be true or false"}
                else:
                    return {'valid': False, 'error': f"Expected boolean, got {type(value).__name__}"}
            
            elif expected_type == 'array':
                if not isinstance(value, list):
                    return {'valid': False, 'error': f"Expected array, got {type(value).__name__}"}
                
                return {'valid': True, 'value': value}
            
            else:
                return {'valid': False, 'error': f"Unknown type: {expected_type}"}
                
        except Exception as e:
            return {'valid': False, 'error': f"Validation error: {str(e)}"}
    
    def _set_db_config_value(self, category: str, key: str, value: Any):
        """Set configuration value in database"""
        # This would typically update a Configuration model
        # For now, just log the change
        logger.info(f"Setting config {category}.{key} = {value}")
    
    def reset_to_defaults(self, category: Optional[str] = None) -> Tuple[bool, List[str]]:
        """Reset configuration to default values"""
        try:
            if category:
                categories = [category]
            else:
                categories = list(self.CONFIG_SCHEMA.keys())
            
            for cat in categories:
                if cat not in self.CONFIG_SCHEMA:
                    continue
                
                # Reset all keys in category to defaults
                schema = self.CONFIG_SCHEMA[cat]
                for key, field_schema in schema.items():
                    self._set_db_config_value(cat, key, field_schema['default'])
            
            # Clear cache
            cache.delete(self.cache_key)
            
            # Log reset
            audit_logger.info(
                f"Configuration reset to defaults: {category or 'all categories'}",
                extra={
                    'user_id': self.user.id if self.user else None,
                    'category': category
                }
            )
            
            return True, []
            
        except Exception as e:
            error_msg = f"Configuration reset failed: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]
    
    def export_configuration(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Export configuration as JSON"""
        config = self.get_configuration(category)
        
        export_data = {
            'exported_at': timezone.now().isoformat(),
            'exported_by': self.user.username if self.user else 'system',
            'configuration': config
        }
        
        return export_data
    
    def import_configuration(self, config_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Import configuration from JSON"""
        errors = []
        
        try:
            if 'configuration' not in config_data:
                errors.append("Invalid configuration format: missing 'configuration' key")
                return False, errors
            
            imported_config = config_data['configuration']
            
            for category, category_config in imported_config.items():
                if category not in self.CONFIG_SCHEMA:
                    errors.append(f"Invalid configuration category: {category}")
                    continue
                
                # Validate and import category configuration
                success, category_errors = self.update_configuration(category, category_config)
                if not success:
                    errors.extend(category_errors)
            
            if errors:
                return False, errors
            
            # Log import
            audit_logger.info(
                "Configuration imported from file",
                extra={
                    'user_id': self.user.id if self.user else None,
                    'imported_at': config_data.get('exported_at'),
                    'exported_by': config_data.get('exported_by')
                }
            )
            
            return True, []
            
        except Exception as e:
            error_msg = f"Configuration import failed: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration"""
        config = self.get_configuration()
        
        summary = {
            'total_categories': len(config),
            'categories': {}
        }
        
        for category, category_config in config.items():
            category_info = self.CATEGORIES.get(category, {})
            summary['categories'][category] = {
                'name': category_info.get('name', category.title()),
                'description': category_info.get('description', ''),
                'icon': category_info.get('icon', 'settings'),
                'config_count': len(category_config),
                'last_modified': None  # Would come from database
            }
        
        return summary
    
    def validate_configuration(self) -> Tuple[bool, List[str]]:
        """Validate entire configuration for consistency"""
        errors = []
        config = self.get_configuration()
        
        # Check for required configurations
        for category, schema in self.CONFIG_SCHEMA.items():
            for key, field_schema in schema.items():
                if field_schema.get('required', False):
                    if key not in config.get(category, {}):
                        errors.append(f"Missing required configuration: {category}.{key}")
        
        # Check for configuration dependencies
        if config.get('notifications', {}).get('email_notifications', False):
            # If email notifications are enabled, check email configuration
            if not hasattr(settings, 'EMAIL_HOST'):
                errors.append("Email notifications enabled but email configuration missing")
        
        if config.get('performance', {}).get('cache_enabled', False):
            # If caching is enabled, check cache configuration
            if not hasattr(settings, 'CACHES'):
                errors.append("Caching enabled but cache configuration missing")
        
        return len(errors) == 0, errors