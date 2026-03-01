import logging
import time
from typing import List, Dict
from app.proto import MarketDataFeed_pb2


logger = logging.getLogger(__name__)


def parse_upstox_feed(message: bytes) -> List[Dict]:

    ticks: List[Dict] = []

    # Log raw message details
    logger.info(f"📦 Received raw protobuf message: {len(message)} bytes")

    try:

        feed_response = MarketDataFeed_pb2.FeedResponse()
        feed_response.ParseFromString(message)

        logger.info(f"🔍 Parsed FeedResponse - feeds count: {len(feed_response.feeds)}")

        if not feed_response.feeds:
            logger.warning("⚠️ No feeds in FeedResponse -可能心跳包")
            # Log the raw structure for debugging
            logger.debug(f"FeedResponse structure: {feed_response}")
            return ticks

        for instrument_key, feed in feed_response.feeds.items():

            logger.debug(f"📊 Processing feed for instrument: {instrument_key}")

            try:

                # Skip if ff missing
                if not hasattr(feed, "ff"):
                    logger.warning(f"❌ Missing 'ff' attribute for {instrument_key}")
                    continue

                ff = feed.ff

                # Only index feed supported here
                if not hasattr(ff, "indexFF"):
                    logger.debug(f"⚠️ No 'indexFF' for {instrument_key} -可能非指数数据")
                    continue

                index_ff = ff.indexFF

                if not hasattr(index_ff, "ltpc"):
                    logger.warning(f"❌ Missing 'ltpc' in indexFF for {instrument_key}")
                    continue

                ltp = index_ff.ltpc.ltp

                if ltp <= 0:
                    logger.warning(f"⚠️ Invalid LTP {ltp} for {instrument_key}")
                    continue

                tick = {
                    "symbol": instrument_key,
                    "ltp": float(ltp),
                    "timestamp": int(time.time() * 1000)
                }

                ticks.append(tick)

                logger.info(f"✅ Parsed tick: {instrument_key} → {ltp}")

            except Exception as inner_error:

                logger.warning(
                    f"❌ Tick parse skipped for {instrument_key} → {inner_error}"
                )
                # Log the feed structure for debugging
                logger.debug(f"Feed structure for {instrument_key}: {feed}")

    except Exception as e:

        logger.error(f"❌ Feed parse error: {e}")
        # Log raw message bytes for debugging (first 100 bytes)
        logger.debug(f"Raw message (first 100 bytes): {message[:100]}")

    logger.info(f"📈 Total ticks parsed: {len(ticks)}")
    return ticks