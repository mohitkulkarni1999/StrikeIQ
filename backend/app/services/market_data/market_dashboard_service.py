import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from .upstox_client import UpstoxClient
from .types import MarketData, MarketStatus, AuthRequiredResponse, AuthenticationError, TokenExpiredError, APIResponseError, MarketClosedError
from ..upstox_auth_service import get_upstox_auth_service

logger = logging.getLogger(__name__)

class MarketDataCache:
    """In-memory cache for market data"""
    
    def __init__(self, ttl_seconds: int = 30):
        self._cache: Dict[str, MarketData] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._ttl = timedelta(seconds=ttl_seconds)
    
    def get(self, symbol: str) -> Optional[MarketData]:
        """Get cached market data"""
        if symbol not in self._cache:
            return None
        
        # Check if cache entry is still valid
        if datetime.now(timezone.utc) - self._timestamps[symbol] > self._ttl:
            self.invalidate(symbol)
            return None
        
        logger.info(f"Cache hit for {symbol}")
        return self._cache[symbol]
    
    def set(self, symbol: str, data: MarketData):
        """Set market data in cache"""
        self._cache[symbol] = data
        self._timestamps[symbol] = datetime.now(timezone.utc)
        logger.info(f"Cached data for {symbol}")
    
    def invalidate(self, symbol: str):
        """Invalidate cache entry"""
        self._cache.pop(symbol, None)
        self._timestamps.pop(symbol, None)
        logger.info(f"Invalidated cache for {symbol}")
    
    def clear(self):
        """Clear all cache"""
        self._cache.clear()
        self._timestamps.clear()
        logger.info("Cache cleared")

