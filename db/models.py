from sqlalchemy import Column, Integer, String, Numeric, Text, BigInteger, DateTime
from datetime import datetime
from db.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    
    # The actual Bank Reference (e.g., FT26096GY83C) - UNIQUE to prevent duplicates!
    transaction_ref = Column(String, unique=True, index=True, nullable=False)
    
    # Who sent it
    merchant_tg_id = Column(BigInteger, nullable=False)
    
    # Extracted data
    amount = Column(Numeric, nullable=True)
    bank_name = Column(String, nullable=True)
    
    # Proof: 'IMAGE' or 'LINK'
    proof_type = Column(String, nullable=False)
    proof_data = Column(Text, nullable=False) # Stores Image ID or Awash URL
    
    # State: PENDING, APPROVED, REJECTED
    status = Column(String, default="PENDING", nullable=False)
    
    # Who approved it
    manager_tg_id = Column(BigInteger, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)