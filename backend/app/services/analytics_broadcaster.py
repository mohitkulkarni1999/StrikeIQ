"""
Analytics Broadcaster for StrikeIQ
Wraps existing analytics engines and broadcasts results
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class AnalyticsBroadcaster:
    """Broadcasts analytics from existing engines"""
    
    def __init__(self):
        # Background task for periodic analytics
        self._analytics_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Cache for last analytics results
        self.analytics_cache: Dict[str, Dict[str, Any]] = {}
        
        # Update interval (3 seconds)
        self.update_interval = 3.0
        
        # Initialize engines (lazy loading)
        self._bias_engine = None
        self._expected_move_engine = None
        self._structural_engine = None
    
    def _get_bias_engine(self):
        """Lazy load market bias engine"""
        if self._bias_engine is None:
            try:
                from app.services.market_bias_engine import MarketBiasEngine
                self._bias_engine = MarketBiasEngine()
            except ImportError as e:
                logger.error(f"Could not import MarketBiasEngine: {e}")
        return self._bias_engine
    
    def _get_expected_move_engine(self):
        """Lazy load expected move engine"""
        if self._expected_move_engine is None:
            try:
                from app.services.expected_move_engine import ExpectedMoveEngine
                self._expected_move_engine = ExpectedMoveEngine()
            except ImportError as e:
                logger.error(f"Could not import ExpectedMoveEngine: {e}")
        return self._expected_move_engine
    
    def _get_structural_engine(self):
        """Lazy load structural engine"""
        if self._structural_engine is None:
            try:
                from app.services.live_structural_engine import LiveStructuralEngine
                from app.core.live_market_state import get_market_state_manager
                market_state_mgr = get_market_state_manager()
                self._structural_engine = LiveStructuralEngine(market_state_mgr)
            except ImportError as e:
                logger.error(f"Could not import LiveStructuralEngine: {e}")
        return self._structural_engine
    
    async def start(self):
        """Start the background analytics computation task"""
        if self._running:
            return
        
        self._running = True
        self._analytics_task = asyncio.create_task(self._analytics_loop())
        logger.info("Analytics broadcaster started")
    
    async def stop(self):
        """Stop the background task"""
        self._running = False
        if self._analytics_task:
            self._analytics_task.cancel()
            try:
                await self._analytics_task
            except asyncio.CancelledError:
                pass
        logger.info("Analytics broadcaster stopped")
    
    async def _analytics_loop(self):
        """Periodic analytics computation"""
        while self._running:
            try:
                await asyncio.sleep(self.update_interval)
                await self._compute_and_broadcast_analytics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in analytics loop: {e}")
    
    async def _compute_and_broadcast_analytics(self):
        """Compute analytics for all active symbols"""
        try:
            # Get option chain data for all symbols
            from app.services.option_chain_builder import option_chain_builder
            
            for symbol in ["NIFTY", "BANKNIFTY"]:  # Active symbols
                chain_data = option_chain_builder.get_chain(symbol)
                if chain_data:
                    analytics_data = await self._compute_analytics(symbol, chain_data)
                    if analytics_data:
                        await self._broadcast_analytics(analytics_data)
                        
        except Exception as e:
            logger.error(f"Error computing analytics: {e}")
    
    async def _compute_analytics(self, symbol: str, chain_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Compute analytics from option chain data"""
        try:
            # Prepare data for engines
            engine_data = {
                "symbol": symbol,
                "spot": chain_data["spot"],
                "calls": [],
                "puts": []
            }
            
            # Convert strikes to engine format
            for strike in chain_data["strikes"]:
                if strike["call_ltp"] > 0:
                    engine_data["calls"].append({
                        "strike": strike["strike"],
                        "ltp": strike["call_ltp"],
                        "oi": strike["call_oi"],
                        "volume": strike["call_volume"]
                    })
                
                if strike["put_ltp"] > 0:
                    engine_data["puts"].append({
                        "strike": strike["strike"],
                        "ltp": strike["put_ltp"],
                        "oi": strike["put_oi"],
                        "volume": strike["put_volume"]
                    })
            
            # Compute analytics using existing engines
            analytics_results = {}
            
            # Market bias
            bias_engine = self._get_bias_engine()
            if bias_engine and engine_data["calls"] and engine_data["puts"]:
                try:
                    bias_result = bias_engine.compute(engine_data)
                    analytics_results["market_bias"] = {
                        "pcr": bias_result.pcr,
                        "bias_strength": bias_result.bias_strength,
                        "divergence_detected": bias_result.divergence_detected,
                        "divergence_type": bias_result.divergence_type,
                        "price_vs_vwap": bias_result.price_vs_vwap
                    }
                except Exception as e:
                    logger.error(f"Error computing market bias: {e}")
            
            # Expected move
            move_engine = self._get_expected_move_engine()
            if move_engine and engine_data["calls"] and engine_data["puts"]:
                try:
                    move_result = move_engine.compute(engine_data)
                    analytics_results["expected_move"] = {
                        "move_1sd": move_result.expected_move_1sd,
                        "move_2sd": move_result.expected_move_2sd,
                        "breakout_detected": move_result.breakout_detected,
                        "breakout_direction": move_result.breakout_direction,
                        "implied_volatility": move_result.implied_volatility
                    }
                except Exception as e:
                    logger.error(f"Error computing expected move: {e}")
            
            # Structural analytics (if available)
            structural_engine = self._get_structural_engine()
            if structural_engine:
                try:
                    # This would need to be adapted based on the actual structural engine interface
                    # For now, add placeholder data
                    analytics_results["structural"] = {
                        "gamma_regime": "neutral",
                        "intent_score": 50.0,
                        "support_level": chain_data["spot"] * 0.98,
                        "resistance_level": chain_data["spot"] * 1.02
                    }
                except Exception as e:
                    logger.error(f"Error computing structural analytics: {e}")
            
            # Create analytics message
            analytics_data = {
                "type": "analytics_update",
                "symbol": symbol,
                "timestamp": int(datetime.now().timestamp()),
                "data": analytics_results
            }
            
            # Cache the result
            self.analytics_cache[symbol] = analytics_data
            
            return analytics_data
            
        except Exception as e:
            logger.error(f"Error computing analytics for {symbol}: {e}")
            return None
    
    async def _broadcast_analytics(self, analytics_data: Dict[str, Any]):
        """Broadcast analytics to WebSocket clients"""
        try:
            from app.core.ws_manager import manager
            
            await manager.broadcast(analytics_data)
            logger.debug(f"Broadcasted analytics for {analytics_data['symbol']}")
            
        except Exception as e:
            logger.error(f"Error broadcasting analytics: {e}")
    
    def get_cached_analytics(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached analytics data for a symbol"""
        return self.analytics_cache.get(symbol)
    
    async def compute_single_analytics(self, symbol: str, chain_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Compute analytics on-demand for a single symbol"""
        return await self._compute_analytics(symbol, chain_data)
    
    def _calculate_pcr_simple(self, calls: List[Dict], puts: List[Dict]) -> float:
        """Simple PCR calculation as fallback"""
        try:
            total_call_oi = sum(call.get("oi", 0) for call in calls)
            total_put_oi = sum(put.get("oi", 0) for put in puts)
            
            return total_put_oi / total_call_oi if total_call_oi > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating PCR: {e}")
            return 0.0
    
    def _find_atm_strike_simple(self, spot: float, strikes: List[Dict]) -> Optional[float]:
        """Find ATM strike as fallback"""
        try:
            if not strikes:
                return None
            
            # Combine calls and puts
            all_strikes = set()
            for strike_data in strikes:
                all_strikes.add(strike_data["strike"])
            
            if not all_strikes:
                return None
            
            # Find closest strike to spot
            atm_strike = min(all_strikes, key=lambda s: abs(s - spot))
            return atm_strike
            
        except Exception as e:
            logger.error(f"Error finding ATM strike: {e}")
            return None

# Global instance
analytics_broadcaster = AnalyticsBroadcaster()
