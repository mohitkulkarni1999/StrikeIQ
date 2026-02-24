import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import HTTPException

from .upstox_client import UpstoxClient
from ..upstox_auth_service import UpstoxAuthService
from ..cache_service import cache_service
from ..market_session_manager import get_market_session_manager, EngineMode
from ...utils.spot_price import get_spot_price
from ..intelligence_aggregator import IntelligenceAggregator

logger = logging.getLogger(__name__)


class OptionChainService:

    def __init__(self, auth_service: UpstoxAuthService):
        self.auth_service = auth_service
        self.client = UpstoxClient()
        self.session_manager = None

    def _get_option_chain_instrument_key(self, symbol: str) -> str:
        OPTION_CHAIN_KEYS = {
            "NIFTY": "NSE_FO|NIFTY",
            "BANKNIFTY": "NSE_FO|BANKNIFTY"
        }
        
        instrument_key = OPTION_CHAIN_KEYS.get(symbol.upper())
        if not instrument_key:
            raise HTTPException(f"Unknown symbol: {symbol}")
        
        logger.info(f"Using CORRECT option chain instrument_key: {instrument_key}")
        return instrument_key

    async def get_contract_instrument_key(self, symbol: str) -> str:
        """Get index instrument key for contract resolution"""
        mapping = {
            "NIFTY": "NSE_INDEX|Nifty 50",
            "BANKNIFTY": "NSE_INDEX|Nifty Bank",
            "FINNIFTY": "NSE_INDEX|Nifty Fin Service"
        }

        if symbol not in mapping:
            raise ValueError(f"Unsupported symbol: {symbol}")

        return mapping[symbol]

    async def get_option_chain(
        self,
        symbol: str,
        expiry_date: Optional[str] = None,
        bypass_cache: bool = False
    ) -> Dict[str, Any]:

        try:

            if not self.session_manager:
                self.session_manager = get_market_session_manager()

            engine_mode = self.session_manager.get_engine_mode()

            token = await self.auth_service.get_valid_access_token()
            if not token:
                raise HTTPException(status_code=401, detail="Auth required")

            expiries = await self.client.get_option_expiries(token, symbol)
            if not expiries:
                raise HTTPException(status_code=404, detail="No expiries")

            if not expiry_date:
                today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
                valid = [e for e in expiries if e >= today]
                expiry_date = valid[0] if valid else expiries[0]

            cache_key = f"option_chain:{symbol}:{expiry_date}"

            # TASK 5 - PREVENT EMPTY WS PUBLISH
            # Always try cache first, but proceed to fetch if no cache
            cached_data = None
            if not bypass_cache:
                try:
                    cached_data = await cache_service.get(cache_key)
                    if cached_data:
                        # TASK 2 - Ignore EMPTY cached chains during LIVE mode
                        calls = cached_data.get("calls", [])
                        puts = cached_data.get("puts", [])
                        
                        if len(calls) == 0 and len(puts) == 0:
                            logger.warning(f"Ignoring EMPTY cached chain {symbol}")
                            cached_data = None
                        else:
                            cached_data["data_source"] = "rest_snapshot"
                            logger.info(f"Using VALID cached chain {symbol}")
                            return cached_data
                except Exception:
                    logger.warning("Cache service unavailable, proceeding with fresh fetch")
                    pass
            else:
                logger.info(f"Bypassing cache for {symbol} (LIVE mode)")

            option_key = self._get_option_chain_instrument_key(symbol)

            response = await self.client.get_option_chain(
                token,
                option_key,
                expiry_date
            )

            if not isinstance(response, dict) or "data" not in response:
                raise HTTPException(status_code=500, detail="Bad API response")

            data = response["data"]

            # Add validation for empty calls/puts
            chain_data = response.get("data", [])
            calls = data.get("calls", [])
            puts = data.get("puts", [])
            
            if isinstance(chain_data, list) and len(chain_data) == 0 or (len(calls) == 0 and len(puts) == 0):
                logger.warning(f"Empty chain for expiry {expiry_date}")
                
                # TASK 3 - Delete poison cache before fallback
                try:
                    await cache_service.delete(cache_key)
                    logger.info(f"Deleted poison cache for {symbol} {expiry_date}")
                except Exception:
                    pass
                
                valid_expiries = await self.client.get_option_expiries(token, symbol)
                
                today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
                future_expiries = [e for e in valid_expiries if e > today]
                
                if future_expiries:
                    next_expiry = future_expiries[0]
                    logger.info(f"Retrying with next live expiry {next_expiry}")
                    
                    response = await self.client.get_option_chain(
                        token,
                        option_key,
                        next_expiry
                    )
                    
                    expiry_date = next_expiry
                    chain_data = response.get("data", [])
                    data = response["data"]
                    calls = data.get("calls", [])
                    puts = data.get("puts", [])
                    
                    # EXPIRY FALLBACK RESUBSCRIPTION LOGIC
                    # Reload option contracts for new expiry and resubscribe market feed
                    try:
                        from app.services.upstox_market_feed import UpstoxMarketFeed, FeedConfig
                        from app.core.live_market_state import MarketStateManager
                        
                        # Extract new instrument keys from the fallback response
                        new_instrument_keys = []
                        for call in calls:
                            instrument_key = call.get("instrument_key")
                            if instrument_key:
                                new_instrument_keys.append(instrument_key)
                        
                        for put in puts:
                            instrument_key = put.get("instrument_key")
                            if instrument_key:
                                new_instrument_keys.append(instrument_key)
                        
                        # Get old instrument keys from market state
                        msm = MarketStateManager()
                        symbol_state = await msm.get_symbol_state(symbol)
                        old_instrument_keys = []
                        
                        if symbol_state and symbol_state.rest_option_chain:
                            for strike, strike_data in symbol_state.rest_option_chain.items():
                                if strike_data.call and strike_data.call.instrument_key:
                                    old_instrument_keys.append(strike_data.call.instrument_key)
                                if strike_data.put and strike_data.put.instrument_key:
                                    old_instrument_keys.append(strike_data.put.instrument_key)
                        
                        # Update expiry in market state
                        await msm.update_expiry(symbol, next_expiry)
                        
                        # Resubscribe market feed to new expiry instruments
                        if new_instrument_keys and old_instrument_keys:
                            # Create market feed instance for resubscription
                            config = FeedConfig(symbol=symbol, spot_instrument_key="")
                            market_feed = UpstoxMarketFeed(config, msm)
                            
                            # Resubscribe to new expiry instruments
                            success = await market_feed.resubscribe_to_new_expiry(
                                old_instrument_keys, new_instrument_keys
                            )
                            
                            if success:
                                logger.info(f"Successfully resubscribed to new expiry {next_expiry}")
                                
                                # Wait for second snapshot tick before attempting rebuild
                                await msm.wait_for_snapshot_tick(symbol, timeout=10.0)
                                
                                logger.info(f"Ready for option chain rebuild with new expiry {next_expiry}")
                            else:
                                logger.warning(f"Failed to resubscribe to new expiry {next_expiry}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to resubscribe on expiry fallback: {e}")
                else:
                    logger.warning("No valid expiries found, using empty data")

            spot = await get_spot_price(symbol)

            total_call_oi = sum(c.get("oi", 0) for c in calls)
            total_put_oi = sum(p.get("oi", 0) for p in puts)

            if total_call_oi == 0:
                total_call_oi = 1

            pcr = total_put_oi / total_call_oi

            analytics = {
                "total_call_oi": total_call_oi,
                "total_put_oi": total_put_oi,
                "pcr": pcr
            }

            intelligence = IntelligenceAggregator.aggregate_intelligence(
                raw_analytics=analytics,
                market_data={"spot_price": spot},
                calls=calls,
                puts=puts
            )

            result = {
                "symbol": symbol,
                "spot": spot,
                "expiry": expiry_date,
                "calls": calls,
                "puts": puts,
                "analytics": analytics,
                "intelligence": intelligence,
                "data_source": "websocket_stream",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            try:
                from app.core.live_market_state import MarketStateManager
                msm = MarketStateManager()

                option_data = {}

                for c in calls:
                    strike = c.get("strike")
                    if strike:
                        option_data[f"NSE_FO|{symbol}|CE|{strike}-0"] = c

                for p in puts:
                    strike = p.get("strike")
                    if strike:
                        option_data[f"NSE_FO|{symbol}|PE|{strike}-0"] = p

                await msm.update_rest_option_chain(symbol, option_data)

                if spot:
                    await msm.update_rest_spot_price(symbol, spot)

            except Exception as e:
                logger.warning(f"MSM update fail: {e}")

            try:
                # TASK 1 - Never cache EMPTY chain
                if len(result.get("calls", [])) > 0 or len(result.get("puts", [])) > 0:
                    await cache_service.set(cache_key, result, ttl=120)
                else:
                    logger.warning(f"Skipping cache for EMPTY chain {symbol} {expiry_date}")
            except Exception:
                pass

            return result

        except HTTPException as e:
            raise e

        except Exception as e:
            logger.exception("OptionChain error")
            raise HTTPException(status_code=500, detail=str(e))