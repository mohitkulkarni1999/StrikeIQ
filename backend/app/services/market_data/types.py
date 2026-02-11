from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone
from enum import Enum

class MarketStatus(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    ERROR = "ERROR"
    AUTH_REQUIRED = "AUTH_REQUIRED"

class SessionType(Enum):
    LIVE = "LIVE"
    AUTH = "AUTH"

@dataclass
class MarketData:
    symbol: str
    spot_price: Optional[float]
    previous_close: Optional[float]
    change: Optional[float]
    change_percent: Optional[float]
    timestamp: datetime
    market_status: MarketStatus
    exchange_timestamp: Optional[datetime] = None

@dataclass
class AuthRequiredResponse:
    session_type: str
    mode: str
    message: str
    login_url: str
    timestamp: datetime

@dataclass
class InstrumentInfo:
    symbol: str
    instrument_key: str
    exchange: str
    segment: str

class MarketDataError(Exception):
    """Base exception for market data errors"""
    pass

class AuthenticationError(MarketDataError):
    """Authentication failed"""
    pass

class TokenExpiredError(AuthenticationError):
    """Token has expired"""
    pass

class InstrumentNotFoundError(MarketDataError):
    """Instrument not found"""
    pass

class APIResponseError(MarketDataError):
    """API response error"""
    pass

class MarketClosedError(MarketDataError):
    """Market is closed"""
    pass
