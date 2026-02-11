import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from .upstox_client import UpstoxClient
from .types import InstrumentInfo, InstrumentNotFoundError, APIResponseError
from ..upstox_auth_service import get_upstox_auth_service

logger = logging.getLogger(__name__)

class InstrumentService:
    """Service for managing instrument keys"""
    
    def __init__(self):
        self.client = UpstoxClient()
        self._instruments_cache: Dict[str, InstrumentInfo] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = timedelta(hours=24)  # Cache for 24 hours
    
    async def get_instrument_key(self, symbol: str) -> str:
        """Get instrument key for a symbol"""
        instrument = await self.get_instrument_info(symbol)
        return instrument.instrument_key
    
    async def get_instrument_info(self, symbol: str) -> InstrumentInfo:
        """Get instrument info for a symbol"""
        # Check cache first
        if self._is_cache_valid():
            if symbol.upper() in self._instruments_cache:
                logger.info(f"Found {symbol} in cache")
                return self._instruments_cache[symbol.upper()]
        
        # Refresh cache if needed
        await self._refresh_instruments()
        
        # Try again after refresh
        if symbol.upper() in self._instruments_cache:
            logger.info(f"Found {symbol} after cache refresh")
            return self._instruments_cache[symbol.upper()]
        
        raise InstrumentNotFoundError(f"Instrument not found: {symbol}")
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if self._cache_timestamp is None:
            return False
        return datetime.now() - self._cache_timestamp < self._cache_ttl
    
    async def _refresh_instruments(self):
        """Refresh instruments cache from Upstox API"""
        try:
            logger.info("Refreshing instruments cache")
            
            # Get access token
            auth_service = get_upstox_auth_service()
            if not auth_service.is_authenticated():
                raise APIResponseError("Not authenticated")
            
            token = await auth_service.get_valid_access_token()
            if not token:
                raise APIResponseError("No access token available")
            
            # Fetch instruments
            instruments_data = await self.client.get_instruments(token)
            
            # Parse and cache relevant instruments
            self._instruments_cache.clear()
            
            for item in instruments_data:
                if not isinstance(item, dict):
                    continue
                
                # Look for NIFTY and BANKNIFTY instruments
                instrument_key = item.get("instrument_key", "")
                name = item.get("name", "").upper()
                exchange = item.get("exchange", "")
                segment = item.get("segment", "")
                
                # Map to our symbols
                if "NIFTY" in name and "BANK" not in name and "NSE_INDEX" in instrument_key:
                    self._instruments_cache["NIFTY"] = InstrumentInfo(
                        symbol="NIFTY",
                        instrument_key=instrument_key,
                        exchange=exchange,
                        segment=segment
                    )
                    logger.info(f"Cached NIFTY: {instrument_key}")
                
                elif "BANKNIFTY" in name and "NSE_INDEX" in instrument_key:
                    self._instruments_cache["BANKNIFTY"] = InstrumentInfo(
                        symbol="BANKNIFTY",
                        instrument_key=instrument_key,
                        exchange=exchange,
                        segment=segment
                    )
                    logger.info(f"Cached BANKNIFTY: {instrument_key}")
            
            self._cache_timestamp = datetime.now()
            logger.info(f"Instruments cache refreshed. Found {len(self._instruments_cache)} instruments")
            
        except Exception as e:
            logger.error(f"Failed to refresh instruments cache: {e}")
            raise APIResponseError(f"Failed to refresh instruments: {e}")
    
    async def close(self):
        """Close client"""
        await self.client.close()
