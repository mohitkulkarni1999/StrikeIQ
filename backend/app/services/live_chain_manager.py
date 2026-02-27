import asyncio
from datetime import datetime, date
from app.services.live_option_chain_builder import LiveOptionChainBuilder


class LiveChainManager:

    def __init__(self):
        self.builders = {}
        self.lock = asyncio.Lock()

    async def get_builder(self, symbol: str, expiry):

        # 🔥 NORMALIZE EXPIRY
        if isinstance(expiry, str):
            expiry = datetime.strptime(expiry, "%Y-%m-%d").date()

        if isinstance(expiry, datetime):
            expiry = expiry.date()

        key = f"{symbol}:{expiry.isoformat()}"

        async with self.lock:

            if key in self.builders:
                print(f"♻️ REUSING Builder → {key}")
                return self.builders[key]

            print(f"🔨 CREATING Builder → {key}")

            builder = LiveOptionChainBuilder(
                symbol=symbol,
                expiry=expiry
            )

            self.builders[key] = builder

            return builder


chain_manager = LiveChainManager()