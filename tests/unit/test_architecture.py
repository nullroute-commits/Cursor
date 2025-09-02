"""
Unit tests for clean architecture base classes.

Tests the core architecture patterns and abstractions.

Last updated: 2025-01-27 by nullroute-commits
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from app.core.architecture.base import (
    BaseEntity,
    Repository,
    Service,
    UnitOfWork,
    EventBus,
    Cache,
    Logger,
    Configuration,
    Result,
    DomainEvent
)


class TestBaseEntity:
    """Test BaseEntity class."""
    
    def test_base_entity_initialization(self):
        """Test BaseEntity initialization with all parameters."""
        entity_id = "test-id"
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        entity = BaseEntity(
            id=entity_id,
            created_at=created_at,
            updated_at=updated_at,
            is_active=True
        )
        
        assert entity.id == entity_id
        assert entity.created_at == created_at
        assert entity.updated_at == updated_at
        assert entity.is_active is True
    
    def test_base_entity_default_timestamps(self):
        """Test BaseEntity auto-initialization of timestamps."""
        entity_id = "test-id"
        
        entity = BaseEntity(id=entity_id)
        
        assert entity.id == entity_id
        assert entity.created_at is not None
        assert entity.updated_at is not None
        assert entity.is_active is True
        assert isinstance(entity.created_at, datetime)
        assert isinstance(entity.updated_at, datetime)
    
    def test_base_entity_partial_timestamps(self):
        """Test BaseEntity with only some timestamps provided."""
        entity_id = "test-id"
        created_at = datetime.now(timezone.utc)
        
        entity = BaseEntity(
            id=entity_id,
            created_at=created_at
        )
        
        assert entity.id == entity_id
        assert entity.created_at == created_at
        assert entity.updated_at is not None
        assert entity.updated_at != created_at


class TestResult:
    """Test Result class."""
    
    def test_success_result_creation(self):
        """Test successful result creation."""
        data = {"key": "value"}
        result = Result.success_result(data)
        
        assert result.success is True
        assert result.data == data
        assert result.error is None
        assert result.timestamp is not None
    
    def test_failure_result_creation(self):
        """Test failure result creation."""
        error_message = "Something went wrong"
        result = Result.failure_result(error_message)
        
        assert result.success is False
        assert result.data is None
        assert result.error == error_message
        assert result.timestamp is not None
    
    def test_result_methods(self):
        """Test Result utility methods."""
        # Success result
        success_result = Result.success_result({"data": "test"})
        assert success_result.is_success() is True
        assert success_result.is_failure() is False
        assert success_result.get_data() == {"data": "test"}
        assert success_result.get_error() is None
        
        # Failure result
        failure_result = Result.failure_result("error")
        assert failure_result.is_success() is False
        assert failure_result.is_failure() is True
        assert failure_result.get_data() is None
        assert failure_result.get_error() == "error"


class TestDomainEvent:
    """Test DomainEvent class."""
    
    def test_domain_event_creation(self):
        """Test domain event creation."""
        event_type = "user.created"
        aggregate_id = "user-123"
        metadata = {"user_type": "admin"}
        
        event = DomainEvent(
            event_type=event_type,
            aggregate_id=aggregate_id,
            **metadata
        )
        
        assert event.event_type == event_type
        assert event.aggregate_id == aggregate_id
        assert event.timestamp is not None
        assert event.version == 1
        assert event.metadata == metadata
    
    def test_domain_event_string_representation(self):
        """Test domain event string representation."""
        event = DomainEvent("test.event", "test-id")
        string_repr = str(event)
        
        assert "test.event" in string_repr
        assert "test-id" in string_repr
        assert "at" in string_repr
    
    def test_domain_event_to_dict(self):
        """Test domain event dictionary conversion."""
        event = DomainEvent("test.event", "test-id", extra="data")
        event_dict = event.to_dict()
        
        assert event_dict["event_type"] == "test.event"
        assert event_dict["aggregate_id"] == "test-id"
        assert event_dict["version"] == 1
        assert event_dict["metadata"]["extra"] == "data"
        assert "timestamp" in event_dict


class TestRepositoryInterface:
    """Test Repository abstract interface."""
    
    def test_repository_interface_methods(self):
        """Test that Repository interface has required methods."""
        # This test ensures the interface contract is maintained
        required_methods = [
            'get_by_id',
            'get_all',
            'create',
            'update',
            'delete',
            'exists',
            'count'
        ]
        
        for method_name in required_methods:
            assert hasattr(Repository, method_name)
            method = getattr(Repository, method_name)
            assert callable(method)


class TestServiceInterface:
    """Test Service abstract interface."""
    
    def test_service_interface_methods(self):
        """Test that Service interface has required methods."""
        required_methods = ['validate', 'process']
        
        for method_name in required_methods:
            assert hasattr(Service, method_name)
            method = getattr(Service, method_name)
            assert callable(method)


class TestUnitOfWorkInterface:
    """Test UnitOfWork abstract interface."""
    
    def test_unit_of_work_interface_methods(self):
        """Test that UnitOfWork interface has required methods."""
        required_methods = ['commit', 'rollback']
        
        for method_name in required_methods:
            assert hasattr(UnitOfWork, method_name)
            method = getattr(UnitOfWork, method_name)
            assert callable(method)
    
    def test_unit_of_work_context_manager(self):
        """Test that UnitOfWork supports context manager protocol."""
        assert hasattr(UnitOfWork, '__enter__')
        assert hasattr(UnitOfWork, '__exit__')


class TestEventBusInterface:
    """Test EventBus abstract interface."""
    
    def test_event_bus_interface_methods(self):
        """Test that EventBus interface has required methods."""
        required_methods = ['publish', 'subscribe', 'unsubscribe']
        
        for method_name in required_methods:
            assert hasattr(EventBus, method_name)
            method = getattr(EventBus, method_name)
            assert callable(method)


class TestCacheInterface:
    """Test Cache abstract interface."""
    
    def test_cache_interface_methods(self):
        """Test that Cache interface has required methods."""
        required_methods = ['get', 'set', 'delete', 'exists', 'clear']
        
        for method_name in required_methods:
            assert hasattr(Cache, method_name)
            method = getattr(Cache, method_name)
            assert callable(method)


class TestLoggerInterface:
    """Test Logger abstract interface."""
    
    def test_logger_interface_methods(self):
        """Test that Logger interface has required methods."""
        required_methods = [
            'debug', 'info', 'warning', 'error', 'critical'
        ]
        
        for method_name in required_methods:
            assert hasattr(Logger, method_name)
            method = getattr(Logger, method_name)
            assert callable(method)


class TestConfigurationInterface:
    """Test Configuration abstract interface."""
    
    def test_configuration_interface_methods(self):
        """Test that Configuration interface has required methods."""
        required_methods = ['get', 'set', 'has', 'reload']
        
        for method_name in required_methods:
            assert hasattr(Configuration, method_name)
            method = getattr(Configuration, method_name)
            assert callable(method)


class TestArchitecturePatterns:
    """Test architecture pattern implementations."""
    
    def test_repository_generic_type(self):
        """Test that Repository supports generic types."""
        # This test ensures type safety is maintained
        class TestEntity(BaseEntity):
            pass
        
        # Should not raise type errors
        repository: Repository[TestEntity, str] = Mock(spec=Repository)
        assert repository is not None
    
    def test_service_generic_type(self):
        """Test that Service supports generic types."""
        class TestEntity(BaseEntity):
            pass
        
        # Should not raise type errors
        service: Service[TestEntity] = Mock(spec=Service)
        assert service is not None
    
    def test_cache_generic_type(self):
        """Test that Cache supports generic types."""
        # Should not raise type errors
        cache: Cache[str] = Mock(spec=Cache)
        assert cache is not None
    
    def test_result_generic_type(self):
        """Test that Result supports generic types."""
        # Should not raise type errors
        result: Result[str] = Result.success_result("test")
        assert result.get_data() == "test"


class TestArchitectureIntegration:
    """Test architecture components integration."""
    
    def test_base_entity_with_repository(self):
        """Test BaseEntity works with Repository pattern."""
        class TestEntity(BaseEntity):
            def __init__(self, id: str, name: str):
                super().__init__(id=id)
                self.name = name
        
        entity = TestEntity("test-id", "test-name")
        
        # Mock repository
        repository = Mock(spec=Repository)
        repository.create.return_value = entity
        
        # Test integration
        created_entity = repository.create(entity)
        assert created_entity.id == "test-id"
        assert created_entity.name == "test-name"
        assert created_entity.is_active is True
    
    def test_domain_event_with_event_bus(self):
        """Test DomainEvent works with EventBus pattern."""
        event = DomainEvent("test.event", "test-id", data="test")
        
        # Mock event bus
        event_bus = Mock(spec=EventBus)
        
        # Test integration
        event_bus.publish(event)
        event_bus.publish.assert_called_once_with(event)
    
    def test_result_with_service(self):
        """Test Result works with Service pattern."""
        class TestService(Service[str]):
            def validate(self, entity: str) -> List[str]:
                return []
            
            def process(self, entity: str) -> str:
                return entity.upper()
        
        service = TestService()
        result = Result.success_result("test")
        
        if result.is_success():
            data = result.get_data()
            processed = service.process(data)
            assert processed == "TEST"
    
    def test_cache_with_repository(self):
        """Test Cache works with Repository pattern."""
        # Mock cache
        cache = Mock(spec=Cache)
        cache.get.return_value = None
        cache.set.return_value = None
        
        # Mock repository
        repository = Mock(spec=Repository)
        repository.get_by_id.return_value = "cached-data"
        
        # Test integration
        cache_key = "test:key"
        cached_data = cache.get(cache_key)
        
        if cached_data is None:
            data = repository.get_by_id("test-id")
            cache.set(cache_key, data, timeout=300)
            assert cache.set.called