class MarketDashboardService:
    """Production-grade market data service with centralized auth handling"""
    
    def __init__(self, db):
        self.db = db
        self.client = UpstoxClient()
        self.cache = MarketDataCache(ttl_seconds=30)
        self.auth_service = get_upstox_auth_service()
    
    async def get_dashboard_data(self, symbol: str) -> Dict[str, Any]:
        """Get market data for a symbol with centralized auth handling"""
        
        try:
            logger.info(f"Fetching dashboard data for {symbol}")
            
            # Check cache first (disabled for testing)
            # cached_data = self.cache.get(symbol.upper())
            # if cached_data:
            #     logger.info(f"Returning cached data for {symbol}")
            #     return self._format_market_data_response(cached_data)
            
            # Check authentication first
            logger.info("Checking authentication...")
            auth_status = await self._check_authentication()
            logger.info(f"Auth status result: {auth_status}")
            
            if not auth_status["authenticated"]:
                logger.info("Authentication failed, creating auth required response")
                auth_response = self._create_auth_required_response()
                logger.info(f"Auth response: {auth_response}")
                return auth_response
            
            # Get access token
            token = auth_status["token"]
            if not token:
                logger.info("No token available, creating auth required response")
                return self._create_auth_required_response()
            
            # Fetch market data
            logger.info(f"Fetching market data with token: {token[:20] if token else 'None'}...")
            market_data = await self._fetch_market_data(symbol, token)
            
            # Cache the result
            self.cache.set(symbol.upper(), market_data)
            
            logger.info(f"Successfully fetched data for {symbol}: {market_data.spot_price}")
            return self._format_market_data_response(market_data)
            
        except TokenExpiredError as e:
            logger.warning(f"Token expired for {symbol}: {e}")
            return self._create_auth_required_response()
        
        except AuthenticationError as e:
            logger.error(f"Authentication error for {symbol}: {e}")
            return self._create_auth_required_response()
        
        except MarketClosedError as e:
            logger.info(f"Market closed for {symbol}: {e}")
            market_data = self._create_market_closed_response(symbol)
            self.cache.set(symbol.upper(), market_data)
            return self._format_market_data_response(market_data)
        
        except APIResponseError as e:
            logger.error(f"API error for {symbol}: {e}")
            market_data = self._create_error_response(symbol, str(e))
            return self._format_market_data_response(market_data)
        
        except Exception as e:
            logger.error(f"Unexpected error for {symbol}: {type(e).__name__}: {e}")
            market_data = self._create_error_response(symbol, f"Unexpected error: {e}")
            return self._format_market_data_response(market_data)
    
    async def _check_authentication(self) -> Dict[str, Any]:
        """Centralized authentication check"""
        try:
            if not self.auth_service.is_authenticated():
                logger.info("Not authenticated - no credentials")
                return {"authenticated": False, "token": None}
            
            try:
                token = await self.auth_service.get_valid_access_token()
                if not token:
                    logger.info("No valid token available")
                    return {"authenticated": False, "token": None}
                
                # Validate token by making a test API call
                logger.info(f"Validating token with test API call...")
                try:
                    test_response = await self.client.get_market_quote(token, "NSE_INDEX|NIFTY50")
                    logger.info(f"Token validation successful")
                    return {"authenticated": True, "token": token}
                except Exception as e:
                    # Check if it's a rate limiting error
                    if "429" in str(e) or "Too Many Requests" in str(e):
                        logger.warning(f"Rate limited, waiting before retry...")
                        await asyncio.sleep(5)  # Wait 5 seconds before retry
                        try:
                            test_response = await self.client.get_market_quote(token, "NSE_INDEX|NIFTY50")
                            logger.info(f"Token validation successful after retry")
                            return {"authenticated": True, "token": token}
                        except Exception as retry_e:
                            logger.error(f"Retry also failed: {retry_e}")
                            return {"authenticated": False, "token": None}
                    else:
                        logger.error(f"Token validation failed: {e}")
                        return {"authenticated": False, "token": None}
                
            except TokenExpiredError as e:
                logger.warning(f"Token expired during check: {e}")
                return {"authenticated": False, "token": None}
            
        except Exception as e:
            logger.error(f"Authentication check failed: {e}")
            return {"authenticated": False, "token": None}
    
    def _create_auth_required_response(self) -> Dict[str, Any]:
        """Create standardized auth required response"""
        from ..upstox_auth_service import get_upstox_auth_service
        
        # Get the actual Upstox authorization URL
        auth_service = get_upstox_auth_service()
        upstox_url = auth_service.get_authorization_url()
        
        return {
            "session_type": "AUTH_REQUIRED",
            "mode": "AUTH",
            "message": "Upstox authentication required",
            "login_url": upstox_url,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _fetch_market_data(self, symbol: str, token: str) -> MarketData:
        """Fetch market data from Upstox API"""
        # This would integrate with instrument service and market status service
        # For now, simplified implementation
        try:
            # Try to get instrument key (simplified)
            instrument_key = await self._get_instrument_key(symbol, token)
            logger.info(f"Using instrument key: {instrument_key}")
            
            # Fetch quote
            api_response = await self.client.get_market_quote(token, instrument_key)
            logger.info(f"API response from Upstox: {api_response}")
            
            # Parse response
            return self._parse_market_data(symbol, api_response)
            
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            raise APIResponseError(f"Failed to fetch market data: {e}")
    
    async def _get_instrument_key(self, symbol: str, token: str) -> str:
        """Get instrument key for symbol (simplified)"""
        # This would integrate with instrument service
        # For now, return common keys
        if symbol.upper() == "NIFTY":
            return "NSE_INDEX|NIFTY50"
        elif symbol.upper() == "BANKNIFTY":
            return "NSE_INDEX|BANKNIFTY"
        else:
            raise APIResponseError(f"Unknown symbol: {symbol}")
    
    def _parse_market_data(self, symbol: str, api_response: Dict[str, Any]) -> MarketData:
        """Parse API response into MarketData"""
        try:
            data_field = api_response.get("data", {})
            
            # Extract LTP from Upstox API response structure
            spot_price = None
            if isinstance(data_field, dict):
                # Upstox API returns ltp in nested structure
                spot_price = data_field.get("ltp") or data_field.get("last_price")
                # Also check for nested data structure
                if not spot_price and "market_quote" in data_field:
                    market_quote = data_field["market_quote"]
                    if isinstance(market_quote, dict):
                        spot_price = market_quote.get("ltp") or market_quote.get("last_price")
            
            logger.info(f"Parsed data for {symbol}: spot_price={spot_price}, api_response={api_response}")
            
            # Get actual market status based on current time
            market_status = self._get_market_status()
            
            return MarketData(
                symbol=symbol,
                spot_price=spot_price,
                previous_close=None,  # Would need previous close data
                change=None,         # Would calculate from previous close
                change_percent=None,  # Would calculate from previous close
                timestamp=datetime.now(timezone.utc),
                market_status=market_status
            )
            
        except Exception as e:
            logger.error(f"Error parsing market data for {symbol}: {e}")
            raise APIResponseError(f"Failed to parse market data: {e}")
    
    def _get_market_status(self) -> MarketStatus:
        """Get actual market status based on NSE trading hours"""
        from datetime import datetime, timezone
        
        # Get current time in IST (UTC+5:30)
        now_utc = datetime.now(timezone.utc)
        now_ist = now_utc + timedelta(hours=5, minutes=30)
        
        # NSE trading hours: 9:15 AM - 3:30 PM IST, Monday-Friday
        current_time = now_ist.time()
        current_day = now_ist.weekday()  # Monday=0, Sunday=6
        
        # Check if it's a weekday
        if current_day >= 5:  # Saturday (5) or Sunday (6)
            logger.info(f"Market closed: Weekend (Day {current_day})")
            return MarketStatus.CLOSED
        
        # Check if within trading hours (9:15 AM - 3:30 PM)
        market_open = datetime.strptime("09:15", "%H:%M").time()
        market_close = datetime.strptime("15:30", "%H:%M").time()
        
        if market_open <= current_time <= market_close:
            logger.info(f"Market open: {current_time} within trading hours")
            return MarketStatus.OPEN
        else:
            logger.info(f"Market closed: {current_time} outside trading hours (09:15-15:30)")
            return MarketStatus.CLOSED
    
    def _create_market_closed_response(self, symbol: str) -> MarketData:
        """Create market closed response"""
        return MarketData(
            symbol=symbol,
            spot_price=None,
            previous_close=None,
            change=None,
            change_percent=None,
            timestamp=datetime.now(timezone.utc),
            market_status=MarketStatus.CLOSED
        )
    
    def _create_error_response(self, symbol: str, error_message: str) -> MarketData:
        """Create error response"""
        return MarketData(
            symbol=symbol,
            spot_price=None,
            previous_close=None,
            change=None,
            change_percent=None,
            timestamp=datetime.now(timezone.utc),
            market_status=MarketStatus.ERROR
        )
    
    def _format_market_data_response(self, market_data: MarketData) -> Dict[str, Any]:
        """Format MarketData for API response"""
        return {
            "symbol": market_data.symbol,
            "spot_price": market_data.spot_price,
            "previous_close": market_data.previous_close,
            "change": market_data.change,
            "change_percent": market_data.change_percent,
            "timestamp": market_data.timestamp.isoformat(),
            "market_status": market_data.market_status.value
        }
    
    async def close(self):
        """Close all services"""
        await self.client.close()
        self.cache.clear()
        logger.info("MarketDashboardService closed")
