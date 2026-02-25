import asyncio
import json
import logging
from typing import Optional

import httpx
import websockets

from app.services.upstox_auth_service import get_upstox_auth_service
from app.services.market_session_manager import get_market_session_manager
from app.services.upstox_protobuf_parser import parse_upstox_feed
from app.services.token_manager import token_manager
from app.core.live_market_state import MarketStateManager

logger = logging.getLogger(__name__)


class WebSocketMarketFeed:

    def __init__(self):
        self.auth_service = get_upstox_auth_service()
        self.session_manager = get_market_session_manager()
        self.market_state_manager = MarketStateManager()

        self.websocket = None
        self.is_connected = False
        self.running = False
        self._connecting = False

        self._message_queue = asyncio.Queue(maxsize=500)
        self._recv_task: Optional[asyncio.Task] = None
        self._process_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None


    async def start(self):
        if self.running:
            return

        self.running = True
        success = await self.connect()

        if not success:
            self.running = False
            raise RuntimeError("Shared WS connect failed")

        self._recv_task = asyncio.create_task(self._recv_loop())
        self._process_task = asyncio.create_task(self._process_loop())
        self._heartbeat_task = asyncio.create_task(self._heartbeat())

        logger.info("Shared Upstox WS started")


    async def connect(self) -> bool:

        if self.is_connected:
            return True

        if self._connecting:
            return False

        self._connecting = True

        try:

            if not token_manager.has_valid_token():
                await token_manager.refresh_access_token()

            response = await self.authorize_feed()

            if response.status_code != 200:
                logger.error(f"WS authorize failed: {response.status_code}")
                return False

            ws_url = response.json().get("data", {}).get("authorizedRedirectUri")

            if not ws_url:
                logger.error("No WS URL received")
                return False

            self.websocket = await websockets.connect(
                ws_url,
                subprotocols=["json"],
                ping_interval=None,
                ping_timeout=None,
                close_timeout=5,
                max_queue=None
            )

            self.is_connected = True
            print("🟢 WS CONNECTED TO UPSTOX SUCCESSFULLY")

            await self.subscribe_indices()

            return True

        except Exception as e:
            print("🔴 WS CONNECTION FAILED:", str(e))
            logger.error(f"WS connect failed: {e}")
            return False

        finally:
            self._connecting = False


    async def authorize_feed(self):

        access_token = await self.auth_service.get_valid_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }

        async with httpx.AsyncClient() as client:
            return await client.get(
                "https://api.upstox.com/v3/feed/market-data-feed/authorize",
                headers=headers
            )


    async def subscribe_indices(self):

        subscribe_payload = {
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

        await self.websocket.send(json.dumps(subscribe_payload))
        print("📡 SUBSCRIBED TO NIFTY & BANKNIFTY")


    async def _heartbeat(self):
        while self.running:
            try:
                if self.websocket:
                    await self.websocket.ping()
                    print("💓 Ping sent to Upstox")
            except Exception as e:
                print("🔴 Heartbeat failed:", e)
            await asyncio.sleep(10)


    async def _recv_loop(self):

        while self.running:
            try:
                message = await self.websocket.recv()

                if not self._message_queue.full():
                    await self._message_queue.put(message)

            except Exception as e:
                logger.error(f"Recv error: {e}")
                await asyncio.sleep(1)


    async def _process_loop(self):

        while self.running:
            try:
                raw = await self._message_queue.get()
                parsed = await asyncio.to_thread(parse_upstox_feed, raw)

                feeds = getattr(parsed, "feeds", None)
                if not feeds:
                    continue

                iterable = feeds.items() if isinstance(feeds, dict) else []

                for instrument_key, feed in iterable:

                    if not hasattr(feed, "ltpc"):
                        continue

                    ltp = getattr(feed.ltpc, "ltp", None)
                    if ltp is None:
                        continue

                    if "Nifty 50" in instrument_key:
                        self.market_state_manager.update_ltp("NIFTY", ltp)
                        ws_feed_manager.market_state["NIFTY"] = ltp
                        ws_feed_manager.market_states.update_ltp("NIFTY", ltp)

                    elif "Nifty Bank" in instrument_key:
                        self.market_state_manager.update_ltp("BANKNIFTY", ltp)
                        ws_feed_manager.market_state["BANKNIFTY"] = ltp
                        ws_feed_manager.market_states.update_ltp("BANKNIFTY", ltp)

            except Exception as e:
                logger.error(f"Process error: {e}")


    async def disconnect(self):
        self.running = False
        self.is_connected = False

        if self._recv_task:
            self._recv_task.cancel()

        if self._process_task:
            self._process_task.cancel()

        if self._heartbeat_task:
            self._heartbeat_task.cancel()

        if self.websocket:
            await self.websocket.close()


class WebSocketFeedManager:

    def __init__(self):

        self.feed: Optional[WebSocketMarketFeed] = None
        self._lock = asyncio.Lock()

        # AI Engine ke liye
        self.market_state = {
            "NIFTY": None,
            "BANKNIFTY": None
        }

        # Structural Engine ke liye
        self.market_states = MarketStateManager()


    async def start_feed(self):

        async with self._lock:

            if self.feed and self.feed.running:
                print("🟢 WS FEED ALREADY RUNNING")
                return self.feed

            print("🚀 STARTING SHARED WS FEED...")

            self.feed = WebSocketMarketFeed()

            try:
                await self.feed.start()
                print("🟢 WS FEED STARTED SUCCESSFULLY")
                return self.feed
            except Exception as e:
                print("🔴 WS START FAILED:", str(e))
                self.feed = None
                return None


    async def get_feed(self):

        async with self._lock:

            if self.feed and self.feed.is_connected:
                return self.feed

            return None


    async def cleanup_all(self):

        async with self._lock:

            if self.feed:
                await self.feed.disconnect()
                self.feed = None


ws_feed_manager = WebSocketFeedManager()