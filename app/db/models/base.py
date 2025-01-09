# db/models/base.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy import Column, Integer, DateTime

Base = declarative_base()

class TimestampMixin:
    created_at = Column(DateTime, default=func.now, nullable=False)
    updated_at = Column(DateTime, default=func.now, onupdate=func.now, nullable=False)