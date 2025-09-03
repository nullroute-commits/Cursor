"""
Database connection and session management for Financial Analytics Platform
Handles PostgreSQL connection, session creation, and database initialization
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.common.config import get_settings

# Get settings
settings = get_settings()

# Database URL
DATABASE_URL = settings.database_url

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20
)

# Create async session maker
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        # Import all models to ensure they are registered
        from src.backend.models.database import (
            Organization, User, UserPermission, Account, Category, 
            Transaction, Budget, AuditLog
        )
        
        # Create all tables
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_session():
    """Get database session as context manager"""
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db():
    """Close database connections"""
    await engine.dispose()


# Database health check
async def check_db_health() -> bool:
    """Check database health"""
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception:
        return False


# Database statistics
async def get_db_stats() -> dict:
    """Get database statistics"""
    try:
        async with engine.begin() as conn:
            # Get table counts
            result = await conn.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY n_tup_ins DESC
            """)
            table_stats = result.fetchall()
            
            # Get database size
            result = await conn.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as db_size
            """)
            db_size = result.fetchone()[0]
            
            return {
                "status": "healthy",
                "database_size": db_size,
                "table_stats": [
                    {
                        "table": row[1],
                        "inserts": row[2],
                        "updates": row[3],
                        "deletes": row[4]
                    }
                    for row in table_stats
                ]
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Export functions and classes
__all__ = [
    "engine",
    "async_session",
    "init_db",
    "get_session",
    "get_db_session",
    "close_db",
    "check_db_health",
    "get_db_stats"
]