# app/models/xero_token.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, BigInteger, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class XeroToken(Base, TimestampMixin):
    __tablename__ = "xero_tokens"

    id = Column(BigInteger, primary_key=True, index=True)
    organization_id = Column(BigInteger, ForeignKey("xero_organizations.id"), nullable=False)
    tenant_id = Column(String(100), nullable=False)
    tenant_name = Column(String(255), nullable=False)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=False)
    token_expires_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False)
    last_sync_at = Column(DateTime, nullable=True)

    # Relación
    organization = relationship("Organization", back_populates="tokens")

    __table_args__ = (
        UniqueConstraint('organization_id', 'tenant_id', name='unique_org_tenant'),
    )

class AuditLog(Base, TimestampMixin):
    __tablename__ = "xero_audit_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    organization_id = Column(BigInteger, ForeignKey("xero_organizations.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("xero_users.id"), nullable=False)
    tenant_id = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100), nullable=False)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)

    # Quitar las relaciones por ahora

from .organization import Organization