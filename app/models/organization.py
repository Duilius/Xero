from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, BigInteger, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
from .user import User
import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.account_structures import XeroAccountStructure

class SubscriptionType(str, enum.Enum):
    TRIAL = "TRIAL"
    BASIC = "BASIC"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"

class OrganizationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"


if TYPE_CHECKING:
    from .account_structures import XeroAccountStructure
    from .xero_mapping import AccountMapping
    from .xero_token import XeroToken
    from .adjustments import Authorizer

class Organization(Base, TimestampMixin):
    __tablename__ = "xero_organizations"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False, unique=True)
    website = Column(String(255), nullable=True)
    status = Column(Enum(OrganizationStatus), default=OrganizationStatus.ACTIVE)
    subscription_type = Column(Enum(SubscriptionType), default=SubscriptionType.TRIAL)
    subscription_ends_at = Column(DateTime, nullable=True)

    # Relaciones
    users = relationship("OrganizationUser", back_populates="organization")
    tokens = relationship("XeroToken", back_populates="organization")
    authorizers = relationship("Authorizer", back_populates="organization")
    account_mappings = relationship("AccountMapping", back_populates="organization")
    accounts = relationship("XeroAccountStructure", back_populates="organization")

class OrganizationUser(Base, TimestampMixin):
    __tablename__ = "xero_organization_users"

    id = Column(BigInteger, primary_key=True, index=True)
    organization_id = Column(BigInteger, ForeignKey("xero_organizations.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("xero_users.id"), nullable=False)

    # Relaciones
    organization = relationship("Organization", back_populates="users")
    user = relationship("User", back_populates="organizations")

    __table_args__ = (
        UniqueConstraint('organization_id', 'user_id', name='org_user_unique'),
    )