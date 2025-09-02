"""
Clean Architecture Base Module.

Implements clean architecture principles with proper abstraction layers.

Last updated: 2025-01-27 by nullroute-commits
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timezone

# Type variables for generic implementations
T = TypeVar('T')
ID = TypeVar('ID')
Entity = TypeVar('Entity')


@dataclass
class BaseEntity:
    """Base entity class with common fields."""
    id: ID
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    
    def __post_init__(self) -> None:
        """Initialize timestamps if not provided."""
        if not hasattr(self, 'created_at') or self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if not hasattr(self, 'updated_at') or self.updated_at is None:
            self.updated_at = datetime.now(timezone.utc)


class Repository(ABC, Generic[T, ID]):
    """
    Abstract repository interface for data access.
    
    Implements the Repository pattern for clean separation
    between business logic and data access.
    """
    
    @abstractmethod
    def get_by_id(self, entity_id: ID) -> Optional[T]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """Get all entities with optional pagination."""
        pass
    
    @abstractmethod
    def create(self, entity: T) -> T:
        """Create new entity."""
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """Update existing entity."""
        pass
    
    @abstractmethod
    def delete(self, entity_id: ID) -> bool:
        """Delete entity by ID."""
        pass
    
    @abstractmethod
    def exists(self, entity_id: ID) -> bool:
        """Check if entity exists."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Get total count of entities."""
        pass


class Service(ABC, Generic[T]):
    """
    Abstract service interface for business logic.
    
    Implements the Service Layer pattern for business logic
    separation from data access and presentation layers.
    """
    
    @abstractmethod
    def validate(self, entity: T) -> List[str]:
        """Validate entity and return list of validation errors."""
        pass
    
    @abstractmethod
    def process(self, entity: T) -> T:
        """Process entity according to business rules."""
        pass


class UnitOfWork(ABC):
    """
    Abstract unit of work interface.
    
    Implements the Unit of Work pattern for transaction management
    and ensuring data consistency.
    """
    
    @abstractmethod
    def __enter__(self):
        """Enter unit of work context."""
        pass
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit unit of work context."""
        pass
    
    @abstractmethod
    def commit(self) -> None:
        """Commit all changes."""
        pass
    
    @abstractmethod
    def rollback(self) -> None:
        """Rollback all changes."""
        pass


class EventBus(ABC):
    """
    Abstract event bus interface.
    
    Implements the Event Bus pattern for loose coupling
    between system components.
    """
    
    @abstractmethod
    def publish(self, event: Any) -> None:
        """Publish event to all subscribers."""
        pass
    
    @abstractmethod
    def subscribe(self, event_type: type, handler: callable) -> None:
        """Subscribe to specific event type."""
        pass
    
    @abstractmethod
    def unsubscribe(self, event_type: type, handler: callable) -> None:
        """Unsubscribe from specific event type."""
        pass


class Cache(ABC, Generic[T]):
    """
    Abstract cache interface.
    
    Implements the Cache pattern for performance optimization
    and reducing database load.
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[T]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: T, timeout: Optional[int] = None) -> None:
        """Set value in cache with optional timeout."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""
        pass


class Logger(ABC):
    """
    Abstract logger interface.
    
    Implements the Logger pattern for consistent logging
    across the application.
    """
    
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        pass
    
    @abstractmethod
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        pass


class Configuration(ABC):
    """
    Abstract configuration interface.
    
    Implements the Configuration pattern for centralized
    configuration management.
    """
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        pass
    
    @abstractmethod
    def has(self, key: str) -> bool:
        """Check if configuration key exists."""
        pass
    
    @abstractmethod
    def reload(self) -> None:
        """Reload configuration from source."""
        pass


class Result(Generic[T]):
    """
    Result wrapper for operation outcomes.
    
    Implements the Result pattern for consistent error handling
    and operation result representation.
    """
    
    def __init__(self, success: bool, data: Optional[T] = None, error: Optional[str] = None) -> None:
        """Initialize result."""
        self.success = success
        self.data = data
        self.error = error
        self.timestamp = datetime.now(timezone.utc)
    
    @classmethod
    def success_result(cls, data: T) -> 'Result[T]':
        """Create successful result."""
        return cls(success=True, data=data)
    
    @classmethod
    def failure_result(cls, error: str) -> 'Result[T]':
        """Create failure result."""
        return cls(success=False, error=error)
    
    def is_success(self) -> bool:
        """Check if result is successful."""
        return self.success
    
    def is_failure(self) -> bool:
        """Check if result is failure."""
        return not self.success
    
    def get_data(self) -> Optional[T]:
        """Get result data if successful."""
        return self.data if self.success else None
    
    def get_error(self) -> Optional[str]:
        """Get error message if failure."""
        return self.error if not self.success else None


class DomainEvent:
    """
    Base class for domain events.
    
    Implements the Domain Event pattern for capturing
    business events and enabling event-driven architecture.
    """
    
    def __init__(self, event_type: str, aggregate_id: str, **kwargs) -> None:
        """Initialize domain event."""
        self.event_type = event_type
        self.aggregate_id = aggregate_id
        self.timestamp = datetime.now(timezone.utc)
        self.version = 1
        self.metadata = kwargs
    
    def __str__(self) -> str:
        """String representation of event."""
        return f"{self.event_type}({self.aggregate_id}) at {self.timestamp}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'event_type': self.event_type,
            'aggregate_id': self.aggregate_id,
            'timestamp': self.timestamp.isoformat(),
            'version': self.version,
            'metadata': self.metadata
        }