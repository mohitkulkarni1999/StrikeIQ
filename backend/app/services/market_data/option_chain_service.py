import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from .upstox_client import UpstoxClient
from .types import APIResponseError, TokenExpiredError, AuthenticationError
from ..intelligence_aggregator import IntelligenceAggregator
from ..upstox_auth_service import get_upstox_auth_service, UpstoxAuthService
from ...utils.spot_price import get_spot_price
from ..cache_service import cache_service
from ..token_manager import get_token_manager
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class OptionChainService:
    """Service for handling option chain data"""
    
    def __init__(self, auth_service: UpstoxAuthService):
        self.auth_service = auth_service
        self.client = UpstoxClient()
        # Use global token manager instance
        from ..token_manager import token_manager
        self.token_manager = token_manager
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
        """Get option chain for a symbol with caching"""
        try:
            logger.info(f"=== INVESTIGATION: get_option_chain called with symbol={symbol}, expiry={expiry_date} ===")
            
            # Check auth service credentials FIRST before any other operations
            logger.info(f"=== INVESTIGATION: Token manager state before check: valid={self.token_manager.is_valid} ===")
            self.token_manager.check_auth_service(self.auth_service)
            logger.info(f"=== INVESTIGATION: Token manager state after check: valid={self.token_manager.is_valid} ===")
            
            # Check cache first
            cache_key = f"option_chain:{symbol}:{expiry_date or 'latest'}"
            cached_result = await cache_service.get(cache_key)
            
            if cached_result:
                logger.info(f"=== INVESTIGATION: Cache hit for {symbol} ===")
                return cached_result
            
            logger.info(f"=== INVESTIGATION: Cache miss for {symbol}, fetching from API ===")
            
            # Get access token
            token = await self.auth_service.get_valid_access_token()
            if not token:
                logger.error("=== INVESTIGATION: No access token available ===")
                self.token_manager.invalidate("No access token available")
                raise HTTPException(
                    status_code=401,
                    detail="Upstox authentication required"
                )
            
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
            try:
                print(f"DEBUG: About to call Upstox client for {symbol}")
                response_data = await self.client.get_option_chain(token, instrument_key, expiry_date)
                print(f"DEBUG: Upstox client returned successfully")
            except HTTPException as e:
                # Preserve original status (401, 403, etc.)
                print(f"DEBUG: HTTPException caught in service: {e.status_code}")
                if e.status_code == 401:
                    self.token_manager.invalidate("Upstox token revoked or expired")
                raise e
            except TokenExpiredError as api_error:
                print(f"DEBUG: TokenExpiredError caught in service: {api_error}")
                self.token_manager.invalidate("Upstox token revoked or expired")
                raise HTTPException(
                    status_code=401,
                    detail="Upstox authentication required"
                )
            except Exception as api_error:
                print(f"DEBUG: Generic API error caught: {api_error}")
                logger.exception("Unexpected internal error in option chain service")
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error"
                )
                    
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
                    
                    # Calculate production-grade OI Analytics
                    total_call_oi = sum(call.get("oi", 0) for call in calls)
                    total_put_oi = sum(put.get("oi", 0) for put in puts)
                    total_oi = total_call_oi + total_put_oi
                    
                    # Calculate PCR with safe division
                    pcr = 0 if total_call_oi == 0 else round(total_put_oi / total_call_oi, 4)
                    
                    # Find strongest support/resistance levels
                    resistance_strike = max(calls, key=lambda x: x.get("oi", 0)).get("strike", 0) if calls else 0
                    support_strike = max(puts, key=lambda x: x.get("oi", 0)).get("strike", 0) if puts else 0
                    
                    # Calculate OI dominance (0-1 scale)
                    oi_dominance = 0 if total_oi == 0 else abs(total_call_oi - total_put_oi) / total_oi
                    
                    # Calculate PCR strength (0-100 scale)
                    pcr_strength = min(abs(pcr - 1) * 100, 100)
                    
                    # Calculate bias score (0-100 scale)
                    # Weighted combination: PCR (40%), OI dominance (30%), positioning (30%)
                    pcr_bias = (pcr - 1) * 50  # PCR contribution (-50 to +50)
                    oi_bias = (total_put_oi - total_call_oi) / max(total_oi, 1) * 50  # OI dominance contribution
                    positioning_bias = 0  # Placeholder for positioning analysis
                    
                    bias_score = max(0, min(100, 50 + pcr_bias + oi_bias * 0.3 + positioning_bias * 0.3))
                    
                    # Determine bias label based on score
                    if bias_score >= 60:
                        bias_label = "BULLISH"
                    elif bias_score <= 40:
                        bias_label = "BEARISH"
                    else:
                        bias_label = "NEUTRAL"
                    
                    # Calculate position score (0-100 scale)
                    # Based on OI concentration and distribution
                    call_oi_concentration = max(call.get("oi", 0) for call in calls) / max(total_call_oi, 1) if calls else 0
                    put_oi_concentration = max(put.get("oi", 0) for put in puts) / max(total_put_oi, 1) if puts else 0
                    position_score = (call_oi_concentration + put_oi_concentration) * 50
                    
                    analytics = {
                        "total_call_oi": total_call_oi,
                        "total_put_oi": total_put_oi,
                        "pcr": pcr,
                        "strongest_resistance": resistance_strike,
                        "strongest_support": support_strike,
                        "bias_score": round(bias_score, 2),
                        "bias_label": bias_label,
                        "oi_dominance": round(oi_dominance, 4),
                        "position_score": round(position_score, 2),
                        "pcr_strength": round(pcr_strength, 2)
                    }
                    
                    logger.info(f"=== INVESTIGATION: Calculated analytics - PCR: {pcr}, Support: {support_strike}, Resistance: {resistance_strike} ===")
                    
                    # Get spot price using shared utility
                    spot_price = await get_spot_price(symbol)
                    logger.info(f"=== INVESTIGATION: Spot price: {spot_price} ===")
                    
                    # Aggregate intelligence with proper spot price handling
                    intelligence = IntelligenceAggregator.aggregate_intelligence(
                        raw_analytics=analytics,
                        market_data={"spot_price": spot_price, "timestamp": datetime.now(timezone.utc).isoformat()},
                        calls=calls,
                        puts=puts
                    )
                    logger.info(f"=== INVESTIGATION: Intelligence aggregated ===")
                    
                    result = {
                        "symbol": symbol,
                        "spot": spot_price,  # Include spot price in response
                        "expiry": expiry_date,
                        "calls": calls,
                        "puts": puts,
                        "analytics": analytics,
                        "intelligence": intelligence,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    
                    logger.info(f"=== INVESTIGATION: Returning result with {len(result.get('calls', []))} calls and {len(result.get('puts', []))} puts ===")
                    
                    # Cache the result for 2 minutes
                    await cache_service.set(cache_key, result, ttl=120)
                    
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
        except HTTPException as e:
            # Re-raise HTTPException (401) without modification
            print(f"🔍 DEBUG: HTTPException re-raised from service: {e.status_code}")
            raise e
        except Exception as e:
            logger.exception("Unexpected internal error fetching option chain")
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )
    
    async def _get_nearest_expiry(self, symbol: str, token: str) -> str:
        """Get nearest expiry date for symbol"""
        try:
            expiries = await self.client.get_option_expiries(token, symbol)
            if expiries and len(expiries) > 0:
                return expiries[0]  # Return first (nearest) expiry
            else:
                raise APIResponseError("No expiry dates available")
        except HTTPException as e:
            # Preserve original status (401, 403, etc.)
            raise e
        except Exception as e:
            logger.exception("Unexpected internal error getting nearest expiry")
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
            
        except HTTPException as e:
            # Preserve original status (401, 403, etc.)
            raise e
        except Exception as e:
            logger.exception("Unexpected internal error calculating OI analysis")
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )
