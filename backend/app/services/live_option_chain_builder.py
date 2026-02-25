"""
Live Option Chain Builder
Builds option chain from Upstox V3 WebSocket feed in real-time
"""

print("🔥 LiveOptionChainBuilder module loaded")

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Set, Any
from pathlib import Path
from dataclasses import dataclass, field
import gzip
import io
from app.services.upstox_auth_service import get_upstox_auth_service
from app.services.market_data.upstox_client import UpstoxClient
from app.core.live_market_state import MarketStateManager
from app.services.market_session_manager import get_market_session_manager
from fastapi import HTTPException
import httpx
from datetime import datetime, timezone
from app.core.ws_manager import manager
from app.models.live_chain_state import LiveChainState
from datetime import datetime

logger = logging.getLogger(__name__)

# Recursion guard for expiry fallback
MAX_EXPIRY_FALLBACK = 3

@dataclass
class StrikeData:
    """Live strike data"""
    strike: float
    ce: Dict[str, Any] = field(default_factory=dict)
    pe: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LiveChainState:
    """Live option chain state for a symbol"""
    symbol: str
    expiry: str
    strike_map: Dict[float, Dict[str, str]] = field(default_factory=dict)  # strike -> {CE: instrument_key, PE: instrument_key}
    reverse_map: Dict[str, Tuple[float, str]] = field(default_factory=dict)  # instrument_key -> (strike, type)
    live_chain: Dict[float, StrikeData] = field(default_factory=dict)
    spot_price: Optional[float] = None
    last_update: Optional[datetime] = None
    
    # ATM strike window management
    current_atm_strike: Optional[float] = None
    strike_step: int = 50  # Standard strike step for NIFTY/BANKNIFTY
    window_size: int = 10  # ATM ± 10 strikes
    subscribed_strikes: Set[float] = field(default_factory=set)
    active_keys: Set[str] = field(default_factory=set)  # Currently subscribed instrument keys
    
    # Hybrid OI aggregation model
    global_call_oi: int = 0  # Total call OI from REST (full chain)
    global_put_oi: int = 0   # Total put OI from REST (full chain)
    window_call_oi: int = 0  # Call OI from WS window only
    window_put_oi: int = 0   # Put OI from WS window only
    rest_window_call_oi: int = 0  # Call OI from REST for window strikes only
    rest_window_put_oi: int = 0   # Put OI from REST for window strikes only
    last_oi_update: Optional[datetime] = None  # Last REST OI fetch
    
    def update_tick(self, instrument_key: str, data: Dict[str, Any]) -> None:
        """Update live chain with tick data"""
        if instrument_key in self.reverse_map:
            strike, option_type = self.reverse_map[instrument_key]
            
            if strike not in self.live_chain:
                self.live_chain[strike] = StrikeData(strike=strike)
            
            strike_data = self.live_chain[strike]
            tick_data = {
                "ltp": data.get("ltp"),
                "ltt": data.get("ltt"),
                "ltq": data.get("ltq"),
                "oi": data.get("oi"),
                "volume": data.get("volume"),
                "cp": data.get("cp"),
                "delta": data.get("delta"),
                "gamma": data.get("gamma"),
                "theta": data.get("theta"),
                "vega": data.get("vega"),
                "iv": data.get("iv")
            }
            
            # Remove None values
            tick_data = {k: v for k, v in tick_data.items() if v is not None}
            
            if option_type == "CE":
                strike_data.ce.update(tick_data)
                # Update window call OI
                if "oi" in tick_data and strike in self.subscribed_strikes:
                    self.window_call_oi = max(0, self.window_call_oi - strike_data.ce.get("prev_oi", 0)) + tick_data["oi"]
                    strike_data.ce["prev_oi"] = tick_data["oi"]
            else:  # PE
                strike_data.pe.update(tick_data)
                # Update window put OI
                if "oi" in tick_data and strike in self.subscribed_strikes:
                    self.window_put_oi = max(0, self.window_put_oi - strike_data.pe.get("prev_oi", 0)) + tick_data["oi"]
                    strike_data.pe["prev_oi"] = tick_data["oi"]
            
            self.last_update = datetime.now(timezone.utc)
    
    def update_global_oi(self, total_call_oi: int, total_put_oi: int) -> None:
        """Update global OI from REST API"""
        self.global_call_oi = total_call_oi
        self.global_put_oi = total_put_oi
        self.last_oi_update = datetime.now(timezone.utc)
    
    def update_rest_window_oi(self, rest_window_call_oi: int, rest_window_put_oi: int) -> None:
        """Update REST window OI for delta sync"""
        self.rest_window_call_oi = rest_window_call_oi
        self.rest_window_put_oi = rest_window_put_oi
    
    def calculate_adjusted_oi(self) -> Tuple[int, int]:
        """Calculate adjusted OI using delta sync"""
        # adjusted_call_oi = global_call_oi - rest_window_call_oi + window_call_oi
        adjusted_call_oi = self.global_call_oi - self.rest_window_call_oi + self.window_call_oi
        
        # adjusted_put_oi = global_put_oi - rest_window_put_oi + window_put_oi
        adjusted_put_oi = self.global_put_oi - self.rest_window_put_oi + self.window_put_oi
        
        return max(0, adjusted_call_oi), max(0, adjusted_put_oi)
    
    def calculate_delta_sync_pcr(self) -> float:
        """Calculate PCR using delta-sync adjusted OI"""
        adjusted_call_oi, adjusted_put_oi = self.calculate_adjusted_oi()
        
        if adjusted_call_oi > 0:
            return adjusted_put_oi / adjusted_call_oi
        return 0.0
    
    def calculate_atm_strike(self, spot_price: float) -> float:
        """Calculate ATM strike based on spot price"""
        return round(spot_price / self.strike_step) * self.strike_step
    
    def get_strike_window(self, atm_strike: float) -> List[float]:
        """Get strikes within ATM ± window_size"""
        all_strikes = sorted(self.strike_map.keys())
        
        # Find strikes within window
        window_strikes = []
        for strike in all_strikes:
            if abs(strike - atm_strike) <= (self.window_size * self.strike_step):
                window_strikes.append(strike)
        
        return window_strikes
    
    def should_rebalance_window(self, new_atm_strike: float) -> bool:
        """Check if ATM window should be rebalanced"""
        if self.current_atm_strike is None:
            return True
        
        # Rebalance if ATM shifted by ≥ 2 strikes
        strike_diff = abs(new_atm_strike - self.current_atm_strike)
        return strike_diff >= (2 * self.strike_step)
    
    def get_active_instrument_keys(self, strikes):

        keys = set()

        for strike in strikes:

            pair = self.strike_map.get(strike)

            if not pair:
                continue

            if not isinstance(pair, dict):
                continue

            ce_key = pair.get("CE")
            pe_key = pair.get("PE")

            if ce_key:
                keys.add(ce_key)

            if pe_key:
                keys.add(pe_key)

        return keys
    
    def build_final_chain(self) -> Dict[str, Any]:
        """Build final option chain for frontend"""
        calls = []
        puts = []
        
        # Sort strikes
        sorted_strikes = sorted(self.live_chain.keys())
        
        for strike in sorted_strikes:
            strike_data = self.live_chain[strike]
            
            # Build call data
            call_data = {
                "strike": strike,
                **strike_data.ce
            }
            calls.append(call_data)
            
            # Build put data
            put_data = {
                "strike": strike,
                **strike_data.pe
            }
            puts.append(put_data)
        
        # Use delta-sync PCR (global OI + real-time window OI)
        adjusted_call_oi, adjusted_put_oi = self.calculate_adjusted_oi()
        pcr = self.calculate_delta_sync_pcr()
        
        return {
            "symbol": self.symbol,
            "expiry": self.expiry,
            "spot": self.spot_price,
            "calls": calls,
            "puts": puts,
            "pcr": pcr,
            "timestamp": self.last_update.isoformat() if self.last_update else None,
            # Add OI breakdown for debugging
            "oi_breakdown": {
                "global_call_oi": self.global_call_oi,
                "global_put_oi": self.global_put_oi,
                "window_call_oi": self.window_call_oi,
                "window_put_oi": self.window_put_oi,
                "rest_window_call_oi": self.rest_window_call_oi,
                "rest_window_put_oi": self.rest_window_put_oi,
                "adjusted_call_oi": adjusted_call_oi,
                "adjusted_put_oi": adjusted_put_oi,
                "last_oi_update": self.last_oi_update.isoformat() if self.last_oi_update else None
            }
        }

