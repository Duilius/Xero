from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey
from sqlalchemy.sql import func, text
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime

class AccountMapping(Base):
    __tablename__ = "xero_account_mappings"
    
    id = Column(BigInteger, primary_key=True)
    organization_id = Column(BigInteger, ForeignKey("xero_organizations.id"))
    account_code = Column(String(50))
    account_id = Column(String(100))
    account_name = Column(String(255))
    account_type = Column(String(50))
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    organization = relationship("Organization", back_populates="account_mappings")
    changes = relationship("AccountChange", back_populates="mapping")

class AccountChange(Base):
    __tablename__ = "xero_account_changes"
    
    id = Column(BigInteger, primary_key=True)
    mapping_id = Column(BigInteger, ForeignKey("xero_account_mappings.id"))
    user_id = Column(BigInteger, ForeignKey("xero_users.id"))
    change_type = Column(String(50))
    old_code = Column(String(50))
    new_code = Column(String(50))
    changed_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    mapping = relationship("AccountMapping", back_populates="changes")
    user = relationship("User", back_populates="account_changes")