"""
SmartMoneyEngine - Detects institutional positioning
Lightweight, optimized for Intel i5 CPU, 8GB RAM
"""

import logging
import time
from typing import Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SmartMoneySignal:
    """Smart money analysis result"""
    signal: str  # BULLISH | BEARISH | NEUTRAL
    confidence: float
    direction: str  # UP | DOWN | NONE
    strength: float
    reason: str

class SmartMoneyEngine:
    """
    Detects institutional positioning and smart money activity
    Analyzes OI patterns, flow, and positioning for institutional signals
    """
    
    def __init__(self):
        # Detection thresholds
        self.pcr_bullish_threshold = 1.3  # PCR > 1.3 suggests put writing (bullish)
        self.pcr_bearish_threshold = 0.7  # PCR < 0.7 suggests call writing (bearish)
        self.flow_imbalance_threshold = 0.25  # 25% flow imbalance
        self.oi_concentration_threshold = 0.3  # 30% OI concentration
        self.intent_score_threshold = 70  # High institutional intent
        
        # Production safety features
        self.last_signal_timestamp = 0
        self.cooldown_seconds = 3
        
        # Safe default output
        self.safe_default = {
            "signal": "NEUTRAL",
            "confidence": 0.0,
            "direction": "NONE",
            "strength": 0.0,
            "reason": "invalid_metrics"
        }
        
        logger.info("SmartMoneyEngine initialized")
    
    def analyze(self, live_metrics) -> Dict[str, Any]:
        """
        Analyze LiveMetrics for smart money positioning
        """
        try:
            # FIX 1: Metrics validation
            if not live_metrics:
                logger.debug("Empty metrics received")
                return self.safe_default
            
            # FIX 1: Safe field access with validation
            pcr = live_metrics.get("pcr") if isinstance(live_metrics, dict) else getattr(live_metrics, 'pcr', 1.0)
            if not pcr or pcr <= 0:
                logger.debug("Invalid or missing PCR")
                return self.safe_default
            
            flow_imbalance = live_metrics.get("flow_imbalance") if isinstance(live_metrics, dict) else getattr(live_metrics, 'flow_imbalance', 0)
            flow_direction = live_metrics.get("flow_direction") if isinstance(live_metrics, dict) else getattr(live_metrics, 'flow_direction', 'neutral')
            total_oi = live_metrics.get("total_oi") if isinstance(live_metrics, dict) else getattr(live_metrics, 'total_oi', 0)
            intent_score = live_metrics.get("intent_score") if isinstance(live_metrics, dict) else getattr(live_metrics, 'intent_score', 50)
            net_gamma = live_metrics.get("net_gamma") if isinstance(live_metrics, dict) else getattr(live_metrics, 'net_gamma', 0)
            volatility_regime = live_metrics.get("volatility_regime") if isinstance(live_metrics, dict) else getattr(live_metrics, 'volatility_regime', 'normal')
            
            # FIX 3: Signal cooldown mechanism
            current_time = time.time()
            if current_time - self.last_signal_timestamp < self.cooldown_seconds:
                logger.debug("Signal in cooldown period")
                return {
                    "signal": "NEUTRAL",
                    "confidence": 0.0,
                    "direction": "NONE",
                    "strength": 0.0,
                    "reason": "signal_cooldown"
                }
            
            # FIX 5: Performance safety - constant time calculations
            # Detect smart money patterns
            bullish_signals = self._detect_bullish_positioning(pcr, flow_direction, intent_score, net_gamma, volatility_regime)
            bearish_signals = self._detect_bearish_positioning(pcr, flow_direction, intent_score, net_gamma, volatility_regime)
            
            # Determine final signal
            if bullish_signals['confidence'] > bearish_signals['confidence'] and bullish_signals['confidence'] > 0.5:
                # FIX 3: Update timestamp for significant signals only
                self.last_signal_timestamp = current_time
                logger.info(f"Smart money BULLISH detected: {bullish_signals['reason']}")
                return {
                    "signal": "BULLISH",
                    "confidence": bullish_signals['confidence'],
                    "direction": "UP",
                    "strength": bullish_signals['confidence'],
                    "reason": bullish_signals['reason']
                }
            elif bearish_signals['confidence'] > bullish_signals['confidence'] and bearish_signals['confidence'] > 0.5:
                # FIX 3: Update timestamp for significant signals only
                self.last_signal_timestamp = current_time
                logger.info(f"Smart money BEARISH detected: {bearish_signals['reason']}")
                return {
                    "signal": "BEARISH",
                    "confidence": bearish_signals['confidence'],
                    "direction": "DOWN",
                    "strength": bearish_signals['confidence'],
                    "reason": bearish_signals['reason']
                }
            else:
                return {
                    "signal": "NEUTRAL",
                    "confidence": 0.0,
                    "direction": "NONE",
                    "strength": 0.0,
                    "reason": "no_smart_money_bias"
                }
                
        except Exception as e:
            # FIX 2: Safe default output on exceptions
            logger.error(f"SmartMoneyEngine analysis error: {e}")
            return self.safe_default
    
    def _detect_bullish_positioning(self, pcr: float, flow_direction: str, intent_score: float, net_gamma: float, volatility_regime: str) -> Dict[str, Any]:
        """Detect bullish institutional positioning"""
        try:
            confidence = 0.0
            reasons = []
            
            # FIX 5: Performance safety - avoid loops, use constant time operations
            # Check PCR for put writing dominance (bullish)
            if pcr > self.pcr_bullish_threshold:
                confidence += 0.3
                reasons.append("high_pcr_put_writing")
            elif pcr > 1.1:
                confidence += 0.15
                reasons.append("moderate_pcr")
            
            # Check flow direction for institutional buying
            if flow_direction == 'call':
                confidence += 0.2
                reasons.append("call_flow_dominance")
            
            # Check intent score
            if intent_score > self.intent_score_threshold:
                confidence += 0.25
                reasons.append("high_institutional_intent")
            elif intent_score > 60:
                confidence += 0.1
                reasons.append("elevated_intent")
            
            # Check net gamma for dealer positioning
            if net_gamma > 50000:  # Strong positive gamma
                confidence += 0.15
                reasons.append("positive_gamma")
            elif net_gamma > 20000:
                confidence += 0.05
                reasons.append("moderate_positive_gamma")
            
            # Check volatility regime (smart money often sells premium)
            if volatility_regime == 'normal':
                confidence += 0.1
                reasons.append("normal_volatility")
            
            logger.debug(f"Bullish positioning analysis: confidence={confidence:.3f}, reasons={reasons}")
            
            return {
                'confidence': min(confidence, 1.0),
                'reason': '; '.join(reasons) if reasons else "no_bullish_signals"
            }
            
        except Exception as e:
            logger.error(f"Bullish positioning detection error: {e}")
            return {'confidence': 0.0, 'reason': 'detection_error'}
    
    def _detect_bearish_positioning(self, pcr: float, flow_direction: str, intent_score: float, net_gamma: float, volatility_regime: str) -> Dict[str, Any]:
        """Detect bearish institutional positioning"""
        try:
            confidence = 0.0
            reasons = []
            
            # FIX 5: Performance safety - avoid loops, use constant time operations
            # Check PCR for call writing dominance (bearish)
            if pcr < self.pcr_bearish_threshold:
                confidence += 0.3
                reasons.append("low_pcr_call_writing")
            elif pcr < 0.9:
                confidence += 0.15
                reasons.append("moderate_pcr")
            
            # Check flow direction for institutional selling
            if flow_direction == 'put':
                confidence += 0.2
                reasons.append("put_flow_dominance")
            
            # Check intent score
            if intent_score > self.intent_score_threshold:
                confidence += 0.25
                reasons.append("high_institutional_intent")
            elif intent_score > 60:
                confidence += 0.1
                reasons.append("elevated_intent")
            
            # Check net gamma for dealer positioning
            if net_gamma < -50000:  # Strong negative gamma
                confidence += 0.15
                reasons.append("negative_gamma")
            elif net_gamma < -20000:
                confidence += 0.05
                reasons.append("moderate_negative_gamma")
            
            # Check volatility regime
            if volatility_regime == 'normal':
                confidence += 0.1
                reasons.append("normal_volatility")
            
            logger.debug(f"Bearish positioning analysis: confidence={confidence:.3f}, reasons={reasons}")
            
            return {
                'confidence': min(confidence, 1.0),
                'reason': '; '.join(reasons) if reasons else "no_bearish_signals"
            }
            
        except Exception as e:
            logger.error(f"Bearish positioning detection error: {e}")
            return {'confidence': 0.0, 'reason': 'detection_error'}
