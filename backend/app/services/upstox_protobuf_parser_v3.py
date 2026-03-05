from app.proto.MarketDataFeedV3_pb2 import FeedResponse
import logging

logger = logging.getLogger(__name__)

def decode_protobuf_message_v3(message: bytes):

    decoded = FeedResponse()
    decoded.ParseFromString(message)

    feeds = decoded.feeds

    logger.info(f"FEEDS COUNT = {len(feeds)}")

    ticks = []

    for entry in feeds:

        instrument_key = entry.key
        feed = entry.value

        if feed.HasField("ltpc"):

            ltp = feed.ltpc.ltp

            logger.info(f"TICK → {instrument_key}")
            logger.info(f"LTP → {ltp}")

            ticks.append({
                "instrument": instrument_key,
                "ltp": float(ltp)
            })

    return ticks


def decode_protobuf_message(message: bytes):
    """
    Decode Upstox V3 Market Data Feed protobuf messages.
    FeedResponse -> feeds (list of FeedsEntry) -> Feed -> ltpc -> ltp
    """
    
    ticks = []
    
    try:
        # STEP 1: ENSURE CORRECT IMPORT
        from app.proto.MarketDataFeedV3_pb2 import FeedResponse
        
        response = FeedResponse()
        response.ParseFromString(message)

        feeds = response.feeds

        logger.info(f"FEEDS COUNT = {len(feeds)}")

        # STEP 3: REPLACE WITH CORRECT ITERATION
        for entry in feeds:
            instrument_key = entry.key
            feed = entry.value

            if feed.HasField("ltpc"):
                ltp = feed.ltpc.ltp

                tick = {
                    "instrument_key": instrument_key,
                    "ltp": ltp
                }

                ticks.append(tick)

                logger.info(f"TICK → {instrument_key}")
                logger.info(f"LTP → {ltp}")

        return ticks

    except Exception as e:
        logger.error(f"PROTOBUF DECODE ERROR: {e}")
        return []


def extract_index_price(feed):

    try:

        if hasattr(feed, "ltpc") and feed.ltpc:
            return float(feed.ltpc.ltp)

        if hasattr(feed, "ff") and feed.ff and hasattr(feed.ff, "indexFF") and feed.ff.indexFF:
            index = feed.ff.indexFF
            if hasattr(index, "ltpc") and index.ltpc:
                return float(index.ltpc.ltp)

    except Exception:
        pass

    return None
