import asyncio
import json
import logging
from typing import Optional
from datetime import datetime
from collections import deque

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

        self._message_queue = deque(maxlen=2000)

        self._recv_task: Optional[asyncio.Task] = None
        self._process_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None

        self._client = httpx.AsyncClient(timeout=30)

    async def start(self):

        if self.running:
            return

        self.running = True

        # Try to connect, but don't fail if authentication fails
        success = await self.connect()
        
        if not success:
            logger.warning("⚠️ WebSocket connection failed - running in REST-only mode")
            # Continue without WebSocket - AI will still work with REST data
            self.running = True
            self._start_tasks()
            return

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
            logger.info("INDEX SUBSCRIBED")
        except Exception as e:
            logger.error(f"Subscribe failed: {e}")

    async def _heartbeat(self):

        while self.running:

            try:

                if self.websocket and self.is_connected:
                    await self.websocket.ping()

                    await manager.broadcast_json(
                        "market_data",
                        {
                            "type": "heartbeat",
                            "timestamp": int(datetime.now().timestamp() * 1000)
                        }
                    )

            except Exception:
                logger.warning("Heartbeat failed")

            await asyncio.sleep(10)

    async def _recv_loop(self):

        while self.running:

            try:

                message = await self.websocket.recv()

                if isinstance(message, str):
                    message = message.encode()

                try:
                    self._message_queue.append(message)
                except Exception:
                    logger.warning("WS queue full → dropping tick")

            except Exception as e:

                logger.error(f"Recv error → reconnecting: {e}")

                await self._handle_disconnect()

                break

    async def _process_loop(self):

        while self.running:

            try:

                if self._message_queue:
                    raw = self._message_queue.popleft()
                else:
                    await asyncio.sleep(0.001)
                    continue

                ticks = await asyncio.to_thread(parse_upstox_feed, raw)

                if not ticks:

                    await manager.broadcast_json(
                        "market_data",
                        {
                            "type": "heartbeat",
                            "timestamp": int(datetime.now().timestamp() * 1000)
                        }
                    )

                    continue

                for tick in ticks:

                    instrument_key = tick.get("symbol")
                    ltp = tick.get("ltp")

                    if not instrument_key or ltp is None:
                        continue

                    symbol = resolve_symbol_from_instrument(instrument_key)

                    if not symbol:
                        continue

                    await manager.broadcast_json(
                        "market_data",
                        {
                            "type": "market_tick",
                            "data": tick
                        }
                    )

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

                logger.error(f"Process error: {e}")

    async def _handle_disconnect(self):

        self.is_connected = False

        try:
            if self.websocket:
                await self.websocket.close()
        except Exception:
            pass

        await self._cancel_tasks()

        await asyncio.sleep(5)

        if self.running:

            success = await self.connect()

            if success:
                self._start_tasks()
            else:
                logger.warning("Reconnect failed, will retry in 5 seconds")

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


ws_feed_manager = WebSocketFeedManager()

websocket_market_feed = WebSocketMarketFeed()