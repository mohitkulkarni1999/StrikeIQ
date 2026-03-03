import logging
import time
from typing import List, Dict, Optional
from app.proto import MarketDataFeed_pb2

logger = logging.getLogger(__name__)


def extract_index_price(decoded: Dict) -> Optional[float]:
    """Extract index price from decoded protobuf message"""
    try:
        feeds = decoded.get("feeds", {})
        for key, value in feeds.items():
            if "indexFF" in value:
                index_data = value["indexFF"]
                if "ltpc" in index_data:
                    return index_data["ltpc"]["ltp"]
    except Exception as e:
        print("INDEX PARSE ERROR:", e)
    return None


def parse_upstox_feed(data_bytes: bytes) -> List[Dict]:

    logger.info("PROTOBUF DECODE START")

    response = MarketDataFeed_pb2.FeedResponse()

    try:
        response.ParseFromString(data_bytes)
    except Exception as e:
        logger.error("PROTOBUF PARSE ERROR: %s", str(e))
        return []

    ticks: List[Dict] = []

    # Debug message type
    logger.info(
        "PROTOBUF MESSAGE TYPE=%s | FEEDS=%s",
        getattr(response, "type", "unknown"),
        len(response.feeds)
    )

    # Heartbeat / empty packets
    if len(response.feeds) == 0:
        logger.warning("PROTOBUF EMPTY MESSAGE (heartbeat or market closed)")
        return []

    logger.info("PROTOBUF FEEDS FOUND: %s", len(response.feeds))

    for instrument_key, feed in response.feeds.items():

        try:

            if not feed.HasField("ff"):
                continue

            ff = feed.ff

            ltp = None

            # INDEX
            if ff.HasField("indexFF"):

                index_ff = ff.indexFF

                if index_ff.HasField("ltpc"):

                    ltpc = index_ff.ltpc
                    ltp = ltpc.ltp

                    logger.info(
                        "INDEX TICK | %s | LTP=%s",
                        instrument_key,
                        ltp
                    )

            # EQUITY / DERIVATIVES
            elif ff.HasField("marketFF"):

                market_ff = ff.marketFF

                if market_ff.HasField("ltpc"):

                    ltpc = market_ff.ltpc
                    ltp = ltpc.ltp

                    logger.info(
                        "MARKET TICK | %s | LTP=%s",
                        instrument_key,
                        ltp
                    )

            if ltp is None:
                continue

            ticks.append({
                "instrument_key": instrument_key,
                "symbol": instrument_key.split("|")[-1],
                "ltp": ltp,
                "timestamp": int(time.time() * 1000)
            })

        except Exception as e:

            logger.error(
                "PROTOBUF PARSE ERROR | %s | %s",
                instrument_key,
                str(e)
            )

    logger.info("PROTOBUF DECODE SUCCESS: %s ticks", len(ticks))

    return ticks


def extract_index_price(feed) -> float | None:
    """
    Extract index LTP from Upstox protobuf feed.
    """

    try:

        # Upstox index feed format
        if hasattr(feed, "ltpc") and feed.ltpc:

            if hasattr(feed.ltpc, "ltp"):

                return float(feed.ltpc.ltp)

    except Exception as e:

        print("INDEX PARSE ERROR:", e)

    return None