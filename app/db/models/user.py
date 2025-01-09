# app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    SUPPORT = "support"
    ACCOUNTANT = "accountant"
    USER = "user"

class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class User(Base, TimestampMixin):
    __tablename__ = "xero_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    email_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)

    organizations = relationship("OrganizationUser", back_populates="user")
