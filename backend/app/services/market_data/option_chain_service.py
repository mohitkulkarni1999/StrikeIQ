import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from .upstox_client import UpstoxClient, TokenExpiredError
from ..upstox_auth_service import UpstoxAuthService
from ..cache_service import cache_service
from ..market_session_manager import get_market_session_manager, MarketSession, EngineMode, is_live_market
from ...utils.spot_price import get_spot_price

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
        self.session_manager = None  # Will be set in get_option_chain
    
    async def _get_instrument_key(self, symbol: str) -> str:
        """Get instrument key for options"""
        try:
            mappings = {
                "NIFTY": "NSE_INDEX|Nifty 50",
                "BANKNIFTY": "NSE_INDEX|BANKNIFTY",
            }
            
            instrument_key = mappings.get(symbol.upper())
            if not instrument_key:
                raise HTTPException(f"Unknown symbol: {symbol}")
            
            logger.info(f"=== INVESTIGATION: Returning instrument_key: {instrument_key} ===")
            return instrument_key
        except Exception as e:
            logger.error(f"=== INVESTIGATION: Error in _get_instrument_key: {e} ===")
            raise HTTPException(f"Failed to get instrument key: {e}")
    
    def get_next_weekly_expiry(self, symbol: str) -> str:
        """
        Get next weekly expiry for BANKNIFTY and NIFTY based on current day and time.
        
        Rules:
        Mon-Wed → use current Thursday
        Thu before 15:30 → use current Thursday  
        Thu after 15:30 → next Thursday
        Fri-Sun → next Thursday
        """
        now = datetime.now(timezone.utc)
        
        # Convert to IST (UTC+5:30) for market hours
        ist_offset = timedelta(hours=5, minutes=30)
        ist_time = now + ist_offset
        
        # Get current day of week (0=Monday, 6=Sunday)
        day_of_week = ist_time.weekday()
        
        # Calculate days until Thursday
        if day_of_week <= 2:  # Monday-Wednesday
            days_until_thursday = 3 - day_of_week
        elif day_of_week == 3:  # Thursday
            # Check if it's before 15:30 IST
            if ist_time.hour < 15 or (ist_time.hour == 15 and ist_time.minute < 30):
                days_until_thursday = 0
            else:
                days_until_thursday = 7  # Next Thursday
        else:  # Friday-Sunday
            days_until_thursday = 7 - day_of_week + 3
        
        # Calculate Thursday date
        next_thursday = ist_time + timedelta(days=days_until_thursday)
        
        # Format as YYYY-MM-DD
        expiry_date = next_thursday.strftime('%Y-%m-%d')
        
        logger.info(f"Calculated next weekly expiry for {symbol}: {expiry_date} (IST: {ist_time}, days_until_thursday: {days_until_thursday})")
        
        return expiry_date
    
    async def get_available_expiries(self, symbol: str, token: str) -> List[str]:
        """Get available expiries using correct instrument key for contracts"""
        try:
            # Use correct contract instrument key
            instrument_key = self.get_contract_instrument_key(symbol)
            logger.info(f"DEBUG: Instrument key for {symbol}: {instrument_key}")
            
            if not instrument_key:
                logger.error(f"DEBUG: No instrument key found for {symbol}")
                raise HTTPException(f"Unknown symbol: {symbol}")
            
            logger.info(f"DEBUG: Fetching expiries for {symbol} using instrument_key: {instrument_key}")
            
            # Make API call for contracts
            import urllib.parse
            encoded_key = urllib.parse.quote(instrument_key, safe='')
            url = f"https://api.upstox.com/v2/option/contract?instrument_key={encoded_key}"
            logger.info(f"DEBUG: Making request to URL: {url}")
            
            response = await self.client._make_request('get', url, access_token=token)
            logger.info(f"DEBUG: Response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"DEBUG: Contract API returned status {response.status_code}")
                logger.error(f"DEBUG: Response text: {response.text}")
                raise HTTPException(f"Failed to fetch contracts: {response.status_code}")
            
            # Parse response
            try:
                response_data = response.json()
                logger.info(f"DEBUG: Response data type: {type(response_data)}")
                if isinstance(response_data, dict) and "data" in response_data:
                    contracts = response_data["data"]
                elif isinstance(response_data, list):
                    contracts = response_data
                else:
                    logger.error(f"DEBUG: Unexpected response format: {response_data}")
                    contracts = []
            except Exception as parse_error:
                logger.error(f"DEBUG: Failed to parse response: {parse_error}")
                contracts = []
            
            # Extract unique expiry dates from real contracts
            expiries_set = set()
            if isinstance(contracts, list):
                logger.info(f"DEBUG: Processing {len(contracts)} contracts")
                for contract in contracts:
                    if isinstance(contract, dict):
                        expiry = contract.get('expiry')
                        if expiry:
                            expiries_set.add(expiry)
            else:
                logger.error(f"DEBUG: Contracts is not a list: {type(contracts)}")
            
            expiries = sorted(list(expiries_set))
            logger.info(f"DEBUG: Found {len(expiries)} expiries for {symbol}: {expiries[:5]}")
            
            return expiries
            
        except Exception as e:
            logger.error(f"DEBUG: Failed to get expiries for {symbol}: {e}")
            logger.exception("DEBUG: Full exception traceback:")
            raise HTTPException(f"Failed to get expiries: {e}")
    
    def get_contract_instrument_key(self, symbol: str) -> str:
        """Get correct instrument key for contract/expiry API"""
        mapping = {
            "NIFTY": "NSE_INDEX|Nifty 50",
            "BANKNIFTY": "NSE_INDEX|Nifty Bank"
        }
        return mapping.get(symbol.upper(), "")
    
    async def get_option_chain(self, symbol: str, expiry_date: Optional[str] = None) -> Dict[str, Any]:
        """Get option chain for a symbol with proper expiry validation and market status integration"""
        try:
            logger.info(f"=== INVESTIGATION: get_option_chain called with symbol={symbol}, expiry={expiry_date} ===")
            
            # Get market session manager
            if not self.session_manager:
                self.session_manager = await get_market_session_manager()
            
            # Check market status and determine data source
            market_status = self.session_manager.get_market_status()
            engine_mode = self.session_manager.get_engine_mode()
            
            logger.info(f"Market status: {market_status.value}, Engine mode: {engine_mode.value}")
            
            # Check auth service credentials FIRST before any other operations
            logger.info(f"=== INVESTIGATION: Token manager state before check: valid={self.token_manager.is_valid} ===")
            self.token_manager.check_auth_service(self.auth_service)
            logger.info(f"=== INVESTIGATION: Token manager state after check: valid={self.token_manager.is_valid} ===")
            
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
            
            # STEP 1: Fetch all available expiries from Upstox instruments API
            all_expiries = await self.client.get_option_expiries(token, symbol)
            if not all_expiries or len(all_expiries) == 0:
                logger.error(f"No expiries available for {symbol}")
                return {
                    "status": "error",
                    "error": "No expiry dates available",
                    "detail": f"No valid expiries found for {symbol}",
                    "data_source": "rest_snapshot" if engine_mode in [EngineMode.SNAPSHOT, EngineMode.HALTED] else "websocket_stream"
                }
            
            # STEP 2: Filter expiry dates where expiry_date >= today
            from datetime import datetime, timezone
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            valid_expiries = [exp for exp in all_expiries if exp >= today]
            
            if not valid_expiries:
                logger.error(f"No valid expiries found for {symbol} (all expired)")
                return {
                    "status": "error", 
                    "error": "No valid expiry dates available",
                    "detail": f"All expiries for {symbol} are expired",
                    "data_source": "rest_snapshot" if engine_mode in [EngineMode.SNAPSHOT, EngineMode.HALTED] else "websocket_stream"
                }
            
            # STEP 3: Select expiry based on market status and requested expiry
            original_expiry = expiry_date
            
            # MARKET STATUS BASED EXPIRY SELECTION
            if market_status.value != "OPEN":
                # Use next weekly expiry for BANKNIFTY and NIFTY when market is not open
                if symbol.upper() in ["BANKNIFTY", "NIFTY"]:
                    expiry_date = self.get_next_weekly_expiry(symbol)
                    logger.info(f"🔄 Expiry rollover triggered for {symbol}: using next weekly expiry {expiry_date} (market: {market_status.value})")
                else:
                    # For other symbols, use nearest valid expiry
                    if not expiry_date:
                        expiry_date = valid_expiries[0]
                        logger.info(f"Auto-selected nearest expiry for {symbol}: {expiry_date}")
                    elif expiry_date not in valid_expiries:
                        expiry_date = valid_expiries[0]
                        logger.info(f"Requested expiry {original_expiry} invalid for {symbol}, using nearest: {expiry_date}")
            else:
                # Market is OPEN - use requested expiry or auto-select
                if not expiry_date:
                    expiry_date = valid_expiries[0]
                    logger.info(f"Auto-selected nearest expiry for {symbol}: {expiry_date}")
                elif expiry_date not in valid_expiries:
                    logger.error(f"Requested expiry {expiry_date} is not valid for {symbol}")
                    return {
                        "status": "error",
                        "error": "Invalid expiry date", 
                        "detail": f"Expiry {expiry_date} is not available or expired for {symbol}",
                        "data_source": "rest_snapshot" if engine_mode in [EngineMode.SNAPSHOT, EngineMode.HALTED] else "websocket_stream"
                    }
                logger.info(f"Using requested expiry for {symbol}: {expiry_date}")
            
            # Check cache first (only for snapshot and halted modes)
            cache_key = f"option_chain:{symbol}:{expiry_date or 'latest'}"
            if engine_mode in [EngineMode.SNAPSHOT, EngineMode.HALTED]:
                cached_result = await cache_service.get(cache_key)
                if cached_result:
                    logger.info(f"=== INVESTIGATION: Cache hit for {symbol} ===")
                    cached_result["data_source"] = "rest_snapshot"
                    return cached_result
            
            logger.info(f"=== INVESTIGATION: Cache miss for {symbol}, fetching from API ===")
            
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
            
            # GUARD: Check if we got valid response data
            if not isinstance(response_data, dict) or "data" not in response_data:
                logger.error(f"=== INVESTIGATION: Invalid response structure: {response_data}")
                return {
                    "status": "error",
                    "error": "Invalid API response",
                    "detail": "Upstox API returned invalid data structure",
                    "data_source": "rest_snapshot" if engine_mode in [EngineMode.SNAPSHOT, EngineMode.HALTED] else "websocket_stream"
                }
                
            chain_data = response_data["data"]
            logger.info(f"=== INVESTIGATION: chain_data type: {type(chain_data)} ===")
            logger.info(f"=== INVESTIGATION: chain_data keys: {list(chain_data.keys()) if isinstance(chain_data, dict) else 'Not a dict'} ===")
            
            # GUARD: Check if calls and puts exist and are not empty
            if not isinstance(chain_data, dict) or "calls" not in chain_data or "puts" not in chain_data:
                logger.warning("=== INVESTIGATION: Invalid chain structure - missing calls/puts")
                return {
                    "status": "error",
                    "error": "Invalid option chain structure",
                    "detail": "Option chain missing calls or puts data",
                    "data_source": "rest_snapshot" if engine_mode in [EngineMode.SNAPSHOT, EngineMode.HALTED] else "websocket_stream"
                }
                
            calls = chain_data.get("calls", [])
            puts = chain_data.get("puts", [])
            
            # CRITICAL GUARD: Return immediately if empty chain
            if not calls and not puts:
                logger.warning("Empty option chain received - attempting retry with next expiry")
                
                # SAFETY FALLBACK: Retry once with next expiry for BANKNIFTY/NIFTY
                if symbol.upper() in ["BANKNIFTY", "NIFTY"] and market_status.value != "OPEN":
                    try:
                        # Get next expiry after current one
                        current_expiry_index = valid_expiries.index(expiry_date) if expiry_date in valid_expiries else 0
                        if current_expiry_index + 1 < len(valid_expiries):
                            next_expiry = valid_expiries[current_expiry_index + 1]
                            logger.info(f"🔄 Retrying with next expiry for {symbol}: {next_expiry}")
                            
                            # Retry API call with next expiry
                            retry_response_data = await self.client.get_option_chain(token, instrument_key, next_expiry)
                            
                            if isinstance(retry_response_data, dict) and "data" in retry_response_data:
                                retry_chain_data = retry_response_data["data"]
                                retry_calls = retry_chain_data.get("calls", [])
                                retry_puts = retry_chain_data.get("puts", [])
                                
                                if retry_calls and retry_puts:
                                    logger.info(f"✅ Retry successful for {symbol} with expiry {next_expiry}")
                                    # Use successful retry data
                                    calls = retry_calls
                                    puts = retry_puts
                                    expiry_date = next_expiry
                                else:
                                    logger.warning(f"Retry also returned empty data for {symbol}")
                    except Exception as retry_error:
                        logger.error(f"Retry failed for {symbol}: {retry_error}")
                
                # If still empty after retry, return safe response
                if not calls and not puts:
                    return {
                        "symbol": symbol,
                        "spot": await get_spot_price(symbol),
                        "expiry": expiry_date,
                        "calls": [],
                        "puts": [],
                        "analytics": {
                            "total_call_oi": 0,
                            "total_put_oi": 0,
                            "pcr": 0,
                            "data_source": "invalid_expiry"
                        },
                        "data_source": "rest_snapshot" if engine_mode in [EngineMode.SNAPSHOT, EngineMode.HALTED] else "websocket_stream",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
            
            logger.info(f"=== INVESTIGATION: Found {len(calls)} calls and {len(puts)} puts ===")
            if calls:
                logger.info(f"=== INVESTIGATION: First call sample: {calls[0]} ===")
            if puts:
                logger.info(f"=== INVESTIGATION: First put sample: {puts[0]} ===")
            
            # Calculate production-grade OI Analytics
            total_call_oi = sum(call.get("oi", 0) for call in calls)
            total_put_oi = sum(put.get("oi", 0) for put in puts)
            
            # SAFETY CHECK: Ensure we have valid OI data
            if total_call_oi == 0 and total_put_oi == 0:
                logger.warning(f"⚠️ Both call and put OI are zero for {symbol} - using fallback values")
                # Set minimal valid values to prevent division by zero
                total_call_oi = 1
                total_put_oi = 1
            
            # Calculate PCR with safety checks
            pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 1.0
            total_oi = total_call_oi + total_put_oi
            
            # Find strongest support/resistance levels
            resistance_strike = max(calls, key=lambda x: x.get("oi", 0)).get("strike", 0) if calls else 0
            support_strike = max(puts, key=lambda x: x.get("oi", 0)).get("strike", 0) if puts else 0
            
            # SAFETY CHECK: Ensure we have valid strikes for calculations
            if resistance_strike == 0 and support_strike == 0:
                logger.warning(f"⚠️ No valid strikes found for {symbol} - using fallback calculations")
                resistance_strike = spot_price * 1.02  # 2% above spot
                support_strike = spot_price * 0.98    # 2% below spot
            
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
                "data_source": "rest_snapshot" if engine_mode in [EngineMode.SNAPSHOT, EngineMode.HALTED] else "websocket_stream",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # FINAL VALIDATION: Ensure all required fields exist for frontend
            validation_errors = []
            
            if not result["calls"]:
                validation_errors.append("Empty calls array")
            if not result["puts"]:
                validation_errors.append("Empty puts array")
            if result["analytics"]["total_call_oi"] <= 0:
                validation_errors.append("Invalid total_call_oi")
            if result["analytics"]["total_put_oi"] <= 0:
                validation_errors.append("Invalid total_put_oi")
            if result["analytics"]["pcr"] <= 0:
                validation_errors.append("Invalid PCR")
            
            if validation_errors:
                logger.warning(f"⚠️ Frontend validation warnings for {symbol}: {validation_errors}")
                # Still return result but with warnings for debugging
            
            logger.info(f"=== INVESTIGATION: Returning result with {len(result.get('calls', []))} calls and {len(result.get('puts', []))} puts ===")
            logger.info(f"✅ Final validation for {symbol}: PCR={result['analytics']['pcr']:.4f}, Total OI={result['analytics']['total_call_oi'] + result['analytics']['total_put_oi']}")
            
            # Cache result for 2 minutes
            await cache_service.set(cache_key, result, ttl=120)
            
            return result
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
