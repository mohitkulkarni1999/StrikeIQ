"""
Live Analytics Engine for real-time options data processing.
Reuses existing calculation logic with live data source.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass

from ..engines.probability_engine import ProbabilityEngine
from .intelligence_aggregator import IntelligenceAggregator

logger = logging.getLogger(__name__)

@dataclass
class LiveMarketState:
    """Live market state for processing"""
    symbol: str
    spot_price: float
    calls: list
    puts: list
    timestamp: datetime
    last_update: datetime

class LiveAnalyticsEngine:
    """
    Live analytics engine that processes real-time market data.
    Reuses existing calculation logic without duplicating code.
    """
    
    def __init__(self):
        self.running = False
        self.market_states: Dict[str, LiveMarketState] = {}
        self.live_metrics_cache: Dict[str, Dict[str, Any]] = {}
        self.update_task: Optional[asyncio.Task] = None
        
        # Reuse existing engines
        self.probability_engine = ProbabilityEngine()
        self.intelligence_aggregator = IntelligenceAggregator()
        
        logger.info("LiveAnalyticsEngine initialized")
    
    async def start(self):
        """Start the live analytics engine"""
        if self.running:
            logger.warning("LiveAnalyticsEngine already running")
            return
        
        self.running = True
        self.update_task = asyncio.create_task(self._update_loop())
        logger.info("LiveAnalyticsEngine started")
    
    async def stop(self):
        """Stop the live analytics engine"""
        self.running = False
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
        
        logger.info("LiveAnalyticsEngine stopped")
    
    def is_running(self) -> bool:
        """Check if engine is running"""
        return self.running
    
    async def update_market_state(self, symbol: str, market_data: Dict[str, Any]):
        """Update market state with new data"""
        try:
            # Extract data in same format as REST service
            spot_price = market_data.get("spot", 0)
            calls = market_data.get("calls", [])
            puts = market_data.get("puts", [])
            
            # Create live market state
            market_state = LiveMarketState(
                symbol=symbol,
                spot_price=spot_price,
                calls=calls,
                puts=puts,
                timestamp=datetime.now(timezone.utc),
                last_update=datetime.now(timezone.utc)
            )
            
            self.market_states[symbol] = market_state
            
            # Trigger analytics calculation
            await self._calculate_live_metrics(symbol, market_state)
            
            logger.info(f"Updated market state for {symbol}: spot={spot_price}, calls={len(calls)}, puts={len(puts)}")
            
        except Exception as e:
            logger.error(f"Error updating market state for {symbol}: {e}")
    
    async def _calculate_live_metrics(self, symbol: str, market_state: LiveMarketState):
        """Calculate live metrics using existing engines"""
        try:
            # Reuse existing analytics calculation logic
            # This mirrors option_chain_service.py calculations
            
            # Calculate OI Analytics (reusing existing logic)
            total_call_oi = sum(call.get("oi", 0) for call in market_state.calls)
            total_put_oi = sum(put.get("oi", 0) for put in market_state.puts)
            total_oi = total_call_oi + total_put_oi
            
            # Calculate PCR (same as existing logic)
            pcr = 0 if total_call_oi == 0 else round(total_put_oi / total_call_oi, 4)
            
            # Find strongest support/resistance (same as existing logic)
            resistance_strike = max(market_state.calls, key=lambda x: x.get("oi", 0)).get("strike", 0) if market_state.calls else 0
            support_strike = max(market_state.puts, key=lambda x: x.get("oi", 0)).get("strike", 0) if market_state.puts else 0
            
            # Calculate OI dominance (same as existing logic)
            oi_dominance = 0 if total_oi == 0 else abs(total_call_oi - total_put_oi) / total_oi
            
            # Calculate PCR strength (same as existing logic)
            pcr_strength = min(abs(pcr - 1) * 100, 100)
            
            # Calculate bias score (same as existing logic)
            pcr_bias = (pcr - 1) * 50  # PCR contribution (-50 to +50)
            oi_bias = (total_put_oi - total_call_oi) / max(total_oi, 1) * 50  # OI dominance contribution
            positioning_bias = 0  # Placeholder for positioning analysis
            
            bias_score = max(0, min(100, 50 + pcr_bias + oi_bias * 0.3 + positioning_bias * 0.3))
            
            # Determine bias label (same as existing logic)
            if bias_score >= 60:
                bias_label = "BULLISH"
            elif bias_score <= 40:
                bias_label = "BEARISH"
            else:
                bias_label = "NEUTRAL"
            
            # Calculate position score (same as existing logic)
            call_oi_concentration = max(call.get("oi", 0) for call in market_state.calls) / max(total_call_oi, 1) if market_state.calls else 0
            put_oi_concentration = max(put.get("oi", 0) for put in market_state.puts) / max(total_put_oi, 1) if market_state.puts else 0
            position_score = (call_oi_concentration + put_oi_concentration) * 50
            
            # Build analytics object (same structure as REST)
            analytics = {
                "total_call_oi": total_call_oi,
                "total_put_oi": total_put_oi,
                "pcr": pcr,
                "strongest_resistance": resistance_strike,
                "strongest_support": support_strike,
                "bias_score": round(bias_score, 2),
                "bias_label": bias_label,
                "oi_dominance": round(oi_dominance, 4),
                "position_score": round(position_score, 2),
                "pcr_strength": round(pcr_strength, 2)
            }
            
            # Aggregate intelligence (reusing existing logic)
            market_data_dict = {
                "spot_price": market_state.spot_price,
                "timestamp": market_state.timestamp.isoformat()
            }
            
            intelligence = self.intelligence_aggregator.aggregate_intelligence(
                raw_analytics=analytics,
                market_data=market_data_dict,
                calls=market_state.calls,
                puts=market_state.puts
            )
            
            # Calculate probability (reusing existing logic)
            probability = self.probability_engine.calculate_probability_metrics(
                spot_price=market_state.spot_price,
                calls=market_state.calls,
                puts=market_state.puts
            )
            
            # Cache live metrics
            self.live_metrics_cache[symbol] = {
                "analytics": analytics,
                "intelligence": intelligence,
                "probability": probability,
                "spot": market_state.spot_price,
                "last_update": market_state.last_update.isoformat()
            }
            
            logger.info(f"Calculated live metrics for {symbol}: bias={bias_label} ({bias_score}), pcr={pcr}")
            
        except Exception as e:
            logger.error(f"Error calculating live metrics for {symbol}: {e}")
    
    async def get_live_metrics(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached live metrics for a symbol"""
        return self.live_metrics_cache.get(symbol)
    
    async def _update_loop(self):
        """Main update loop for live processing"""
        logger.info("LiveAnalyticsEngine update loop started")
        
        while self.running:
            try:
                # Simulate live updates (in real implementation, this would come from market data feed)
                for symbol in list(self.market_states.keys()):
                    # In real implementation, this would be triggered by market data events
                    # For now, we'll just update timestamps to simulate live activity
                    if symbol in self.market_states:
                        self.market_states[symbol].last_update = datetime.now(timezone.utc)
                        
                        # Prepare live data for broadcasting
                        live_data = {
                            "spot": self.market_states[symbol].spot_price,
                            "timestamp": self.market_states[symbol].last_update.isoformat(),
                            "analytics": self.live_metrics_cache.get(symbol, {}).get("analytics", {}),
                            "intelligence": self.live_metrics_cache.get(symbol, {}).get("intelligence", {}),
                            "probability": self.live_metrics_cache.get(symbol, {}).get("probability", {})
                        }
                        
                        # Broadcast live update to WebSocket clients
                        # This will be handled by the WebSocket manager when called
                        # Note: In real implementation, this would call:
                        # await broadcast_live_update(symbol, live_data)
                        
                # Update every 1 second (configurable)
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                logger.info("LiveAnalyticsEngine update loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in live update loop: {e}")
                await asyncio.sleep(1)  # Prevent tight error loop
        
        logger.info("LiveAnalyticsEngine update loop stopped")

# Global instance
live_analytics_engine = LiveAnalyticsEngine()
