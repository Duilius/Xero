# db/models/xero_token.py
class XeroToken(Base, TimestampMixin):
    __tablename__ = "xero_tokens"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    user = relationship("User", back_populates="xero_tokens")