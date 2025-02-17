from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, BigInteger, UniqueConstraint, TIMESTAMP, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import json
from redis import Redis
from app.services.xero_api import xero_api
from .base import Base, TimestampMixin

class XeroAccountStructure(Base):
   __tablename__ = "xero_account_structures"
   
   id = Column(Integer, primary_key=True)
   organization_id = Column(BigInteger, ForeignKey("xero_organizations.id"))
   account_id = Column(String(100))  # Del AccountID de Xero API
   code = Column(String(20))         # Del Code de Xero API
   name = Column(String(255))        # Del Name de Xero API
   type = Column(String(50))         # Del Type de Xero API
   report_type = Column(String(20))  # BS o PL según Type
   last_sync = Column(DateTime)

   organization = relationship("Organization", back_populates="accounts")  

# Servicio híbrido
async def get_account_balance(org_id: str, account_id: str):
    # Cache en Redis para saldos
    cache_key = f"balance:{org_id}:{account_id}"
    ttl = 7200  # 2 horas
    # 1. Intentar cache
    balance = await Redis.get(cache_key)
    if balance:
        return json.loads(balance)
        
    # 2. Consultar Xero
    balance = await xero_api.get_balance(org_id, account_id)
    await Redis.set(cache_key, json.dumps(balance), ex=ttl)
    return balance