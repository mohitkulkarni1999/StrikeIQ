from datetime import datetime, time
from enum import Enum
import pytz

IST = pytz.timezone("Asia/Kolkata")

class EngineMode(str, Enum):
    LIVE = "LIVE"
    PAPER = "PAPER"
    CLOSED = "CLOSED"

def check_market_time():
    """Return True if NSE market hours are active"""

    now = datetime.now(IST)

    # weekend
    if now.weekday() >= 5:
        return False

    market_open = time(9, 15)
    market_close = time(15, 30)

    return market_open <= now.time() <= market_close


class MarketSessionManager:

    def is_market_open(self):
        return check_market_time()

# Singleton instance for global access
_market_session_manager = MarketSessionManager()

def get_market_session_manager():
    """Return global MarketSessionManager instance"""
    return _market_session_manager
