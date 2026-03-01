"""
LiquidityVacuumEngine - Detects sudden liquidity disappearance
Lightweight, optimized for Intel i5 CPU, 8GB RAM
Execution time: < 1ms
"""

import logging
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)

class LiquidityVacuumEngine:
    """
    Detects sudden liquidity disappearance leading to explosive price movement
    Analyzes volatility, OI changes, and price positioning for liquidity vacuum signals
    """
    
    def __init__(self):
        # Detection thresholds
        self.volatility_extreme_threshold = 1.5  # 1.5x normal volatility
        self.oi_change_threshold = 1000  # 1000 OI change threshold
        self.support_resistance_proximity = 0.02  # 2% proximity to S/R levels
        self.vacuum_strength_threshold = 0.6  # 60% confidence for vacuum detection
        
        # Production safety features
        self.last_signal_timestamp = 0
        self.cooldown_seconds = 3
        
        # Safe default output
        self.safe_default = {
            "signal": "NONE",
            "confidence": 0.0,
            "direction": "NONE",
            "strength": 0.0,
            "reason": "error"
        }
        
        logger.info("LiquidityVacuumEngine initialized")
    
    def analyze(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze LiveMetrics for liquidity vacuum patterns
        
        Args:
            metrics: Dictionary with live market data
            
        Returns:
            Dictionary with liquidity vacuum analysis
        """
        try:
            # Metrics validation
            if not metrics:
                logger.debug("Empty metrics received")
                return self.safe_default
            
            # Safe field access with validation
            spot_price = float(metrics.get('spot_price', 0))
            support = float(metrics.get('support', 0))
            resistance = float(metrics.get('resistance', 0))
            volatility_regime = str(metrics.get('volatility_regime', 'normal'))
            oi_change = float(metrics.get('oi_change', 0))
            
            if not spot_price or spot_price <= 0:
                logger.debug("Invalid or missing spot price")
                return self.safe_default
            
            if not support or not resistance or support <= 0 or resistance <= 0:
                logger.debug("Invalid or missing support/resistance levels")
                return self.safe_default
            
            # Signal cooldown mechanism
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
            
            # Performance safety - constant time calculations
            # Calculate distances from support/resistance
            support_distance = (spot_price - support) / support
            resistance_distance = (resistance - spot_price) / resistance
            
            # Detect liquidity vacuum patterns
            vacuum_up = self._detect_vacuum_up(spot_price, resistance_distance, volatility_regime, oi_change)
            vacuum_down = self._detect_vacuum_down(spot_price, support_distance, volatility_regime, oi_change)
            
            # Determine final signal
            if vacuum_up['confidence'] > vacuum_down['confidence'] and vacuum_up['confidence'] > self.vacuum_strength_threshold:
                # Update timestamp for significant signals only
                self.last_signal_timestamp = current_time
                logger.info(f"Liquidity vacuum UP detected: {vacuum_up['reason']}")
                return {
                    "signal": "LIQUIDITY_VACUUM_UP",
                    "confidence": vacuum_up['confidence'],
                    "direction": "UP",
                    "strength": vacuum_up['strength'],
                    "reason": vacuum_up['reason']
                }
            elif vacuum_down['confidence'] > vacuum_up['confidence'] and vacuum_down['confidence'] > self.vacuum_strength_threshold:
                # Update timestamp for significant signals only
                self.last_signal_timestamp = current_time
                logger.info(f"Liquidity vacuum DOWN detected: {vacuum_down['reason']}")
                return {
                    "signal": "LIQUIDITY_VACUUM_DOWN",
                    "confidence": vacuum_down['confidence'],
                    "direction": "DOWN",
                    "strength": vacuum_down['strength'],
                    "reason": vacuum_down['reason']
                }
            else:
                return {
                    "signal": "NONE",
                    "confidence": max(vacuum_up['confidence'], vacuum_down['confidence']),
                    "direction": "NONE",
                    "strength": 0.0,
                    "reason": "no_liquidity_vacuum"
                }
                
        except Exception as e:
            logger.error(f"LiquidityVacuumEngine analysis error: {e}")
            return self.safe_default
    
    def _detect_vacuum_up(self, spot_price: float, resistance_distance: float, volatility_regime: str, oi_change: float) -> Dict[str, Any]:
        """Detect upward liquidity vacuum (buyers chasing liquidity)"""
        try:
            confidence = 0.0
            reasons = []
            
            # Performance safety - avoid loops, use constant time operations
            
            # Check if price is near resistance
            if resistance_distance < self.support_resistance_proximity:
                confidence += 0.3
                reasons.append("price_near_resistance")
            
            # Check for extreme volatility
            if volatility_regime == 'extreme':
                confidence += 0.4
                reasons.append("extreme_volatility")
            elif volatility_regime == 'elevated':
                confidence += 0.2
                reasons.append("elevated_volatility")
            
            # Check for strong positive OI change (buying pressure)
            if oi_change > self.oi_change_threshold:
                confidence += 0.3
                reasons.append("strong_oi_increase")
            elif oi_change > self.oi_change_threshold * 0.5:
                confidence += 0.15
                reasons.append("moderate_oi_increase")
            
            # Additional vacuum indicators
            if resistance_distance < 0.01:  # Very close to resistance
                confidence += 0.2
                reasons.append("very_close_to_resistance")
            
            # Calculate strength based on confidence and OI magnitude
            strength = min(confidence * (abs(oi_change) / self.oi_change_threshold), 1.0)
            
            logger.debug(f"Vacuum UP analysis: confidence={confidence:.3f}, reasons={reasons}")
            
            return {
                'confidence': min(confidence, 1.0),
                'strength': strength,
                'reason': '; '.join(reasons) if reasons else "no_vacuum_indicators"
            }
            
        except Exception as e:
            logger.error(f"Vacuum up detection error: {e}")
            return {'confidence': 0.0, 'strength': 0.0, 'reason': 'detection_error'}
    
    def _detect_vacuum_down(self, spot_price: float, support_distance: float, volatility_regime: str, oi_change: float) -> Dict[str, Any]:
        """Detect downward liquidity vacuum (liquidity collapse)"""
        try:
            confidence = 0.0
            reasons = []
            
            # Performance safety - avoid loops, use constant time operations
            
            # Check if price is near support
            if support_distance < self.support_resistance_proximity:
                confidence += 0.3
                reasons.append("price_near_support")
            
            # Check for extreme volatility
            if volatility_regime == 'extreme':
                confidence += 0.4
                reasons.append("extreme_volatility")
            elif volatility_regime == 'elevated':
                confidence += 0.2
                reasons.append("elevated_volatility")
            
            # Check for strong negative OI change (selling pressure/liquidity collapse)
            if oi_change < -self.oi_change_threshold:
                confidence += 0.3
                reasons.append("strong_oi_decrease")
            elif oi_change < -self.oi_change_threshold * 0.5:
                confidence += 0.15
                reasons.append("moderate_oi_decrease")
            
            # Additional vacuum indicators
            if support_distance < 0.01:  # Very close to support
                confidence += 0.2
                reasons.append("very_close_to_support")
            
            # Calculate strength based on confidence and OI magnitude
            strength = min(confidence * (abs(oi_change) / self.oi_change_threshold), 1.0)
            
            logger.debug(f"Vacuum DOWN analysis: confidence={confidence:.3f}, reasons={reasons}")
            
            return {
                'confidence': min(confidence, 1.0),
                'strength': strength,
                'reason': '; '.join(reasons) if reasons else "no_vacuum_indicators"
            }
            
        except Exception as e:
            logger.error(f"Vacuum down detection error: {e}")
            return {'confidence': 0.0, 'strength': 0.0, 'reason': 'detection_error'}

# Global instance
_liquidity_vacuum_engine = None

def get_liquidity_vacuum_engine() -> LiquidityVacuumEngine:
    """
    Get or create global LiquidityVacuumEngine instance
    """
    global _liquidity_vacuum_engine
    if _liquidity_vacuum_engine is None:
        _liquidity_vacuum_engine = LiquidityVacuumEngine()
    return _liquidity_vacuum_engine

def analyze_liquidity_vacuum(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to analyze liquidity vacuum
    
    Args:
        metrics: Dictionary with live market data
        
    Returns:
        Dictionary with liquidity vacuum analysis
    """
    engine = get_liquidity_vacuum_engine()
    return engine.analyze(metrics)
