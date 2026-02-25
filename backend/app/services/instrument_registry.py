import asyncio
import aiohttp
import gzip
import json
from datetime import datetime

UPSTOX_CDN = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz"


def normalize_expiry(exp):

    if isinstance(exp, int):
        return datetime.utcfromtimestamp(exp/1000).date().isoformat()

    if isinstance(exp, str):
        if "-" in exp:
            return exp
        return datetime.strptime(exp, "%Y%m%d").date().isoformat()

    return None


class InstrumentRegistry:

    def __init__(self):

        self._loaded = asyncio.Event()
        self._lock = asyncio.Lock()

        # OPTIONS
        # {symbol:{expiry:{strike:{CE,PE}}}}
        self.options = {}

        # FUTURES
        # {symbol:{expiry:instrument_key}}
        self.futidx = {}

    async def load(self):

        if self._loaded.is_set():
            return

        async with self._lock:

            if self._loaded.is_set():
                return

            async with aiohttp.ClientSession() as s:
                async with s.get(UPSTOX_CDN) as r:
                    gz = await r.read()

            raw = gzip.decompress(gz)
            data = json.loads(raw)

            if isinstance(data, dict) and "data" in data:
                data = data["data"]

            for inst in data:

                # only FO segment
                if inst.get("segment") != "NSE_FO":
                    continue

                name = inst.get("name")
                itype = inst.get("instrument_type")

                # only index instruments
                if name not in ("NIFTY", "BANKNIFTY"):
                    continue

                expiry = normalize_expiry(inst.get("expiry"))

                if not expiry:
                    continue

                # ============================
                # OPTIONS (CE / PE)
                # ============================

                if itype in ("CE", "PE"):

                    strike = int(inst["strike_price"])

                    self.options \
                        .setdefault(name, {}) \
                        .setdefault(expiry, {}) \
                        .setdefault(strike, {})[itype] = inst["instrument_key"]

                # ============================
                # FUTURES  ✅ FIX HERE
                # ============================

                elif itype == "FUT":

                    self.futidx \
                        .setdefault(name, {})[expiry] = inst["instrument_key"]

            print("📦 Runtime instruments loaded from Upstox CDN")
            print(f"🟢 FUTIDX Loaded: {list(self.futidx.keys())}")

            self._loaded.set()

    async def wait_until_ready(self):
        await self._loaded.wait()