import threading
import asyncio
import httpx
import logging
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from ...core.config import settings
from .types import InstrumentInfo, APIResponseError, AuthenticationError, TokenExpiredError

logger = logging.getLogger(__name__)

# Redis imports for caching
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory caching")

class UpstoxClient:
    """Production-grade API client with centralized rate limiting"""
    
    _instance: Optional['UpstoxClient'] = None
    _instance_lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        
        self.base_url_v2 = "https://api.upstox.com/v2"
        self.base_url_v3 = "https://api.upstox.com/v3"
        self._client = None
        self._cache = {}
        
        # Rate limiting controls
        self._rate_limit = asyncio.Semaphore(5)  # Max 5 concurrent requests
        self._last_request_time = 0.0
        self._min_delay = 0.25  # 250ms between requests
        self._backoff_multiplier = 1.0  # Exponential backoff
        
        # Initialize Redis cache if available
        if REDIS_AVAILABLE:
            try:
                self._redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    decode_responses=True
                )
                logger.info("Redis cache initialized")
            except Exception as e:
                logger.error(f"Redis initialization failed: {e}")
                self._redis_client = None
        else:
            self._redis_client = None
        
        # In-memory cache fallback
        self._memory_cache = {}
        self._cache_timestamps = {}
        
        # Cache TTL settings
        self._expiry_cache_ttl = 3600  # 1 hour for expiries
        self._contracts_cache_ttl = 1800  # 30 minutes for contracts
        
        self._initialized = True
    
    def _get_cache_key(self, symbol: str, data_type: str) -> str:
        """Generate cache key"""
        return f"upstox:{data_type}:{symbol.lower()}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache is still valid"""
        if cache_key not in self._cache_timestamps:
            return False
        
        cache_time = self._cache_timestamps[cache_key]
        ttl = self._expiry_cache_ttl if 'expiry' in cache_key else self._contracts_cache_ttl
        return (time.time() - cache_time) < ttl
    
    def _set_cache(self, cache_key: str, data: Any, ttl: int = None) -> None:
        """Set cache data"""
        try:
            # Use Redis if available
            if self._redis_client:
                if ttl:
                    self._redis_client.setex(cache_key, ttl, json.dumps(data))
                else:
                    self._redis_client.set(cache_key, json.dumps(data))
                logger.debug(f"Cached to Redis: {cache_key}")
            else:
                # Fallback to memory cache
                self._memory_cache[cache_key] = data
                logger.debug(f"Cached to memory: {cache_key}")
            
            # Set timestamp
            self._cache_timestamps[cache_key] = time.time()
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def _get_cache(self, cache_key: str) -> Optional[Any]:
        """Get cache data"""
        try:
            # Use Redis if available
            if self._redis_client:
                data = self._redis_client.get(cache_key)
                if data:
                    logger.debug(f"Cache hit from Redis: {cache_key}")
                    return json.loads(data)
                else:
                    logger.debug(f"Cache miss from Redis: {cache_key}")
                    return None
            else:
                # Fallback to memory cache
                if cache_key in self._memory_cache:
                    logger.debug(f"Cache hit from memory: {cache_key}")
                    return self._memory_cache[cache_key]
                else:
                    logger.debug(f"Cache miss from memory: {cache_key}")
                    return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache is still valid"""
        if cache_key not in self._cache_timestamps:
            return False
        
        cache_time = self._cache_timestamps[cache_key]
        ttl = self._expiry_cache_ttl if 'expiry' in cache_key else self._contracts_cache_ttl
        return (time.time() - cache_time) < ttl
    
    def _get_cache(self, cache_key: str) -> Optional[Any]:
        """Get cache data"""
        try:
            # Use Redis if available
            if self._redis_client:
                data = self._redis_client.get(cache_key)
                if data:
                    logger.debug(f"Cache hit from Redis: {cache_key}")
                    return json.loads(data)
                else:
                    logger.debug(f"Cache miss from Redis: {cache_key}")
                    return None
            else:
                # Fallback to memory cache
                if cache_key in self._memory_cache:
                    logger.debug(f"Cache hit from memory: {cache_key}")
                    return self._memory_cache[cache_key]
                else:
                    logger.debug(f"Cache miss from memory: {cache_key}")
                    return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def _get_client(self, access_token: str, version: str = "v3") -> httpx.AsyncClient:
        """Get authenticated HTTP client"""
        base_url = self.base_url_v3 if version == "v3" else self.base_url_v2
        
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=base_url,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=30.0
            )
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _make_request(self, method: str, url: str, access_token: str, **kwargs) -> httpx.Response:
        """Rate-limited request with 429 backoff"""
        async with self._rate_limit:
            # Defensive guard for rate limiting attributes
            if not hasattr(self, "_last_request_time"):
                self._last_request_time = 0.0
            if not hasattr(self, "_min_delay"):
                self._min_delay = 0.25
            
            # Rate limiting: minimum delay between requests
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            if time_since_last < self._min_delay:
                await asyncio.sleep(self._min_delay - time_since_last)
            
            self._last_request_time = time.time()
            
            client = await self._get_client(access_token)
            response = await getattr(client, method)(url, **kwargs)
            
            # Handle 429 rate limiting with exponential backoff
            if response.status_code == 429:
                logger.warning(f"Rate limited (429) - applying backoff")
                
                # Exponential backoff: 1s → 2s → 4s
                backoff_time = min(1.0 * self._backoff_multiplier, 4.0)
                self._backoff_multiplier = min(self._backoff_multiplier * 2, 8.0)
                
                logger.info(f"Waiting {backoff_time}s before retry (multiplier: {self._backoff_multiplier})")
                await asyncio.sleep(backoff_time)
                
                # Retry the request
                return await self._make_request(method, url, access_token, **kwargs)
            
            # Reset backoff on success
            self._backoff_multiplier = 1.0
            
            return response
    
    async def get_option_expiries(self, access_token: str, symbol: str) -> List[str]:
        """Get available expiry dates for symbol - WITH CACHING"""
        cache_key = self._get_cache_key(symbol, "expiry")
        
        # Check cache first
        cached_expiries = self._get_cache(cache_key)
        if cached_expiries and self._is_cache_valid(cache_key):
            logger.info(f"Cache hit for {symbol} expiries: {cached_expiries}")
            return cached_expiries
        
        try:
            # Get instrument key first
            instrument_key = self.INSTRUMENT_MAP.get(symbol.upper())
            if not instrument_key:
                raise APIResponseError(f"Unknown symbol: {symbol}")
            
            # Use REAL option contracts API
            response = await self._make_request(
                'get',
                f"https://api.upstox.com/v2/option/contract",
                access_token=access_token,
                params={
                    "instrument_key": instrument_key
                }
            )
            
            if response.status_code == 401:
                raise TokenExpiredError("Access token expired")
            elif response.status_code != 200:
                raise APIResponseError(f"HTTP {response.status_code}: Failed to fetch option contracts")
            
            data = response.json()
            logger.info(f"Downloaded {len(data)} option contracts for {symbol}")
            
            # Extract unique expiry dates from real contracts
            expiries_set = set()
            for contract in data:
                expiry = contract.get('expiry')
                if expiry:
                    expiries_set.add(expiry)
            
            # Convert to sorted list
            expiries = sorted(list(expiries_set))
            
            # Cache the result
            self._set_cache(cache_key, expiries, self._expiry_cache_ttl)
            
            logger.info(f"Real expiries for {symbol}: {expiries}")
            return expiries
            
        except Exception as e:
            logger.error(f"Error fetching option expiries for {symbol}: {e}")
            # Return fallback expiries on error - use current month logic
            from datetime import datetime, timedelta
            today = datetime.now()
            
            # Find next Thursdays (NSE expiry days) - same logic as above
            next_thursdays = []
            current_date = today
            
            # Find next 3 Thursdays
            while len(next_thursdays) < 3:
                # Move to next Thursday
                days_until_thursday = (3 - current_date.weekday() + 7) % 7
                if days_until_thursday == 0:
                    days_until_thursday = 7  # If today is Thursday, get next Thursday
                
                next_thursday = current_date + timedelta(days=days_until_thursday)
                next_thursdays.append(next_thursday.strftime('%Y-%m-%d'))
                current_date = next_thursday
            
            # Cache fallback result
            self._set_cache(cache_key, next_thursdays, self._expiry_cache_ttl)
            
            logger.info(f"Using emergency fallback expiries for {symbol}: {next_thursdays}")
            return next_thursdays
    
    async def get_option_chain(self, access_token: str, instrument_key: str, expiry_date: str = None) -> Dict[str, Any]:
        """Fetch option chain from Upstox API - WORKING ENDPOINT"""
        try:
            logger.info(f"=== INVESTIGATION: get_option_chain called with instrument_key={instrument_key}, expiry={expiry_date} ===")
            
            # Use WORKING option chain endpoint
            # Try without URL encoding first (like original working version)
            contracts_response = await self._make_request(
                'get',
                f"https://api.upstox.com/v2/option/chain",
                access_token=access_token,
                params={
                    "instrument_key": instrument_key,
                    "expiry_date": expiry_date
                }
            )
            
            logger.info(f"=== INVESTIGATION: Trying without URL encoding ===")
            logger.info(f"=== INVESTIGATION: HTTP Status: {contracts_response.status_code} ===")
            
            if contracts_response.status_code == 401:
                raise TokenExpiredError("Access token expired")
            elif contracts_response.status_code == 404:
                logger.error(f"Upstox 404 error for option contracts: {contracts_response.text}")
                raise APIResponseError(f"Invalid instrument or expiry: {instrument_key}, {expiry_date}")
            elif contracts_response.status_code != 200:
                logger.error(f"Upstox API error: {contracts_response.status_code} - {contracts_response.text}")
                raise APIResponseError(f"HTTP {contracts_response.status_code}: {contracts_response.text}")
            
            try:
                contracts_data = contracts_response.json()
                logger.info(f"=== INVESTIGATION: Option chain raw response type: {type(contracts_data)} ===")
                logger.info(f"=== INVESTIGATION: Option chain raw response: {str(contracts_data)[:500]} ===")
            except Exception as e:
                logger.error(f"=== INVESTIGATION: Error parsing option chain JSON: {e}")
                logger.error(f"=== INVESTIGATION: Response text: {contracts_response.text}")
                raise APIResponseError(f"Failed to parse option chain response: {e}")
            logger.info(f"=== INVESTIGATION: Raw JSON response type: {type(contracts_data)} ===")
            logger.info(f"=== INVESTIGATION: Raw JSON response keys: {list(contracts_data.keys()) if isinstance(contracts_data, dict) else 'Not a dict'} ===")
            
            # Process the raw Upstox data into expected format
            if isinstance(contracts_data, dict) and "data" in contracts_data:
                raw_data = contracts_data.get("data", [])
                logger.info(f"=== INVESTIGATION: Extracted raw_data type: {type(raw_data)}, length: {len(raw_data) if isinstance(raw_data, list) else 'Not a list'} ===")
            else:
                raw_data = contracts_data if isinstance(contracts_data, list) else []
                logger.info(f"=== INVESTIGATION: Using contracts_data directly as raw_data, type: {type(raw_data)}, length: {len(raw_data) if isinstance(raw_data, list) else 'Not a list'} ===")
            
            # Handle the actual Upstox response structure (ARRAY of strikes)
            calls = []
            puts = []
            
            if isinstance(raw_data, list):
                logger.info(f"=== INVESTIGATION: Processing {len(raw_data)} strike objects ===")
                # Upstox returns an array of strike objects
                for i, strike_data in enumerate(raw_data):
                    if isinstance(strike_data, dict):
                        strike_price = strike_data.get("strike_price", 0)
                        logger.info(f"=== INVESTIGATION: Processing strike {i+1}: {strike_price} ===")
                        
                        # Process call options
                        call_opt = strike_data.get("call_options", {})
                        if call_opt and "market_data" in call_opt:
                            calls.append({
                                "strike": strike_price,
                                "oi": call_opt["market_data"].get("oi", 0),
                                "ltp": call_opt["market_data"].get("ltp", 0),
                                "volume": call_opt["market_data"].get("volume", 0),
                                "iv": call_opt.get("option_greeks", {}).get("iv", 0),
                                "change": call_opt["market_data"].get("oi", 0) - call_opt["market_data"].get("prev_oi", 0)
                            })
                            logger.info(f"=== INVESTIGATION: Added call for strike {strike_price}: OI={call_opt['market_data'].get('oi', 0)} ===")
                        
                        # Process put options
                        put_opt = strike_data.get("put_options", {})
                        if put_opt and "market_data" in put_opt:
                            puts.append({
                                "strike": strike_price,
                                "oi": put_opt["market_data"].get("oi", 0),
                                "ltp": put_opt["market_data"].get("ltp", 0),
                                "volume": put_opt["market_data"].get("volume", 0),
                                "iv": put_opt.get("option_greeks", {}).get("iv", 0),
                                "change": put_opt["market_data"].get("oi", 0) - put_opt["market_data"].get("prev_oi", 0)
                            })
                            logger.info(f"=== INVESTIGATION: Added put for strike {strike_price}: OI={put_opt['market_data'].get('oi', 0)} ===")
                    else:
                        logger.warning(f"=== INVESTIGATION: Strike {i+1} is not a dict: {type(strike_data)} ===")
                else:
                    logger.warning(f"=== INVESTIGATION: raw_data is not a list: {type(raw_data)} ===")
            
            logger.info(f"=== INVESTIGATION: Final counts - Calls: {len(calls)}, Puts: {len(puts)} ===")
            
            # Return processed option chain data
            # Extract symbol name from instrument_key (e.g., "NSE_INDEX|Nifty 50" -> "Nifty 50")
            symbol_name = instrument_key.split("|")[-1] if "|" in instrument_key else instrument_key
            
            result = {
                "status": "success",
                "data": {
                    "calls": calls,
                    "puts": puts,
                    "symbol": symbol_name,
                    "expiry": expiry_date,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
            logger.info(f"=== INVESTIGATION: Returning result with {len(calls)} calls and {len(puts)} puts ===")
            return result
        except httpx.RequestError as e:
            logger.error(f"Network error fetching option chain for {instrument_key}: {e}")
            raise APIResponseError(f"Network error: {e}")
        except TokenExpiredError as e:
            logger.error(f"Token expired fetching option chain for {instrument_key}: {e}")
            raise APIResponseError(f"Token expired: {e}")
        except APIResponseError as e:
            logger.error(f"API error fetching option chain for {instrument_key}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching option chain: {e}")
            raise APIResponseError(f"Unexpected error: {e}")

    async def get_option_greeks(self, access_token: str, instrument_key: str) -> Dict[str, Any]:
        """Get option Greeks from Upstox API"""
        try:
            response = await self._make_request(
                'get',
                f"https://api.upstox.com/v3/market-quote/option-greek",
                access_token=access_token,
                params={
                    "instrument_key": instrument_key
                }
            )
            
            if response.status_code == 401:
                raise TokenExpiredError("Access token expired")
            elif response.status_code != 200:
                logger.error(f"Upstox API error: {response.status_code} - {response.text}")
                raise APIResponseError(f"HTTP {response.status_code}: {response.text}")
            
            data = response.json()
            logger.info(f"Option Greeks response for {instrument_key}: {data}")
            
            # Validate response structure
            if not isinstance(data, dict) or "data" not in data:
                raise APIResponseError("Invalid option Greeks response structure")
            
            return {
                "status": "success",
                "data": data["data"],
                "instrument_key": instrument_key,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except httpx.RequestError as e:
            logger.error(f"Network error fetching option Greeks for {instrument_key}: {e}")
            raise APIResponseError(f"Network error: {e}")
        except TokenExpiredError as e:
            logger.error(f"Token expired fetching option Greeks for {instrument_key}: {e}")
            raise
        except APIResponseError as e:
            logger.error(f"API error fetching option Greeks for {instrument_key}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching option Greeks: {e}")
            raise APIResponseError(f"Unexpected error: {e}")
    
    async def get_market_quote(self, access_token: str, instrument_key: str) -> Dict[str, Any]:
        """Get market quote from Upstox API - WORKING ENDPOINT"""
        try:
            response = await self._make_request(
                'get',
                f"https://api.upstox.com/v2/market-quote/ltp",
                access_token=access_token,
                params={
                    "instrument_key": instrument_key
                }
            )
            if response.status_code == 401:
                raise TokenExpiredError("Access token expired")
            elif response.status_code != 200:
                logger.error(f"Upstox API error: {response.status_code} - {response.text}")
                raise APIResponseError(f"HTTP {response.status_code}: {response.text}")
            
            data = response.json()
            logger.info(f"Upstox LTP response for {instrument_key}: {data}")
            
            # Validate response structure according to Upstox schema
            if not isinstance(data, dict):
                raise APIResponseError(f"Expected dict, got {type(data)}")
            
            if "status" not in data:
                raise APIResponseError("Missing 'status' field in response")
            
            if data["status"] != "success":
                raise APIResponseError(f"API returned status: {data['status']}")
            
            # Check for data field
            if "data" not in data:
                raise APIResponseError("Missing 'data' field in response")
            
            return data
            
        except httpx.RequestError as e:
            logger.error(f"Network error fetching LTP for {instrument_key}: {e}")
            raise APIResponseError(f"Network error: {e}")
        except TokenExpiredError as e:
            logger.error(f"Token expired fetching quote for {instrument_key}: {e}")
            raise  # Re-raise TokenExpiredError without changing it
        except APIResponseError as e:
            logger.error(f"API error fetching quote for {instrument_key}: {e}")
            raise  # Re-raise APIResponseError without changing it
        except Exception as e:
            logger.error(f"Unexpected error fetching quote for {instrument_key}: {e}")
            raise APIResponseError(f"Unexpected error: {e}")

    async def _log_final_response(self, response_data: Dict[str, Any]) -> None:
        """Log final backend response for forensic audit"""
        logger.info("=== TRANSFORMED BACKEND RESPONSE ===")
        logger.info(json.dumps(response_data, indent=2))
        logger.info("=== END TRANSFORMED BACKEND RESPONSE ===")
