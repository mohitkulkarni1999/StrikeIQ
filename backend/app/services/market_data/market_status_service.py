import logging
import httpx
from typing import Optional, Dict
from datetime import datetime, timezone, timedelta
from .types import MarketStatus, MarketClosedError

logger = logging.getLogger(__name__)

class MarketStatusService:
    """TASK 7: SERVICE FOR CHECKING MARKET STATUS USING OFFICIAL UPSTOX API"""
    
    def __init__(self):
        self._client = httpx.AsyncClient(timeout=30)
        self._cache_timeout = 60  # Cache for 60 seconds
        self._last_check = None
        self._last_status = None
    
    async def get_market_status_from_upstox(self, token: str) -> Dict:
        """
        TASK 7: GET MARKET STATUS FROM OFFICIAL UPSTOX API
        Endpoint: GET https://api.upstox.com/v2/market/status
        """
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = await self._client.get(
                "https://api.upstox.com/v2/market/status",
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"Upstox market status API failed: {response.status_code}")
                return {"status": "UNKNOWN"}
            
            data = response.json()
            
            # Extract NSE status from response
            nse_status = data.get("data", {}).get("NSE", {}).get("status", "UNKNOWN")
            
            logger.info(f"Upstox NSE market status: {nse_status}")
            
            return {"status": nse_status}
            
        except Exception as e:
            logger.error(f"Error fetching market status from Upstox: {e}")
            return {"status": "UNKNOWN"}
    
    async def get_market_status(self, token: str, force_refresh: bool = False) -> Dict:
        """
        Get market status with caching
        """
        now = datetime.now()
        
        # Return cached status if available and not force refresh
        if (not force_refresh and 
            self._last_check and 
            self._last_status and 
            (now - self._last_check).seconds < self._cache_timeout):
            return self._last_status
        
        # Fetch fresh status from Upstox
        status = await self.get_market_status_from_upstox(token)
        
        # Update cache
        self._last_check = now
        self._last_status = status
        
        return status
    
    async def is_market_open(self, token: str, force_refresh: bool = False) -> bool:
        """
        Check if market is currently open using Upstox API
        """
        status = await self.get_market_status(token, force_refresh)
        return status.get("status") == "OPEN"
    
    async def validate_market_open(self, token: str) -> None:
        """
        Validate market is open using Upstox API, raise exception if closed
        """
        if not await self.is_market_open(token):
            raise MarketClosedError("Market is currently closed")
    
    async def close(self):
        """
        Close HTTP client
        """
        await self._client.aclose()
