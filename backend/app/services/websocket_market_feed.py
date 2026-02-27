import asyncio
import json
import logging
from typing import Optional
from datetime import datetime

import httpx
import websockets
from fastapi import HTTPException

from app.services.token_manager import token_manager
from app.services.market_session_manager import get_market_session_manager
from app.services.upstox_protobuf_parser import parse_upstox_feed
from app.core.live_market_state import MarketStateManager
from app.services.live_chain_manager import chain_manager
from app.core.ws_manager import manager

logger = logging.getLogger(__name__)


def resolve_symbol_from_instrument(instrument_key: str):
    if not instrument_key:
        return None

    if instrument_key == "NSE_INDEX|Nifty 50":
        return "NIFTY"

    if instrument_key == "NSE_INDEX|Nifty Bank":
        return "BANKNIFTY"

    if "BANKNIFTY" in instrument_key:
        return "BANKNIFTY"

    if "FINNIFTY" in instrument_key:
        return "FINNIFTY"

    if "MIDCPNIFTY" in instrument_key:
        return "MIDCPNIFTY"

    if "NIFTY" in instrument_key:
        return "NIFTY"

    return None


class WebSocketMarketFeed:

    def __init__(self):

        self.session_manager = get_market_session_manager()
        self.market_state_manager = MarketStateManager()

        self.websocket = None
        self.is_connected = False
        self.running = False
        self._connecting = False

        self._message_queue = asyncio.Queue(maxsize=2000)

        self._recv_task: Optional[asyncio.Task] = None
        self._process_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None

        self._client = httpx.AsyncClient(timeout=10)

    # ================= START =================

    async def start(self):

        if self.running:
            return

        self.running = True

        success = await self.connect()

        if not success:
            self.running = False
            raise RuntimeError("Shared WS connect failed")

        self._start_tasks()

        logger.info("Shared Upstox WS started")

    def _start_tasks(self):

        self._recv_task = asyncio.create_task(self._recv_loop())
        self._process_task = asyncio.create_task(self._process_loop())
        self._heartbeat_task = asyncio.create_task(self._heartbeat())

    async def _cancel_tasks(self):

        tasks = [self._recv_task, self._process_task, self._heartbeat_task]

        for task in tasks:
            if task and not task.done():
                task.cancel()

        await asyncio.gather(*[t for t in tasks if t], return_exceptions=True)

    # ================= CONNECT =================

    async def connect(self) -> bool:

        if self.is_connected:
            return True

        if self._connecting:
            return False

        self._connecting = True

        try:

            token = await token_manager.get_valid_token()

            ws_url = await self._authorize_feed(token)

            if not ws_url:
                logger.error("WS authorize returned empty URL")
                return False

            self.websocket = await websockets.connect(
                ws_url,
                ping_interval=None,
                ping_timeout=None,
                close_timeout=5,
                max_queue=None
            )

            self.is_connected = True

            logger.info("WS CONNECTED TO UPSTOX")

            await self.subscribe_indices()

            return True

        except HTTPException as e:

            if e.status_code == 401:
                token_manager.invalidate_permanently("WebSocket auth failed")

            return False

        except Exception as e:

            logger.error(f"WS connect failed: {e}")
            return False

        finally:

            self._connecting = False

    # ================= AUTHORIZE =================

    async def _authorize_feed(self, token: str) -> Optional[str]:

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        try:

            response = await self._client.get(
                "https://api.upstox.com/v3/feed/market-data-feed/authorize",
                headers=headers
            )

            if response.status_code != 200:
                logger.error(f"WS authorize failed: {response.status_code}")
                return None

            return response.json().get("data", {}).get("authorizedRedirectUri")

        except Exception as e:

            logger.error(f"Authorize request failed: {e}")
            return None

    # ================= SUBSCRIBE =================

    async def subscribe_indices(self):

        if not self.websocket:
            return

        payload = {
            "guid": "index-feed",
            "method": "sub",
            "data": {
                "mode": "full",
                "instrumentKeys": [
                    "NSE_INDEX|Nifty 50",
                    "NSE_INDEX|Nifty Bank"
                ]
            }
        }

        try:
            await self.websocket.send(json.dumps(payload))
            logger.info(f"✅ INDEX SUBSCRIBED: {payload}")
        except Exception as e:
            logger.error(f"❌ Subscribe failed: {e}")

    # ================= HEARTBEAT =================

    async def _heartbeat(self):

        while self.running:

            try:
                if self.websocket and self.is_connected:
                    await self.websocket.ping()
            except Exception:
                logger.warning("Heartbeat ping failed")

            await asyncio.sleep(10)

    # ================= RECEIVE =================

    async def _recv_loop(self):

        while self.running:

            try:

                if not self.websocket:
                    await asyncio.sleep(1)
                    continue

                message = await self.websocket.recv()

                logger.info(f"📨 Received message from Upstox WS: {len(message)} bytes")

                if isinstance(message, str):
                    logger.info(f"📝 Received text message: {message}")
                    message = message.encode()

                try:
                    self._message_queue.put_nowait(message)
                    logger.debug(f"📤 Message queued successfully")

                except asyncio.QueueFull:
                    logger.warning("⚠️ WS queue full → dropping tick")

            except Exception as e:

                logger.error(f"❌ Recv error → reconnecting: {e}")

                await self._handle_disconnect()

                break

    # ================= PROCESS =================

    async def _process_loop(self):

        while self.running:

            try:

                raw = await self._message_queue.get()

                logger.info(f"🔄 Processing message from queue: {len(raw)} bytes")

                ticks = await asyncio.to_thread(parse_upstox_feed, raw)

                logger.info(f"📊 Parsed {len(ticks)} ticks from protobuf")

                if not ticks:
                    logger.debug("⚠️ No ticks to broadcast")
                    continue

                for tick in ticks:

                    instrument_key = tick.get("symbol")
                    ltp = tick.get("ltp")

                    if not instrument_key or ltp is None:
                        logger.warning(f"⚠️ Invalid tick data: {tick}")
                        continue

                    symbol = resolve_symbol_from_instrument(instrument_key)

                    if not symbol:
                        logger.warning(f"⚠️ Could not resolve symbol for: {instrument_key}")
                        continue

                    logger.info(f"🎯 Broadcasting tick: {symbol} @ {ltp}")

                    # 🔥 Broadcast to frontend
                    try:

                        await manager.broadcast_json(
                            "market_data",
                            {
                                "type": "market_tick",
                                "data": tick
                            }
                        )

                        logger.info(f"✅ Successfully broadcasted tick for {symbol}")

                    except Exception as e:
                        logger.warning(f"❌ Broadcast skipped: {e}")

                    tick_data = {
                        "instrument_key": instrument_key,
                        "ltp": ltp,
                        "timestamp": tick.get(
                            "timestamp",
                            int(datetime.now().timestamp() * 1000)
                        )
                    }

                    await self._route_tick_to_builders(symbol, instrument_key, tick_data)

            except Exception as e:

                logger.error(f"❌ Process error: {e}")

    # ================= RECONNECT =================

    async def _handle_disconnect(self):

        self.is_connected = False

        try:
            if self.websocket:
                await self.websocket.close()
        except Exception:
            pass

        await self._cancel_tasks()

        await asyncio.sleep(3)

        if self.running:

            success = await self.connect()

            if success:
                self._start_tasks()

    async def disconnect(self):

        self.running = False
        self.is_connected = False

        await self._cancel_tasks()

        try:
            if self.websocket:
                await self.websocket.close()
        except Exception:
            pass

        await self._client.aclose()

    # ================= ROUTE =================

    async def _route_tick_to_builders(self, symbol, instrument_key, tick_data):

        active_keys = [
            key for key in manager.active_connections.keys()
            if key.startswith(f"{symbol}:")
        ]

        for key in active_keys:

            try:

                _, expiry_str = key.split(":")

                expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()

                builder = await chain_manager.get_builder(symbol, expiry_date)

                if builder:

                    asyncio.create_task(
                        builder.handle_tick(symbol, instrument_key, tick_data)
                    )

            except Exception as e:

                logger.error(f"Tick routing failed for {key}: {e}")


# ================= FEED MANAGER =================


class WebSocketFeedManager:

    def __init__(self):

        self.feed: Optional[WebSocketMarketFeed] = None
        self._lock = asyncio.Lock()

        self.market_states = {}

    @property
    def is_connected(self) -> bool:
        return self.feed is not None and self.feed.is_connected

    async def start_feed(self):

        async with self._lock:

            if self.feed and self.feed.running:
                return self.feed

            self.feed = WebSocketMarketFeed()

            await self.feed.start()

            return self.feed

    async def get_feed(self):

        async with self._lock:

            if self.feed and self.feed.running:
                return self.feed

            return None

    async def cleanup_all(self):

        async with self._lock:

            if self.feed:
                await self.feed.disconnect()
                self.feed = None


# REQUIRED EXPORTS
ws_feed_manager = WebSocketFeedManager()

# backward compatibility instance
websocket_market_feed = WebSocketMarketFeed()