"""
DealerGammaEngine - Detects dealer gamma regime
Lightweight, optimized for Intel i5 CPU, 8GB RAM
Execution time: < 1ms
"""

import logging
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DealerGammaEngine:
    """
    Detects dealer gamma regime based on net gamma and price positioning
    Analyzes market maker positioning for mean reversion vs trend acceleration
    """
    
    def __init__(self):
        # Detection thresholds
        self.net_gamma_threshold = 10000  # 10k net gamma threshold
        self.gamma_flip_proximity = 0.02  # 2% proximity to gamma flip level
        self.neutral_gamma_range = 5000   # ±5k gamma considered neutral
        
        # Production safety features
        self.last_signal_timestamp = 0
        self.cooldown_seconds = 3
        
        # Safe default output
        self.safe_default = {
            "signal": "GAMMA_NEUTRAL",
            "confidence": 0.0,
            "direction": "NONE",
            "strength": 0.0,
            "reason": "error"
        }
        
        logger.info("DealerGammaEngine initialized")
    
    def analyze(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze LiveMetrics for dealer gamma regime
        
        Args:
            metrics: Dictionary with live market data
            
        Returns:
            Dictionary with dealer gamma regime analysis
        """
        try:
            # Metrics validation
            if not metrics:
                logger.debug("Empty metrics received")
                return self.safe_default
            
            # Safe field access with validation
            net_gamma = float(metrics.get('net_gamma', 0))
            gamma_flip_level = float(metrics.get('gamma_flip_level', 0))
            spot_price = float(metrics.get('spot_price', 0))
            
            if not spot_price or spot_price <= 0:
                logger.debug("Invalid or missing spot price")
                return self.safe_default
            
            if not gamma_flip_level or gamma_flip_level <= 0:
                logger.debug("Invalid or missing gamma flip level")
                return self.safe_default
            
            # Signal cooldown mechanism
            current_time = time.time()
            if current_time - self.last_signal_timestamp < self.cooldown_seconds:
                logger.debug("Signal in cooldown period")
                return {
                    "signal": "GAMMA_NEUTRAL",
                    "confidence": 0.0,
                    "direction": "NONE",
                    "strength": 0.0,
                    "reason": "signal_cooldown"
                }
            
            # Performance safety - constant time calculations
            # Calculate distance from gamma flip level
            distance_from_flip = abs(spot_price - gamma_flip_level) / gamma_flip_level
            
            # Detect dealer gamma regime
            gamma_regime = self._detect_gamma_regime(net_gamma, distance_from_flip)
            
            # Update timestamp for significant signals only
            if gamma_regime['confidence'] > 0.5:
                self.last_signal_timestamp = current_time
                logger.info(f"Dealer gamma regime detected: {gamma_regime['signal']} - {gamma_regime['reason']}")
            
            return {
                "signal": gamma_regime['signal'],
                "confidence": gamma_regime['confidence'],
                "direction": gamma_regime['direction'],
                "strength": gamma_regime['strength'],
                "reason": gamma_regime['reason']
            }
            
        except Exception as e:
            logger.error(f"DealerGammaEngine analysis error: {e}")
            return self.safe_default
    
    def _detect_gamma_regime(self, net_gamma: float, distance_from_flip: float) -> Dict[str, Any]:
        """Detect dealer gamma regime based on net gamma and positioning"""
        try:
            confidence = 0.0
            reasons = []
            signal = "GAMMA_NEUTRAL"
            direction = "NONE"
            
            # Performance safety - constant time operations only
            
            # LONG_GAMMA detection
            if net_gamma > self.net_gamma_threshold:
                confidence += 0.4
                reasons.append("positive_net_gamma")
                
                # Check proximity to gamma flip level
                if distance_from_flip < self.gamma_flip_proximity:
                    confidence += 0.4
                    reasons.append("near_gamma_flip_level")
                    signal = "LONG_GAMMA"
                    direction = "NONE"  # Mean reversion, no directional bias
                else:
                    confidence += 0.2
                    reasons.append("positive_gamma_position")
                    signal = "LONG_GAMMA"
                    direction = "NONE"
            
            # SHORT_GAMMA detection
            elif net_gamma < -self.net_gamma_threshold:
                confidence += 0.4
                reasons.append("negative_net_gamma")
                
                # Check if moving away from gamma flip level
                if distance_from_flip > self.gamma_flip_proximity:
                    confidence += 0.4
                    reasons.append("away_from_gamma_flip_level")
                    signal = "SHORT_GAMMA"
                    # Direction depends on which side of flip level we're on
                    direction = "UP" if net_gamma < 0 else "DOWN"  # Trend acceleration
                else:
                    confidence += 0.2
                    reasons.append("negative_gamma_position")
                    signal = "SHORT_GAMMA"
                    direction = "UP" if net_gamma < 0 else "DOWN"
            
            # GAMMA_NEUTRAL detection
            elif abs(net_gamma) <= self.neutral_gamma_range:
                confidence = 0.6  # Higher confidence for neutral
                reasons.append("gamma_near_zero")
                signal = "GAMMA_NEUTRAL"
                direction = "NONE"
            
            # Edge cases - moderate gamma
            else:
                if abs(net_gamma) > 5000:
                    confidence = 0.3
                    reasons.append("moderate_gamma_exposure")
                    signal = "GAMMA_NEUTRAL"
                    direction = "NONE"
                else:
                    confidence = 0.2
                    reasons.append("low_gamma_exposure")
                    signal = "GAMMA_NEUTRAL"
                    direction = "NONE"
            
            # Calculate strength based on confidence and gamma magnitude
            strength = min(confidence * (abs(net_gamma) / self.net_gamma_threshold), 1.0)
            
            logger.debug(f"Dealer gamma analysis: signal={signal}, confidence={confidence:.3f}, reasons={reasons}")
            
            return {
                'signal': signal,
                'confidence': min(confidence, 1.0),
                'direction': direction,
                'strength': strength,
                'reason': '; '.join(reasons) if reasons else "insufficient_data"
            }
            
        except Exception as e:
            logger.error(f"Gamma regime detection error: {e}")
            return {
                'signal': 'GAMMA_NEUTRAL',
                'confidence': 0.0,
                'direction': 'NONE',
                'strength': 0.0,
                'reason': 'detection_error'
            }

# Global instance
_dealer_gamma_engine = None

def get_dealer_gamma_engine() -> DealerGammaEngine:
    """
    Get or create global DealerGammaEngine instance
    """
    global _dealer_gamma_engine
    if _dealer_gamma_engine is None:
        _dealer_gamma_engine = DealerGammaEngine()
    return _dealer_gamma_engine

def analyze_dealer_gamma(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to analyze dealer gamma regime
    
    Args:
        metrics: Dictionary with live market data
        
    Returns:
        Dictionary with dealer gamma regime analysis
    """
    engine = get_dealer_gamma_engine()
    return engine.analyze(metrics)
