"""
Live Option Chain Builder
Builds option chain from Upstox V3 WebSocket feed in real-time
"""

print(" LiveOptionChainBuilder module loaded")

import asyncio
import json
import logging
from datetime import datetime, timezone, date
from typing import Dict, Any, Optional, List, Set, Tuple
from dataclasses import dataclass, field
from copy import deepcopy
from app.services.upstox_auth_service import get_upstox_auth_service
from app.services.market_data.upstox_client import UpstoxClient
from app.core.live_market_state import MarketStateManager
from app.services.market_session_manager import get_market_session_manager
from app.services.instrument_registry import get_instrument_registry
from fastapi import HTTPException
import httpx
from app.core.ws_manager import manager
from app.models.live_chain_state import LiveChainState
from datetime import datetime

def resolve_symbol_from_instrument(instrument_key: str) -> str | None:

    if instrument_key.startswith("NSE_INDEX|Nifty"):
        return "NIFTY"

    if "BANKNIFTY" in instrument_key:
        return "BANKNIFTY"

    if "FINNIFTY" in instrument_key:
        return "FINNIFTY"

    if "MIDCPNIFTY" in instrument_key:
        return "MIDCPNIFTY"

    if "NIFTY" in instrument_key:
        return "NIFTY"

    return None

logger = logging.getLogger(__name__)

