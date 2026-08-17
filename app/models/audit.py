from sqlalchemy import Column, Integer, String, JSON, DateTime
from datetime import datetime
from app.models.base import TenantBase


class AuditLog(TenantBase):
    """
    Task 37: Audit Logs.
    Tracks 'Who did What, When, and to Which record'.
    Essential for compliance (GDPR, PCI-DSS) and internal security investigations.
    """

    __tablename__ = "audit_logs"

    user_id = Column(
        Integer, index=True, nullable=True
    )  # ID of the user performing the action
    action = Column(String(50), nullable=False)  # e.g., 'CREATE', 'UPDATE', 'DELETE'
    entity_name = Column(String(100), nullable=False)  # e.g., 'Order', 'User'
    entity_id = Column(Integer, nullable=False)  # ID of the record being modified

    # Store the changes (old vs new)
    changes = Column(JSON, default={})

    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
