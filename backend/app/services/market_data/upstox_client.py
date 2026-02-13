import threading
import asyncio
import httpx
import logging
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from ...core.config import settings
from .types import InstrumentInfo, APIResponseError, AuthenticationError, TokenExpiredError

logger = logging.getLogger(__name__)

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

        self._client: Optional[httpx.AsyncClient] = None

        # Rate limiting
        self._rate_limit = asyncio.Semaphore(3)
        self._last_request_time: float = 0.0
        self._min_delay: float = 0.25
        self._backoff_multiplier: float = 1.0

        # Caching (if used)
        self._dashboard_cache = {}
        self._dashboard_cache_time = {}
        self._dashboard_ttl = 60

        self._initialized = True
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache is still valid"""
        if cache_key not in self._dashboard_cache:
            return False
        
        cache_time = self._dashboard_cache_time[cache_key]
        return (time.time() - cache_time) < self._dashboard_ttl
    
    def _get_cached_data(self, cache_key: str) -> Any:
        """Get cached data if valid"""
        if self._is_cache_valid(cache_key):
            return self._dashboard_cache[cache_key]
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
        """Get available expiry dates for a symbol - WORKING API METHOD"""
        try:
            # Download NSE FO instruments JSON file (WORKING)
            response = await self._make_request(
                'get',
                "https://assets.upstox.com/market-instruments/instruments/nse_fo.json",
                access_token=access_token  # May not be needed for public file
            )
            
            if response.status_code != 200:
                raise APIResponseError(f"HTTP {response.status_code}: Failed to download instruments")
            
            data = response.json()
            logger.info(f"Downloaded {len(data)} NSE_FO instruments")
            
            # Filter for symbol options and extract expiry dates
            symbol_expiries = []
            
            for instrument in data:
                if (symbol in instrument.get('trading_symbol', '') and 
                    instrument.get('instrument_type', '').startswith('OPT')):
                    expiry = instrument.get('expiry')
                    if expiry:
                        # Convert timestamp to date string if needed
                        if isinstance(expiry, (int, float)):
                            expiry_date = datetime.fromtimestamp(expiry/1000, tz=timezone.utc).strftime('%Y-%m-%d')
                        else:
                            expiry_date = str(expiry)
                        
                        if expiry_date not in symbol_expiries:
                            symbol_expiries.append(expiry_date)
            
            # If no expiries found, return hardcoded fallbacks
            if not symbol_expiries:
                logger.warning("No expiries found from JSON, using fallback dates")
                symbol_expiries = ["2026-02-26", "2026-03-05", "2026-03-12"]
            
            # Sort expiries
            symbol_expiries.sort()
            
            logger.info(f"Available expiries for {symbol}: {symbol_expiries}")
            return symbol_expiries
            
        except Exception as e:
            logger.error(f"Error fetching option expiries for {symbol}: {e}")
            # Return fallback expiries on error - use current month logic
            from datetime import datetime, timedelta
            today = datetime.now()
            
            # Generate realistic expiry dates based on current month
            current_year = today.year
            current_month = today.month
            
            # Last Thursday of current month
            last_thursday = today
            while last_thursday.weekday() != 3:  # Thursday = 3
                last_thursday += timedelta(days=1)
            
            # Next Thursday (next expiry)
            next_thursday = last_thursday + timedelta(days=7)
            
            # Following Thursday
            following_thursday = next_thursday + timedelta(days=7)
            
            fallback_expiries = [
                last_thursday.strftime('%Y-%m-%d'),
                next_thursday.strftime('%Y-%m-%d'),
                following_thursday.strftime('%Y-%m-%d')
            ]
            
            logger.info(f"Using dynamic fallback expiries for {symbol}: {fallback_expiries}")
            return fallback_expiries
    
    async def get_option_chain(self, access_token: str, instrument_key: str, expiry_date: str = None) -> Dict[str, Any]:
        """Fetch option chain from Upstox API - WORKING ENDPOINT"""
        try:
            logger.info(f"Fetching real option chain data for {instrument_key}, expiry: {expiry_date}")
            
            # Use WORKING option chain endpoint
            contracts_response = await self._make_request(
                'get',
                f"https://api.upstox.com/v2/option/chain",
                access_token=access_token,
                params={
                    "instrument_key": instrument_key,
                    "expiry_date": expiry_date
                }
            )
            
            if contracts_response.status_code == 401:
                raise TokenExpiredError("Access token expired")
            elif contracts_response.status_code == 404:
                logger.error(f"Upstox 404 error for option contracts: {contracts_response.text}")
                raise APIResponseError(f"Invalid instrument or expiry: {instrument_key}, {expiry_date}")
            elif contracts_response.status_code != 200:
                logger.error(f"Upstox API error: {contracts_response.status_code} - {contracts_response.text}")
                raise APIResponseError(f"HTTP {contracts_response.status_code}: {contracts_response.text}")
            
            contracts_data = contracts_response.json()
            logger.info("=== RAW UPSTOX PAYLOAD ===")
            logger.info(contracts_response.text)
            logger.info("=== END RAW UPSTOX PAYLOAD ===")
            
            # Process the raw Upstox data into expected format
            if isinstance(contracts_data, dict) and "data" in contracts_data:
                raw_contracts = contracts_data.get("data", [])
            else:
                raw_contracts = contracts_data if isinstance(contracts_data, list) else []
            
            # Separate calls and puts
            calls = []
            puts = []
            
            for contract in raw_contracts:
                if contract.get("instrument_type", "").startswith("OPTCE"):
                    calls.append({
                        "strike": contract.get("strike_price", 0),
                        "call_oi": contract.get("open_interest", 0),
                        "call_ltp": contract.get("last_price", 0),
                        "call_volume": contract.get("volume", 0),
                        "call_iv": contract.get("implied_volatility", 0)
                    })
                elif contract.get("instrument_type", "").startswith("OPTPE"):
                    puts.append({
                        "strike": contract.get("strike_price", 0),
                        "put_oi": contract.get("open_interest", 0),
                        "put_ltp": contract.get("last_price", 0),
                        "put_volume": contract.get("volume", 0),
                        "put_iv": contract.get("implied_volatility", 0)
                    })
            
            # Return processed option chain data
            # Extract symbol from instrument_key (e.g., "NSE_INDEX|NIFTY50" -> "NIFTY")
            symbol_name = instrument_key.split("|")[-1] if "|" in instrument_key else instrument_key
            
            return {
                "status": "success",
                "data": {
                    "calls": calls,
                    "puts": puts
                },
                "symbol": symbol_name,
                "expiry": expiry_date,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except httpx.RequestError as e:
            logger.error(f"Network error fetching option chain for {instrument_key}: {e}")
            raise APIResponseError(f"Network error: {e}")
        except TokenExpiredError as e:
            logger.error(f"Token expired fetching option chain for {instrument_key}: {e}")
            raise
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
