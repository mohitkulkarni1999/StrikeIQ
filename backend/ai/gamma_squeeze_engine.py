"""
GammaSqueezeEngine - Detects gamma squeeze probability
Lightweight, optimized for Intel i5 CPU, 8GB RAM
"""

import logging
import time
from typing import Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class GammaSqueezeSignal:
    """Gamma squeeze analysis result"""
    signal: str  # SQUEEZE_UP | SQUEEZE_DOWN | NONE
    confidence: float
    direction: str  # UP | DOWN | NONE
    strength: float
    reason: str

class GammaSqueezeEngine:
    """
    Detects gamma squeeze probability
    Analyzes gamma exposure, flip levels, and positioning for squeeze potential
    """
    
    def __init__(self):
        # Detection thresholds
        self.gamma_flip_proximity_threshold = 0.02  # 2% proximity to flip level
        self.net_gamma_threshold = 100000  # 100k net gamma threshold
        self.flow_imbalance_threshold = 0.3  # 30% flow imbalance
        self.volatility_squeeze_threshold = 0.02  # 2% volatility for squeeze
        self.oi_velocity_threshold = 800  # High OI velocity
        
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
        
        logger.info("GammaSqueezeEngine initialized")
    
    def analyze(self, live_metrics) -> Dict[str, Any]:
        """
        Analyze LiveMetrics for gamma squeeze potential
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
            
            net_gamma = live_metrics.get("net_gamma") if isinstance(live_metrics, dict) else getattr(live_metrics, 'net_gamma', 0)
            gamma_flip_level = live_metrics.get("gamma_flip_level") if isinstance(live_metrics, dict) else getattr(live_metrics, 'gamma_flip_level', 0)
            distance_from_flip = live_metrics.get("distance_from_flip") if isinstance(live_metrics, dict) else getattr(live_metrics, 'distance_from_flip', 0)
            flow_imbalance = live_metrics.get("flow_imbalance") if isinstance(live_metrics, dict) else getattr(live_metrics, 'flow_imbalance', 0)
            flow_direction = live_metrics.get("flow_direction") if isinstance(live_metrics, dict) else getattr(live_metrics, 'flow_direction', 'neutral')
            volatility_regime = live_metrics.get("volatility_regime") if isinstance(live_metrics, dict) else getattr(live_metrics, 'volatility_regime', 'normal')
            oi_velocity = live_metrics.get("oi_velocity") if isinstance(live_metrics, dict) else getattr(live_metrics, 'oi_velocity', 0)
            expected_move = live_metrics.get("expected_move") if isinstance(live_metrics, dict) else getattr(live_metrics, 'expected_move', spot * 0.02)
            pcr = live_metrics.get("pcr") if isinstance(live_metrics, dict) else getattr(live_metrics, 'pcr', 1.0)
            
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
            # Detect squeeze patterns
            up_squeeze = self._detect_upward_squeeze(spot, gamma_flip_level, distance_from_flip, net_gamma, flow_direction, flow_imbalance, oi_velocity, volatility_regime)
            down_squeeze = self._detect_downward_squeeze(spot, gamma_flip_level, distance_from_flip, net_gamma, flow_direction, flow_imbalance, oi_velocity, volatility_regime)
            
            # Determine final signal
            if up_squeeze['probability'] > down_squeeze['probability'] and up_squeeze['probability'] > 0.5:
                # FIX 3: Update timestamp for significant signals only
                self.last_signal_timestamp = current_time
                logger.info(f"Gamma squeeze UP detected: {up_squeeze['reason']}")
                return {
                    "signal": "SQUEEZE_UP",
                    "confidence": up_squeeze['probability'],
                    "direction": "UP",
                    "strength": up_squeeze['probability'],
                    "reason": up_squeeze['reason']
                }
            elif down_squeeze['probability'] > up_squeeze['probability'] and down_squeeze['probability'] > 0.5:
                # FIX 3: Update timestamp for significant signals only
                self.last_signal_timestamp = current_time
                logger.info(f"Gamma squeeze DOWN detected: {down_squeeze['reason']}")
                return {
                    "signal": "SQUEEZE_DOWN",
                    "confidence": down_squeeze['probability'],
                    "direction": "DOWN",
                    "strength": down_squeeze['probability'],
                    "reason": down_squeeze['reason']
                }
            else:
                return {
                    "signal": "NONE",
                    "confidence": 0.0,
                    "direction": "NONE",
                    "strength": 0.0,
                    "reason": "no_gamma_squeeze"
                }
                
        except Exception as e:
            # FIX 2: Safe default output on exceptions
            logger.error(f"GammaSqueezeEngine analysis error: {e}")
            return self.safe_default
    
    def _detect_upward_squeeze(self, spot: float, gamma_flip_level: float, distance_from_flip: float, net_gamma: float, flow_direction: str, flow_imbalance: float, oi_velocity: float, volatility_regime: str) -> Dict[str, Any]:
        """Detect upward gamma squeeze potential"""
        try:
            probability = 0.0
            reasons = []
            
            # FIX 5: Performance safety - avoid loops, use constant time operations
            # Check proximity to gamma flip level
            if gamma_flip_level > 0:
                flip_proximity = abs(spot - gamma_flip_level) / spot
                if flip_proximity < self.gamma_flip_proximity_threshold:
                    probability += 0.3
                    reasons.append("near_gamma_flip")
                elif flip_proximity < 0.05:  # 5%
                    probability += 0.15
                    reasons.append("moderate_flip_proximity")
            
            # Check net gamma (high positive gamma can fuel squeeze)
            if net_gamma > self.net_gamma_threshold:
                probability += 0.25
                reasons.append("high_positive_gamma")
            elif net_gamma > 50000:
                probability += 0.1
                reasons.append("moderate_positive_gamma")
            
            # Check call flow dominance
            if flow_direction == 'call' and flow_imbalance > self.flow_imbalance_threshold:
                probability += 0.2
                reasons.append("call_flow_dominance")
            elif flow_direction == 'call' and flow_imbalance > 0.15:
                probability += 0.1
                reasons.append("moderate_call_flow")
            
            # Check OI velocity (rapid OI changes indicate positioning)
            if abs(oi_velocity) > self.oi_velocity_threshold:
                probability += 0.15
                reasons.append("high_oi_velocity")
            
            # Check volatility regime (squeezes often happen in normal vol)
            if volatility_regime == 'normal':
                probability += 0.1
                reasons.append("normal_volatility")
            
            logger.debug(f"Upward squeeze analysis: probability={probability:.3f}, reasons={reasons}")
            
            return {
                'probability': min(probability, 1.0),
                'reason': '; '.join(reasons) if reasons else "no_squeeze_indicators"
            }
            
        except Exception as e:
            logger.error(f"Upward squeeze detection error: {e}")
            return {'probability': 0.0, 'reason': 'detection_error'}
    
    def _detect_downward_squeeze(self, spot: float, gamma_flip_level: float, distance_from_flip: float, net_gamma: float, flow_direction: str, flow_imbalance: float, oi_velocity: float, volatility_regime: str) -> Dict[str, Any]:
        """Detect downward gamma squeeze potential"""
        try:
            probability = 0.0
            reasons = []
            
            # FIX 5: Performance safety - avoid loops, use constant time operations
            # Check proximity to gamma flip level
            if gamma_flip_level > 0:
                flip_proximity = abs(spot - gamma_flip_level) / spot
                if flip_proximity < self.gamma_flip_proximity_threshold:
                    probability += 0.3
                    reasons.append("near_gamma_flip")
                elif flip_proximity < 0.05:  # 5%
                    probability += 0.15
                    reasons.append("moderate_flip_proximity")
            
            # Check net gamma (high negative gamma can fuel downward squeeze)
            if net_gamma < -self.net_gamma_threshold:
                probability += 0.25
                reasons.append("high_negative_gamma")
            elif net_gamma < -50000:
                probability += 0.1
                reasons.append("moderate_negative_gamma")
            
            # Check put flow dominance
            if flow_direction == 'put' and flow_imbalance > self.flow_imbalance_threshold:
                probability += 0.2
                reasons.append("put_flow_dominance")
            elif flow_direction == 'put' and flow_imbalance > 0.15:
                probability += 0.1
                reasons.append("moderate_put_flow")
            
            # Check OI velocity
            if abs(oi_velocity) > self.oi_velocity_threshold:
                probability += 0.15
                reasons.append("high_oi_velocity")
            
            # Check volatility regime
            if volatility_regime == 'normal':
                probability += 0.1
                reasons.append("normal_volatility")
            
            logger.debug(f"Downward squeeze analysis: probability={probability:.3f}, reasons={reasons}")
            
            return {
                'probability': min(probability, 1.0),
                'reason': '; '.join(reasons) if reasons else "no_squeeze_indicators"
            }
            
        except Exception as e:
            logger.error(f"Downward squeeze detection error: {e}")
            return {'probability': 0.0, 'reason': 'detection_error'}
