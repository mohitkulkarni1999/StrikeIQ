"""
Entry Exit Engine - Determines entry, target, and stoploss prices
Lightweight, optimized for Intel i5 CPU, 8GB RAM
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import math

logger = logging.getLogger(__name__)

@dataclass
class EntryExitLevels:
    """Entry, target, and stoploss levels"""
    entry_price: float
    target_price: float
    stoploss_price: float
    risk_reward_ratio: float
    confidence: float
    reasoning: str

class EntryExitEngine:
    """
    Determines optimal entry, target, and stoploss prices
    Ensures minimum 1:2 risk/reward ratio and avoids stoploss hunt zones
    """
    
    def __init__(self):
        # Risk management parameters
        self.min_risk_reward_ratio = 2.0  # Minimum 1:2 risk/reward
        self.default_stoploss_pct = 0.25  # 25% of premium as stoploss
        self.default_target_pct = 0.50   # 50% of premium as target
        self.stoploss_buffer_pct = 0.005  # 0.5% buffer to avoid hunt zones
        
        # Option pricing parameters
        self.min_premium = 20.0  # Minimum premium to consider
        self.max_premium = 500.0  # Maximum premium to consider
        self.contract_multiplier = 75  # NFO contract multiplier
    
    def calculate_levels(self, strike: float, option_type: str, metrics, 
                        market_bias: str, regime: str) -> EntryExitLevels:
        """
        Calculate entry, target, and stoploss levels
        """
        try:
            # Estimate option premium
            premium = self._estimate_option_premium(strike, option_type, metrics)
            
            if premium < self.min_premium or premium > self.max_premium:
                return EntryExitLevels(
                    entry_price=0,
                    target_price=0,
                    stoploss_price=0,
                    risk_reward_ratio=0,
                    confidence=0,
                    reasoning=f"Premium {premium:.2f} outside acceptable range [{self.min_premium}, {self.max_premium}]"
                )
            
            # Calculate base levels
            entry_price = premium
            base_stoploss = premium * (1 - self.default_stoploss_pct)
            base_target = premium * (1 + self.default_target_pct)
            
            # Adjust levels based on market conditions
            adjusted_stoploss = self._adjust_stoploss(base_stoploss, strike, option_type, metrics, market_bias)
            adjusted_target = self._adjust_target(base_target, strike, option_type, metrics, regime)
            
            # Ensure minimum risk/reward ratio
            final_target, final_stoploss = self._ensure_risk_reward(
                entry_price, adjusted_target, adjusted_stoploss
            )
            
            # Calculate final risk/reward ratio
            risk = abs(entry_price - final_stoploss)
            reward = abs(final_target - entry_price)
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            # Calculate confidence based on risk/reward and market conditions
            confidence = self._calculate_confidence(risk_reward_ratio, metrics, market_bias, regime)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                entry_price, final_target, final_stoploss, risk_reward_ratio,
                strike, option_type, metrics, market_bias, regime
            )
            
            return EntryExitLevels(
                entry_price=round(entry_price, 2),
                target_price=round(final_target, 2),
                stoploss_price=round(final_stoploss, 2),
                risk_reward_ratio=risk_reward_ratio,
                confidence=confidence,
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"Entry/exit calculation error: {e}")
            return EntryExitLevels(
                entry_price=0,
                target_price=0,
                stoploss_price=0,
                risk_reward_ratio=0,
                confidence=0,
                reasoning="Error in entry/exit calculation"
            )
    
    def _estimate_option_premium(self, strike: float, option_type: str, metrics) -> float:
        """Estimate option premium based on market conditions"""
        try:
            spot = metrics.spot
            
            # Calculate intrinsic value
            if option_type == "CE":
                intrinsic_value = max(0, spot - strike)
            else:  # PE
                intrinsic_value = max(0, strike - spot)
            
            # Calculate time value
            expected_move = getattr(metrics, 'expected_move', spot * 0.02)
            volatility_regime = getattr(metrics, 'volatility_regime', 'normal')
            
            # Volatility multiplier
            vol_multipliers = {
                'low': 0.8,
                'normal': 1.0,
                'elevated': 1.3,
                'extreme': 1.6
            }
            vol_multiplier = vol_multipliers.get(volatility_regime, 1.0)
            
            # Distance from strike affects time value
            distance_pct = abs(strike - spot) / spot
            time_value = expected_move * vol_multiplier * math.exp(-distance_pct * 3)
            
            # Adjust for gamma regime
            gamma_regime = getattr(metrics, 'gamma_regime', 'neutral')
            if gamma_regime == "positive":
                time_value *= 1.1  # Positive gamma increases time value
            elif gamma_regime == "negative":
                time_value *= 0.9  # Negative gamma decreases time value
            
            # Total premium
            premium = intrinsic_value + time_value
            
            # Ensure reasonable bounds
            return max(self.min_premium, min(premium, self.max_premium))
            
        except Exception as e:
            logger.error(f"Premium estimation error: {e}")
            return self.min_premium * 2  # Conservative default
    
    def _adjust_stoploss(self, base_stoploss: float, strike: float, option_type: str, 
                        metrics, market_bias: str) -> float:
        """Adjust stoploss to avoid hunt zones and use support/resistance"""
        try:
            adjusted_stoploss = base_stoploss
            
            # Get support/resistance levels
            support_level = getattr(metrics, 'support_level', 0)
            resistance_level = getattr(metrics, 'resistance_level', 0)
            spot = metrics.spot
            
            # For call options, consider support levels
            if option_type == "CE" and support_level > 0:
                # Calculate option value at support level
                support_distance = (spot - support_level) / spot
                if support_distance > 0.02:  # Support is at least 2% away
                    # Option would lose value if spot drops to support
                    support_option_value = self._estimate_option_premium(strike, option_type, metrics) * (1 - support_distance * 10)
                    adjusted_stoploss = max(adjusted_stoploss, support_option_value)
            
            # For put options, consider resistance levels
            elif option_type == "PE" and resistance_level > 0:
                # Calculate option value at resistance level
                resistance_distance = (resistance_level - spot) / spot
                if resistance_distance > 0.02:  # Resistance is at least 2% away
                    # Option would lose value if spot rises to resistance
                    resistance_option_value = self._estimate_option_premium(strike, option_type, metrics) * (1 - resistance_distance * 10)
                    adjusted_stoploss = max(adjusted_stoploss, resistance_option_value)
            
            # Add buffer to avoid stoploss hunt zones
            buffer_amount = adjusted_stoploss * self.stoploss_buffer_pct
            adjusted_stoploss -= buffer_amount
            
            # Ensure stoploss is not too low
            min_stoploss = base_stoploss * 0.5  # Don't reduce below 50% of base
            adjusted_stoploss = max(adjusted_stoploss, min_stoploss)
            
            return adjusted_stoploss
            
        except Exception as e:
            logger.error(f"Stoploss adjustment error: {e}")
            return base_stoploss
    
    def _adjust_target(self, base_target: float, strike: float, option_type: str, 
                      metrics, regime: str) -> float:
        """Adjust target based on market regime and expected move"""
        try:
            adjusted_target = base_target
            
            # Adjust based on regime
            if regime == "TREND":
                # Trend following - higher targets
                adjusted_target *= 1.2
            elif regime == "BREAKOUT":
                # Breakout - higher targets
                adjusted_target *= 1.3
            elif regime == "RANGE":
                # Range bound - lower targets
                adjusted_target *= 0.8
            elif regime == "MEAN_REVERSION":
                # Mean reversion - moderate targets
                adjusted_target *= 0.9
            elif regime == "HIGH_VOLATILITY":
                # High volatility - higher targets but more risk
                adjusted_target *= 1.15
            elif regime == "LOW_VOLATILITY":
                # Low volatility - lower targets
                adjusted_target *= 0.7
            
            # Adjust based on expected move
            expected_move = getattr(metrics, 'expected_move', 0)
            spot = getattr(metrics, 'spot', 1)
            if spot > 0:
                expected_move_pct = expected_move / spot
                
                # If expected move is high, increase target
                if expected_move_pct > 0.03:  # > 3%
                    adjusted_target *= 1.1
                elif expected_move_pct < 0.015:  # < 1.5%
                    adjusted_target *= 0.9
            
            # Adjust based on volatility regime
            volatility_regime = getattr(metrics, 'volatility_regime', 'normal')
            if volatility_regime == "extreme":
                adjusted_target *= 1.25
            elif volatility_regime == "elevated":
                adjusted_target *= 1.1
            elif volatility_regime == "low":
                adjusted_target *= 0.85
            
            return adjusted_target
            
        except Exception as e:
            logger.error(f"Target adjustment error: {e}")
            return base_target
    
    def _ensure_risk_reward(self, entry_price: float, target_price: float, 
                          stoploss_price: float) -> Tuple[float, float]:
        """Ensure minimum risk/reward ratio is maintained"""
        try:
            risk = abs(entry_price - stoploss_price)
            reward = abs(target_price - entry_price)
            
            if risk <= 0:
                return target_price, stoploss_price
            
            current_ratio = reward / risk
            
            if current_ratio >= self.min_risk_reward_ratio:
                return target_price, stoploss_price
            
            # Need to adjust to meet minimum ratio
            required_reward = risk * self.min_risk_reward_ratio
            adjusted_target = entry_price + required_reward
            
            return adjusted_target, stoploss_price
            
        except Exception as e:
            logger.error(f"Risk/reward adjustment error: {e}")
            return target_price, stoploss_price
    
    def _calculate_confidence(self, risk_reward_ratio: float, metrics, 
                             market_bias: str, regime: str) -> float:
        """Calculate confidence in entry/exit levels"""
        try:
            confidence = 0.5  # Base confidence
            
            # Risk/reward ratio contributes to confidence
            if risk_reward_ratio >= 3.0:
                confidence += 0.2
            elif risk_reward_ratio >= 2.5:
                confidence += 0.15
            elif risk_reward_ratio >= 2.0:
                confidence += 0.1
            
            # Market regime confidence
            if regime in ["TREND", "BREAKOUT"]:
                confidence += 0.1
            elif regime == "RANGE":
                confidence += 0.05
            elif regime == "HIGH_VOLATILITY":
                confidence -= 0.05  # Higher uncertainty
            
            # Volatility regime confidence
            volatility_regime = getattr(metrics, 'volatility_regime', 'normal')
            if volatility_regime == "normal":
                confidence += 0.05
            elif volatility_regime == "extreme":
                confidence -= 0.1  # High uncertainty
            
            # Market bias confidence
            if market_bias in ["bullish", "bearish"]:
                confidence += 0.05
            
            # Clamp to valid range
            return max(0.1, min(1.0, confidence))
            
        except Exception as e:
            logger.error(f"Confidence calculation error: {e}")
            return 0.5
    
    def _generate_reasoning(self, entry_price: float, target_price: float, stoploss_price: float,
                           risk_reward_ratio: float, strike: float, option_type: str,
                           metrics, market_bias: str, regime: str) -> str:
        """Generate reasoning for entry/exit levels"""
        try:
            reasoning_parts = []
            
            # Base calculation
            reasoning_parts.append(f"Base entry: ₹{entry_price:.2f}")
            
            # Risk/reward information
            reasoning_parts.append(f"Risk/Reward: 1:{risk_reward_ratio:.2f}")
            
            # Stoploss reasoning
            support_level = getattr(metrics, 'support_level', 0)
            resistance_level = getattr(metrics, 'resistance_level', 0)
            
            if option_type == "CE" and support_level > 0:
                reasoning_parts.append(f"Stoploss adjusted above support at {support_level}")
            elif option_type == "PE" and resistance_level > 0:
                reasoning_parts.append(f"Stoploss adjusted below resistance at {resistance_level}")
            else:
                reasoning_parts.append(f"Stoploss at {self.default_stoploss_pct:.0%} of premium")
            
            # Target reasoning
            if regime == "TREND":
                reasoning_parts.append("Target increased for trend following")
            elif regime == "BREAKOUT":
                reasoning_parts.append("Target increased for breakout potential")
            elif regime == "RANGE":
                reasoning_parts.append("Target reduced for range-bound market")
            
            # Volatility adjustment
            volatility_regime = getattr(metrics, 'volatility_regime', 'normal')
            if volatility_regime == "extreme":
                reasoning_parts.append("Target increased for high volatility")
            elif volatility_regime == "low":
                reasoning_parts.append("Target reduced for low volatility")
            
            # Expected move consideration
            expected_move = getattr(metrics, 'expected_move', 0)
            spot = getattr(metrics, 'spot', 1)
            if spot > 0 and expected_move / spot > 0.03:
                reasoning_parts.append("Target adjusted for high expected move")
            
            return "; ".join(reasoning_parts)
            
        except Exception as e:
            logger.error(f"Reasoning generation error: {e}")
            return f"Entry: ₹{entry_price:.2f}, Target: ₹{target_price:.2f}, Stoploss: ₹{stoploss_price:.2f}"
