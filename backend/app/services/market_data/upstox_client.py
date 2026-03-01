import threading
import asyncio
import httpx
import logging
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from ...core.config import settings
from .types import InstrumentInfo, APIResponseError, AuthenticationError
from app.utils.upstox_retry import retry_on_upstox_401
from fastapi import HTTPException
from app.services.upstox_auth_service import get_upstox_auth_service
from typing import Optional
from app.services.token_manager import token_manager

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
        
        # Instrument mapping for expiry fetching
        self.INSTRUMENT_MAP = {
            "NIFTY": "NSE_INDEX|Nifty 50",
            "BANKNIFTY": "NSE_INDEX|Nifty Bank",
            "FINNIFTY": "NSE_INDEX|Nifty Fin Service"
        }
        
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
            # Fallback to memory cache
            self._memory_cache[cache_key] = data
            logger.debug(f"Cached to memory: {cache_key}")
            
            # Set timestamp
            self._cache_timestamps[cache_key] = time.time()
            
        except Exception as e:
            logger.exception("Cache set error")
    
    def _get_cache(self, cache_key: str) -> Optional[Any]:
        """Get cache data"""
        try:
            # Fallback to memory cache
            if cache_key in self._memory_cache:
                logger.debug(f"Cache hit from memory: {cache_key}")
                return self._memory_cache[cache_key]
            else:
                logger.debug(f"Cache miss from memory: {cache_key}")
                return None
            
        except Exception as e:
            logger.exception("Cache get error")
            return None
    
    async def _get_client(self, access_token: str, version: str = "v3") -> httpx.AsyncClient:
        """Get authenticated HTTP client"""
        base_url = self.base_url_v3 if version == "v3" else self.base_url_v2
        
        # Recreate client ONLY if token or version changed
        auth_header = f"Bearer {access_token}"
        if self._client is None or self._client.headers.get("Authorization") != auth_header:
            if self._client:
                await self._client.aclose()
            
            self._client = httpx.AsyncClient(
                base_url=base_url,
                headers={"Authorization": auth_header},
                timeout=30.0
            )
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    @retry_on_upstox_401
    async def _make_request(self, method: str, url: str, **kwargs) -> httpx.Response:

        async with self._rate_limit:

            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            if time_since_last < self._min_delay:
                await asyncio.sleep(self._min_delay - time_since_last)

            self._last_request_time = time.time()

            access_token = await token_manager.get_valid_token()

            client = await self._get_client(access_token)

            method = method.lower()
            request_fn = getattr(client, method)

            response = await request_fn(url, **kwargs)

            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Upstox authentication required")

            if response.status_code == 429:
                await asyncio.sleep(1)
                return await request_fn(url, **kwargs)

        return response
    
    async def get_option_expiries(self, symbol: str) -> List[str]:
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
                params={
                    "instrument_key": instrument_key
                }
            )
            
            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Upstox authentication required")
            elif response.status_code != 200:
                raise APIResponseError(f"HTTP {response.status_code}: Failed to fetch option contracts")
            
            data = response.json()
            logger.info(f"Downloaded option contracts for {symbol}: {data}")
            
            # TASK 3 - FIX EXPIRY PARSING
            # Handle Upstox response: {"status":"success", "data":["2026-02-24","2026-03-02"]}
            contracts = data.get("data", [])
            expiries = []
            
            for contract in contracts:
                if isinstance(contract, str):
                    expiries.append(contract)
                elif isinstance(contract, dict):
                    expiry = contract.get("expiry")
                    if expiry:
                        expiries.append(expiry)
            
            # Sort expiries
            expiries = sorted(expiries)
            
            # Cache the result
            self._set_cache(cache_key, expiries, self._expiry_cache_ttl)
            
            logger.info(f"Real expiries for {symbol}: {expiries}")
            return expiries
            
        except HTTPException as e:
            # Preserve original status (401, 403, etc.)
            raise e
        except Exception as e:
            logger.exception("Unexpected internal error fetching option expiries")
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
    
    async def get_option_contracts(self, symbol: str) -> List[Dict[str, Any]]:
        """Get option contracts for index from local instruments file"""
        try:
            logger.info(f"Loading option contracts for {symbol} from local instruments")
            
            # For INDEX symbols, use local instruments.json instead of REST API
            if symbol.upper() in ["NIFTY", "BANKNIFTY"]:
                return await self._load_contracts_from_instruments(symbol)
            
            # For other symbols, validate and raise error
            raise ValueError(f"Unsupported symbol: {symbol}. Supported: NIFTY, BANKNIFTY")
                
        except Exception as e:
            logger.exception(f"Exception while fetching option contracts: {e}")
            raise APIResponseError(f"Failed to fetch option contracts: {str(e)}")
    
    async def _load_contracts_from_instruments(self, symbol: str) -> List[Dict[str, Any]]:
        """Load option contracts from local instruments.json file"""
        try:
            import json
            from pathlib import Path
            
            instruments_file = Path("data/instruments.json")
            if not instruments_file.exists():
                raise FileNotFoundError(f"Instruments file not found: {instruments_file}")
            
            with open(instruments_file, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            
            if isinstance(raw, dict) and "instruments" in raw:
                instruments = raw["instruments"]
            elif isinstance(raw, list):
                instruments = raw
            else:
                raise ValueError("Invalid instruments.json format")
            
            symbol_upper = symbol.upper()
            contracts = []
            
            for instrument in instruments:
                
                if not isinstance(instrument, dict):
                    continue
                    
                if (
                    instrument.get("segment") == "NSE_FO" and
                    instrument.get("name") == symbol_upper and
                    instrument.get("instrument_type") in ["CE", "PE"]
                ):
                    
                    required_fields = ["strike_price", "expiry", "instrument_key"]
                    if not all(field in instrument for field in required_fields):
                        continue
                    
                    # 🔥🔥🔥 EXPIRY NORMALIZATION FIX 🔥🔥🔥
                    expiry_raw = instrument.get("expiry")

                    try:
                        # Case 1: YYYYMMDD int (20260226)
                        if isinstance(expiry_raw, int) and len(str(expiry_raw)) == 8:
                            expiry = datetime.strptime(
                                str(expiry_raw),
                                "%Y%m%d"
                            ).strftime("%Y-%m-%d")

                        # Case 2: Epoch millis
                        elif isinstance(expiry_raw, (int, float)) and expiry_raw > 10**12:
                            expiry = datetime.fromtimestamp(
                                expiry_raw / 1000
                            ).strftime("%Y-%m-%d")

                        # Case 3: Already correct
                        else:
                            expiry = str(expiry_raw)

                    except Exception:
                        continue

                    contract = {
                        "strike": float(instrument["strike_price"]),
                        "option_type": instrument["instrument_type"],
                        "expiry": expiry,
                        "instrument_key": instrument["instrument_key"]
                    }
                    
                    contracts.append(contract)
            
            logger.info(f"Transformed {len(contracts)} contracts for {symbol}")
            return contracts
            
        except Exception as e:
            logger.error(f"Failed to load contracts from instruments.json: {e}")
            raise
    
    async def get_instruments(self) -> List[Dict[str, Any]]:
        """Get all instruments from Upstox API"""
        try:
            logger.info("Fetching instruments from Upstox API")
            
            response = await self._make_request(
                "GET",
                f"{self.base_url_v2}/instruments"
            )
            
            if response.status_code == 200:
                data = response.json()
                instruments = data.get("data", [])
                logger.info(f"Retrieved {len(instruments)} instruments from Upstox API")
                return instruments
            elif response.status_code == 401:
                raise HTTPException(status_code=401, detail="Upstox authentication required")
            elif response.status_code == 403:
                logger.error("Access forbidden while fetching instruments")
                raise AuthenticationError("Access forbidden")
            else:
                logger.error(f"Failed to fetch instruments: {response.status_code} - {response.text}")
                raise APIResponseError(f"API Error: {response.status_code}")
                
        except Exception as e:
            logger.exception(f"Exception while fetching instruments: {e}")
            raise APIResponseError(f"Failed to fetch instruments: {str(e)}")
    
    async def get_option_chain(self, instrument_key: str, expiry_date: str = None) -> Dict[str, Any]:
        """Fetch option chain from Upstox API - WORKING ENDPOINT"""
        try:
            # Use WORKING option chain endpoint
            # Try without URL encoding first (like original working version)
            contracts_response = await self._make_request(
                'get',
                f"https://api.upstox.com/v2/option/chain",
                params={
                    "instrument_key": instrument_key,
                    "expiry_date": expiry_date
                }
            )
            
            if contracts_response.status_code == 401:
                raise HTTPException(status_code=401, detail="Upstox authentication required")
            elif contracts_response.status_code == 404:
                logger.error(f"Upstox 404 error for option contracts: {contracts_response.text}")
                raise APIResponseError(f"Invalid instrument or expiry: {instrument_key}, {expiry_date}")
            elif contracts_response.status_code != 200:
                logger.error(f"Upstox API error: {contracts_response.status_code} - {contracts_response.text}")
                raise APIResponseError(f"HTTP {contracts_response.status_code}: {contracts_response.text}")
            
            try:
                contracts_data = contracts_response.json()
            except HTTPException as e:
                raise e
            except Exception as e:
                logger.exception("Unexpected internal error parsing JSON")
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error"
                )
            
            # Process the raw Upstox data into expected format
            if isinstance(contracts_data, dict) and "data" in contracts_data:
                raw_data = contracts_data.get("data", [])
            else:
                raw_data = contracts_data if isinstance(contracts_data, list) else []
            
            # Handle the actual Upstox response structure (ARRAY of strikes)
            calls = []
            puts = []
            
            if isinstance(raw_data, list):
                # Upstox returns an array of strike objects
                for i, strike_data in enumerate(raw_data):
                    if isinstance(strike_data, dict):
                        strike_price = strike_data.get("strike_price", 0)
                        
                        # Process call options
                        call_opt = strike_data.get("call_options", {})
                        if call_opt and "market_data" in call_opt:
                            calls.append({
                                "strike": strike_price,
                                "oi": call_opt["market_data"].get("oi", 0),
                                "ltp": call_opt["market_data"].get("ltp") or call_opt["market_data"].get("last_price") or call_opt["market_data"].get("last_traded_price") or 0,
                                "volume": call_opt["market_data"].get("volume", 0),
                                "iv": call_opt.get("option_greeks", {}).get("iv", 0),
                                "change": call_opt["market_data"].get("oi", 0) - call_opt["market_data"].get("prev_oi", 0)
                            })
                        
                        # Process put options
                        put_opt = strike_data.get("put_options", {})
                        if put_opt and "market_data" in put_opt:
                            puts.append({
                                "strike": strike_price,
                                "oi": put_opt["market_data"].get("oi", 0),
                                "ltp": put_opt["market_data"].get("ltp") or put_opt["market_data"].get("last_price") or put_opt["market_data"].get("last_traded_price") or 0,
                                "volume": put_opt["market_data"].get("volume", 0),
                                "iv": put_opt.get("option_greeks", {}).get("iv", 0),
                                "change": put_opt["market_data"].get("oi", 0) - put_opt["market_data"].get("prev_oi", 0)
                            })
            
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
            
            return result
        except httpx.RequestError as e:
            logger.error(f"Network error fetching option chain for {instrument_key}: {e}")
            raise APIResponseError(f"Network error: {e}")
        except HTTPException as e:
            # Preserve original status (401, 403, etc.)
            raise e
        except Exception as e:
            logger.exception("Unexpected internal error fetching option chain")
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )

    async def get_option_greeks(self, instrument_key: str) -> Dict[str, Any]:
        """Get option Greeks from Upstox API"""
        try:
            response = await self._make_request(
                'get',
                f"https://api.upstox.com/v3/market-quote/option-greek",
                params={
                    "instrument_key": instrument_key
                }
            )
            
            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Upstox authentication required")
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
        except HTTPException as e:
            # Preserve original status (401, 403, etc.)
            raise e
        except APIResponseError as e:
            logger.error(f"API error fetching option Greeks for {instrument_key}: {e}")
            raise
        except Exception as e:
            logger.exception("Unexpected internal error fetching option Greeks")
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )
    
    async def get_market_quote(self, instrument_key: str) -> Dict[str, Any]:
        """Get market quote from Upstox API - WORKING ENDPOINT"""
        try:
            response = await self._make_request(
                'get',
                f"https://api.upstox.com/v2/market-quote/ltp",
                params={
                    "instrument_key": instrument_key
                }
            )
            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Upstox authentication required")
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
        except HTTPException as e:
            # Preserve original status (401, 403, etc.)
            raise e
        except APIResponseError as e:
            logger.error(f"API error fetching quote for {instrument_key}: {e}")
            raise
        except Exception as e:
            logger.exception("Unexpected internal error fetching quote")
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )
    async def get_ltp(self, instrument_key: str) -> Optional[float]:
        """
        Fetch latest LTP for index instrument (NIFTY / BANKNIFTY)
        Used by LiveOptionChainBuilder REST fallback for ATM initialization
        """
        try:
            
            token = await token_manager.get_valid_token()

            if not token:
                logger.error("❌ No access token for LTP fetch")
                return None

            response = await self.get_market_quote(instrument_key)

            if not response or "data" not in response:
                logger.error(f"❌ Invalid LTP response for {instrument_key}")
                return None

            key = next(iter(response["data"]))
            ltp = response["data"][key].get("last_price")

            if ltp:
                return float(ltp)

            return None

        except Exception as e:
            logger.error(f"❌ LTP REST ERROR for {instrument_key}: {e}")
            return None

    async def _log_final_response(self, response_data: Dict[str, Any]) -> None:
        """Log final backend response for forensic audit"""
        logger.info("=== TRANSFORMED BACKEND RESPONSE ===")
        logger.info(json.dumps(response_data, indent=2))
        logger.info("=== END TRANSFORMED BACKEND RESPONSE ===")
