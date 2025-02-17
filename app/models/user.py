# app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, JSON, BigInteger
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
import enum

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    DEVELOPER = "DEVELOPER"
    SUPPORT = "SUPPORT"
    ACCOUNTANT = "ACCOUNTANT"
    USER = "USER"

class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"

class User(Base, TimestampMixin):
    __tablename__ = "xero_users"

    id = Column(BigInteger, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    email_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    xero_roles = Column(JSON, nullable=True)

    # Solo las relaciones que realmente necesitas
    organizations = relationship("OrganizationUser", back_populates="user")

    # app/models/user.py
    account_changes = relationship("AccountChange", back_populates="user")
    
    #role = Column(Enum(UserRole), nullable=False)
    #status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
