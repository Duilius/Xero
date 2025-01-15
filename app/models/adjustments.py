from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text ,Enum as SQLEnum, Numeric, Boolean
from sqlalchemy.orm import relationship
import enum
from .base import Base, TimestampMixin

class AdjustmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class Authorizer(Base, TimestampMixin):
    __tablename__ = "xero_authorizers"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("xero_organizations.id"), nullable=False)
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)

    # Relaciones
    organization = relationship("Organization", back_populates="authorizers")
    approvals = relationship("AdjustmentApproval", back_populates="authorizer")

class AdjustmentRequest(Base, TimestampMixin):
    __tablename__ = "xero_adjustment_requests"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("xero_organizations.id"), nullable=False)
    requestor_id = Column(Integer, ForeignKey("xero_users.id"), nullable=False)
    adjust_in_org_id = Column(Integer, ForeignKey("xero_organizations.id"), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    justification = Column(Text, nullable=False)
    status = Column(SQLEnum(AdjustmentStatus), default=AdjustmentStatus.PENDING)
    comparison_data = Column(JSON)  # Guarda datos de la comparación

    # Relaciones
    organization = relationship("Organization", foreign_keys=[organization_id])
    adjust_in_org = relationship("Organization", foreign_keys=[adjust_in_org_id])
    requestor = relationship("User")
    approvals = relationship("AdjustmentApproval", back_populates="request")

class AdjustmentApproval(Base, TimestampMixin):
    __tablename__ = "xero_adjustment_approvals"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("xero_adjustment_requests.id"), nullable=False)
    authorizer_id = Column(Integer, ForeignKey("xero_authorizers.id"), nullable=False)
    status = Column(SQLEnum(AdjustmentStatus), nullable=True)  # NULL significa pendiente
    comment = Column(Text, nullable=True)

    # Relaciones
    request = relationship("AdjustmentRequest", back_populates="approvals")
    authorizer = relationship("Authorizer", back_populates="approvals")