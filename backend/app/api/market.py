"""
Market Status API
Provides market status, server time, and supported symbols
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pytz import timezone as tz

router = APIRouter(prefix="/api/v1/market", tags=["market"])
logger = logging.getLogger(__name__)

# IST timezone
IST_TZ = tz("Asia/Kolkata")

class MarketStatusChecker:
    """Handles market status determination with IST timezone"""
    
    MARKET_OPEN_TIME = (9, 15)  # 9:15 AM
    MARKET_CLOSE_TIME = (15, 30)  # 3:30 PM
    MARKET_DAYS = {0, 1, 2, 3, 4}  # Monday to Friday
    
    @classmethod
    def is_market_open(cls, check_time: datetime = None) -> bool:
        """Check if market is currently open"""
        if check_time is None:
            check_time = datetime.now(IST_TZ)
        
        # Check if it's a weekday
        if check_time.weekday() not in cls.MARKET_DAYS:
            return False
        
        # Check time range
        current_time = (check_time.hour, check_time.minute)
        return cls.MARKET_OPEN_TIME <= current_time <= cls.MARKET_CLOSE_TIME

@router.get("/status", response_model=Dict[str, Any])
async def get_market_status() -> Dict[str, Any]:
    """
    Get current market status, server time, and supported symbols
    """
    try:
        # Get current time in IST
        ist_time = datetime.now(IST_TZ)
        
        # Check market status
        market_open = MarketStatusChecker.is_market_open()
        
        # Check WebSocket status - check actual connections
        from ..api.v1.live_ws import upstox_feeds
        websocket_status = "CONNECTED" if upstox_feeds else "DISCONNECTED"
        
        # Supported symbols
        supported_symbols = ["NIFTY", "BANKNIFTY"]
        
        return {
            "market_status": "OPEN" if market_open else "CLOSED",
            "server_time": ist_time.isoformat(),
            "symbol_supported": supported_symbols,
            "websocket_status": websocket_status
        }
        
    except Exception as e:
        logger.error(f"Error getting market status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get market status")
