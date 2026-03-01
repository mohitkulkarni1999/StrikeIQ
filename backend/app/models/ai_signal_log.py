"""
AI Signal Log Model - SQLAlchemy ORM model for AI signal logging
Replaces raw SQL database operations with standardized ORM approach
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from .database import Base

class AiSignalLog(Base):
    """
    AI Signal Log table for storing AI engine signals
    Replaces duplicate database infrastructure with unified ORM approach
    """
    __tablename__ = "ai_signal_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    symbol = Column(String, index=True)
    signal = Column(String, index=True)
    confidence = Column(Float)
    spot_price = Column(Float)
    extra_metadata = Column("metadata", JSON)  # Store additional signal metadata as JSON
    
    def __repr__(self):
        return f"<AiSignalLog(id={self.id}, symbol={self.symbol}, signal={self.signal})>"
