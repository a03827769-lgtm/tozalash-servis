from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declared_attr
from datetime import datetime
from app.db.session import Base


class TenantBase(Base):
    """
    Abstract base model that includes company_id for multi-tenancy.
    All models that belong to a specific tenant (company) should inherit from this.
    """

    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, index=True, nullable=False)  # Multi-tenant key
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Company(Base):
    """
    Root model for a Tenant / Company.
    """

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
