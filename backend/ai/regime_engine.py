"""
Regime Engine - Detects market regime using market metrics
Lightweight, optimized for Intel i5 CPU, 8GB RAM
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class RegimeDetection:
    """Market regime detection result"""
    regime: str  # TREND, RANGE, BREAKOUT, MEAN_REVERSION, HIGH_VOLATILITY, LOW_VOLATILITY
    confidence: float  # 0.0 - 1.0
    reasoning: str  # Explanation of regime detection
    indicators: Dict[str, float]  # Key indicator values

class RegimeEngine:
    """
    Detects market regime based on LiveMetrics
    Uses gamma, PCR, expected_move, flow_imbalance, intent_score
    """
    
    def __init__(self):
        # Regime detection thresholds
        self.thresholds = {
            'trend_strength': 0.6,
            'range_bound': 0.4,
            'breakout_momentum': 0.7,
            'mean_reversion_strength': 0.65,
            'high_volatility_threshold': 25,
            'low_volatility_threshold': 12
        }
        
        # Indicator weights for regime calculation
        self.regime_weights = {
            'TREND': {
                'gamma_regime': 0.3,
                'flow_direction': 0.25,
                'intent_score': 0.2,
                'pcr_trend': 0.15,
                'breach_probability': 0.1
            },
            'RANGE': {
                'breach_probability': 0.3,
                'expected_move_ratio': 0.25,
                'gamma_regime': 0.2,
                'flow_balance': 0.15,
                'volatility_regime': 0.1
            },
            'BREAKOUT': {
                'breach_probability': 0.3,
                'volume_spike': 0.25,
                'volatility_expansion': 0.2,
                'flow_intensity': 0.15,
                'expected_move_expansion': 0.1
            },
            'MEAN_REVERSION': {
                'gamma_regime': 0.35,
                'extreme_pcr': 0.25,
                'volatility_contraction': 0.2,
                'support_resistance_proximity': 0.15,
                'flow_exhaustion': 0.05
            },
            'HIGH_VOLATILITY': {
                'volatility_regime': 0.4,
                'expected_move_expansion': 0.3,
                'volume_intensity': 0.2,
                'gamma_instability': 0.1
            },
            'LOW_VOLATILITY': {
                'volatility_regime': 0.4,
                'expected_move_contraction': 0.3,
                'volume_suppression': 0.2,
                'gamma_stability': 0.1
            }
        }
    
    def detect_regime(self, metrics) -> RegimeDetection:
        """
        Detect current market regime from LiveMetrics
        """
        try:
            # Extract key indicators
            indicators = self._extract_indicators(metrics)
            
            # Calculate regime scores
            regime_scores = {}
            
            for regime_name, weights in self.regime_weights.items():
                score = self._calculate_regime_score(regime_name, indicators, weights)
                regime_scores[regime_name] = score
            
            # Find best regime
            best_regime = max(regime_scores.items(), key=lambda x: x[1])
            regime_name = best_regime[0]
            confidence = best_regime[1]
            
            # Generate reasoning
            reasoning = self._generate_regime_reasoning(regime_name, indicators, confidence)
            
            # Apply minimum confidence threshold
            if confidence < 0.5:
                regime_name = "RANGE"  # Default to range if confidence low
                confidence = 0.5
                reasoning = "Low confidence in specific regime, defaulting to range-bound"
            
            return RegimeDetection(
                regime=regime_name,
                confidence=confidence,
                reasoning=reasoning,
                indicators=indicators
            )
            
        except Exception as e:
            logger.error(f"Regime detection error: {e}")
            return RegimeDetection(
                regime="RANGE",
                confidence=0.5,
                reason="Regime detection error, defaulting to range",
                indicators={}
            )
    
    def _extract_indicators(self, metrics) -> Dict[str, float]:
        """Extract and normalize key indicators from LiveMetrics"""
        try:
            indicators = {}
            
            # Gamma regime indicator
            gamma_regime = getattr(metrics, 'gamma_regime', 'neutral')
            indicators['gamma_regime'] = {
                'positive': 0.8,
                'negative': -0.8,
                'neutral': 0.0
            }.get(gamma_regime, 0.0)
            
            # PCR indicator
            pcr = getattr(metrics, 'pcr', 1.0)
            indicators['pcr_value'] = pcr
            indicators['pcr_trend'] = (pcr - 1.0) / 1.0  # Normalize around 1.0
            
            # Expected move indicator
            expected_move = getattr(metrics, 'expected_move', 0)
            spot = getattr(metrics, 'spot', 1)
            if spot > 0:
                expected_move_ratio = expected_move / spot
                indicators['expected_move_ratio'] = min(expected_move_ratio / 0.03, 1.0)  # Normalize to 3% as max
            else:
                indicators['expected_move_ratio'] = 0.5
            
            # Flow imbalance indicator
            flow_imbalance = getattr(metrics, 'flow_imbalance', 0)
            indicators['flow_imbalance'] = abs(flow_imbalance)
            
            flow_direction = getattr(metrics, 'flow_direction', 'neutral')
            indicators['flow_direction'] = {
                'call': 0.8,
                'put': -0.8,
                'neutral': 0.0
            }.get(flow_direction, 0.0)
            
            # Intent score indicator
            intent_score = getattr(metrics, 'intent_score', 50)
            indicators['intent_score'] = intent_score / 100.0  # Normalize to 0-1
            
            # Breach probability indicator
            breach_probability = getattr(metrics, 'breach_probability', 37)
            indicators['breach_probability'] = breach_probability / 100.0
            
            # Volatility regime indicator
            volatility_regime = getattr(metrics, 'volatility_regime', 'normal')
            volatility_map = {
                'low': 0.2,
                'normal': 0.5,
                'elevated': 0.75,
                'extreme': 0.95
            }
            indicators['volatility_regime'] = volatility_map.get(volatility_regime, 0.5)
            
            # Distance from flip indicator
            distance_from_flip = getattr(metrics, 'distance_from_flip', 0)
            spot = getattr(metrics, 'spot', 1)
            if spot > 0 and distance_from_flip is not None:
                indicators['gamma_flip_proximity'] = 1.0 - min(abs(distance_from_flip) / spot / 0.02, 1.0)
            else:
                indicators['gamma_flip_proximity'] = 0.5
            
            # Support/Resistance proximity
            support_level = getattr(metrics, 'support_level', 0)
            resistance_level = getattr(metrics, 'resistance_level', 0)
            if support_level > 0 and resistance_level > 0 and spot > 0:
                support_distance = abs(spot - support_level) / spot
                resistance_distance = abs(resistance_level - spot) / spot
                indicators['support_resistance_proximity'] = 1.0 - min((support_distance + resistance_distance) / 2 / 0.03, 1.0)
            else:
                indicators['support_resistance_proximity'] = 0.5
            
            # Volume intensity (proxy via intent score)
            indicators['volume_intensity'] = indicators['intent_score']
            
            # Flow balance
            indicators['flow_balance'] = 1.0 - indicators['flow_imbalance']
            
            # Flow intensity
            indicators['flow_intensity'] = indicators['flow_imbalance']
            
            # Gamma stability (inverse of flip proximity)
            indicators['gamma_stability'] = 1.0 - indicators['gamma_flip_proximity']
            
            # Gamma instability
            indicators['gamma_instability'] = indicators['gamma_flip_proximity']
            
            return indicators
            
        except Exception as e:
            logger.error(f"Indicator extraction error: {e}")
            return {}
    
    def _calculate_regime_score(self, regime_name: str, indicators: Dict[str, float], weights: Dict[str, float]) -> float:
        """Calculate regime score based on weighted indicators"""
        try:
            score = 0.0
            total_weight = 0.0
            
            for indicator_name, weight in weights.items():
                if indicator_name in indicators:
                    indicator_value = indicators[indicator_name]
                    
                    # Apply regime-specific logic
                    if regime_name == "TREND":
                        if indicator_name == 'gamma_regime':
                            # Positive gamma supports trend
                            score += weight * max(0, indicator_value)
                        elif indicator_name == 'flow_direction':
                            # Strong directional flow supports trend
                            score += weight * abs(indicator_value)
                        elif indicator_name == 'intent_score':
                            # High institutional intent supports trend
                            score += weight * indicator_value
                        elif indicator_name == 'pcr_trend':
                            # Strong PCR bias supports trend
                            score += weight * abs(indicator_value)
                        elif indicator_name == 'breach_probability':
                            # Higher breach probability supports trend
                            score += weight * indicator_value
                    
                    elif regime_name == "RANGE":
                        if indicator_name == 'breach_probability':
                            # Low breach probability supports range
                            score += weight * (1.0 - indicator_value)
                        elif indicator_name == 'expected_move_ratio':
                            # Low expected move supports range
                            score += weight * (1.0 - indicator_value)
                        elif indicator_name == 'gamma_regime':
                            # Neutral gamma supports range
                            score += weight * (1.0 - abs(indicator_value))
                        elif indicator_name == 'flow_balance':
                            # Balanced flow supports range
                            score += weight * indicator_value
                        elif indicator_name == 'volatility_regime':
                            # Normal volatility supports range
                            score += weight * (1.0 - abs(indicator_value - 0.5))
                    
                    elif regime_name == "BREAKOUT":
                        if indicator_name == 'breach_probability':
                            # High breach probability supports breakout
                            score += weight * indicator_value
                        elif indicator_name == 'volume_intensity':
                            # High volume supports breakout
                            score += weight * indicator_value
                        elif indicator_name == 'volatility_regime':
                            # Elevated volatility supports breakout
                            score += weight * indicator_value
                        elif indicator_name == 'flow_intensity':
                            # Strong flow supports breakout
                            score += weight * indicator_value
                        elif indicator_name == 'expected_move_ratio':
                            # Expanding expected move supports breakout
                            score += weight * indicator_value
                    
                    elif regime_name == "MEAN_REVERSION":
                        if indicator_name == 'gamma_regime':
                            # Positive gamma supports mean reversion
                            score += weight * max(0, indicator_value)
                        elif indicator_name == 'pcr_trend':
                            # Extreme PCR supports mean reversion
                            score += weight * abs(indicator_value)
                        elif indicator_name == 'volatility_regime':
                            # Low volatility supports mean reversion
                            score += weight * (1.0 - indicator_value)
                        elif indicator_name == 'support_resistance_proximity':
                            # Near S/R supports mean reversion
                            score += weight * indicator_value
                        elif indicator_name == 'flow_intensity':
                            # Low flow intensity supports mean reversion
                            score += weight * (1.0 - indicator_value)
                    
                    elif regime_name == "HIGH_VOLATILITY":
                        if indicator_name == 'volatility_regime':
                            # High volatility regime
                            score += weight * indicator_value
                        elif indicator_name == 'expected_move_ratio':
                            # High expected move
                            score += weight * indicator_value
                        elif indicator_name == 'volume_intensity':
                            # High volume
                            score += weight * indicator_value
                        elif indicator_name == 'gamma_instability':
                            # Gamma instability
                            score += weight * indicator_value
                    
                    elif regime_name == "LOW_VOLATILITY":
                        if indicator_name == 'volatility_regime':
                            # Low volatility regime
                            score += weight * (1.0 - indicator_value)
                        elif indicator_name == 'expected_move_ratio':
                            # Low expected move
                            score += weight * (1.0 - indicator_value)
                        elif indicator_name == 'volume_intensity':
                            # Low volume
                            score += weight * (1.0 - indicator_value)
                        elif indicator_name == 'gamma_stability':
                            # Gamma stability
                            score += weight * indicator_value
                    
                    total_weight += weight
            
            if total_weight > 0:
                return score / total_weight
            else:
                return 0.5
                
        except Exception as e:
            logger.error(f"Regime score calculation error: {e}")
            return 0.5
    
    def _generate_regime_reasoning(self, regime_name: str, indicators: Dict[str, float], confidence: float) -> str:
        """Generate human-readable reasoning for regime detection"""
        try:
            reasoning_parts = []
            
            if regime_name == "TREND":
                if indicators.get('gamma_regime', 0) > 0.5:
                    reasoning_parts.append("Positive gamma indicates trend persistence")
                if indicators.get('flow_direction', 0) > 0.5:
                    reasoning_parts.append("Strong call flow supports uptrend")
                elif indicators.get('flow_direction', 0) < -0.5:
                    reasoning_parts.append("Strong put flow supports downtrend")
                if indicators.get('intent_score', 0) > 0.7:
                    reasoning_parts.append("High institutional intent confirms trend")
            
            elif regime_name == "RANGE":
                if indicators.get('breach_probability', 0.5) < 0.3:
                    reasoning_parts.append("Low breach probability suggests range-bound")
                if indicators.get('expected_move_ratio', 0.5) < 0.5:
                    reasoning_parts.append("Modest expected move supports range")
                if abs(indicators.get('gamma_regime', 0)) < 0.3:
                    reasoning_parts.append("Neutral gamma indicates range")
            
            elif regime_name == "BREAKOUT":
                if indicators.get('breach_probability', 0.5) > 0.6:
                    reasoning_parts.append("High breakout probability detected")
                if indicators.get('volume_intensity', 0.5) > 0.7:
                    reasoning_parts.append("Volume surge supports breakout")
                if indicators.get('volatility_regime', 0.5) > 0.7:
                    reasoning_parts.append("Elevated volatility precedes breakout")
            
            elif regime_name == "MEAN_REVERSION":
                if indicators.get('gamma_regime', 0) > 0.5:
                    reasoning_parts.append("Positive gamma suggests mean reversion")
                if abs(indicators.get('pcr_trend', 0)) > 0.3:
                    reasoning_parts.append("Extreme PCR indicates reversal potential")
                if indicators.get('support_resistance_proximity', 0.5) > 0.6:
                    reasoning_parts.append("Near key support/resistance levels")
            
            elif regime_name == "HIGH_VOLATILITY":
                if indicators.get('volatility_regime', 0.5) > 0.8:
                    reasoning_parts.append("Extreme volatility regime detected")
                if indicators.get('expected_move_ratio', 0.5) > 0.7:
                    reasoning_parts.append("Expanding expected move")
                if indicators.get('volume_intensity', 0.5) > 0.7:
                    reasoning_parts.append("High volume activity")
            
            elif regime_name == "LOW_VOLATILITY":
                if indicators.get('volatility_regime', 0.5) < 0.3:
                    reasoning_parts.append("Low volatility environment")
                if indicators.get('expected_move_ratio', 0.5) < 0.3:
                    reasoning_parts.append("Contracted expected move")
                if indicators.get('volume_intensity', 0.5) < 0.3:
                    reasoning_parts.append("Suppressed volume activity")
            
            # Add confidence level
            reasoning_parts.append(f"Confidence: {confidence:.1%}")
            
            return "; ".join(reasoning_parts) if reasoning_parts else f"Regime detected with {confidence:.1%} confidence"
            
        except Exception as e:
            logger.error(f"Regime reasoning generation error: {e}")
            return f"Regime: {regime_name} with {confidence:.1%} confidence"
