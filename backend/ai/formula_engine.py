"""
Formula Engine - Generates 10 formula signals from LiveMetrics
Lightweight, optimized for Intel i5 CPU, 8GB RAM
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class FormulaSignal:
    """Single formula signal output"""
    signal: str  # BUY, SELL, HOLD
    confidence: float  # 0.0 - 1.0
    reason: str  # Human readable explanation

class FormulaEngine:
    """
    Generates 10 formula signals from LiveMetrics
    Each formula analyzes specific market conditions
    """
    
    def __init__(self):
        self.formulas = {
            "F01": self._pcr_signal,
            "F02": self._oi_imbalance_signal,
            "F03": self._gamma_regime_signal,
            "F04": self._volume_spike_signal,
            "F05": self._expected_move_breakout_signal,
            "F06": self._delta_imbalance_signal,
            "F07": self._volatility_expansion_signal,
            "F08": self._oi_velocity_signal,
            "F09": self._gamma_flip_proximity_signal,
            "F10": self._flow_imbalance_signal
        }
    
    def analyze(self, metrics) -> Dict[str, FormulaSignal]:
        """
        Run all 10 formulas on LiveMetrics
        Returns dict of formula_id -> FormulaSignal
        """
        signals = {}
        
        try:
            for formula_id, formula_func in self.formulas.items():
                signal = formula_func(metrics)
                signals[formula_id] = signal
                
        except Exception as e:
            logger.error(f"FormulaEngine analysis error: {e}")
            # Return neutral signals on error
            for formula_id in self.formulas.keys():
                signals[formula_id] = FormulaSignal(
                    signal="HOLD",
                    confidence=0.0,
                    reason="Analysis error"
                )
        
        return signals
    
    def _pcr_signal(self, metrics) -> FormulaSignal:
        """F01: PCR signal - analyzes Put-Call Ratio"""
        try:
            pcr = metrics.pcr
            
            if pcr > 1.3:
                return FormulaSignal(
                    signal="BUY",
                    confidence=0.75,
                    reason=f"PCR bullish at {pcr:.2f}, put writing dominant"
                )
            elif pcr < 0.7:
                return FormulaSignal(
                    signal="SELL",
                    confidence=0.75,
                    reason=f"PCR bearish at {pcr:.2f}, call writing dominant"
                )
            elif pcr > 1.1:
                return FormulaSignal(
                    signal="BUY",
                    confidence=0.60,
                    reason=f"PCR moderately bullish at {pcr:.2f}"
                )
            elif pcr < 0.9:
                return FormulaSignal(
                    signal="SELL",
                    confidence=0.60,
                    reason=f"PCR moderately bearish at {pcr:.2f}"
                )
            else:
                return FormulaSignal(
                    signal="HOLD",
                    confidence=0.50,
                    reason=f"PCR neutral at {pcr:.2f}"
                )
                
        except Exception as e:
            logger.error(f"F01 PCR signal error: {e}")
            return FormulaSignal("HOLD", 0.0, "PCR analysis error")
    
    def _oi_imbalance_signal(self, metrics) -> FormulaSignal:
        """F02: OI imbalance signal - analyzes call/put OI distribution"""
        try:
            # Use total_oi and pcr to derive call/put OI
            total_oi = metrics.total_oi
            pcr = metrics.pcr
            
            if pcr > 0 and total_oi > 0:
                put_oi = total_oi * pcr / (1 + pcr)
                call_oi = total_oi / (1 + pcr)
                
                if total_oi > 0:
                    imbalance = abs(call_oi - put_oi) / total_oi
                    
                    if imbalance > 0.4:
                        direction = "BUY" if put_oi > call_oi else "SELL"
                        confidence = min(0.80, 0.50 + imbalance)
                        
                        return FormulaSignal(
                            signal=direction,
                            confidence=confidence,
                            reason=f"Strong OI imbalance ({imbalance:.1%}), {'put' if put_oi > call_oi else 'call'} dominant"
                        )
                    elif imbalance > 0.25:
                        direction = "BUY" if put_oi > call_oi else "SELL"
                        
                        return FormulaSignal(
                            signal=direction,
                            confidence=0.65,
                            reason=f"Moderate OI imbalance ({imbalance:.1%})"
                        )
            
            return FormulaSignal(
                signal="HOLD",
                confidence=0.50,
                reason="OI balance neutral"
            )
            
        except Exception as e:
            logger.error(f"F02 OI imbalance signal error: {e}")
            return FormulaSignal("HOLD", 0.0, "OI imbalance analysis error")
    
    def _gamma_regime_signal(self, metrics) -> FormulaSignal:
        """F03: Gamma regime signal - analyzes gamma exposure"""
        try:
            gamma_regime = getattr(metrics, 'gamma_regime', 'neutral')
            net_gamma = getattr(metrics, 'net_gamma', 0)
            
            if gamma_regime == "positive":
                return FormulaSignal(
                    signal="BUY",
                    confidence=0.70,
                    reason=f"Positive gamma regime ({net_gamma:.0f}), dealer support likely"
                )
            elif gamma_regime == "negative":
                return FormulaSignal(
                    signal="SELL",
                    confidence=0.70,
                    reason=f"Negative gamma regime ({net_gamma:.0f}), trend acceleration"
                )
            else:
                return FormulaSignal(
                    signal="HOLD",
                    confidence=0.50,
                    reason=f"Neutral gamma regime ({net_gamma:.0f})"
                )
                
        except Exception as e:
            logger.error(f"F03 gamma regime signal error: {e}")
            return FormulaSignal("HOLD", 0.0, "Gamma regime analysis error")
    
    def _volume_spike_signal(self, metrics) -> FormulaSignal:
        """F04: Volume spike signal - analyzes unusual volume activity"""
        try:
            # Use intent_score as proxy for volume activity
            intent_score = metrics.intent_score
            
            if intent_score > 80:
                return FormulaSignal(
                    signal="HOLD",  # Volume spike alone doesn't indicate direction
                    confidence=0.75,
                    reason=f"High volume activity detected (intent: {intent_score})"
                )
            elif intent_score > 65:
                return FormulaSignal(
                    signal="HOLD",
                    confidence=0.60,
                    reason=f"Moderate volume activity (intent: {intent_score})"
                )
            else:
                return FormulaSignal(
                    signal="HOLD",
                    confidence=0.50,
                    reason=f"Normal volume activity (intent: {intent_score})"
                )
                
        except Exception as e:
            logger.error(f"F04 volume spike signal error: {e}")
            return FormulaSignal("HOLD", 0.0, "Volume spike analysis error")
    
    def _expected_move_breakout_signal(self, metrics) -> FormulaSignal:
        """F05: Expected move breakout signal - analyzes price vs expected ranges"""
        try:
            spot = metrics.spot
            upper_1sd = metrics.upper_1sd
            lower_1sd = metrics.lower_1sd
            breach_probability = metrics.breach_probability
            
            # Check if price is near range boundaries
            upper_distance = (upper_1sd - spot) / spot
            lower_distance = (spot - lower_1sd) / spot
            
            if upper_distance < 0.01:  # Within 1% of upper bound
                return FormulaSignal(
                    signal="SELL",
                    confidence=0.65,
                    reason=f"Near upper expected move ({upper_distance:.1%}), potential rejection"
                )
            elif lower_distance < 0.01:  # Within 1% of lower bound
                return FormulaSignal(
                    signal="BUY",
                    confidence=0.65,
                    reason=f"Near lower expected move ({lower_distance:.1%}), potential support"
                )
            elif breach_probability > 60:
                return FormulaSignal(
                    signal="HOLD",
                    confidence=0.60,
                    reason=f"High breakout probability ({breach_probability:.0f}%)"
                )
            else:
                return FormulaSignal(
                    signal="HOLD",
                    confidence=0.50,
                    reason=f"Within expected range (breach prob: {breach_probability:.0f}%)"
                )
                
        except Exception as e:
            logger.error(f"F05 expected move breakout signal error: {e}")
            return FormulaSignal("HOLD", 0.0, "Expected move analysis error")
    
    def _delta_imbalance_signal(self, metrics) -> FormulaSignal:
        """F06: Delta imbalance signal - analyzes directional pressure"""
        try:
            # Use flow_imbalance and flow_direction as delta proxies
            flow_imbalance = getattr(metrics, 'flow_imbalance', 0)
            flow_direction = getattr(metrics, 'flow_direction', 'neutral')
            
            if abs(flow_imbalance) > 0.3:
                if flow_direction == "call":
                    return FormulaSignal(
                        signal="BUY",
                        confidence=0.70,
                        reason=f"Strong call flow imbalance ({flow_imbalance:.1%})"
                    )
                elif flow_direction == "put":
                    return FormulaSignal(
                        signal="SELL",
                        confidence=0.70,
                        reason=f"Strong put flow imbalance ({flow_imbalance:.1%})"
                    )
            elif abs(flow_imbalance) > 0.15:
                if flow_direction == "call":
                    return FormulaSignal(
                        signal="BUY",
                        confidence=0.60,
                        reason=f"Moderate call flow ({flow_imbalance:.1%})"
                    )
                elif flow_direction == "put":
                    return FormulaSignal(
                        signal="SELL",
                        confidence=0.60,
                        reason=f"Moderate put flow ({flow_imbalance:.1%})"
                    )
            
            return FormulaSignal(
                signal="HOLD",
                confidence=0.50,
                reason=f"Flow balance neutral ({flow_imbalance:.1%})"
            )
            
        except Exception as e:
            logger.error(f"F06 delta imbalance signal error: {e}")
            return FormulaSignal("HOLD", 0.0, "Delta imbalance analysis error")
    
    def _volatility_expansion_signal(self, metrics) -> FormulaSignal:
        """F07: Volatility expansion signal - analyzes volatility regime"""
        try:
            volatility_regime = metrics.volatility_regime
            
            if volatility_regime == "extreme":
                return FormulaSignal(
                    signal="HOLD",  # High volatility = uncertain direction
                    confidence=0.75,
                    reason="Extreme volatility regime - high uncertainty"
                )
            elif volatility_regime == "elevated":
                return FormulaSignal(
                    signal="HOLD",
                    confidence=0.65,
                    reason="Elevated volatility regime"
                )
            elif volatility_regime == "low":
                return FormulaSignal(
                    signal="HOLD",
                    confidence=0.60,
                    reason="Low volatility regime - potential breakout setup"
                )
            else:
                return FormulaSignal(
                    signal="HOLD",
                    confidence=0.50,
                    reason="Normal volatility regime"
                )
                
        except Exception as e:
            logger.error(f"F07 volatility expansion signal error: {e}")
            return FormulaSignal("HOLD", 0.0, "Volatility analysis error")
    
    def _oi_velocity_signal(self, metrics) -> FormulaSignal:
        """F08: OI velocity signal - analyzes rate of OI change"""
        try:
            oi_velocity = getattr(metrics, 'oi_velocity', 0)
            call_oi_velocity = getattr(metrics, 'call_oi_velocity', 0)
            put_oi_velocity = getattr(metrics, 'put_oi_velocity', 0)
            
            # Check for significant OI velocity
            if abs(oi_velocity) > 1000:  # High velocity threshold
                if oi_velocity > 0:
                    return FormulaSignal(
                        signal="HOLD",
                        confidence=0.65,
                        reason=f"High OI accumulation (+{oi_velocity:.0f})"
                    )
                else:
                    return FormulaSignal(
                        signal="HOLD",
                        confidence=0.65,
                        reason=f"High OI unwinding ({oi_velocity:.0f})"
                    )
            elif call_oi_velocity > 500:
                return FormulaSignal(
                    signal="SELL",
                    confidence=0.60,
                    reason=f"Call OI building (+{call_oi_velocity:.0f})"
                )
            elif put_oi_velocity > 500:
                return FormulaSignal(
                    signal="BUY",
                    confidence=0.60,
                    reason=f"Put OI building (+{put_oi_velocity:.0f})"
                )
            
            return FormulaSignal(
                signal="HOLD",
                confidence=0.50,
                reason="OI velocity normal"
            )
            
        except Exception as e:
            logger.error(f"F08 OI velocity signal error: {e}")
            return FormulaSignal("HOLD", 0.0, "OI velocity analysis error")
    
    def _gamma_flip_proximity_signal(self, metrics) -> FormulaSignal:
        """F09: Gamma flip proximity signal - analyzes distance to gamma flip level"""
        try:
            distance_from_flip = getattr(metrics, 'distance_from_flip', None)
            gamma_flip_level = getattr(metrics, 'gamma_flip_level', None)
            
            if distance_from_flip is None or gamma_flip_level is None:
                return FormulaSignal("HOLD", 0.50, "Gamma flip level unknown")
            
            # Convert distance to percentage of spot
            spot = metrics.spot
            distance_pct = abs(distance_from_flip) / spot if spot > 0 else 1
            
            if distance_pct < 0.005:  # Within 0.5% of flip level
                return FormulaSignal(
                    signal="HOLD",  # Near flip level = high uncertainty
                    confidence=0.75,
                    reason=f"Very close to gamma flip level ({distance_pct:.1%})"
                )
            elif distance_pct < 0.02:  # Within 2% of flip level
                return FormulaSignal(
                    signal="HOLD",
                    confidence=0.65,
                    reason=f"Near gamma flip zone ({distance_pct:.1%})"
                )
            else:
                return FormulaSignal(
                    signal="HOLD",
                    confidence=0.50,
                    reason=f"Clear of gamma flip level ({distance_pct:.1%})"
                )
                
        except Exception as e:
            logger.error(f"F09 gamma flip proximity signal error: {e}")
            return FormulaSignal("HOLD", 0.0, "Gamma flip analysis error")
    
    def _flow_imbalance_signal(self, metrics) -> FormulaSignal:
        """F10: Flow imbalance signal - analyzes order flow imbalance"""
        try:
            flow_imbalance = getattr(metrics, 'flow_imbalance', 0)
            flow_direction = getattr(metrics, 'flow_direction', 'neutral')
            
            if abs(flow_imbalance) > 0.4:
                if flow_direction == "call":
                    return FormulaSignal(
                        signal="BUY",
                        confidence=0.75,
                        reason=f"Extreme call flow imbalance ({flow_imbalance:.1%})"
                    )
                elif flow_direction == "put":
                    return FormulaSignal(
                        signal="SELL",
                        confidence=0.75,
                        reason=f"Extreme put flow imbalance ({flow_imbalance:.1%})"
                    )
            elif abs(flow_imbalance) > 0.2:
                if flow_direction == "call":
                    return FormulaSignal(
                        signal="BUY",
                        confidence=0.65,
                        reason=f"Strong call flow ({flow_imbalance:.1%})"
                    )
                elif flow_direction == "put":
                    return FormulaSignal(
                        signal="SELL",
                        confidence=0.65,
                        reason=f"Strong put flow ({flow_imbalance:.1%})"
                    )
            
            return FormulaSignal(
                signal="HOLD",
                confidence=0.50,
                reason=f"Flow balanced ({flow_imbalance:.1%})"
            )
            
        except Exception as e:
            logger.error(f"F10 flow imbalance signal error: {e}")
            return FormulaSignal("HOLD", 0.0, "Flow imbalance analysis error")
