from .base import Base, TimestampMixin
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, BigInteger, Text, UniqueConstraint
from sqlalchemy.orm import relationship
# app/db/models/subscription.py
class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    stripe_subscription_id = Column(String(255))
    stripe_customer_id = Column(String(255))
    plan_id = Column(String(50))
    status = Column(String(50))
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    canceled_at = Column(DateTime, nullable=True)
    payment_method = Column(String(50))
    
    user = relationship("User", back_populates="subscription")