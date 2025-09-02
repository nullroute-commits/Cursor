"""
Financial App Configuration
"""

from django.apps import AppConfig


class FinancialConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.financial'
    verbose_name = 'Financial Management'

    def ready(self):
        """Initialize app when ready"""
        try:
            import app.financial.signals  # noqa
        except ImportError:
            pass