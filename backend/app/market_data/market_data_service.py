from app.services.live_option_chain_builder import get_live_chain_builder
from app.services.instrument_registry import get_instrument_registry
import logging

logger = logging.getLogger(__name__)

async def get_latest_option_chain(symbol: str, db=None):
    """
    Get latest option chain using factory function
    """
    try:
        instrument_registry = get_instrument_registry()
        expiries = instrument_registry.get_expiries(symbol)
        
        if not expiries:
            logger.debug(f"No expiries found for {symbol}")
            return {"expiries": []}
            
        expiry = expiries[0]
        builder = get_live_chain_builder(symbol, expiry)
        
        if hasattr(builder, "build"):
            chain = builder.build(symbol)
        else:
            chain = {
                "symbol": symbol,
                "chain": []
            }
        
        return chain
    except Exception as e:
        logger.debug(f"Error in get_latest_option_chain for {symbol}: {e}")
        return {"error": str(e), "calls": [], "puts": []}
