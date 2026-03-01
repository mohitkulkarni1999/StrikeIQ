"""
OptionsTrapEngine - Detects Options Market Traps
Lightweight, optimized for Intel i5 CPU, 8GB RAM
Execution time: < 1ms
"""

import logging
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)

class OptionsTrapEngine:
    """
    Detects options market traps (bull traps, bear traps)
    Analyzes price action, volatility, and smart money patterns
    """
    
    def __init__(self):
        # Detection thresholds
        self.resistance_break_threshold = 0.01  # 1% above resistance
        self.support_break_threshold = 0.01   # 1% below support
        self.reversal_threshold = 0.005       # 0.5% reversal
        self.volatility_spike_threshold = 1.5  # 1.5x normal volatility
        self.weak_smart_money_threshold = 0.3  # 30% weak bias threshold
        self.accumulation_threshold = 0.4     # 40% accumulation threshold
        
        # Production safety features
        self.last_signal_timestamp = 0
        self.cooldown_seconds = 3
        
        # FIX 2: Safe default output
        self.safe_default = {
            "signal": "NONE",
            "confidence": 0.0,
            "direction": "NONE",
            "strength": 0.0,
            "reason": "invalid_metrics"
        }
        
        logger.info("OptionsTrapEngine initialized")
    
    def detect_trap(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect options market traps from LiveMetrics
        
        Args:
            metrics: Dictionary with live market data
            
        Returns:
            Dictionary with trap detection results
        """
        try:
            # FIX 1: Metrics validation
            if not metrics:
                logger.debug("Empty metrics received")
                return self.safe_default
            
            # FIX 1: Safe field access with validation
            spot_price = float(metrics.get('spot_price', 0))
            if not spot_price or spot_price <= 0:
                logger.debug("Invalid or missing spot price")
                return self.safe_default
            
            support = float(metrics.get('support', 0))
            resistance = float(metrics.get('resistance', 0))
            pcr = float(metrics.get('pcr', 1.0))
            net_gamma = float(metrics.get('net_gamma', 0))
            gamma_flip_level = float(metrics.get('gamma_flip_level', 0))
            volatility_regime = str(metrics.get('volatility_regime', 'normal'))
            oi_change = float(metrics.get('oi_change', 0))
            
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
            
            # Skip analysis if essential data is missing
            if support <= 0 or resistance <= 0:
                logger.debug("Insufficient support/resistance data")
                return self.safe_default
            
            # FIX 5: Performance safety - constant time calculations
            # Detect bull trap
            bull_trap = self._detect_bull_trap(
                spot_price, resistance, volatility_regime, pcr, net_gamma, oi_change
            )
            
            # Detect bear trap
            bear_trap = self._detect_bear_trap(
                spot_price, support, volatility_regime, pcr, net_gamma, oi_change
            )
            
            # Determine final signal
            if bull_trap['confidence'] > bear_trap['confidence'] and bull_trap['confidence'] > 0.5:
                # FIX 3: Update timestamp for significant signals only
                self.last_signal_timestamp = current_time
                logger.info(f"Bull trap detected: {bull_trap['reason']}")
                return {
                    "signal": "BULL_TRAP",
                    "confidence": bull_trap['confidence'],
                    "direction": "DOWN",
                    "strength": bull_trap['strength'],
                    "reason": bull_trap['reason']
                }
            elif bear_trap['confidence'] > bull_trap['confidence'] and bear_trap['confidence'] > 0.5:
                # FIX 3: Update timestamp for significant signals only
                self.last_signal_timestamp = current_time
                logger.info(f"Bear trap detected: {bear_trap['reason']}")
                return {
                    "signal": "BEAR_TRAP",
                    "confidence": bear_trap['confidence'],
                    "direction": "UP",
                    "strength": bear_trap['strength'],
                    "reason": bear_trap['reason']
                }
            else:
                return {
                    "signal": "NONE",
                    "confidence": 0.0,
                    "direction": "NONE",
                    "strength": 0.0,
                    "reason": "no_trap_detected"
                }
            
        except Exception as e:
            # FIX 2: Safe default output on exceptions
            logger.error(f"OptionsTrapEngine error: {e}")
            return self.safe_default
    
    def _detect_bull_trap(self, spot_price: float, resistance: float, 
                         volatility_regime: str, pcr: float, net_gamma: float, 
                         oi_change: float) -> Dict[str, Any]:
        """
        Detect bull trap (false breakout above resistance)
        """
        try:
            confidence = 0.0
            strength = 0.0
            reasons = []
            
            # FIX 5: Performance safety - avoid loops, use constant time operations
            # Check if price broke resistance
            resistance_distance = (spot_price - resistance) / resistance
            if resistance_distance > self.resistance_break_threshold:
                confidence += 0.3
                strength += 0.25
                reasons.append("price_broke_resistance")
            
            # Check for volatility spike (common in traps)
            if volatility_regime == 'extreme':
                confidence += 0.25
                strength += 0.2
                reasons.append("extreme_volatility")
            elif volatility_regime == 'elevated':
                confidence += 0.15
                strength += 0.1
                reasons.append("elevated_volatility")
            
            # Check for weak smart money bias (indicates trap)
            smart_money_bias = self._calculate_smart_money_bias(pcr, net_gamma)
            if abs(smart_money_bias) < self.weak_smart_money_threshold:
                confidence += 0.2
                strength += 0.15
                reasons.append("weak_smart_money_bias")
            elif smart_money_bias < -self.weak_smart_money_threshold:
                confidence += 0.15
                strength += 0.1
                reasons.append("bearish_smart_money_bias")
            
            # Check OI change (rapid OI changes can indicate trap setup)
            if abs(oi_change) > 1000:  # High OI velocity
                confidence += 0.15
                strength += 0.1
                reasons.append("high_oi_velocity")
            
            # Check net gamma (negative gamma can indicate trap)
            if net_gamma < -50000:
                confidence += 0.1
                strength += 0.1
                reasons.append("negative_gamma")
            
            logger.debug(f"Bull trap analysis: confidence={confidence:.3f}, strength={strength:.3f}, reasons={reasons}")
            
            return {
                'confidence': min(confidence, 1.0),
                'strength': min(strength, 1.0),
                'reason': '; '.join(reasons) if reasons else "no_bull_trap_indicators"
            }
            
        except Exception as e:
            logger.error(f"Bull trap detection error: {e}")
            return {'confidence': 0.0, 'strength': 0.0, 'reason': 'detection_error'}
    
    def _detect_bear_trap(self, spot_price: float, support: float, 
                         volatility_regime: str, pcr: float, net_gamma: float, 
                         oi_change: float) -> Dict[str, Any]:
        """
        Detect bear trap (false breakdown below support)
        """
        try:
            confidence = 0.0
            strength = 0.0
            reasons = []
            
            # FIX 5: Performance safety - avoid loops, use constant time operations
            # Check if price broke support
            support_distance = (support - spot_price) / support
            if support_distance > self.support_break_threshold:
                confidence += 0.3
                strength += 0.25
                reasons.append("price_broke_support")
            
            # Check for volatility spike
            if volatility_regime == 'extreme':
                confidence += 0.25
                strength += 0.2
                reasons.append("extreme_volatility")
            elif volatility_regime == 'elevated':
                confidence += 0.15
                strength += 0.1
                reasons.append("elevated_volatility")
            
            # Check for smart money accumulation (indicates trap)
            smart_money_bias = self._calculate_smart_money_bias(pcr, net_gamma)
            if abs(smart_money_bias) < self.weak_smart_money_threshold:
                confidence += 0.2
                strength += 0.15
                reasons.append("weak_smart_money_bias")
            elif smart_money_bias > self.weak_smart_money_threshold:
                confidence += 0.15
                strength += 0.1
                reasons.append("bullish_smart_money_bias")
            
            # Check OI change
            if abs(oi_change) > 1000:  # High OI velocity
                confidence += 0.15
                strength += 0.1
                reasons.append("high_oi_velocity")
            
            # Check net gamma (positive gamma can indicate trap)
            if net_gamma > 50000:
                confidence += 0.1
                strength += 0.1
                reasons.append("positive_gamma")
            
            logger.debug(f"Bear trap analysis: confidence={confidence:.3f}, strength={strength:.3f}, reasons={reasons}")
            
            return {
                'confidence': min(confidence, 1.0),
                'strength': min(strength, 1.0),
                'reason': '; '.join(reasons) if reasons else "no_bear_trap_indicators"
            }
            
        except Exception as e:
            logger.error(f"Bear trap detection error: {e}")
            return {'confidence': 0.0, 'strength': 0.0, 'reason': 'detection_error'}
    
    def _calculate_smart_money_bias(self, pcr: float, net_gamma: float) -> float:
        """
        Calculate smart money bias from PCR and net gamma
        
        Returns:
            float: -1 to 1 (negative = bearish, positive = bullish)
        """
        try:
            # FIX 5: Performance safety - constant time calculations
            # PCR bias (high PCR = bullish, low PCR = bearish)
            pcr_bias = (pcr - 1.0) / 1.0  # Normalize around 1.0
            pcr_bias = max(-1.0, min(1.0, pcr_bias))  # Clamp to [-1, 1]
            
            # Gamma bias (positive gamma = bullish, negative = bearish)
            gamma_bias = net_gamma / 100000.0  # Normalize by 100k
            gamma_bias = max(-1.0, min(1.0, gamma_bias))  # Clamp to [-1, 1]
            
            # Combined bias (weighted average)
            combined_bias = (pcr_bias * 0.6) + (gamma_bias * 0.4)
            
            return combined_bias
            
        except Exception as e:
            logger.error(f"Smart money bias calculation error: {e}")
            return 0.0
