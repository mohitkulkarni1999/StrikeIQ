import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from .types import MarketStatus, MarketClosedError

logger = logging.getLogger(__name__)

class MarketStatusService:
    """Service for checking market status"""
    
    # IST timezone (UTC+5:30)
    IST = timezone(timedelta(hours=5, minutes=30))
    
    # Market hours: 9:15 AM - 3:30 PM IST
    MARKET_OPEN_TIME = (9, 15)  # hour, minute
    MARKET_CLOSE_TIME = (15, 30)  # hour, minute
    
    # Market holidays (simplified - in production, use official holiday calendar)
    WEEKEND_DAYS = {5, 6}  # Saturday (5), Sunday (6)
    
    def is_market_open(self, check_time: Optional[datetime] = None) -> bool:
        """Check if market is currently open"""
        if check_time is None:
            check_time = datetime.now(self.IST)
        
        # Convert to IST if timezone-aware
        if check_time.tzinfo is None:
            check_time = check_time.replace(tzinfo=self.IST)
        else:
            check_time = check_time.astimezone(self.IST)
        
        # Check if it's a weekend
        if check_time.weekday() in self.WEEKEND_DAYS:
            logger.info(f"Market closed: Weekend ({check_time.strftime('%A')})")
            return False
        
        # Check market hours
        current_time = (check_time.hour, check_time.minute)
        
        if current_time < self.MARKET_OPEN_TIME:
            logger.info(f"Market closed: Before opening time ({current_time} < {self.MARKET_OPEN_TIME})")
            return False
        
        if current_time >= self.MARKET_CLOSE_TIME:
            logger.info(f"Market closed: After closing time ({current_time} >= {self.MARKET_CLOSE_TIME})")
            return False
        
        logger.info(f"Market is open at {check_time.strftime('%H:%M %Z')}")
        return True
    
    def get_market_status(self, check_time: Optional[datetime] = None) -> MarketStatus:
        """Get market status as enum"""
        if self.is_market_open(check_time):
            return MarketStatus.OPEN
        return MarketStatus.CLOSED
    
    def validate_market_open(self, check_time: Optional[datetime] = None) -> None:
        """Validate market is open, raise exception if closed"""
        if not self.is_market_open(check_time):
            raise MarketClosedError("Market is currently closed")
    
    def get_next_market_open_time(self, from_time: Optional[datetime] = None) -> datetime:
        """Get next market open time"""
        if from_time is None:
            from_time = datetime.now(self.IST)
        
        # Convert to IST if timezone-aware
        if from_time.tzinfo is None:
            from_time = from_time.replace(tzinfo=self.IST)
        else:
            from_time = from_time.astimezone(self.IST)
        
        # If it's weekend, move to Monday
        if from_time.weekday() in self.WEEKEND_DAYS:
            days_until_monday = (7 - from_time.weekday()) % 7 or 7
            next_open = from_time + timedelta(days=days_until_monday)
        else:
            # If market is still open today, next open is tomorrow
            if self.is_market_open(from_time):
                next_open = from_time + timedelta(days=1)
            else:
                # If before market open today, next open is today
                if (from_time.hour, from_time.minute) < self.MARKET_OPEN_TIME:
                    next_open = from_time
                else:
                    # If after market close today, next open is tomorrow
                    next_open = from_time + timedelta(days=1)
        
        # Set to market open time
        next_open = next_open.replace(
            hour=self.MARKET_OPEN_TIME[0],
            minute=self.MARKET_OPEN_TIME[1],
            second=0,
            microsecond=0
        )
        
        return next_open
