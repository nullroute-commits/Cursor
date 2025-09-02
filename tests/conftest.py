"""
Pytest configuration and fixtures.

Provides comprehensive testing setup for Django application.

Last updated: 2025-01-27 by nullroute-commits
"""
import pytest
import os
import sys
from typing import Generator, Dict, Any
from unittest.mock import Mock, patch

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.testing')

import django
from django.conf import settings
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.core.management import execute_from_command_line

# Configure Django
django.setup()

from app.core.models import User, Role, Permission
from app.core.architecture.base import BaseEntity
from app.core.patterns.repository import RepositoryFactory


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Setup Django database for testing."""
    with django_db_blocker.unblock():
        # Run migrations
        execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
        yield


@pytest.fixture
def db_access_without_rollback_and_truncate(django_db_setup, django_db_blocker):
    """Database access without rollback and truncate."""
    django_db_blocker.unblock()
    yield
    django_db_blocker.restore()


@pytest.fixture
def request_factory() -> RequestFactory:
    """Provide Django request factory."""
    return RequestFactory()


@pytest.fixture
def mock_user() -> Mock:
    """Provide mock user for testing."""
    user = Mock(spec=User)
    user.id = "test-user-id"
    user.username = "testuser"
    user.email = "test@example.com"
    user.is_active = True
    user.is_superuser = False
    user.is_staff = False
    return user


@pytest.fixture
def mock_role() -> Mock:
    """Provide mock role for testing."""
    role = Mock(spec=Role)
    role.id = "test-role-id"
    role.name = "test-role"
    role.description = "Test role for testing"
    role.is_active = True
    return role


@pytest.fixture
def mock_permission() -> Mock:
    """Provide mock permission for testing."""
    permission = Mock(spec=Permission)
    permission.id = "test-permission-id"
    permission.name = "test.permission"
    permission.resource = "test-resource"
    permission.action = "read"
    permission.is_active = True
    return permission


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Provide sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "User",
        "is_active": True
    }


@pytest.fixture
def sample_role_data() -> Dict[str, Any]:
    """Provide sample role data for testing."""
    return {
        "name": "test-role",
        "description": "Test role for testing purposes",
        "is_active": True
    }


@pytest.fixture
def sample_permission_data() -> Dict[str, Any]:
    """Provide sample permission data for testing."""
    return {
        "name": "test.permission",
        "resource": "test-resource",
        "action": "read",
        "is_active": True
    }


@pytest.fixture
def mock_repository() -> Mock:
    """Provide mock repository for testing."""
    repository = Mock()
    repository.get_by_id.return_value = None
    repository.get_all.return_value = []
    repository.create.return_value = Mock()
    repository.update.return_value = Mock()
    repository.delete.return_value = True
    repository.exists.return_value = False
    repository.count.return_value = 0
    return repository


@pytest.fixture
def mock_cache() -> Mock:
    """Provide mock cache for testing."""
    cache = Mock()
    cache.get.return_value = None
    cache.set.return_value = None
    cache.delete.return_value = True
    cache.exists.return_value = False
    cache.clear.return_value = None
    return cache


@pytest.fixture
def mock_audit_logger() -> Mock:
    """Provide mock audit logger for testing."""
    logger = Mock()
    logger.log_activity.return_value = "test-audit-id"
    logger.log_model_change.return_value = "test-audit-id"
    logger.log_request.return_value = "test-audit-id"
    return logger


@pytest.fixture
def mock_nist_compliance_manager() -> Mock:
    """Provide mock NIST compliance manager for testing."""
    manager = Mock()
    manager.get_compliance_report.return_value = {
        "overall_compliance": {
            "compliance_percentage": 85.0
        }
    }
    manager.assess_control.return_value = True
    return manager


@pytest.fixture
def test_entity() -> Mock:
    """Provide test entity for testing."""
    entity = Mock(spec=BaseEntity)
    entity.id = "test-entity-id"
    entity.created_at = "2025-01-27T00:00:00Z"
    entity.updated_at = "2025-01-27T00:00:00Z"
    entity.is_active = True
    return entity


@pytest.fixture
def mock_event_bus() -> Mock:
    """Provide mock event bus for testing."""
    event_bus = Mock()
    event_bus.publish.return_value = None
    event_bus.subscribe.return_value = None
    event_bus.unsubscribe.return_value = None
    return event_bus


@pytest.fixture
def mock_unit_of_work() -> Mock:
    """Provide mock unit of work for testing."""
    uow = Mock()
    uow.__enter__.return_value = uow
    uow.__exit__.return_value = None
    uow.commit.return_value = None
    uow.rollback.return_value = None
    return uow


@pytest.fixture
def mock_configuration() -> Mock:
    """Provide mock configuration for testing."""
    config = Mock()
    config.get.return_value = None
    config.set.return_value = None
    config.has.return_value = False
    config.reload.return_value = None
    return config


@pytest.fixture
def mock_logger() -> Mock:
    """Provide mock logger for testing."""
    logger = Mock()
    logger.debug.return_value = None
    logger.info.return_value = None
    logger.warning.return_value = None
    logger.error.return_value = None
    logger.critical.return_value = None
    return logger


@pytest.fixture
def sample_domain_event() -> Mock:
    """Provide sample domain event for testing."""
    event = Mock()
    event.event_type = "test.event"
    event.aggregate_id = "test-aggregate-id"
    event.timestamp = "2025-01-27T00:00:00Z"
    event.version = 1
    event.metadata = {"test": "data"}
    return event


@pytest.fixture
def mock_result() -> Mock:
    """Provide mock result for testing."""
    result = Mock()
    result.success = True
    result.data = {"test": "data"}
    result.error = None
    result.timestamp = "2025-01-27T00:00:00Z"
    result.is_success.return_value = True
    result.is_failure.return_value = False
    result.get_data.return_value = {"test": "data"}
    result.get_error.return_value = None
    return result


@pytest.fixture
def test_settings() -> Dict[str, Any]:
    """Provide test settings for testing."""
    return {
        "DEBUG": True,
        "SECRET_KEY": "test-secret-key",
        "DATABASE_URL": "sqlite:///:memory:",
        "CACHE_URL": "memory://",
        "AUDIT_ENABLED": True,
        "RBAC_ENABLED": True,
        "NIST_COMPLIANCE_ENABLED": True
    }


@pytest.fixture
def mock_database_session() -> Mock:
    """Provide mock database session for testing."""
    session = Mock()
    session.query.return_value = Mock()
    session.add.return_value = None
    session.commit.return_value = None
    session.rollback.return_value = None
    session.refresh.return_value = None
    session.merge.return_value = None
    return session


@pytest.fixture
def mock_query() -> Mock:
    """Provide mock query for testing."""
    query = Mock()
    query.filter.return_value = query
    query.first.return_value = None
    query.all.return_value = []
    query.count.return_value = 0
    query.offset.return_value = query
    query.limit.return_value = query
    return query


@pytest.fixture
def sample_validation_errors() -> list:
    """Provide sample validation errors for testing."""
    return [
        "Username is required",
        "Email must be valid",
        "Password must be at least 8 characters"
    ]


@pytest.fixture
def mock_service() -> Mock:
    """Provide mock service for testing."""
    service = Mock()
    service.validate.return_value = []
    service.process.return_value = Mock()
    return service


@pytest.fixture
def test_context() -> Dict[str, Any]:
    """Provide test context for testing."""
    return {
        "user_id": "test-user-id",
        "session_id": "test-session-id",
        "ip_address": "127.0.0.1",
        "user_agent": "test-user-agent",
        "request_id": "test-request-id"
    }


# Pytest markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security tests"
    )
    config.addinivalue_line(
        "markers", "database: marks tests that require database access"
    )
    config.addinivalue_line(
        "markers", "cache: marks tests that require cache access"
    )


# Pytest hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add unit marker to test files without specific markers
        if not any(marker.name in ['integration', 'security', 'database'] for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)
        
        # Add database marker to tests that use database fixtures
        if 'db_access_without_rollback_and_truncate' in item.fixturenames:
            item.add_marker(pytest.mark.database)
        
        # Add cache marker to tests that use cache fixtures
        if 'mock_cache' in item.fixturenames:
            item.add_marker(pytest.mark.cache)


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db_access_without_rollback_and_truncate):
    """Enable database access for all tests."""
    pass