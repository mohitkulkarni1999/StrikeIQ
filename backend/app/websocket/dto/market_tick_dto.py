"""
Market Tick DTO
Internal data transfer object for decoded market ticks
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class MarketTickDTO:
    """
    Internal DTO for decoded market tick data
    Isolates protobuf structure from business logic
    """
    
    # Message metadata
    message_id: Optional[str]
    instrument_key: str
    timestamp: datetime
    
    # Basic market data
    last_price: float
    volume: int
    bid_price: float
    ask_price: float
    
    # Options-specific data (optional)
    open_interest: int = 0
    oi_change: int = 0
    
    # Greeks (optional for options)
    delta: float = 0.0
    theta: float = 0.0
    gamma: float = 0.0
    vega: float = 0.0
    
    # Additional fields for future use
    bid_size: int = 0
    ask_size: int = 0
    vwap: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open_price: Optional[float] = None
    
    def is_option_tick(self) -> bool:
        """Check if this tick contains options data"""
        return self.open_interest > 0 or any([
            self.delta != 0.0,
            self.theta != 0.0,
            self.gamma != 0.0,
            self.vega != 0.0
        ])
    
    def get_spread(self) -> float:
        """Calculate bid-ask spread"""
        if self.bid_price > 0 and self.ask_price > 0:
            return self.ask_price - self.bid_price
        return 0.0
    
    def get_mid_price(self) -> float:
        """Calculate mid price"""
        if self.bid_price > 0 and self.ask_price > 0:
            return (self.bid_price + self.ask_price) / 2.0
        return self.last_price
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'message_id': self.message_id,
            'instrument_key': self.instrument_key,
            'timestamp': self.timestamp.isoformat(),
            'last_price': self.last_price,
            'volume': self.volume,
            'bid_price': self.bid_price,
            'ask_price': self.ask_price,
            'open_interest': self.open_interest,
            'oi_change': self.oi_change,
            'delta': self.delta,
            'theta': self.theta,
            'gamma': self.gamma,
            'vega': self.vega,
            'bid_size': self.bid_size,
            'ask_size': self.ask_size,
            'vwap': self.vwap,
            'high': self.high,
            'low': self.low,
            'open_price': self.open_price,
            'is_option': self.is_option_tick(),
            'spread': self.get_spread(),
            'mid_price': self.get_mid_price()
        }
