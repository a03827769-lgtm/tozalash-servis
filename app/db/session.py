from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# Master database for Writes
engine = create_async_engine(
    settings.get_database_url,
    echo=False,
    future=True,
    pool_size=50,  # High pool size for high concurrency
    max_overflow=20,  # Max overflow connections
    pool_timeout=30,  # Timeout if pool is exhausted
)

# Optional: Read-Replica database for Reads (Scale out)
# In a real environment, this URL would point to a different host.
# For local dev, we point it to the same DB or a read-replica node if configured.
read_engine = create_async_engine(
    settings.get_database_url,  # Assume read replica url here
    echo=False,
    future=True,
    pool_size=50,
    max_overflow=20,
)

# Session for Master (Writes)
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# Session for Slave (Reads)
AsyncReadSessionLocal = async_sessionmaker(
    bind=read_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    """Dependency for Write operations (Master)"""
    async with AsyncSessionLocal() as session:
        yield session


async def get_read_db():
    """Dependency for Read operations (Slave)"""
    async with AsyncReadSessionLocal() as session:
        yield session


Base = declarative_base()
