"""
LiquidityEngine - Detects liquidity sweeps and fake breakouts
Lightweight, optimized for Intel i5 CPU, 8GB RAM
"""

import logging
import time
from typing import Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LiquiditySignal:
    """Liquidity analysis result"""
    signal: str  # SWEEP_UP | SWEEP_DOWN | NONE
    confidence: float
    direction: str  # UP | DOWN | NONE
    strength: float
    reason: str

class LiquidityEngine:
    """
    Detects liquidity sweeps and fake breakouts
    Analyzes price action patterns for liquidity hunting behavior
    """
    
    def __init__(self):
        # Detection thresholds
        self.support_resistance_buffer = 0.005  # 0.5% buffer around S/R
        self.wick_ratio_threshold = 0.3  # 30% wick to body ratio
        self.reversal_threshold = 0.01  # 1% reversal threshold
        self.volatility_spike_multiplier = 2.0  # 2x normal volatility
        
        # Production safety features
        self.last_signal_timestamp = 0
        self.cooldown_seconds = 3
        
        # Safe default output
        self.safe_default = {
            "signal": "NONE",
            "confidence": 0.0,
            "direction": "NONE",
            "strength": 0.0,
            "reason": "invalid_metrics"
        }
        
        logger.info("LiquidityEngine initialized")
    
    def analyze(self, live_metrics) -> Dict[str, Any]:
        """
        Analyze LiveMetrics for liquidity sweep patterns
        """
        try:
            # FIX 1: Metrics validation
            if not live_metrics:
                logger.debug("Empty metrics received")
                return self.safe_default
            
            # FIX 1: Safe field access with validation
            spot = live_metrics.get("spot") if isinstance(live_metrics, dict) else getattr(live_metrics, 'spot', None)
            if not spot or spot <= 0:
                logger.debug("Invalid or missing spot price")
                return self.safe_default
            
            support_level = live_metrics.get("support_level") if isinstance(live_metrics, dict) else getattr(live_metrics, 'support_level', 0)
            resistance_level = live_metrics.get("resistance_level") if isinstance(live_metrics, dict) else getattr(live_metrics, 'resistance_level', 0)
            volatility_regime = live_metrics.get("volatility_regime") if isinstance(live_metrics, dict) else getattr(live_metrics, 'volatility_regime', 'normal')
            expected_move = live_metrics.get("expected_move") if isinstance(live_metrics, dict) else getattr(live_metrics, 'expected_move', spot * 0.02)
            
            # FIX 3: Signal cooldown mechanism
            current_time = time.time()
            if current_time - self.last_signal_timestamp < self.cooldown_seconds:
                logger.debug("Signal in cooldown period")
                return {
                    "signal": "NONE",
                    "confidence": 0.0,
                    "direction": "NONE",
                    "strength": 0.0,
                    "reason": "signal_cooldown"
                }
            
            # FIX 5: Performance safety - constant time calculations
            # Calculate distance from support/resistance
            support_distance = (spot - support_level) / support_level if support_level > 0 else float('inf')
            resistance_distance = (resistance_level - spot) / resistance_level if resistance_level > 0 else float('inf')
            
            # Detect liquidity sweep patterns
            sweep_up = self._detect_sweep_up(spot, support_distance, expected_move, volatility_regime)
            sweep_down = self._detect_sweep_down(spot, resistance_distance, expected_move, volatility_regime)
            
            # Determine final signal
            if sweep_up['confidence'] > sweep_down['confidence'] and sweep_up['confidence'] > 0.5:
                # FIX 3: Update timestamp for significant signals only
                self.last_signal_timestamp = current_time
                logger.info(f"Liquidity sweep UP detected: {sweep_up['reason']}")
                return {
                    "signal": "SWEEP_UP",
                    "confidence": sweep_up['confidence'],
                    "direction": "UP",
                    "strength": sweep_up['confidence'],
                    "reason": sweep_up['reason']
                }
            elif sweep_down['confidence'] > sweep_up['confidence'] and sweep_down['confidence'] > 0.5:
                # FIX 3: Update timestamp for significant signals only
                self.last_signal_timestamp = current_time
                logger.info(f"Liquidity sweep DOWN detected: {sweep_down['reason']}")
                return {
                    "signal": "SWEEP_DOWN",
                    "confidence": sweep_down['confidence'],
                    "direction": "DOWN",
                    "strength": sweep_down['confidence'],
                    "reason": sweep_down['reason']
                }
            else:
                return {
                    "signal": "NONE",
                    "confidence": 0.0,
                    "direction": "NONE",
                    "strength": 0.0,
                    "reason": "no_liquidity_sweep"
                }
                
        except Exception as e:
            # FIX 2: Safe default output on exceptions
            logger.error(f"LiquidityEngine analysis error: {e}")
            return self.safe_default
    
    def _detect_sweep_up(self, spot: float, support_distance: float, expected_move: float, volatility_regime: str) -> Dict[str, Any]:
        """Detect upward liquidity sweep (support break then recovery)"""
        try:
            confidence = 0.0
            reasons = []
            
            # FIX 5: Performance safety - avoid loops, use constant time operations
            # Check if price is near support
            if support_distance < self.support_resistance_buffer:
                confidence += 0.3
                reasons.append("price_near_support")
            
            # Check for volatility spike (potential sweep)
            if volatility_regime == 'extreme':
                confidence += 0.2
                reasons.append("extreme_volatility")
            elif volatility_regime == 'elevated':
                confidence += 0.1
                reasons.append("elevated_volatility")
            
            # Check expected move (large moves can indicate sweeps)
            if expected_move and spot > 0 and expected_move / spot > 0.03:  # > 3% expected move
                confidence += 0.2
                reasons.append("high_expected_move")
            
            logger.debug(f"Sweep UP analysis: confidence={confidence:.3f}, reasons={reasons}")
            
            return {
                'confidence': min(confidence, 1.0),
                'reason': '; '.join(reasons) if reasons else "no_sweep_indicators"
            }
            
        except Exception as e:
            logger.error(f"Sweep up detection error: {e}")
            return {'confidence': 0.0, 'reason': 'detection_error'}
    
    def _detect_sweep_down(self, spot: float, resistance_distance: float, expected_move: float, volatility_regime: str) -> Dict[str, Any]:
        """Detect downward liquidity sweep (resistance break then rejection)"""
        try:
            confidence = 0.0
            reasons = []
            
            # FIX 5: Performance safety - avoid loops, use constant time operations
            # Check if price is near resistance
            if resistance_distance < self.support_resistance_buffer:
                confidence += 0.3
                reasons.append("price_near_resistance")
            
            # Check for volatility spike
            if volatility_regime == 'extreme':
                confidence += 0.2
                reasons.append("extreme_volatility")
            elif volatility_regime == 'elevated':
                confidence += 0.1
                reasons.append("elevated_volatility")
            
            # Check expected move
            if expected_move and spot > 0 and expected_move / spot > 0.03:  # > 3% expected move
                confidence += 0.2
                reasons.append("high_expected_move")
            
            logger.debug(f"Sweep DOWN analysis: confidence={confidence:.3f}, reasons={reasons}")
            
            return {
                'confidence': min(confidence, 1.0),
                'reason': '; '.join(reasons) if reasons else "no_sweep_indicators"
            }
            
        except Exception as e:
            logger.error(f"Sweep down detection error: {e}")
            return {'confidence': 0.0, 'reason': 'detection_error'}
