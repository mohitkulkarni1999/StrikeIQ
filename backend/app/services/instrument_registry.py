from __future__ import annotations

import asyncio
import aiohttp
import gzip
import json
from datetime import datetime, date
from typing import Optional, Dict

from app.core.redis_client import redis_client

UPSTOX_CDN = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz"


def normalize_expiry(exp) -> Optional[str]:
    if isinstance(exp, int):
        return datetime.utcfromtimestamp(exp / 1000).date().isoformat()

    if isinstance(exp, str):
        if "-" in exp:
            return exp
        return datetime.strptime(exp, "%Y%m%d").date().isoformat()

    return None


class InstrumentRegistry:
    """
    Production-safe Instrument Registry.

    ✔ Each worker loads its own in-memory registry
    ✔ Redis used only for distributed locking
    ✔ No fake ready flags
    ✔ Expiry normalization safe for both str & date
    """

    def __init__(self):

        self._ready_event = asyncio.Event()
        self._local_lock = asyncio.Lock()

        # OPTIONS
        # {symbol:{expiry:{strike:{CE,PE}}}}
        self.options: Dict[str, Dict[str, Dict[int, Dict[str, str]]]] = {}

        # FUTURES
        # {symbol:{expiry:instrument_key}}
        self.futidx: Dict[str, Dict[str, str]] = {}

    # --------------------------------------------------
    # PUBLIC LOAD
    # --------------------------------------------------

    async def load(self):

        if self._ready_event.is_set():
            return

        lock = redis_client.lock("instrument_registry_lock", timeout=120)

        async with lock:

            if self._ready_event.is_set():
                return

            print("🔥 Loading Instrument Registry from Upstox CDN...")

            async with self._local_lock:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(UPSTOX_CDN) as response:
                            gz = await response.read()

                    raw = gzip.decompress(gz)
                    data = json.loads(raw)

                    if isinstance(data, dict) and "data" in data:
                        data = data["data"]

                    for inst in data:

                        if inst.get("segment") != "NSE_FO":
                            continue

                        name = inst.get("name")
                        itype = inst.get("instrument_type")

                        # Only index derivatives
                        if name not in ("NIFTY", "BANKNIFTY"):
                            continue

                        expiry = normalize_expiry(inst.get("expiry"))
                        if not expiry:
                            continue

                        # -------------------------
                        # OPTIONS
                        # -------------------------
                        if itype in ("CE", "PE"):

                            strike = int(inst["strike_price"])

                            self.options \
                                .setdefault(name, {}) \
                                .setdefault(expiry, {}) \
                                .setdefault(strike, {})[itype] = inst["instrument_key"]

                        # -------------------------
                        # FUTURES
                        # -------------------------
                        elif itype == "FUT":

                            self.futidx \
                                .setdefault(name, {})[expiry] = inst["instrument_key"]

                    print("🟢 Instrument Registry Loaded Successfully")
                    print(f"Available Symbols: {list(self.options.keys())}")

                    self._ready_event.set()

                except Exception as e:
                    print(f"⚠️ CDN load failed: {e}")
                    print("🔄 Attempting to load from local cache...")
                    
                    # Fallback to local cache
                    try:
                        await self._load_from_local_cache()
                    except Exception as cache_error:
                        print(f" Local cache fallback failed: {cache_error}")
                        raise Exception("Both CDN and local cache failed")

    async def _load_from_local_cache(self):
        """Load instruments from local cache file"""
        import os
        from pathlib import Path
        
        cache_file = Path("data/instruments.json")
        
        if not cache_file.exists():
            raise FileNotFoundError("Local cache file not found")
        
        print(f" Loading from local cache: {cache_file}")
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        
        if isinstance(raw, dict) and "instruments" in raw:
            data = raw["instruments"]
        elif isinstance(raw, list):
            data = raw
        else:
            raise ValueError("Invalid cache format")

        for inst in data:
            if inst.get("segment") != "NSE_FO":
                continue

            name = inst.get("name")
            itype = inst.get("instrument_type")

            # Only index derivatives
            if name not in ("NIFTY", "BANKNIFTY"):
                continue

            expiry = normalize_expiry(inst.get("expiry"))
            if not expiry:
                continue

            # -------------------------
            # OPTIONS
            # -------------------------
            if itype in ("CE", "PE"):
                strike = int(inst["strike_price"])

                self.options \
                    .setdefault(name, {}) \
                    .setdefault(expiry, {}) \
                    .setdefault(strike, {})[itype] = inst["instrument_key"]

            # -------------------------
            # FUTURES
            # -------------------------
            elif itype == "FUT":
                self.futidx \
                    .setdefault(name, {})[expiry] = inst["instrument_key"]

        print(" Instrument Registry Loaded from Local Cache")
        print(f"Available Symbols: {list(self.options.keys())}")
        
        self._ready_event.set()

    # --------------------------------------------------
    # WAIT FOR READY
    # --------------------------------------------------

    async def wait_until_ready(self):
        await self._ready_event.wait()

    # --------------------------------------------------
    # SAFE ACCESSORS (FIXED)
    # --------------------------------------------------

    def get_options(self, symbol: str, expiry):
        # 🔥 Normalize expiry to string
        if isinstance(expiry, date):
            expiry = expiry.isoformat()
        return self.options.get(symbol, {}).get(expiry)

    def get_future(self, symbol: str, expiry):
        # 🔥 Normalize expiry to string
        if isinstance(expiry, date):
            expiry = expiry.isoformat()
        return self.futidx.get(symbol, {}).get(expiry)


# --------------------------------------------------
# SINGLETON
# --------------------------------------------------

_registry_instance: InstrumentRegistry | None = None


def get_instrument_registry() -> InstrumentRegistry:
    global _registry_instance

    if _registry_instance is None:
        _registry_instance = InstrumentRegistry()

    return _registry_instance