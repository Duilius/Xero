# db/models/organization.py
class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    xero_tenant_id = Column(String, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    user = relationship("User", back_populates="organizations")
    transactions = relationship("Transaction", back_populates="organization")