from app.services.live_option_chain_builder import get_live_chain_builder
import logging

logger = logging.getLogger(__name__)

async def get_latest_option_chain(symbol: str, db=None):
    """
    Get latest option chain using factory function
    """
    try:
        # Use factory function to get builder instance
        builder = get_live_chain_builder(symbol)
        
        # Get the latest option chain state
        state = builder.get_latest_option_chain(symbol)
        
        if state:
            # Sync from global feed to ensure LTP is fresh before returning
            await builder.build_chain_payload(symbol)
            return state.build_final_chain()
            
        return {
            "symbol": symbol,
            "error": "Chain not initialized",
            "calls": [],
            "puts": []
        }
    except Exception as e:
        logger.error(f"Error in get_latest_option_chain for {symbol}: {e}")
        return {"error": str(e), "calls": [], "puts": []}
