from sqlalchemy import Column, Integer, String, Float, Index
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import TenantBase


class Order(TenantBase):
    __tablename__ = "orders"

    amount = Column(Float, nullable=False)
    status = Column(Integer, default=0)  # 0: pending, 1: paid

    # Storing flexible metadata (like items, customer preferences)
    metadata_data = Column(JSONB, default={})

    client_name = Column(String(255), index=True)  # Standard B-Tree index

    # Task 22: Advanced Indexing
    __table_args__ = (
        Index("idx_order_metadata_gin", metadata_data, postgresql_using="gin"),
    )


class OrderArchive(TenantBase):
    """
    Task 26: Data Archiving.
    Cold storage for old orders to keep the main 'orders' table fast and lean.
    """

    __tablename__ = "orders_archive"

    original_id = Column(Integer, index=True)
    amount = Column(Float)
    status = Column(Integer)
    client_name = Column(String(255))
