"""
Repository Pattern Implementation.

Implements the Repository pattern for clean data access abstraction.

Last updated: 2025-01-27 by nullroute-commits
"""
import logging
from typing import List, Optional, Type, TypeVar, Generic, Dict, Any
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session, Query
from sqlalchemy.exc import SQLAlchemyError
from app.core.architecture.base import Repository, Result, BaseEntity
from app.core.db.connection import get_db_session

logger = logging.getLogger(__name__)

# Type variables
T = TypeVar('T', bound=BaseEntity)
ID = TypeVar('ID')


class SQLAlchemyRepository(Repository[T, ID], Generic[T, ID]):
    """
    SQLAlchemy-based repository implementation.
    
    Provides concrete implementation of the Repository pattern
    using SQLAlchemy ORM for data access.
    """
    
    def __init__(self, entity_class: Type[T]) -> None:
        """
        Initialize repository with entity class.
        
        Args:
            entity_class: The entity class to manage
        """
        self.entity_class = entity_class
        self.logger = logging.getLogger(f"{__name__}.{entity_class.__name__}")
    
    def get_by_id(self, entity_id: ID) -> Optional[T]:
        """
        Get entity by ID.
        
        Args:
            entity_id: Entity identifier
        
        Returns:
            Entity instance or None if not found
        """
        try:
            with get_db_session() as session:
                entity = session.query(self.entity_class).filter(
                    self.entity_class.id == entity_id,
                    self.entity_class.is_active == True
                ).first()
                return entity
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving entity {entity_id}: {e}")
            return None
    
    def get_all(
        self, 
        limit: Optional[int] = None, 
        offset: Optional[int] = None
    ) -> List[T]:
        """
        Get all entities with optional pagination.
        
        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip
        
        Returns:
            List of entities
        """
        try:
            with get_db_session() as session:
                query = session.query(self.entity_class).filter(
                    self.entity_class.is_active == True
                )
                
                if offset:
                    query = query.offset(offset)
                if limit:
                    query = query.limit(limit)
                
                return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving entities: {e}")
            return []
    
    def create(self, entity: T) -> T:
        """
        Create new entity.
        
        Args:
            entity: Entity to create
        
        Returns:
            Created entity with updated ID
        """
        try:
            with get_db_session() as session:
                session.add(entity)
                session.commit()
                session.refresh(entity)
                
                self.logger.info(f"Created entity {entity.id}")
                return entity
        except SQLAlchemyError as e:
            self.logger.error(f"Error creating entity: {e}")
            raise
    
    def update(self, entity: T) -> T:
        """
        Update existing entity.
        
        Args:
            entity: Entity to update
        
        Returns:
            Updated entity
        """
        try:
            with get_db_session() as session:
                # Update timestamp
                entity.updated_at = entity.updated_at
                
                session.merge(entity)
                session.commit()
                session.refresh(entity)
                
                self.logger.info(f"Updated entity {entity.id}")
                return entity
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating entity {entity.id}: {e}")
            raise
    
    def delete(self, entity_id: ID) -> bool:
        """
        Soft delete entity by ID.
        
        Args:
            entity_id: Entity identifier
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with get_db_session() as session:
                entity = session.query(self.entity_class).filter(
                    self.entity_class.id == entity_id
                ).first()
                
                if entity:
                    entity.is_active = False
                    entity.updated_at = entity.updated_at
                    session.commit()
                    
                    self.logger.info(f"Soft deleted entity {entity_id}")
                    return True
                else:
                    self.logger.warning(f"Entity {entity_id} not found for deletion")
                    return False
        except SQLAlchemyError as e:
            self.logger.error(f"Error deleting entity {entity_id}: {e}")
            return False
    
    def exists(self, entity_id: ID) -> bool:
        """
        Check if entity exists.
        
        Args:
            entity_id: Entity identifier
        
        Returns:
            True if entity exists, False otherwise
        """
        try:
            with get_db_session() as session:
                return session.query(self.entity_class).filter(
                    self.entity_class.id == entity_id,
                    self.entity_class.is_active == True
                ).first() is not None
        except SQLAlchemyError as e:
            self.logger.error(f"Error checking entity existence {entity_id}: {e}")
            return False
    
    def count(self) -> int:
        """
        Get total count of active entities.
        
        Returns:
            Total count of active entities
        """
        try:
            with get_db_session() as session:
                return session.query(self.entity_class).filter(
                    self.entity_class.is_active == True
                ).count()
        except SQLAlchemyError as e:
            self.logger.error(f"Error counting entities: {e}")
            return 0
    
    def find_by_criteria(
        self, 
        criteria: Dict[str, Any], 
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[T]:
        """
        Find entities by custom criteria.
        
        Args:
            criteria: Dictionary of field-value pairs for filtering
            limit: Maximum number of entities to return
            offset: Number of entities to skip
        
        Returns:
            List of entities matching criteria
        """
        try:
            with get_db_session() as session:
                query = session.query(self.entity_class).filter(
                    self.entity_class.is_active == True
                )
                
                # Apply criteria filters
                for field, value in criteria.items():
                    if hasattr(self.entity_class, field):
                        if isinstance(value, (list, tuple)):
                            query = query.filter(getattr(self.entity_class, field).in_(value))
                        else:
                            query = query.filter(getattr(self.entity_class, field) == value)
                
                if offset:
                    query = query.offset(offset)
                if limit:
                    query = query.limit(limit)
                
                return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error finding entities by criteria: {e}")
            return []
    
    def bulk_create(self, entities: List[T]) -> List[T]:
        """
        Create multiple entities in bulk.
        
        Args:
            entities: List of entities to create
        
        Returns:
            List of created entities
        """
        try:
            with get_db_session() as session:
                session.add_all(entities)
                session.commit()
                
                # Refresh all entities to get generated IDs
                for entity in entities:
                    session.refresh(entity)
                
                self.logger.info(f"Bulk created {len(entities)} entities")
                return entities
        except SQLAlchemyError as e:
            self.logger.error(f"Error bulk creating entities: {e}")
            raise
    
    def bulk_update(self, entities: List[T]) -> List[T]:
        """
        Update multiple entities in bulk.
        
        Args:
            entities: List of entities to update
        
        Returns:
            List of updated entities
        """
        try:
            with get_db_session() as session:
                for entity in entities:
                    entity.updated_at = entity.updated_at
                    session.merge(entity)
                
                session.commit()
                
                self.logger.info(f"Bulk updated {len(entities)} entities")
                return entities
        except SQLAlchemyError as e:
            self.logger.error(f"Error bulk updating entities: {e}")
            raise


class CachedRepository(Repository[T, ID], Generic[T, ID]):
    """
    Cached repository implementation.
    
    Implements caching layer on top of base repository
    for performance optimization.
    """
    
    def __init__(self, base_repository: Repository[T, ID], cache: Any) -> None:
        """
        Initialize cached repository.
        
        Args:
            base_repository: Base repository implementation
            cache: Cache implementation
        """
        self.base_repository = base_repository
        self.cache = cache
        self.logger = logging.getLogger(f"{__name__}.{type(base_repository).__name__}")
    
    def _get_cache_key(self, entity_id: ID) -> str:
        """Generate cache key for entity."""
        return f"{self.base_repository.entity_class.__name__}:{entity_id}"
    
    def _get_cache_key_pattern(self) -> str:
        """Generate cache key pattern for all entities."""
        return f"{self.base_repository.entity_class.__name__}:*"
    
    def get_by_id(self, entity_id: ID) -> Optional[T]:
        """Get entity by ID with caching."""
        cache_key = self._get_cache_key(entity_id)
        
        # Try cache first
        cached_entity = self.cache.get(cache_key)
        if cached_entity is not None:
            self.logger.debug(f"Cache hit for entity {entity_id}")
            return cached_entity
        
        # Fall back to base repository
        entity = self.base_repository.get_by_id(entity_id)
        if entity:
            # Cache the result
            self.cache.set(cache_key, entity, timeout=300)  # 5 minutes
            self.logger.debug(f"Cached entity {entity_id}")
        
        return entity
    
    def get_all(
        self, 
        limit: Optional[int] = None, 
        offset: Optional[int] = None
    ) -> List[T]:
        """Get all entities (no caching for paginated results)."""
        return self.base_repository.get_all(limit=limit, offset=offset)
    
    def create(self, entity: T) -> T:
        """Create entity and invalidate cache."""
        result = self.base_repository.create(entity)
        self._invalidate_cache()
        return result
    
    def update(self, entity: T) -> T:
        """Update entity and invalidate cache."""
        result = self.base_repository.update(entity)
        self._invalidate_cache()
        return result
    
    def delete(self, entity_id: ID) -> bool:
        """Delete entity and invalidate cache."""
        result = self.base_repository.delete(entity_id)
        if result:
            self._invalidate_cache()
        return result
    
    def exists(self, entity_id: ID) -> bool:
        """Check entity existence with caching."""
        cache_key = f"exists:{self._get_cache_key(entity_id)}"
        
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        result = self.base_repository.exists(entity_id)
        self.cache.set(cache_key, result, timeout=300)
        return result
    
    def count(self) -> int:
        """Get entity count with caching."""
        cache_key = f"count:{self.base_repository.entity_class.__name__}"
        
        cached_count = self.cache.get(cache_key)
        if cached_count is not None:
            return cached_count
        
        count = self.base_repository.count()
        self.cache.set(cache_key, count, timeout=300)
        return count
    
    def _invalidate_cache(self) -> None:
        """Invalidate all cached data for this entity type."""
        pattern = self._get_cache_key_pattern()
        self.cache.delete(pattern)
        self.logger.debug(f"Invalidated cache for pattern: {pattern}")


class RepositoryFactory:
    """
    Factory for creating repository instances.
    
    Implements the Factory pattern for repository creation
    and configuration.
    """
    
    _repositories: Dict[str, Repository] = {}
    
    @classmethod
    def get_repository(
        cls, 
        entity_class: Type[T], 
        use_cache: bool = True
    ) -> Repository[T, ID]:
        """
        Get or create repository instance.
        
        Args:
            entity_class: Entity class for repository
            use_cache: Whether to use cached repository
        
        Returns:
            Repository instance
        """
        entity_name = entity_class.__name__
        cache_key = f"{entity_name}:{use_cache}"
        
        if cache_key not in cls._repositories:
            base_repo = SQLAlchemyRepository(entity_class)
            
            if use_cache:
                # Import here to avoid circular imports
                from app.core.cache.memcached import MemcachedCache
                cache = MemcachedCache()
                cls._repositories[cache_key] = CachedRepository(base_repo, cache)
            else:
                cls._repositories[cache_key] = base_repo
            
            cls._repositories[cache_key].entity_class = entity_class
        
        return cls._repositories[cache_key]
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached repositories."""
        cls._repositories.clear()