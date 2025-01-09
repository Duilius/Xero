# app/models/xero_token.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class XeroToken(Base, TimestampMixin):
    __tablename__ = "xero_tokens"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("xero_organizations.id"), nullable=False)
    tenant_id = Column(String(100), nullable=False)
    tenant_name = Column(String(255), nullable=False)
    access_token = Column(String(4000))
    refresh_token = Column(String(4000), nullable=False)
    token_expires_at = Column(DateTime, nullable=False)
    last_sync_at = Column(DateTime, nullable=True)

    organization = relationship("Organization", back_populates="xero_tokens")

class AuditLog(Base, TimestampMixin):
    __tablename__ = "xero_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("xero_organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("xero_users.id"), nullable=False)
    tenant_id = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100), nullable=False)
    old_value = Column(String(4000))  # JSON string
    new_value = Column(String(4000))  # JSON string

    organization = relationship("Organization")
    user = relationship("User")