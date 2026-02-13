import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from .upstox_client import UpstoxClient, APIResponseError, TokenExpiredError
from ..upstox_auth_service import UpstoxAuthService

logger = logging.getLogger(__name__)

class OptionChainService:
    """Service for handling option chain data"""
    
    def __init__(self, auth_service: UpstoxAuthService):
        self.auth_service = auth_service
        self.client = UpstoxClient()
        self._cache_lock = asyncio.Lock()
        self._oi_cache = {}  # Cache for OI change calculations
    
    async def _get_instrument_key(self, symbol: str) -> str:
        """Get instrument key for options"""
        try:
            mappings = {
                "NIFTY": "NSE_INDEX|Nifty 50",
                "BANKNIFTY": "NSE_INDEX|Nifty Bank",
            }
            
            instrument_key = mappings.get(symbol.upper())
            if not instrument_key:
                raise APIResponseError(f"Unknown symbol: {symbol}")
            
            logger.info(f"=== INVESTIGATION: Returning instrument_key: {instrument_key} ===")
            return instrument_key
        except Exception as e:
            logger.error(f"=== INVESTIGATION: Error in _get_instrument_key: {e} ===")
            raise APIResponseError(f"Failed to get instrument key: {e}")
    
    async def get_option_chain(self, symbol: str, expiry_date: Optional[str] = None) -> Dict[str, Any]:
        """Get option chain for a symbol"""
        try:
            logger.info(f"=== INVESTIGATION: get_option_chain called with symbol={symbol}, expiry={expiry_date} ===")
            
            # Get access token
            token = await self.auth_service.get_valid_access_token()
            if not token:
                logger.error("=== INVESTIGATION: No access token available ===")
                raise APIResponseError("No access token available")
            
            logger.info(f"=== INVESTIGATION: Got token, length={len(token) if token else 0} ===")
            
            # If no expiry provided, resolve to nearest expiry
            if not expiry_date:
                logger.info(f"No expiry provided, resolving nearest expiry for {symbol}")
                expiry_date = await self._get_nearest_expiry(symbol, token)
                logger.info(f"Resolved to expiry: {expiry_date}")
            
            # Get instrument key for options (NSE_FO namespace)
            instrument_key = await self._get_instrument_key(symbol)
            logger.info(f"=== INVESTIGATION: Using instrument_key: {instrument_key} ===")
            
            # Fetch option chain
            logger.info(f"=== INVESTIGATION: Fetching option chain for {symbol}, expiry: {expiry_date} ===")
            
            # Make API call using Upstox client
            response_data = await self.client.get_option_chain(token, instrument_key, expiry_date)
            logger.info(f"=== INVESTIGATION: Upstox client response type: {type(response_data)} ===")
            logger.info(f"=== INVESTIGATION: Upstox client response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'} ===")
            
            if isinstance(response_data, dict) and "data" in response_data:
                chain_data = response_data["data"]
                logger.info(f"=== INVESTIGATION: chain_data type: {type(chain_data)} ===")
                logger.info(f"=== INVESTIGATION: chain_data keys: {list(chain_data.keys()) if isinstance(chain_data, dict) else 'Not a dict'} ===")
                
                if isinstance(chain_data, dict) and "calls" in chain_data:
                    calls = chain_data["calls"]
                    puts = chain_data["puts"]
                    
                    logger.info(f"=== INVESTIGATION: Found {len(calls)} calls and {len(puts)} puts ===")
                    if calls:
                        logger.info(f"=== INVESTIGATION: First call sample: {calls[0]} ===")
                    if puts:
                        logger.info(f"=== INVESTIGATION: First put sample: {puts[0]} ===")
                    
                    result = {
                        "symbol": symbol,
                        "expiry": expiry_date,
                        "calls": calls,
                        "puts": puts,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    
                    logger.info(f"=== INVESTIGATION: Returning result with {len(result.get('calls', []))} calls and {len(result.get('puts', []))} puts ===")
                    return result
                else:
                    logger.error(f"=== INVESTIGATION: Invalid chain_data structure: {chain_data} ===")
                    raise APIResponseError("Invalid data structure from Upstox API")
            else:
                logger.error(f"=== INVESTIGATION: Invalid response structure from Upstox API: {response_data} ===")
                raise APIResponseError("Invalid response structure from Upstox API")
        
        except TokenExpiredError as e:
            logger.error(f"Token expired fetching option chain for {symbol}: {e}")
            raise
        except APIResponseError as e:
            logger.error(f"API error for {symbol}: {e}")
            # Return proper error response for frontend
            if "404" in str(e):
                return {
                    "status": "error",
                    "error": "Invalid instrument or expiry",
                    "detail": str(e)
                }
            elif "429" in str(e):
                return {
                    "status": "rate_limit",
                    "error": "Rate limit exceeded",
                    "detail": str(e)
                }
            else:
                return {
                    "status": "error",
                    "error": "API error",
                    "detail": str(e)
                }
        except Exception as e:
            logger.error(f"Unexpected error fetching option chain for {symbol}: {e}")
            raise APIResponseError(f"Unexpected error: {e}")
    
    async def _get_nearest_expiry(self, symbol: str, token: str) -> str:
        """Get nearest expiry date for symbol"""
        try:
            expiries = await self.client.get_option_expiries(token, symbol)
            if expiries and len(expiries) > 0:
                return expiries[0]  # Return first (nearest) expiry
            else:
                raise APIResponseError("No expiry dates available")
        except Exception as e:
            logger.error(f"Error getting nearest expiry: {e}")
            raise APIResponseError(f"Failed to get expiry dates: {e}")
    
    async def get_oi_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get OI analysis from option chain data"""
        try:
            # Get option chain data
            chain_data = await self.get_option_chain(symbol)
            
            if not chain_data:
                return {"error": "No option chain data available"}
            
            # Calculate OI metrics
            total_call_oi = sum(item.get("oi", 0) for item in chain_data.get("calls", []))
            total_put_oi = sum(item.get("oi", 0) for item in chain_data.get("puts", []))
            
            put_call_ratio = total_put_oi / total_call_oi if total_call_oi > 0 else 0
            
            return {
                "symbol": symbol,
                "total_call_oi": total_call_oi,
                "total_put_oi": total_put_oi,
                "put_call_ratio": put_call_ratio,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating OI analysis: {e}")
            return {"error": "Failed to calculate OI analysis"}
