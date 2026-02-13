import asyncio
import logging
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from ...models.market_data import OptionChainSnapshot
from .upstox_client import UpstoxClient
from .types import APIResponseError, TokenExpiredError
from ..upstox_auth_service import get_upstox_auth_service

logger = logging.getLogger(__name__)

class OptionChainService:
    """Service for fetching and managing option chain data"""
    
    def __init__(self):
        # Use singleton UpstoxClient instance
        from .upstox_client import UpstoxClient
        self.client = UpstoxClient()
        self.auth_service = get_upstox_auth_service()
        # OI cache for change calculation
        self._oi_cache: Dict[str, Dict[str, Dict[str, Dict[str, float]]]] = {}
        # Thread safety lock
        self._cache_lock = threading.Lock()
        # Storage for all expiries
        self._all_expiries = {}

    async def _get_instrument_key(self, symbol: str) -> str:
        """Get instrument key for symbol"""
        # Use hardcoded mappings for now - in production, use instrument service
        mappings = {
            "NIFTY": "NSE_FO|NIFTY",
            "BANKNIFTY": "NSE_FO|BANKNIFTY",
        }
    
        instrument_key = mappings.get(symbol.upper())
        if not instrument_key:
            raise APIResponseError(f"Unknown symbol: {symbol}")
    
        return instrument_key
    
    async def get_option_chain(self, symbol: str, expiry_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get option chain for a symbol"""
        try:
            # Add debug log for OI recalculation
            logger.info("Option chain recalculated - no response caching used")
            
            # Get access token
            token = await self.auth_service.get_valid_access_token()
            if not token:
                raise APIResponseError("No access token available")
            
            # If no expiry provided, resolve to nearest expiry
            if not expiry_date:
                logger.info(f"No expiry provided, resolving nearest expiry for {symbol}")
                expiry_date = await self._get_nearest_expiry(symbol, token)
                logger.info(f"Resolved to expiry: {expiry_date}")
            
            # Get instrument key for options (NSE_FO namespace)
            instrument_key = await self._get_instrument_key(symbol)
            logger.info(f"Using instrument_key for options: {instrument_key}")
            
            # Fetch option chain
            logger.info(f"Fetching option chain for {symbol}, expiry: {expiry_date}")
            
            # Make API call using Upstox client
            response_data = await self.client.get_option_chain(token, instrument_key, expiry_date)
            logger.info(f"Upstox option chain response status: {response_data}")
            
            # Handle 404 errors specifically
            if isinstance(response_data, dict) and "status_code" in response_data:
                if response_data["status_code"] == 404:
                    logger.error(f"Upstox 404 error for instrument {instrument_key}: {response_data}")
                    raise APIResponseError(f"Invalid instrument for options: {instrument_key}")
            
            # Extract the actual data from response
            # Handle real Upstox data structure
            if isinstance(response_data, dict) and "data" in response_data:
                chain_data = response_data["data"]
                
                # Real Upstox data format
                if isinstance(chain_data, dict) and "calls" in chain_data:
                    # Real data format from Upstox API
                    calls = chain_data["calls"]
                    puts = chain_data["puts"]
                    
                    # Thread-safe OI cache operations
                    with self._cache_lock:
                        # Initialize OI cache for symbol if not exists
                        if symbol not in self._oi_cache:
                            self._oi_cache[symbol] = {}
                        if expiry_date not in self._oi_cache[symbol]:
                            self._oi_cache[symbol][expiry_date] = {}
                        
                        # Process calls for OI change calculation
                        for item in calls:
                            strike = str(item.get("strike", ""))
                            if strike:
                                if strike not in self._oi_cache[symbol][expiry_date]:
                                    self._oi_cache[symbol][expiry_date][strike] = {}
                                
                                current_oi = item.get("oi", 0)
                                previous_oi = self._oi_cache[symbol][expiry_date][strike].get("call_oi", 0)
                                oi_change = current_oi - previous_oi
                                
                                # Update cache
                                self._oi_cache[symbol][expiry_date][strike]["call_oi"] = current_oi
                                self._oi_cache[symbol][expiry_date][strike]["call_change"] = oi_change
                                
                                # Update item with change
                                item["change"] = oi_change
                        
                        # Process puts for OI change calculation
                        for item in puts:
                            strike = str(item.get("strike", ""))
                            if strike:
                                if strike not in self._oi_cache[symbol][expiry_date]:
                                    self._oi_cache[symbol][expiry_date][strike] = {}
                                
                                current_oi = item.get("oi", 0)
                                previous_oi = self._oi_cache[symbol][expiry_date][strike].get("put_oi", 0)
                                oi_change = current_oi - previous_oi
                                
                                # Update cache
                                self._oi_cache[symbol][expiry_date][strike]["put_oi"] = current_oi
                                self._oi_cache[symbol][expiry_date][strike]["put_change"] = oi_change
                                
                                # Update item with change
                                item["change"] = oi_change
                    
                    # Return the structured option chain data
                    result = {
                        "symbol": symbol,
                        "expiry": expiry_date,
                        "calls": calls,
                        "puts": puts,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    
                    # Log final backend response for forensic audit
                    await self.client._log_final_response(result)
                    
                    return result
                else:
                    raise APIResponseError("Invalid data structure from Upstox API")
            else:
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
    
    async def get_oi_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get OI analysis from option chain data"""
        try:
            # Get current option chain
            chain_data = await self.get_option_chain(symbol)
            
            if not chain_data:
                return {"error": "No option chain data available"}
            
            # Calculate OI metrics
            total_call_oi = sum(item.get("call_oi", 0) for item in chain_data if item.get("option_type") == "CE")
            total_put_oi = sum(item.get("put_oi", 0) for item in chain_data if item.get("option_type") == "PE")
            
            # Find ATM strike
            strikes = [item.get("strike_price", 0) for item in chain_data]
            atm_strike = min(strikes, key=lambda x: abs(x - strikes[0]) if strikes else 0)
            
            # Calculate PCR
            pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 0
            
            # OI concentration
            top_3_calls = sorted([item for item in chain_data if item.get("option_type") == "CE"], 
                               key=lambda x: x.get("call_oi", 0), reverse=True)[:3]
            top_3_puts = sorted([item for item in chain_data if item.get("option_type") == "PE"], 
                              key=lambda x: x.get("put_oi", 0), reverse=True)[:3]
            
            return {
                "total_call_oi": total_call_oi,
                "total_put_oi": total_put_oi,
                "pcr": round(pcr, 2),
                "atm_strike": atm_strike,
                "top_3_call_strikes": top_3_calls,
                "top_3_put_strikes": top_3_puts,
                "total_strikes": len(chain_data),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating OI analysis for {symbol}: {e}")
            return {
                "error": "Failed to calculate OI analysis",
                "detail": str(e)
            }
    
    async def _get_nearest_expiry(self, symbol: str, token: str) -> str:
        """Get nearest expiry date for symbol - REAL UPSTOX API VERSION"""
        try:
            # Use the new dedicated expiry method
            expiries = await self.client.get_option_expiries(token, symbol)
            
            if not expiries:
                raise APIResponseError("No expiry dates available")
            
            # Return the nearest expiry
            nearest_expiry = expiries[0]
            logger.info(f"Nearest expiry for {symbol}: {nearest_expiry}")
            
            # Store all expiries for dropdown
            self._all_expiries[symbol] = expiries
            
            return nearest_expiry
            
        except Exception as e:
            logger.error(f"Error getting expiry for {symbol}: {e}")
            raise APIResponseError(f"Failed to get expiry: {e}")