class LiveOptionChainBuilder:
    """
    Live Option Chain Builder using Upstox V3 WebSocket feed
    Implements WS-scoped subscriptions and real-time chain building
    """
    
    def __init__(self, symbol: Optional[str] = None):
        self.symbol = symbol # Assign symbol for per-symbol builders
        self.auth_service = get_upstox_auth_service()
        self.client = UpstoxClient()  # Use singleton without parameters
        self.market_state = MarketStateManager()
        self.session_manager = get_market_session_manager()
        self.oi_data = {}
        # WS-scoped state management
        self.chain_states: Dict[str, LiveChainState] = {}  # symbol -> LiveChainState
        self.option_chain_states = self.chain_states       # REQUIRED ALIAS for state access
        self.ws_connections: Dict[str, Any] = {}  # symbol -> WebSocket connection
        self.subscribed_symbols: Dict[str, bool] = {}  # symbol -> subscribed flag
        
        # OI update task management
        self.oi_update_tasks: Dict[str, asyncio.Task] = {}  # symbol -> OI update task
        
        # Batch processing task management
        self._batch_compute_tasks: Dict[str, asyncio.Task] = {}  # symbol -> batch compute task
        
        # Instance-scoped instrument cache state
        self._instruments_loaded = False
        self._cached_instruments = []
        self._instrument_lookup = {}
        self._instrument_reverse_lookup = {}
        
        # Multi-expiry initialization tracking
        self.initialized_chains: Dict[str, bool] = {}  # symbol:expiry -> initialized flag
        
        # Load cached instruments at startup
       

    async def start(self, expiry: Optional[str] = None) -> None:
        """
        Start the builder for its assigned symbol
        """
        if not self.symbol:
            logger.warning("Builder started without an assigned symbol - operating in multi-symbol mode")
            return
            
        # Initialize chain for this specific symbol
        await self.initialize_chain(self.symbol, expiry)
        logger.info(f"LifeCycle: Started GLOBAL builder for {self.symbol}")

    def get_latest_option_chain(self, symbol: str) -> Optional[LiveChainState]:
        """
        Return symbol-specific chain_state: return self.option_chain_states.get(symbol)
        """
        return self.option_chain_states.get(symbol)

    def resolve_instrument_key(self, tradingsymbol: str) -> Optional[str]:
        """
        Resolve numeric instrument_key from tradingsymbol string
        """
        return self._instrument_lookup.get(tradingsymbol)

    def resolve_trading_symbol(self, instrument_key: str) -> Optional[str]:
        """
        Resolve tradingsymbol from numeric instrument_key
        """
        return self._instrument_reverse_lookup.get(instrument_key)
    def _get_nearest_monthly_future(self, symbol: str, opt_expiry: str):
        futs = self.futidx_map.get(symbol, {})

        if not futs:
            raise Exception(f"No FUTIDX instruments found for {symbol}")

        opt_date = datetime.strptime(opt_expiry, "%Y-%m-%d")

        valid_futures = []

        for fut_expiry, inst in futs.items():
            fut_date = datetime.strptime(fut_expiry, "%Y-%m-%d")
            if fut_date >= opt_date:
                valid_futures.append((fut_date, inst))

        if not valid_futures:
            raise Exception(f"No valid FUTIDX available for {symbol}")

        valid_futures.sort(key=lambda x: x[0])

        nearest_expiry = valid_futures[0][0].strftime("%Y-%m-%d")
        print(f"🟢 Using nearest FUTIDX expiry: {nearest_expiry}")

        return valid_futures[0][1]
    
    async def ensure_instruments_loaded(self) -> None:
        """
        Public async method to ensure instruments are loaded (from cache or CDN)
        """
        if self._instruments_loaded:
            return
        
        # Try local cache first (synchronous part)
        self._load_cached_instruments()
        
        # If still not loaded, fetch from CDN
        if not self._instruments_loaded:
            await self._fetch_instruments_from_cdn()
    
    def _load_cached_instruments(self) -> None:
        if self._instruments_loaded:
            return
    
        try:
            instruments_file = Path("data/instruments.json")
        
            if not instruments_file.exists():
                logger.warning("Cached instruments file not found")
                self._cached_instruments = []
                self._instruments_loaded = False
                return
        
            with open(instruments_file, 'r', encoding='utf-8') as f:
                raw = json.load(f)
        
            if isinstance(raw, dict) and "instruments" in raw:
                instruments = raw["instruments"]
            elif isinstance(raw, list):
                instruments = raw
            else:
                raise ValueError("Invalid instruments.json format")
        
            self._cached_instruments = instruments
        
            self._instrument_lookup = {
                inst.get("tradingsymbol"): inst.get("instrument_key")
                for inst in self._cached_instruments
                if isinstance(inst, dict)
                and inst.get("tradingsymbol")
                and inst.get("instrument_key")
            }
        
            self._instrument_reverse_lookup = {
                inst.get("instrument_key"): inst.get("tradingsymbol")
                for inst in self._cached_instruments
                if isinstance(inst, dict)
                and inst.get("tradingsymbol")
                and inst.get("instrument_key")
            }
        
            self._instruments_loaded = True
            logger.info(f"Loaded {len(self._cached_instruments)} instruments successfully")
        
        except Exception as e:
            logger.error(f"Failed to load cached instruments: {e}")
            self._cached_instruments = []
            self._instruments_loaded = False

    
        
    async def initialize_chain(self, symbol: str, expiry: str, registry, attempt: int = 0) -> LiveChainState:
        import asyncio

        key = f"{symbol}:{expiry}"

        if key in self.initialized_chains:
            return self.chain_states.get(symbol)

        retry = 0
        while not registry._loaded.is_set():
            if retry >= 10:
                raise Exception("Instrument store not ready after 5 seconds")
            await asyncio.sleep(0.5)
            retry += 1

        logger.info(f"🚀 Initializing option chain for {symbol}:{expiry}")

        try:
            # 🔥 WAIT UNTIL CDN REGISTRY READY
            await registry.wait_until_ready()

            token = await self.auth_service.get_valid_access_token()

            if not token:
                logger.warning("Auth token missing → returning empty chain")
                chain = LiveChainState(symbol=symbol, expiry=expiry)
                self.chain_states[symbol] = chain
                return chain

            # 🔥 BUILD STRIKE MAP FROM REGISTRY (NOT LOCAL JSON)
            expiry_map = registry.options.get(symbol)

            if not expiry_map:
                raise RuntimeError(f"No option instruments for {symbol}")

            if expiry not in expiry_map:
                nearest = sorted(expiry_map.keys())[0]
                logger.warning(f"Requested expiry {expiry} not found")
                logger.warning(f"Using nearest expiry {nearest}")
                expiry = nearest

            strike_map = expiry_map[expiry]

            chain_state = LiveChainState(
                symbol=symbol,
                expiry=expiry,
                strike_map=strike_map
            )

            self.chain_states[symbol] = chain_state

            # 🔥 FUTIDX MUST EXIST BEFORE OI LOOP
            # 🔥 FUTIDX MUST EXIST BEFORE OI LOOP
            fut_map = registry.futidx.get(symbol)

            if not fut_map:
                raise RuntimeError(f"No FUTIDX MAP for {symbol}")

            target_expiry = chain_state.expiry

            # agar exact FUT expiry nahi mila
            opt_date = datetime.strptime(target_expiry, "%Y-%m-%d")

            valid_futures = []

            for fut_expiry, inst in fut_map.items():
                fut_date = datetime.strptime(fut_expiry, "%Y-%m-%d")
                
                # 👇 FUT MUST BE SAME OR AFTER OPTION EXPIRY
                if fut_date >= opt_date:
                    valid_futures.append((fut_date, inst))

            if not valid_futures:
                raise RuntimeError(f"No valid FUTIDX available for {symbol}")

            valid_futures.sort(key=lambda x: x[0])

            nearest_expiry = valid_futures[0][0].strftime("%Y-%m-%d")
            logger.info(f"🟢 Using nearest MONTHLY FUTIDX expiry {nearest_expiry}")

            chain_state.fut_key = valid_futures[0][1]

            # Mark this symbol:expiry combination as successfully initialized
            self.initialized_chains[key] = True
            logger.info(f"🔥 ATM ladder built for {symbol}:{expiry}")

            await self._start_oi_updates(symbol, expiry, registry)
            await self._start_batch_compute(symbol, expiry, registry)
            return chain_state

        except Exception as e:
            logger.error(f"Failed to initialize chain for {symbol}: {e}")
            raise
    
    async def _handle_expiry_fallback(self, symbol: str, current_expiry: str, attempt: int) -> LiveChainState:
        """
        Handle weekly expiry fallback by getting next available expiry
        """
        try:
            # Get valid access token
            token = await self.auth_service.get_valid_access_token()
            
            # Get all expiries for the symbol
            option_key = await self._get_option_chain_instrument_key(symbol)
            valid_expiries = await self.client.get_option_expiries(token, symbol)
            
            # Find next future expiry
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            future_expiries = [e for e in valid_expiries if e > today and e != current_expiry]
            
            if not future_expiries:
                logger.error(f"No future expiries available for {symbol}")
                raise HTTPException(status_code=404, detail="No valid expiries available")
            
            next_expiry = min(future_expiries)
            logger.info(f"Fallback: Using next expiry {next_expiry} for {symbol} (attempt {attempt})")
            
            # Initialize chain with new expiry
            return await self.initialize_chain(symbol, next_expiry, attempt)
            
        except Exception as e:
            logger.error(f"Expiry fallback failed for {symbol}: {e}")
            raise
    
    async def _initialize_from_contracts(self, symbol: str, expiry: str) -> LiveChainState:
        """
        Initialize option chain by fetching contracts first
        """

        try:

            token = await self.auth_service.get_valid_access_token()
            if not token:
                raise HTTPException(status_code=401, detail="Authentication required")

            # 🟢 IMPORTANT FIX
            contracts = await self.client.get_option_contracts(token, symbol)

            if not contracts or not isinstance(contracts, list):
                logger.error(f"Invalid contracts response for {symbol}")
                return LiveChainState(symbol=symbol, expiry=expiry)

            # Get all available expiries
            available_expiries = sorted(
                list(set(c.get("expiry") for c in contracts if c.get("expiry")))
            )

            if not available_expiries:
                logger.error(f"No expiries available for {symbol}")
                return LiveChainState(symbol=symbol, expiry=expiry)

            # If requested expiry not present → fallback to nearest
            if expiry not in available_expiries:

                logger.warning(f"Requested expiry {expiry} not found")

                from datetime import datetime

                req = datetime.strptime(expiry, "%Y-%m-%d")

                nearest = min(
                    available_expiries,
                    key=lambda e: abs(datetime.strptime(e, "%Y-%m-%d") - req)
                )

                logger.warning(f"Using nearest expiry {nearest}")

                expiry = nearest

            # Normalize expiries to string
            available_expiries = sorted(
                list(
                    set(
                        str(c.get("expiry"))
                        for c in contracts
                        if c.get("expiry")
                    )
                )
            )

            if not available_expiries:
                logger.error(f"No expiries available for {symbol}")
                return LiveChainState(symbol=symbol, expiry=expiry)

            expiry = str(expiry)

            if expiry not in available_expiries:

                logger.warning(f"Requested expiry {expiry} not found")

                try:
                    req = datetime.strptime(expiry, "%Y-%m-%d")

                    nearest = min(
                        available_expiries,
                        key=lambda e: abs(
                            datetime.strptime(str(e), "%Y-%m-%d") - req
                        )
                    )

                    logger.warning(f"Using nearest expiry {nearest}")
                    expiry = nearest

                except Exception as e:
                    logger.error(f"Expiry fallback parsing failed: {e}")
                    expiry = available_expiries[0]

            filtered_contracts = [
                c for c in contracts
                if str(c.get("expiry")) == expiry
            ]

            strike_map = {}
            reverse_map = {}

            # 🟢 IMPORTANT FIX: USE TRANSFORMED FIELDS
            for contract in filtered_contracts:

                strike = contract.get("strike")
                instrument_key = contract.get("instrument_key")
                option_type = contract.get("option_type", "").upper()

                if strike and instrument_key and option_type in ["CE", "PE"]:

                    if strike not in strike_map:
                        strike_map[strike] = {}

                    strike_map[strike][option_type] = {
                        "instrument_key": instrument_key,
                        "ltp": 0,
                        "oi": 0,
                        "volume": 0,
                        "prev_oi": 0
                    }

                    reverse_map[instrument_key] = (strike, option_type)

            logger.info(f"Created strike map from {len(filtered_contracts)} contracts for {symbol}")

            return LiveChainState(
                symbol=symbol,
                expiry=expiry,
                strike_map=strike_map,
                reverse_map=reverse_map
            )

        except Exception as e:
            logger.error(f"Failed to initialize from contracts for {symbol}: {e}")
            raise
    
    def _get_index_instrument_key(self, symbol: str) -> str:
        """Get index instrument key for symbol"""
        INDEX_KEYS = {
            "NIFTY": "NSE_INDEX|Nifty 50",
            "BANKNIFTY": "NSE_INDEX|Nifty Bank"
        }
        
        index_key = INDEX_KEYS.get(symbol.upper())
        if not index_key:
            raise HTTPException(status_code=404, detail=f"Unknown index symbol: {symbol}")
        return index_key
    
    async def _get_option_chain_instrument_key(self, symbol: str) -> str:
        """
        Get FUTIDX instrument key for option chain from cached data
        """
        try:
            if not self._instruments_loaded or not self._cached_instruments:
                raise HTTPException(status_code=500, detail="Instruments not loaded")
            
            # Filter for FUTIDX instruments of the symbol from cached data
            futidx_instruments = [
                inst for inst in self._cached_instruments
                if (inst.get("segment") == "NSE_FO" and 
                    inst.get("instrument_type") == "FUTIDX" and 
                    inst.get("name") == symbol.upper())
            ]
            
            if not futidx_instruments:
                raise HTTPException(status_code=404, detail=f"No FUTIDX instrument found for {symbol}")
            
            # Sort by expiry and select nearest future expiry
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            
            future_instruments = [
                inst for inst in futidx_instruments
                if inst.get("expiry", "") >= today
            ]
            
            if not future_instruments:
                # If no future expiry, use the latest available
                selected_instrument = futidx_instruments[0]
            else:
                # Sort by expiry and select the nearest
                future_instruments.sort(key=lambda x: x.get("expiry", ""))
                selected_instrument = future_instruments[0]
            
            instrument_key = selected_instrument.get("instrument_key")
            if not instrument_key:
                raise HTTPException(status_code=500, detail="No instrument_key found")
            
            logger.info(f"Selected FUTIDX instrument: {instrument_key} for {symbol}")
            return instrument_key
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get FUTIDX instrument key for {symbol}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get instrument key: {str(e)}")
    
    async def subscribe_to_instruments(self, symbol: str) -> List[str]:
        """
        Subscribe to ATM ± window instruments for a symbol
        Returns list of instrument keys to subscribe to
        """
        if symbol not in self.chain_states:
            raise HTTPException(status_code=404, detail=f"Chain not initialized for {symbol}")
        
        chain_state = self.chain_states[symbol]
        
        # Get spot price from market state
        spot = chain_state.spot_price
        
        # WS tick not received yet → fallback to REST
        if not spot:
            try:
                from app.services.market_data.upstox_client import UpstoxClient
                
                client = UpstoxClient()
                
                # Determine index key based on symbol
                index_key = "NSE_INDEX|Nifty 50" if symbol == "NIFTY" else "NSE_INDEX|Nifty Bank"
                spot = await client.get_ltp(index_key)

                if spot:
                    chain_state.spot_price = float(spot)
                    logger.warning(f"REST FALLBACK SPOT USED for {symbol} → {spot}")
                
            except Exception as e:
                logger.error(f"REST fallback failed for {symbol}: {e}")
                return []
        
        # If still no spot price after fallback, return empty
        if not spot:
            logger.warning(f"No spot price available for {symbol} - cannot subscribe to FO instruments")
            return []
        
        # Calculate ATM strike
        atm_strike = chain_state.calculate_atm_strike(spot)
        chain_state.current_atm_strike = atm_strike
        
        # Get strike window (ATM ± window_size)
        window_strikes = chain_state.get_strike_window(atm_strike)
        
        # Get active instrument keys for window only
        active_keys = chain_state.get_active_instrument_keys(window_strikes)
        
        # Add spot instrument key
        spot_key = f"NSE_INDEX|{symbol}"
        all_keys = list(active_keys) + [spot_key]
        
        # Update state
        chain_state.subscribed_strikes = set(window_strikes)
        chain_state.active_keys = active_keys
        
        logger.info(f"Subscribing to {symbol}: ATM={atm_strike}, window={len(window_strikes)} strikes, {len(active_keys)} option instruments")
        return all_keys
    
    async def handle_tick(self, symbol: str, instrument_key: str, data: Dict[str, Any]) -> None:
        """
        Handle incoming tick data and update live chain
        OPTIMIZED: Only store data, no computation - batching handles computation
        """
        if symbol not in self.chain_states:
            logger.debug(f"No chain state for {symbol}, ignoring tick")
            return
        
        chain_state = self.chain_states[symbol]
        
        # Handle spot price updates (minimal computation)
        if instrument_key == f"NSE_INDEX|{symbol}":
            spot_price = data.get("ltp") or data.get("last_price")
            if spot_price:
                chain_state.spot_price = float(spot_price)
                
                # Initialize ATM window on first spot price (only once)
                if chain_state.current_atm_strike is None:
                    await self.initialize_atm_window(symbol)
                # Note: ATM rebalancing moved to batch compute loop
            return
        
        # Handle option instrument updates (STORE ONLY)
        chain_state.update_tick(instrument_key, data)
        # No computation here - batch loop handles PCR, payload, broadcast
    
    async def _rebalance_strike_window(self, symbol: str, new_atm_strike: float) -> None:
        """
        Rebalance strike window when ATM shifts
        """
        if symbol not in self.chain_states:
            return
        
        chain_state = self.chain_states[symbol]
        
        # Get new strike window
        new_strikes = chain_state.get_strike_window(new_atm_strike)
        new_active_keys = chain_state.get_active_instrument_keys(new_strikes)
        
        # Get keys to unsubscribe (old but not in new)
        keys_to_unsubscribe = chain_state.active_keys - new_active_keys
        
        # Get keys to subscribe (new but not in old)
        keys_to_subscribe = new_active_keys - chain_state.active_keys
        
        if keys_to_unsubscribe or keys_to_subscribe:
            logger.info(f"Rebalancing {symbol}: unsubscribe {len(keys_to_unsubscribe)}, subscribe {len(keys_to_subscribe)}")
            
            # Get WebSocket feed for rebalancing (Step 4 singleton)
            from app.services.upstox_market_feed import get_global_feed
            ws_feed = get_global_feed(symbol)
            
            if not ws_feed:
                logger.warning(f"Global feed for {symbol} not found during rebalance")
                return

            # Unsubscribe old keys
            if keys_to_unsubscribe:
                await ws_feed.unsubscribe_from_instruments(list(keys_to_unsubscribe))
            
            # Subscribe new keys
            if keys_to_subscribe:
                await ws_feed.subscribe_to_instruments(list(keys_to_subscribe))
            
            # Update state
            chain_state.current_atm_strike = new_atm_strike
            chain_state.subscribed_strikes = set(new_strikes)
            chain_state.active_keys = new_active_keys
            
            logger.info(f"Rebalanced {symbol} window: ATM={new_atm_strike}, strikes={len(new_strikes)}")
    
    async def initialize_atm_window(self, symbol: str) -> None:
        """
        Initialize ATM window subscription after spot price is received
        """
        if symbol not in self.chain_states:
            return
        
        chain_state = self.chain_states[symbol]
        
        if chain_state.spot_price is None:
            logger.warning(f"No spot price available for {symbol} to initialize ATM window")
            return
        
        # Calculate ATM and get window
        atm_strike = chain_state.calculate_atm_strike(chain_state.spot_price)
        window_strikes = chain_state.get_strike_window(atm_strike)
        active_keys = chain_state.get_active_instrument_keys(window_strikes)
        
        # Subscribe to window instruments
        if active_keys:
            from app.services.upstox_market_feed import get_global_feed
            ws_feed = get_global_feed(symbol)
            
            if not ws_feed:
                logger.warning(f"Global feed for {symbol} not found for ATM window init")
                return

            all_keys = list(active_keys) + [f"NSE_INDEX|{symbol}"]
            await ws_feed.subscribe_to_instruments(all_keys)
            
            # Update state
            chain_state.current_atm_strike = atm_strike
            chain_state.subscribed_strikes = set(window_strikes)
            chain_state.active_keys = active_keys
            
            logger.info(f"Initialized {symbol} ATM window: ATM={atm_strike}, strikes={len(window_strikes)}, instruments={len(active_keys)}")
    
    async def _start_oi_updates(self, symbol: str, expiry: str, registry) -> None:
        """
        Start periodic OI updates from REST API
        """
        key = f"{symbol}:{expiry}"
        if key in self.oi_update_tasks:
            return  # Already running
        
        # Create and start OI update task
        task = asyncio.create_task(self._oi_update_loop(symbol, expiry, registry))
        self.oi_update_tasks[key] = task
        logger.debug(f"Started OI updates for {symbol}:{expiry}")
    
    async def _safe_cancel(self, task):
        """
        Safely cancel a task without blocking the caller
        """
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    async def stop_tasks(self, symbol: str, expiry: str) -> None:
        """
        Stop background tasks for specific symbol+expiry combination
        Called when WebSocket disconnects to prevent zombie tasks
        Uses non-blocking cancellation to prevent ASGI blocking
        """
        key = f"{symbol}:{expiry}"

        # Stop OI update task (non-blocking)
        if key in self.oi_update_tasks:
            task = self.oi_update_tasks[key]
            asyncio.create_task(self._safe_cancel(task))
            del self.oi_update_tasks[key]
            logger.debug(f"Stopped OI update task for {key}")

        # Stop batch compute task (non-blocking)
        if key in self._batch_compute_tasks:
            task = self._batch_compute_tasks[key]
            asyncio.create_task(self._safe_cancel(task))
            del self._batch_compute_tasks[key]
            logger.debug(f"Stopped batch compute task for {key}")

        logger.info(f"Stopped background tasks for {key}")
    
    async def _stop_oi_updates(self, symbol: str) -> None:
        """
        Stop periodic OI updates
        """
        if symbol in self.oi_update_tasks:
            task = self.oi_update_tasks[symbol]
            task.cancel()
            del self.oi_update_tasks[symbol]
            logger.info(f"Stopped OI updates for {symbol}")
    
    async def _oi_update_loop(self, symbol: str, expiry: str, registry) -> None:
        """
        Periodic OI update loop - runs every 60 seconds
        """
        # 🔥 WAIT FOR REGISTRY BEFORE BACKGROUND ACCESS
        await registry.wait_until_ready()
        
        try:
            while True:
                await self._fetch_global_oi(symbol, expiry, registry)
                await asyncio.sleep(60)  # Update every 60 seconds
        
        except asyncio.CancelledError:
            logger.debug(f"Loop cancelled for {symbol}:{expiry}")
            raise
        except Exception as e:
            logger.error(f"Error in OI update loop for {symbol}:{expiry}: {e}")
    
    async def _fetch_global_oi(self, symbol: str, expiry: str, registry) -> None:
        """
        Fetch global OI from REST API for active expiry
        """
        try:
            if symbol not in self.chain_states:
                return
            
            chain_state = self.chain_states[symbol]
            
            # Get access token
            token = await self.auth_service.get_valid_access_token()
            if not token:
                logger.warning(f"No access token for OI update: {symbol}")
                return
            
            # Fetch option chain from REST
            option_key = await self._get_option_chain_instrument_key(symbol)
            response = await self.client.get_option_chain(token, option_key, chain_state.expiry)
            
            if not isinstance(response, dict) or "data" not in response:
                logger.warning(f"Invalid OI response for {symbol}")
                return
            
            data = response["data"]
            calls = data.get("calls", [])
            puts = data.get("puts", [])
            
            # Calculate total OI from full chain
            total_call_oi = sum(call.get("oi", 0) for call in calls if call.get("oi"))
            total_put_oi = sum(put.get("oi", 0) for put in puts if put.get("oi"))
            
            # Calculate window OI from REST for current subscribed strikes only
            rest_window_call_oi = 0
            rest_window_put_oi = 0
            
            for call in calls:
                strike = call.get("strike")
                if strike in chain_state.subscribed_strikes and call.get("oi"):
                    rest_window_call_oi += call["oi"]
            
            for put in puts:
                strike = put.get("strike")
                if strike in chain_state.subscribed_strikes and put.get("oi"):
                    rest_window_put_oi += put["oi"]
            
            # Update global OI in chain state
            chain_state.update_global_oi(total_call_oi, total_put_oi)
            
            # Update REST window OI for delta sync
            chain_state.update_rest_window_oi(rest_window_call_oi, rest_window_put_oi)
            
            logger.debug(f"Updated global OI for {symbol}: Call={total_call_oi}, Put={total_put_oi}, Window_Call={rest_window_call_oi}, Window_Put={rest_window_put_oi}, PCR={chain_state.calculate_delta_sync_pcr():.4f}")
            
        except Exception as e:
            logger.error(f"Failed to fetch global OI for {symbol}: {e}")
    
    async def build_chain_payload(self, symbol: str) -> Dict[str, Any]:
        """
        Build final option chain payload for WebSocket transmission
        """
        if symbol not in self.chain_states:
            return {
                "symbol": symbol,
                "expiry": None,
                "spot": None,
                "calls": [],
                "puts": [],
                "pcr": 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # STEP 3: Ensure builder reads from: websocket_market_feed.latest_ticks
        await self._sync_from_global_feed(symbol)
        
        chain_state = self.chain_states[symbol]
        return chain_state.build_final_chain()

    async def _sync_from_global_feed(self, symbol: str) -> None:
        """
        Surgically sync builder state from global Upstox singleton ticks cache
        """
        try:
            from app.services.upstox_market_feed import get_global_feed
            ws_feed = get_global_feed(symbol)
            
            if ws_feed and hasattr(ws_feed, 'latest_ticks'):
                # Extract copy of ticks to avoid mutation errors during iteration
                ticks = dict(ws_feed.latest_ticks)
                for instrument_key, tick_data in ticks.items():
                    # Direct update to bypass create_task overhead in high-frequency loop
                    if symbol in self.chain_states:
                        chain_state = self.chain_states[symbol]
                        
                        # Handle spot price
                        if instrument_key == f"NSE_INDEX|{symbol}":
                            spot_price = tick_data.get("ltp")
                            if spot_price:
                                chain_state.spot_price = float(spot_price)
                        else:
                            # Handle option ticks
                            chain_state.update_tick(instrument_key, tick_data)
        except Exception as e:
            logger.error(f"Error syncing from global feed for {symbol}: {e}")
    
    async def cleanup_symbol(self, symbol: str) -> None:
        """
        Clean up resources for a symbol
        """
        # Stop batch compute loop
        await self._stop_batch_compute(symbol)
        
        # Stop OI updates
        await self._stop_oi_updates(symbol)
        
        # Clean up chain state
        if symbol in self.chain_states:
            del self.chain_states[symbol]
        
        if symbol in self.subscribed_symbols:
            del self.subscribed_symbols[symbol]
        
        logger.info(f"Cleaned up resources for {symbol}")
    
    async def _start_batch_compute(self, symbol: str, expiry: str, registry) -> None:
        """
        Start batch compute loop for optimized processing
        """
        key = f"{symbol}:{expiry}"
        if key in self._batch_compute_tasks:
            logger.warning(f"Batch compute task already running for {symbol}:{expiry}")
            return
        
        self._batch_compute_tasks[key] = asyncio.create_task(
            self._batch_compute_loop(symbol, expiry, registry)
        )
        logger.info(f"Started batch compute loop for {symbol}:{expiry}")
    
    async def _stop_batch_compute(self, symbol: str) -> None:
        """
        Stop batch compute loop
        """
        if symbol in self._batch_compute_tasks:
            task = self._batch_compute_tasks[symbol]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            del self._batch_compute_tasks[symbol]
            logger.info(f"Stopped batch compute loop for {symbol}")
    
    async def _batch_compute_loop(self, symbol: str, expiry: str, registry) -> None:
        """
        Batch compute loop - handles PCR calculation, payload building, and broadcasting
        Runs every 500ms to optimize performance
        Updated to broadcast payload even when market is CLOSED for development
        """
        # 🔥 WAIT FOR REGISTRY BEFORE BACKGROUND ACCESS
        await registry.wait_until_ready()
        
        logger.debug(f"Starting batch compute loop for {symbol}:{expiry}")
        
        try:
            while True:
                await asyncio.sleep(0.5)  # 500ms batching window
                
                chain = self.chain_states.get(symbol)
                if not chain:
                    continue
                
                try:
                    # ENSURE SPOT PRICE VIA REST FALLBACK (even when market is CLOSED)
                    if not chain.spot_price:
                        try:
                            from app.services.market_data.upstox_client import UpstoxClient
                            client = UpstoxClient()
                            
                            # Determine index key based on symbol
                            index_key = "NSE_INDEX|Nifty 50" if symbol == "NIFTY" else "NSE_INDEX|Nifty Bank"
                            spot = await client.get_ltp(index_key)

                            if spot:
                                chain.spot_price = float(spot)
                                logger.info(f"🔄 REST FALLBACK SPOT for {symbol} → {spot}")
                                
                                # Initialize ATM window on first spot price
                                if chain.current_atm_strike is None:
                                    atm_strike = chain.calculate_atm_strike(chain.spot_price)
                                    chain.current_atm_strike = atm_strike
                                    logger.info(f"🔄 ATM initialized for {symbol} → {atm_strike}")
                        except Exception as e:
                            logger.error(f"REST fallback failed for {symbol}: {e}")
                            # Continue without spot price - still broadcast empty payload for development
                    
                    # Check for ATM rebalancing (if we have spot price)
                    if chain.spot_price and chain.current_atm_strike:
                        new_atm_strike = chain.calculate_atm_strike(chain.spot_price)
                        if chain.should_rebalance_window(new_atm_strike):
                            logger.info(f"ATM shifted for {symbol}: {chain.current_atm_strike} -> {new_atm_strike}")
                            await self._rebalance_strike_window(symbol, new_atm_strike)
                    
                    # Compute PCR once per batch
                    chain.pcr = self._calculate_pcr(chain)
                    
                    # Build payload once per batch (works even with live OI = 0)
                    payload = self._build_payload(chain)
                    
                    # Broadcast once per batch (even when market is CLOSED)
                    await self._broadcast(symbol, payload)
                    
                except Exception as e:
                    logger.error(f"Error in batch compute for {symbol}: {e}")
                    
        except asyncio.CancelledError:
            logger.debug(f"Loop cancelled for {symbol}:{expiry}")
            raise
        finally:
            logger.info(f"Batch compute loop ended for {symbol}:{expiry}")
    
    def _calculate_pcr(self, chain: LiveChainState) -> float:

        try:
            total_call_oi = 0
            total_put_oi = 0

            for strike, pair in chain.strike_map.items():

                if not isinstance(pair, dict):
                    continue

                ce_key = pair.get("CE")
                pe_key = pair.get("PE")

                if ce_key:
                    ce_oi = self.oi_data.get(ce_key, {}).get("oi", 0)
                    total_call_oi += ce_oi

                if pe_key:
                    pe_oi = self.oi_data.get(pe_key, {}).get("oi", 0)
                    total_put_oi += pe_oi

            if total_call_oi == 0:
                return 0.0

            return total_put_oi / total_call_oi

        except Exception as e:
            logger.error(f"Error calculating PCR: {e}")
            return 0.0
    
    def _build_payload(self, chain: LiveChainState) -> Dict[str, Any]:

        try:
            payload = {
                "symbol": chain.symbol,
                "spot_price": chain.spot_price,
                "atm_strike": chain.current_atm_strike,
                "pcr": chain.pcr,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "calls": [],
                "puts": []
            }

            # BUILD PAYLOAD USING STRIKE_MAP even when live OI = 0
            for strike, pair in chain.strike_map.items():

                if not isinstance(pair, dict):
                    continue

                ce_key = pair.get("CE")
                pe_key = pair.get("PE")

                # Use live OI data if available, otherwise use 0 (development mode)
                ce_data = self.oi_data.get(ce_key, {}) if ce_key else {}
                pe_data = self.oi_data.get(pe_key, {}) if pe_key else {}

                if ce_key:
                    payload["calls"].append({
                        "strike": strike,
                        "instrument_key": ce_key,
                        "ltp": ce_data.get("ltp", 0),
                        "oi": ce_data.get("oi", 0),  # Will be 0 when market is closed
                        "volume": ce_data.get("volume", 0)
                    })

                if pe_key:
                    payload["puts"].append({
                        "strike": strike,
                        "instrument_key": pe_key,
                        "ltp": pe_data.get("ltp", 0),
                        "oi": pe_data.get("oi", 0),  # Will be 0 when market is closed
                        "volume": pe_data.get("volume", 0)
                    })

            payload["calls"].sort(key=lambda x: x["strike"])
            payload["puts"].sort(key=lambda x: x["strike"])

            return payload

        except Exception as e:
            logger.error(f"Error building payload: {e}")
            return {
                "symbol": chain.symbol,
                "spot_price": chain.spot_price,
                "atm_strike": chain.current_atm_strike,
                "pcr": 0.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "calls": [],
                "puts": []
            }
        
    async def _broadcast(self, symbol: str, payload: Dict[str, Any]) -> None:
        try:
            # 🔥 FORWARD RAW PAYLOAD DIRECTLY (no market_data wrapper)
            # This ensures calls[] and puts[] reach frontend as expected
            await manager.broadcast_json(symbol, payload)

            print(f"📡 WS BROADCAST SENT for {symbol}")

        except Exception as e:
            logger.error(f"Broadcast failed for {symbol}: {e}")

# Global instance
_builder_instance = None

def get_live_chain_builder():
    global _builder_instance
    if _builder_instance is None:
        _builder_instance = LiveOptionChainBuilder()
    return _builder_instance
