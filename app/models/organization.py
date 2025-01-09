# app/models/organization.py
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
import enum

class SubscriptionType(str, enum.Enum):
    TRIAL = "trial"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class OrganizationStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"

class Organization(Base, TimestampMixin):
    __tablename__ = "xero_organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    website = Column(String(255))
    status = Column(Enum(OrganizationStatus), default=OrganizationStatus.ACTIVE)
    subscription_type = Column(Enum(SubscriptionType), default=SubscriptionType.TRIAL)
    subscription_ends_at = Column(DateTime, nullable=True)

    users = relationship("OrganizationUser", back_populates="organization")
    xero_tokens = relationship("XeroToken", back_populates="organization")

class OrganizationRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"

class OrganizationUser(Base, TimestampMixin):
    __tablename__ = "xero_organization_users"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("xero_organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("xero_users.id"), nullable=False)
    role = Column(Enum(OrganizationRole), default=OrganizationRole.MEMBER)

    organization = relationship("Organization", back_populates="users")
    user = relationship("User", back_populates="organizations")