# Index symbol mapping for registry lookup
INDEX_SYMBOL_MAP = {
    "NIFTY": "NIFTY",
    "BANKNIFTY": "BANKNIFTY", 
    "FINNIFTY": "FINNIFTY"
}

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
    symbol: str  # Original symbol for WS payload
    registry_symbol: str  # Normalized symbol for registry lookup
    expiry: date  # Changed from str to date
    strike_map: Dict[float, Dict[str, str]] = field(default_factory=dict)  # strike -> {CE: instrument_key, PE: instrument_key}
    reverse_map: Dict[str, Tuple[float, str]] = field(default_factory=dict)  # instrument_key -> (strike, type)
    live_chain: Dict[float, StrikeData] = field(default_factory=dict)
    spot_price: Optional[float] = None
    last_update: Optional[datetime] = None
    
    # ATM strike window management
    current_atm_strike: Optional[float] = None
    strike_step: int = 50  # Standard strike step for NIFTY/BANKNIFTY
    atm_strikes: List[float] = field(default_factory=list)
    subscribed_strikes: Set[float] = field(default_factory=set)
    active_keys: Set[str] = field(default_factory=set)  # Currently subscribed instrument keys
    is_active: bool = False  # Builder ready flag
    pending_option_ticks: List[Tuple[str, dict]] = field(default_factory=list)  # Buffer for ticks before activation
    is_replaying: bool = False  # Replay lock flag
    is_draining: bool = False  # Background drain guard flag
    
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
    
    def calculate_atm_strike(self, spot):

        step = 50

        return round(spot / step) * step
    
    def get_strike_window(self, atm_strike: float):
        """Get strikes around ATM using new window builder"""
        return self.build_atm_window(atm_strike)
    
    def build_atm_window(self, atm_strike):

        strikes = sorted(self.strike_map.keys())

        if not strikes:
            return []

        closest = min(strikes, key=lambda s: abs(s - atm_strike))

        idx = strikes.index(closest)

        start = max(0, idx - 8)
        end = idx + 9

        return strikes[start:end]
    
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
    
    
    def __init__(self, symbol: str, expiry):
        # 🔥 NORMALIZE EXPIRY
        if isinstance(expiry, str):
            expiry = datetime.strptime(expiry, "%Y-%m-%d").date()
        
        if isinstance(expiry, datetime):
            expiry = expiry.date()

        self.original_symbol = symbol
        self.symbol = symbol  # Use symbol exactly as received
        self.expiry = expiry
        self.key = f"{symbol}:{expiry.isoformat()}"  # Keep original symbol for key consistency

        self.initialized = False
        self.init_lock = asyncio.Lock()
        self.subscription_done = False
        self.clients = set()

        self.auth_service = get_upstox_auth_service()
        self.client = UpstoxClient()
        self.market_state = MarketStateManager()
        self.session_manager = get_market_session_manager()

        # Instrument cache
        self._instruments_loaded = False
        self._cached_instruments = []
        self._instrument_lookup = {}
        self._instrument_reverse_lookup = {}

        # ✅ SINGLE CHAIN STATE ONLY
        self.chain_state: Optional[LiveChainState] = None

        # OI update task
        self.oi_update_task: Optional[asyncio.Task] = None

        # Batch compute task
        self._batch_compute_task: Optional[asyncio.Task] = None

        # OI data store
        self.oi_data = {}
        
        # Chain rebuild flag
        self._rebuild_in_progress = False
        
        # Load cached instruments at startup
       

    async def start(self) -> None:
        """
        Start builder lifecycle (only once per symbol:expiry)
        """

        if self.initialized:
            return

        from app.services.instrument_registry import get_instrument_registry
        registry = get_instrument_registry()

        logger.info(f"🚀 Initializing Builder → {self.symbol}:{self.expiry}")

        # 🔥 MUST PASS SYMBOL + EXPIRY
        await self.initialize_chain(registry)

        await self._start_oi_updates(registry)
        await self._start_batch_compute(registry)

        # 🔥 CRITICAL FIX: Initialize ATM window and subscribe to options
        if self.chain_state and self.chain_state.strike_map:
            logger.info(f"🔥 TRIGGERING OPTION SUBSCRIPTION for {self.symbol}:{self.expiry}")
            await self.initialize_atm_window()
        else:
            logger.warning(f"⚠️ No strike map available for {self.symbol}:{self.expiry} - will subscribe after spot price")

        self.initialized = True

        logger.info(f"✅ Builder Started → {self.symbol}:{self.expiry}")

    def get_latest_option_chain(self) -> Optional[LiveChainState]:
        return self.chain_state

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

    
        
    async def initialize_chain(self, registry, attempt: int = 0) -> LiveChainState:
        import asyncio

        if self.chain_state:
            return self.chain_state

        retry = 0
        while not registry._ready_event.is_set():
            if retry >= 10:
                raise Exception("Instrument store not ready after 5 seconds")
            await asyncio.sleep(0.5)
            retry += 1

        logger.info(f"🚀 Initializing option chain for {self.symbol}:{self.expiry}")

        # Create chain state at the VERY TOP before any registry lookups
        chain = LiveChainState(
            symbol=self.original_symbol,
            registry_symbol=self.symbol,
            expiry=self.expiry
        )

        try:
            # 🔥 WAIT UNTIL CDN REGISTRY READY
            await registry.wait_until_ready()

            token = await self.auth_service.get_valid_access_token()

            if not token:
                logger.warning("Auth token missing → returning empty chain")
                self.chain_state = chain
                return chain

            # 🔥 BUILD STRIKE MAP FROM REGISTRY (NOT LOCAL JSON)
            # 🔥 SAFE SYMBOL NORMALIZATION
            builder_symbol = str(chain.registry_symbol).strip().upper()
            logger.info(f"Registry lookup using symbol: {builder_symbol}")
            
            # Try exact match first
            expiry_map = registry.options.get(builder_symbol)
            
            # If not found, try normalized match (handle NIFTY vs NIFTY 50)
            if not expiry_map:
                for reg_symbol in registry.options.keys():
                    reg_symbol_norm = str(reg_symbol).strip().upper().replace(" 50", "")
                    if reg_symbol_norm == builder_symbol.replace(" 50", ""):
                        expiry_map = registry.options.get(reg_symbol)
                        logger.info(f"Using normalized symbol match: {reg_symbol} → {builder_symbol}")
                        break

            if not expiry_map:
                logger.error(f"No option instruments found for {chain.registry_symbol} in registry")
                raise RuntimeError(f"No option instruments for {chain.registry_symbol}")

            # 🔥 VALIDATE EXPIRY EXISTS IN REGISTRY
            available_expiries = set(str(e) for e in expiry_map.keys())
            requested_expiry = str(chain.expiry)
            
            if requested_expiry not in available_expiries:
                logger.error(
                    f"Invalid expiry requested: {requested_expiry}. "
                    f"Available expiries: {sorted(available_expiries)}"
                )
                raise ValueError(
                    f"Expiry {requested_expiry} not available in registry"
                )

            strike_map = None
            
            # Find expiry match by comparing date parts
            logger.info(f"Available expiries: {[e.date() if hasattr(e, 'date') else e for e in expiry_map.keys()]}")
            for reg_expiry, strikes in expiry_map.items():
                # 🔥 SAFE EXPIRY COMPARISON
                reg_expiry_date = reg_expiry.date() if hasattr(reg_expiry, 'date') else reg_expiry
                if isinstance(reg_expiry_date, str):
                    try:
                        reg_expiry_date = datetime.strptime(reg_expiry_date, "%Y-%m-%d").date()
                    except ValueError:
                        continue  # skip invalid format safely
                elif isinstance(reg_expiry_date, datetime):
                    reg_expiry_date = reg_expiry_date.date()
                
                if reg_expiry_date == chain.expiry:
                    strike_map = strikes
                    logger.info(f"Found strike map for expiry {chain.expiry}")
                    break
            
            if not strike_map:
                logger.error(f"No strikes found for {chain.registry_symbol}:{chain.expiry}")
                logger.info(f"Available expiries: {[e.date() if hasattr(e, 'date') else e for e in expiry_map.keys()]}")
                raise RuntimeError(f"No strikes for expiry {chain.expiry}")

            reverse_map = {}

            for strike, pair in strike_map.items():
                if not isinstance(pair, dict):
                    continue

                ce_data = pair.get("CE") if isinstance(pair.get("CE"), dict) else None
                pe_data = pair.get("PE") if isinstance(pair.get("PE"), dict) else None
                
                if ce_data:
                    ce_token = (
                        ce_data.get("instrument_token")
                        or ce_data.get("instrument_key")
                    )
                    if ce_token:
                        reverse_map[ce_token] = (strike, "CE")
                
                if pe_data:
                    pe_token = (
                        pe_data.get("instrument_token")
                        or pe_data.get("instrument_key")
                    )
                    if pe_token:
                        reverse_map[pe_token] = (strike, "PE")

            # Update the existing chain object with strike data
            chain.strike_map = strike_map
            chain.build_reverse_map()

            self.chain_state = chain

            # 🔥 DEBUG LOGS - Count loaded instruments
            ce_count = sum(1 for pair in strike_map.values() if pair.get("CE"))
            pe_count = sum(1 for pair in strike_map.values() if pair.get("PE"))
            logger.info(f"Loaded CE instruments: {ce_count}")
            logger.info(f"Loaded PE instruments: {pe_count}")
            
            # 🔥 FIX 7 — COMPREHENSIVE LOGGING
            logger.info(f"🔧 Builder initialized → {self.symbol}:{self.expiry}")
            logger.info(f"📊 Strike map size: {len(strike_map)}")
            logger.info(f"🔄 Reverse map size: {len(reverse_map)}")
            logger.info(f"🎯 ATM strike: {chain.current_atm_strike}")
            logger.info(f"📈 ATM window size: {len(chain.get_strike_window(chain.current_atm_strike))}")

            # 🔥 FUTIDX MUST EXIST BEFORE OI LOOP
            fut_map = registry.futidx.get(chain.registry_symbol)

            if not fut_map:
                raise RuntimeError(f"No FUTIDX MAP for {chain.registry_symbol}")

            target_expiry = chain.expiry.strftime("%Y-%m-%d")

            # agar exact FUT expiry nahi mila
            opt_date = datetime.strptime(target_expiry, "%Y-%m-%d")

            valid_futures = []

            for fut_expiry, inst in fut_map.items():
                fut_date = datetime.strptime(fut_expiry, "%Y-%m-%d")
                
                # 👇 FUT MUST BE SAME OR AFTER OPTION EXPIRY
                if fut_date >= opt_date:
                    valid_futures.append((fut_date, inst))

            if not valid_futures:
                raise RuntimeError(f"No valid FUTIDX available for {chain.registry_symbol}")

            valid_futures.sort(key=lambda x: x[0])

            nearest_expiry = valid_futures[0][0].strftime("%Y-%m-%d")
            logger.info(f"🟢 Using nearest MONTHLY FUTIDX expiry {nearest_expiry}")

            chain.fut_key = valid_futures[0][1]

            logger.info(f"🔥 ATM ladder built for {chain.registry_symbol}:{chain.expiry}")

            return chain

        except Exception as e:
            logger.error(f"Chain initialization failed for {chain.registry_symbol}:{chain.expiry} → {e}")

            # Assign empty chain so WS builder survives
            chain.strike_map = {}
            chain.reverse_map = {}
            chain.atm_strikes = []
            chain.fut_key = None

            self.chain_state = chain
            return   # DO NOT raise exception
    
    async def _handle_expiry_fallback(self, symbol: str, current_expiry: str, attempt: int) -> LiveChainState:
        """
        Handle weekly expiry fallback by getting next available expiry
        """
        try:
            token = await self.auth_service.get_valid_access_token()

            valid_expiries = await self.client.get_option_expiries(token, symbol)

            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            future_expiries = [e for e in valid_expiries if e > today and e != current_expiry]

            if not future_expiries:
                logger.error(f"No future expiries available for {symbol}")
                raise HTTPException(status_code=404, detail="No valid expiries available")

            next_expiry = min(future_expiries)
            logger.info(f"Fallback: Using next expiry {next_expiry} for {symbol} (attempt {attempt})")

            # 🔥🔥🔥 CRITICAL FIX
            from app.services.instrument_registry import get_instrument_registry
            registry = get_instrument_registry()

            self.expiry = next_expiry
            self.key = f"{self.symbol}:{self.expiry}"
            return await self.initialize_chain(registry, attempt)

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
    
    async def _get_option_chain_instrument_key(self, symbol: str, registry) -> str:

        # Use normalized symbol for registry lookup
        normalized_symbol = INDEX_SYMBOL_MAP.get(symbol, symbol)
        fut_map = registry.futidx.get(normalized_symbol)

        if not fut_map:
            raise HTTPException(status_code=500, detail=f"No FUTIDX found for {normalized_symbol}")

        today = datetime.now().date()

        valid = []

        for expiry, key in fut_map.items():
            fut_date = datetime.strptime(expiry, "%Y-%m-%d").date()
            if fut_date >= today:
                valid.append((fut_date, key))

        if not valid:
            valid = [
                (datetime.strptime(e, "%Y-%m-%d").date(), k)
                for e, k in fut_map.items()
            ]

        valid.sort(key=lambda x: x[0])

        return valid[0][1]
    
    async def subscribe_to_instruments(self) -> List[str]:
        """
        Subscribe to ATM ± window instruments for a symbol
        Returns list of instrument keys to subscribe to
        """
        if not self.chain_state:
            raise HTTPException(status_code=404, detail=f"Chain not initialized for {self.symbol}")

        chain_state = self.chain_state

        # 🛑 DO NOT RE-SUBSCRIBE AGAIN
        if chain_state.subscribed_strikes:
            logger.debug(f"{self.symbol} already subscribed → skipping")
            return []
        
        # Get spot price from market state
        spot = chain_state.spot_price
        
        # WS tick not received yet → fallback to REST
        if not spot:
            try:
                from app.services.market_data.upstox_client import UpstoxClient
                
                client = UpstoxClient()
                
                # Determine index key based on symbol
                index_key = "NSE_INDEX|Nifty 50" if self.symbol == "NIFTY" else "NSE_INDEX|Nifty Bank"
                spot = await client.get_ltp(index_key)

                if spot:
                    chain_state.spot_price = float(spot)
                    logger.warning(f"REST FALLBACK SPOT USED for {self.symbol} → {spot}")
                    
                    if chain_state.current_atm_strike is None:
                        atm_strike = chain_state.calculate_atm_strike(chain_state.spot_price)
                        chain_state.current_atm_strike = atm_strike
                        logger.info(f"ATM initialized → {atm_strike}")
                
            except Exception as e:
                logger.error(f"REST fallback failed for {self.symbol}: {e}")
                return []
        
        # If still no spot price after fallback, return empty
        if not spot:
            logger.warning(f"No spot price available for {self.symbol} - cannot subscribe to FO instruments")
            return []
        
        # Calculate ATM strike
        try:
            spot_value = float(spot)
        except:
            return
        
        if not chain_state.strike_step:
            return
        
        atm_strike = round(spot_value / chain_state.strike_step) * chain_state.strike_step
        atm_strike = float(atm_strike)
        chain_state.current_atm_strike = atm_strike
        
        # Get strike window (ATM ± window_size)
        logger.info(f"ATM strike: {atm_strike} type={type(atm_strike)}")
        logger.info(f"Sample strike type: {type(next(iter(chain_state.strike_map.keys()))) if chain_state.strike_map else 'No strikes'}")
        window_strikes = chain_state.get_strike_window(atm_strike)
        
        # Get active instrument keys for window only
        active_keys = chain_state.get_active_instrument_keys(window_strikes)
        
        # Add spot instrument key
        spot_key = f"NSE_INDEX|{self.symbol}"
        all_keys = list(active_keys) + [spot_key]
        
        # Update state
        chain_state.subscribed_strikes = set(window_strikes)
        chain_state.active_keys = active_keys
        
        logger.info(f"Subscribing to {self.symbol}: ATM={atm_strike}, window={len(window_strikes)} strikes, {len(active_keys)} option instruments")
        return all_keys
    
    async def handle_tick(self, instrument_key: str, data: Dict[str, Any]) -> None:
        """
        Handle incoming tick data and update live chain
        OPTIMIZED: Only store data, no computation - batching handles computation
        """
        logger.info(f"[TICK] {self.symbol} → builder={id(self)} | {instrument_key}")
        
        # DEBUG: Check if this is an index tick
        if instrument_key.startswith("NSE_INDEX"):
            logger.info(f"🔍 [INDEX TICK RECEIVED] {self.symbol} | {instrument_key} | LTP={data.get('ltp')}")
        
        if not self.chain_state:
            logger.debug(f"No chain state for {self.symbol}, ignoring tick")
            return
        
        chain_state = self.chain_state
        if not chain_state:
            return
        
        # Handle spot price updates (minimal computation)
        if instrument_key.startswith("NSE_INDEX"):
            spot_price = data.get("ltp") or data.get("last_price")
            if spot_price:
                old_spot = chain_state.spot_price
                chain_state.spot_price = float(spot_price)
                logger.info(f"📈 {self.symbol} INDEX LTP → {spot_price} (was {old_spot})")
                
                if chain_state.current_atm_strike is None:
                    atm_strike = chain_state.calculate_atm_strike(chain_state.spot_price)
                    chain_state.current_atm_strike = atm_strike
                    logger.info(f"ATM initialized → {atm_strike}")
                if not chain_state.strike_map and not self._rebuild_in_progress:
                    self._rebuild_in_progress = True
                    asyncio.create_task(self._retry_chain_build())
                
                # Initialize ATM window on first spot price (only once)
                if chain_state.current_atm_strike is None:
                    await self.initialize_atm_window()
                # Note: ATM rebalancing moved to batch compute loop
            else:
                logger.warning(f"⚠️ INDEX TICK NO LTP: {instrument_key} | data={data}")
            return
        
        # Handle option instrument updates (STORE ONLY)
        logger.info(f"📊 OPTION TICK: {self.symbol} | {instrument_key} | LTP={data.get('ltp')}")
        chain_state.update_tick(instrument_key, data)
        logger.info(f"✅ CHAIN UPDATED: {instrument_key} | Chain size: {len(chain_state.live_chain)}")
        
        # Only process option ticks if builder is active
        if not chain_state.is_active:
            # Buffer ticks until mapping is ready
            if not chain_state.reverse_map or not chain_state.active_keys:
                chain_state.pending_option_ticks.append((instrument_key, deepcopy(data)))
                logger.info(f"📦 BUFFERED OPTION TICK: {instrument_key} (pending={len(chain_state.pending_option_ticks)})")
                return
            chain_state.is_active = True
            chain_state.is_replaying = True  # Start replay lock
            logger.info(f"Builder stream live → {self.symbol}:{self.expiry}")
            
            # Create immutable replay batch
            replay_batch = chain_state.pending_option_ticks.copy()
            
            # Immediately clear original buffer
            chain_state.pending_option_ticks.clear()
            
            # Replay ONLY replay_batch
            for key, tick in replay_batch:
                await self._process_option_tick(key, tick)
            
            # Bounded replay drain - prevent infinite loop
            max_drain_rounds = 3
            rounds = 0
            
            while chain_state.pending_option_ticks and rounds < max_drain_rounds:
                # Take snapshot of current buffer
                replay_batch = chain_state.pending_option_ticks.copy()
                
                # Clear buffer for new arrivals
                chain_state.pending_option_ticks.clear()
                
                # Replay current batch
                for key, tick in replay_batch:
                    await self._process_option_tick(key, tick)
                
                rounds += 1
            
            chain_state.is_replaying = False  # End replay lock only after bounded drain
            
            # Schedule background drain for remaining ticks
            if chain_state.pending_option_ticks and not chain_state.is_draining:
                chain_state.is_draining = True
                asyncio.create_task(self._drain_remaining_ticks())
            
        # Buffer live ticks during replay
        elif chain_state.is_replaying:
            chain_state.pending_option_ticks.append((instrument_key, deepcopy(data)))
            logger.info(f"📦 BUFFERED DURING REPLAY: {instrument_key}")
            return
            
        # Process current tick normally
        await self._process_option_tick(instrument_key, data)
    
    async def _process_option_tick(self, instrument_key: str, data: Dict[str, Any]) -> None:
        """
        Process individual option tick after activation
        """
        if not self.chain_state:
            return
        
        chain_state = self.chain_state
        if not chain_state:
            return
        
        # Store tick data
        chain_state.update_tick(instrument_key, data)
        logger.info(f"✅ OPTION TICK PROCESSED: {instrument_key} | LTP={data.get('ltp')} | Chain size: {len(chain_state.live_chain)}")
        # No computation here - batch loop handles PCR, payload, broadcast
    
    async def _drain_remaining_ticks(self):
        """
        Drain remaining buffered ticks in background
        """
        chain_state = self.chain_state
        if not chain_state:
            return
        
        try:
            while chain_state.pending_option_ticks:
                # Take batch of remaining ticks
                batch = chain_state.pending_option_ticks.copy()
                
                # Clear buffer for new arrivals
                chain_state.pending_option_ticks.clear()
                
                # Process batch
                for key, tick in batch:
                    await self._process_option_tick(key, tick)
                
                # Small delay to prevent overwhelming the event loop
                await asyncio.sleep(0)
        
        finally:
            if chain_state.pending_option_ticks:
                # Schedule final drain if buffer still has ticks
                asyncio.create_task(self._drain_remaining_ticks())
            else:
                chain_state.is_draining = False
    
    async def _retry_chain_build(self):
        """
        Retry chain build when strike_map is empty
        """
        try:
            logger.info(f"Retrying chain rebuild → {self.symbol}:{self.expiry}")
            await self.initialize_chain()
            
            # Initialize ATM window immediately after successful rebuild
            chain = self.chain_state
            if chain and chain.strike_map and chain.spot and not chain.atm_strikes:
                logger.info(f"Lazy ATM init after rebuild → {self.symbol}:{self.expiry}")
                await self._initialize_atm_window(chain.spot)
                
                # Note: Builder will be activated after subscription completes
            
            self._rebuild_in_progress = False
        except Exception as e:
            logger.warning(f"Retry failed → will retry on next index tick: {e}")
            self._rebuild_in_progress = False
    
    async def _rebalance_strike_window(self, new_atm_strike: float) -> None:
        """
        Rebalance strike window when ATM shifts
        """
        if not self.chain_state:
            return
        
        chain_state = self.chain_state
        if not chain_state:
            return
        
        # Get new strike window
        new_strikes = chain_state.get_strike_window(new_atm_strike)
        new_active_keys = chain_state.get_active_instrument_keys(new_strikes)
        
        # Get keys to unsubscribe (old but not in new)
        keys_to_unsubscribe = chain_state.active_keys - new_active_keys
        
        # Get keys to subscribe (new but not in old)
        keys_to_subscribe = new_active_keys - chain_state.active_keys
        
        if keys_to_unsubscribe or keys_to_subscribe:
            logger.info(f"Rebalancing {self.symbol}: unsubscribe {len(keys_to_unsubscribe)}, subscribe {len(keys_to_subscribe)}")
            
            # Subscribe to window instruments
            from app.services.websocket_market_feed import ws_feed_manager
            
            # Get the global feed (not the old upstox_market_feed)
            ws_feed = await ws_feed_manager.get_feed()
            
            if not ws_feed:
                logger.warning(f"Global feed for {self.symbol} not found during rebalance")
                return

            # Unsubscribe old keys
            if keys_to_unsubscribe:
                await ws_feed.unsubscribe_from_instruments(list(keys_to_unsubscribe))
            
            # Subscribe new keys
            if keys_to_subscribe:
                success = await ws_feed.subscribe_to_instruments(list(keys_to_subscribe))
                if success:
                    logger.info(f"🔥 REBALANCE SUBSCRIPTION SUCCESS: {len(keys_to_subscribe)} new instruments for {self.symbol}")
                else:
                    logger.error(f"❌ REBALANCE SUBSCRIPTION FAILED for {self.symbol}")
            
            # Update state
            chain_state.current_atm_strike = new_atm_strike
            chain_state.subscribed_strikes = set(new_strikes)
            chain_state.active_keys = new_active_keys
            
            logger.info(f"Rebalanced {self.symbol} window: ATM={new_atm_strike}, strikes={len(new_strikes)}")
    
    async def initialize_atm_window(self)-> None:
        """
        Initialize ATM window subscription after spot price is received
        """
        if not self.chain_state:
            return
        
        chain_state = self.chain_state
        if not chain_state:
            return
        
        if chain_state.spot_price is None:
            logger.warning(f"No spot price available for {self.symbol} to initialize ATM window")
            return
        
        # Calculate ATM and get window
        atm_strike = chain_state.calculate_atm_strike(chain_state.spot_price)
        window_strikes = chain_state.get_strike_window(atm_strike)
        active_keys = chain_state.get_active_instrument_keys(window_strikes)
        
        # Subscribe to window instruments
        if active_keys:
            from app.services.websocket_market_feed import ws_feed_manager
            
            # Get the global feed (not the old upstox_market_feed)
            ws_feed = await ws_feed_manager.get_feed()
            
            if not ws_feed:
                logger.warning(f"Global feed not found for ATM window init for {self.symbol}")
                return

            all_keys = list(active_keys) + [f"NSE_INDEX|{self.symbol}"]
            success = await ws_feed.subscribe_to_instruments(all_keys)
            
            if success:
                logger.info(f"🔥 OPTION SUBSCRIPTION SUCCESS: {len(all_keys)} instruments for {self.symbol}")
            else:
                logger.error(f"❌ OPTION SUBSCRIPTION FAILED for {self.symbol}")
            
            # Update state
            chain_state.current_atm_strike = atm_strike
            chain_state.subscribed_strikes = set(window_strikes)
            chain_state.active_keys = active_keys
            
            logger.info(f"Initialized {self.symbol} ATM window: ATM={atm_strike}, strikes={len(window_strikes)}, instruments={len(active_keys)}")
    
    async def _start_oi_updates(self, registry) -> None:
        """
        Start periodic OI updates from REST API
        """
        if self.oi_update_task and not self.oi_update_task.done():
            return  # Already running
        
        # Create and start OI update task
        task = asyncio.create_task(self._oi_update_loop(registry))
        self.oi_update_task = task
        logger.debug(f"Started OI updates for {self.symbol}:{self.expiry}")
    
    async def _safe_cancel(self, task):
        """
        Safely cancel a task without blocking the caller
        """
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    async def stop_tasks(self) -> None:
        """
        Stop background tasks for this builder instance
        Called when WebSocket disconnects to prevent zombie tasks
        Uses non-blocking cancellation to prevent ASGI blocking
        """

        # Stop OI update task (non-blocking)
        if self.oi_update_task and not self.oi_update_task.done():
            asyncio.create_task(self._safe_cancel(self.oi_update_task))
            logger.debug(f"Stopped OI update task for {self.key}")

        # Stop batch compute task (non-blocking)
        if self._batch_compute_task and not self._batch_compute_task.done():
            asyncio.create_task(self._safe_cancel(self._batch_compute_task))
            logger.debug(f"Stopped batch compute task for {self.key}")

        logger.info(f"Stopped background tasks for {self.key}")
    
    async def _oi_update_loop(self, registry) -> None:
        """
        Periodic OI update loop - runs every 60 seconds
        """
        # 🔥 WAIT FOR REGISTRY BEFORE BACKGROUND ACCESS
        await registry.wait_until_ready()
        
        try:
            while True:
                await self._fetch_global_oi(registry)
                await asyncio.sleep(60)  # Update every 60 seconds
        
        except asyncio.CancelledError:
            logger.debug(f"Loop cancelled for {self.symbol}:{self.expiry}")
            raise
    
    async def _fetch_global_oi(self, registry) -> None:
        """
        Fetch global OI from REST API for active expiry
        """
        try:
            if not self.chain_state:
                return
            
            chain_state = self.chain_state
            if not chain_state:
                return
            
            # Get access token
            token = await self.auth_service.get_valid_access_token()
            if not token:
                logger.warning(f"No access token for OI update: {self.symbol}")
                return
            
            # Fetch option chain from REST
            # OPTION CHAIN REST API NEEDS INDEX KEY (NOT FUTIDX)
            if self.symbol == "NIFTY":
                option_key = "NSE_INDEX|Nifty 50"
            elif self.symbol == "BANKNIFTY":
                option_key = "NSE_INDEX|Nifty Bank"
            else:
                return
            
            response = await self.client.get_option_chain(option_key, self.expiry.strftime("%Y-%m-%d"))
            
            if not response or not response.get("data"):
                logger.warning(f"No option chain data from REST for {self.symbol}")
                return
            
            # Process option chain and update OI
            for item in response["data"]:
                if not isinstance(item, dict):
                    continue
                
                strike = float(item.get("strike_price"))
                ce_oi = item.get("ce", {}).get("oi", 0)
                pe_oi = item.get("pe", {}).get("oi", 0)
                
                if strike in chain_state.strike_map:
                    chain_state.strike_map[strike]["CE"]["oi"] = ce_oi
                    chain_state.strike_map[strike]["PE"]["oi"] = pe_oi
            
            logger.info(f"Updated OI from REST for {len(chain_state.strike_map)} strikes")
            
        except Exception as e:
            logger.error(f"Failed to fetch global OI for {self.symbol}: {e}")
            response = await self.client.get_option_chain(option_key, chain_state.expiry.strftime("%Y-%m-%d"))
            
            if not isinstance(response, dict):
                logger.error("Invalid option chain response type")
                return

            response_data = response.get("data")

            data = []

            # Case 1 — data already list
            if isinstance(response_data, list):
                data = response_data

            # Case 2 — wrapped dict structure
            elif isinstance(response_data, dict):

                # Format A
                if "records" in response_data:
                    records = response_data.get("records")

                    if isinstance(records, dict):
                        data = records.get("data", [])

                # Format B
                elif "data" in response_data:
                    nested = response_data.get("data")

                    if isinstance(nested, list):
                        data = nested

            # Final safety
            if not isinstance(data, list):
                logger.error(f"Unexpected option chain format: {type(data)}")
                return

            logger.info(f"Option chain records received: {len(data)}")
            
            # 🔥 REBUILD STRIKE_MAP FROM ACTUAL UPSTOX V2 RESPONSE
            strike_map = {}
            
            for item in data:
                if not isinstance(item, dict):
                    continue
                
                raw_strike = (
                    item.get("strike_price")
                    or item.get("strike")
                    or item.get("strikePrice")
                )
                
                if raw_strike is None:
                    continue
                
                try:
                    strike = float(raw_strike)
                except:
                    continue
                
                if strike not in strike_map:
                    strike_map[strike] = {}
                
                ce_data = (
                    item.get("CE")
                    or item.get("call_options")
                    or item.get("callOptions")
                )
                
                pe_data = (
                    item.get("PE")
                    or item.get("put_options")
                    or item.get("putOptions")
                )
                
                if isinstance(ce_data, dict):
                    strike_map[strike]["CE"] = ce_data
                
                if isinstance(pe_data, dict):
                    strike_map[strike]["PE"] = pe_data
            
            logger.info(f"Total strikes loaded from REST: {len(strike_map)}")
            
            # 🔥 FIX 3 — OPTION CHAIN FALLBACK
            # If REST returned empty, fallback to instrument registry
            if len(strike_map) == 0:
                logger.warning("⚠️ REST option chain empty → falling back to registry")
                
                # Load from registry instead
                registry = get_instrument_registry()
                symbol_upper = chain_state.registry_symbol.upper().strip()
                expiry_map = registry.options.get(symbol_upper)
                
                if expiry_map:
                    for reg_expiry, strikes in expiry_map.items():
                        # 🔥 SAFE EXPIRY COMPARISON
                        reg_expiry_date = reg_expiry.date() if hasattr(reg_expiry, 'date') else reg_expiry
                        if isinstance(reg_expiry_date, str):
                            try:
                                reg_expiry_date = datetime.strptime(reg_expiry_date, "%Y-%m-%d").date()
                            except ValueError:
                                continue
                        elif isinstance(reg_expiry_date, datetime):
                            reg_expiry_date = reg_expiry_date.date()
                        
                        if reg_expiry_date == chain_state.expiry:
                            # Use registry strikes as fallback
                            for strike, pair in strikes.items():
                                if isinstance(pair, dict) and strike not in chain_state.strike_map:
                                    chain_state.strike_map[strike] = pair
                    
                    logger.info(f"🔄 Fallback loaded {len(chain_state.strike_map)} strikes from registry")
            
            # Update chain state with new strike_map
            chain_state.strike_map = strike_map
            
            # STEP 2 — CALL REVERSE MAP AFTER STRIKE MAP BUILD
            chain_state.build_reverse_map()
            
    def build_reverse_map(self):

        self.reverse_map = {}

        for strike, contracts in self.strike_map.items():

            ce_token = contracts.get("CE")
            pe_token = contracts.get("PE")

            if ce_token:
                self.reverse_map[ce_token] = {
                    "strike": strike,
                    "type": "CE"
                }

            if pe_token:
                self.reverse_map[pe_token] = {
                    "strike": strike,
                    "type": "PE"
                }

        logger.info(f"Reverse map built with {len(self.reverse_map)} entries")
    
    async def build_chain_payload(self) -> Dict[str, Any]:
        """
        Build final option chain payload for WebSocket transmission
        """
        if not self.chain_state:
            return {
                "symbol": self.symbol,
                "expiry": None,
                "spot": None,
                "calls": [],
                "puts": [],
                "pcr": 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # STEP 3: Ensure builder reads from: websocket_market_feed.latest_ticks
        await self._sync_from_global_feed()
        
        chain_state = self.chain_state
        if not chain_state:
            return {}
        return chain_state.build_final_chain()

    async def _sync_from_global_feed(self) -> None:
        """
        Surgically sync builder state from global Upstox singleton ticks cache
        """
        try:
            from app.services.upstox_market_feed import get_global_feed
            ws_feed = get_global_feed(self.symbol)
            
            if ws_feed and hasattr(ws_feed, 'latest_ticks'):
                # Extract copy of ticks to avoid mutation errors during iteration
                ticks = dict(ws_feed.latest_ticks)
                for instrument_key, tick_data in ticks.items():
                    # Direct update to bypass create_task overhead in high-frequency loop
                    if not self.chain_state:
                        continue
                    chain_state = self.chain_state
                    
                    # Handle spot price
                    if instrument_key == f"NSE_INDEX|{self.symbol}":
                        spot_price = tick_data.get("ltp")
                        if spot_price:
                            chain_state.spot_price = float(spot_price)
                            
                            if chain_state.current_atm_strike is None:
                                atm_strike = chain_state.calculate_atm_strike(chain_state.spot_price)
                                chain_state.current_atm_strike = atm_strike
                                logger.info(f"ATM initialized → {atm_strike}")
                    else:
                        # Handle option ticks
                        chain_state.update_tick(instrument_key, tick_data)
        except Exception as e:
            logger.error(f"Error syncing from global feed for {self.symbol}: {e}")
    
    async def _start_batch_compute(self, registry) -> None:
        """
        Start batch compute loop for optimized processing
        """
        if self._batch_compute_task and not self._batch_compute_task.done():
            logger.warning(f"Batch compute task already running for {self.symbol}:{self.expiry}")
            return
        
        self._batch_compute_task = asyncio.create_task(
            self._batch_compute_loop(registry)
        )
        logger.info(f"Started batch compute loop for {self.symbol}:{self.expiry}")
    
    async def _batch_compute_loop(self, registry) -> None:
        """
        Batch compute loop - handles PCR calculation, payload building, and broadcasting
        Runs every 500ms to optimize performance
        Updated to broadcast payload even when market is CLOSED for development
        """
        # 🔥 WAIT FOR REGISTRY BEFORE BACKGROUND ACCESS
        await registry.wait_until_ready()
        
        logger.debug(f"Starting batch compute loop for {self.symbol}:{self.expiry}")
        logger.info(f"🔄 BATCH COMPUTE STARTED: {self.symbol}:{self.expiry}")
        
        try:
            while True:
                await asyncio.sleep(0.5)  # 500ms batching window
                
                chain = self.chain_state
                if not chain:
                    continue
                
                try:
                    # ENSURE SPOT PRICE VIA REST FALLBACK (even when market is CLOSED)
                    if not chain.spot_price:
                        try:
                            from app.services.market_data.upstox_client import UpstoxClient
                            client = UpstoxClient()
                            
                            # Determine index key based on symbol
                            index_key = "NSE_INDEX|Nifty 50" if self.symbol == "NIFTY" else "NSE_INDEX|Nifty Bank"
                            spot = await client.get_ltp(index_key)

                            if spot:
                                old_spot = chain.spot_price
                                chain.spot_price = float(spot)
                                logger.info(f"🔄 REST FALLBACK SPOT for {self.symbol} → {spot} (was {old_spot})")
                                
                                # Initialize ATM window on first spot price
                                if chain.current_atm_strike is None:
                                    atm_strike = chain.calculate_atm_strike(chain.spot_price)
                                    chain.current_atm_strike = atm_strike
                                    logger.info(f"🔄 ATM initialized for {self.symbol} → {atm_strike}")
                        except Exception as e:
                            logger.error(f"REST fallback failed for {self.symbol}: {e}")
                            # Continue without spot price - still broadcast empty payload for development
                    else:
                        logger.debug(f"🔍 [SPOT EXISTS] {self.symbol}: spot_price={chain.spot_price} - skipping REST fallback")
                    
                    # Check for ATM rebalancing (if we have spot price)
                    if chain.spot_price and chain.current_atm_strike:
                        new_atm_strike = chain.calculate_atm_strike(chain.spot_price)
                        if chain.should_rebalance_window(new_atm_strike):
                            logger.info(f"ATM shifted for {self.symbol}: {chain.current_atm_strike} -> {new_atm_strike}")
                            await self._rebalance_strike_window(new_atm_strike)
                    
                    # Compute PCR once per batch
                    chain.pcr = self._calculate_pcr(chain)
                    
                    # Build payload once per batch (works even with live OI = 0)
                    payload = self._build_payload(chain)
                    
                    # Broadcast once per batch (even when market is CLOSED)
                    await self._broadcast(payload)
                    logger.info(f"📡 BATCH BROADCAST: {self.symbol} | Calls: {len(payload.get('calls', []))} | Puts: {len(payload.get('puts', []))}")
                    
                except Exception as e:
                    logger.error(f"Error in batch compute for {self.symbol}: {e}")
                    
        except asyncio.CancelledError:
            logger.debug(f"Loop cancelled for {self.symbol}:{self.expiry}")
            raise
        finally:
            logger.info(f"Batch compute loop ended for {self.symbol}:{self.expiry}")
    
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
                "symbol": chain.symbol,  # Use original symbol for WS payload
                "expiry": chain.expiry.isoformat() if chain.expiry else None,
                "spot": chain.spot_price,  # 🔥 FIX: Use 'spot' instead of 'spot_price'
                "atm_strike": chain.current_atm_strike,
                "pcr": chain.pcr,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "calls": [],
                "puts": []
            }
            
            logger.info(f"🔍 [PAYLOAD SPOT] {self.symbol}: spot={chain.spot_price}, atm_strike={chain.current_atm_strike}")

            # 🚨 ATM WINDOW NOT READY? → USE STRIKE_MAP FALLBACK
            if not chain.subscribed_strikes:

                logger.warning("⚠️ ATM window empty → using fallback strikes")

                all_strikes = sorted(chain.strike_map.keys())

                if chain.current_atm_strike:
                    window = [
                        s for s in all_strikes
                        if abs(s - chain.current_atm_strike) <= (10 * chain.strike_step)
                    ]
                else:
                    # absolute fallback
                    mid = len(all_strikes) // 2
                    window = all_strikes[mid-10:mid+10]

            else:
                window = list(chain.subscribed_strikes)

            for strike in window:

                pair = chain.strike_map.get(strike)

                if not isinstance(pair, dict):
                    continue

                ce_key = pair.get("CE")
                pe_key = pair.get("PE")

                strike_data = chain.live_chain.get(strike)

                ce_data = strike_data.ce if strike_data else {}
                pe_data = strike_data.pe if strike_data else {}

                if ce_key:
                    payload["calls"].append({
                        "strike": strike,
                        "instrument_key": ce_key,
                        "ltp": ce_data.get("ltp", 0),
                        "oi": ce_data.get("oi", 0),
                        "volume": ce_data.get("volume", 0)
                    })

                if pe_key:
                    payload["puts"].append({
                        "strike": strike,
                        "instrument_key": pe_key,
                        "ltp": pe_data.get("ltp", 0),
                        "oi": pe_data.get("oi", 0),
                        "volume": pe_data.get("volume", 0)
                    })

            payload["calls"].sort(key=lambda x: x["strike"])
            payload["puts"].sort(key=lambda x: x["strike"])

            return payload

        except Exception as e:
            logger.error(f"Error building payload: {e}")
            return {
                "symbol": chain.symbol,
                "spot": chain.spot_price,  # 🔥 FIX: Use 'spot' instead of 'spot_price'
                "atm_strike": chain.current_atm_strike,
                "pcr": 0.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "calls": [],
                "puts": []
            }
        
    async def _broadcast(self, payload: Dict[str, Any]) -> None:
        try:
            # 🔥 FORWARD RAW PAYLOAD DIRECTLY (no market_data wrapper)
            # This ensures calls[] and puts[] reach frontend as expected
            await manager.broadcast_json(self.key, payload)

            print(f"📡 WS BROADCAST SENT for {self.symbol}")

        except Exception as e:
            logger.error(f"Broadcast failed for {self.symbol}: {e}")

# Global instance
_builder_instances: Dict[str, LiveOptionChainBuilder] = {}

def get_live_chain_builder(symbol: str, expiry: date) -> LiveOptionChainBuilder:
    key = f"{symbol}:{expiry}"
    if key not in _builder_instances:
        _builder_instances[key] = LiveOptionChainBuilder(symbol, expiry)
    return _builder_instances[key]


