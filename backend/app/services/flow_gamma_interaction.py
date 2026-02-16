"""
Flow + Gamma Interaction Model
Computes unique interaction states between gamma and flow
"""

import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class GammaState(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class FlowState(Enum):
    CALL_WRITING = "call_writing"
    PUT_WRITING = "put_writing"
    CALL_BUYING = "call_buying"
    PUT_BUYING = "put_buying"
    BEARISH_BUILD = "bearish_build"
    BALANCED = "balanced"
    NEUTRAL = "neutral"

class InteractionType(Enum):
    RANGE_COMPRESSION = "range_compression"
    DOWNSIDE_ACCELERATION = "downside_acceleration"
    UPSIDE_BREAKOUT_RISK = "upside_breakout_risk"
    CHOPPY_MARKET = "choppy_market"
    MOMENTUM_BUILD = "momentum_build"
    MEAN_REVERSION_SETUP = "mean_reversion_setup"
    VOLATILITY_EXPANSION = "volatility_expansion"
    STRUCTURAL_STABILITY = "structural_stability"

@dataclass
class StructuralInteraction:
    """Gamma + Flow interaction state"""
    gamma_state: GammaState
    flow_state: FlowState
    interaction_type: InteractionType
    confidence: float  # 0-100
    description: str
    trading_implications: Dict[str, Any]
    risk_factors: Dict[str, Any]
    opportunities: Dict[str, Any]

class FlowGammaInteractionEngine:
    """
    Computes unique gamma + flow interaction states
    This is StrikeIQ's competitive edge
    """
    
    def __init__(self):
        self.interaction_matrix = self._build_interaction_matrix()
        
    def compute_interaction(self, metrics: Dict[str, Any]) -> StructuralInteraction:
        """
        Compute the current structural interaction state
        """
        try:
            # Extract states
            gamma_state = self._determine_gamma_state(metrics)
            flow_state = self._determine_flow_state(metrics)
            
            # Get interaction type
            interaction_type = self._get_interaction_type(gamma_state, flow_state)
            
            # Calculate confidence
            confidence = self._calculate_interaction_confidence(
                gamma_state, flow_state, metrics
            )
            
            # Generate description and implications
            description = self._generate_description(gamma_state, flow_state, interaction_type)
            trading_implications = self._generate_trading_implications(interaction_type)
            risk_factors = self._generate_risk_factors(interaction_type, metrics)
            opportunities = self._generate_opportunities(interaction_type, metrics)
            
            return StructuralInteraction(
                gamma_state=gamma_state,
                flow_state=flow_state,
                interaction_type=interaction_type,
                confidence=confidence,
                description=description,
                trading_implications=trading_implications,
                risk_factors=risk_factors,
                opportunities=opportunities
            )
            
        except Exception as e:
            logger.error(f"Error computing interaction: {e}")
            return self._create_default_interaction()
    
    def _determine_gamma_state(self, metrics: Dict[str, Any]) -> GammaState:
        """Determine current gamma state"""
        net_gamma = metrics.get("net_gamma", 0)
        
        if net_gamma > 1000000:  # Threshold for positive gamma
            return GammaState.POSITIVE
        elif net_gamma < -1000000:  # Threshold for negative gamma
            return GammaState.NEGATIVE
        else:
            return GammaState.NEUTRAL
    
    def _determine_flow_state(self, metrics: Dict[str, Any]) -> FlowState:
        """Determine current flow state"""
        flow_direction = metrics.get("flow_direction", "neutral")
        flow_imbalance = metrics.get("flow_imbalance", 0)
        call_velocity = metrics.get("call_oi_velocity", 0)
        put_velocity = metrics.get("put_oi_velocity", 0)
        
        # Map flow direction to state
        if flow_direction == "call_writing":
            return FlowState.CALL_WRITING
        elif flow_direction == "put_writing":
            return FlowState.PUT_WRITING
        elif flow_direction == "call_buying":
            return FlowState.CALL_BUYING
        elif flow_direction == "put_buying":
            return FlowState.PUT_BUYING
        elif flow_direction == "bearish_build":
            return FlowState.BEARISH_BUILD
        elif flow_direction == "balanced" or abs(flow_imbalance) < 0.1:
            return FlowState.BALANCED
        else:
            return FlowState.NEUTRAL
    
    def _get_interaction_type(self, gamma_state: GammaState, flow_state: FlowState) -> InteractionType:
        """Get interaction type from gamma + flow combination"""
        return self.interaction_matrix.get((gamma_state, flow_state), InteractionType.STRUCTURAL_STABILITY)
    
    def _calculate_interaction_confidence(self, gamma_state: GammaState, flow_state: FlowState, metrics: Dict[str, Any]) -> float:
        """Calculate confidence in interaction classification"""
        try:
            confidence = 50  # Base confidence
            
            # Adjust based on regime confidence
            regime_confidence = metrics.get("regime_confidence", 50)
            confidence += (regime_confidence - 50) * 0.3
            
            # Adjust based on flow strength
            flow_imbalance = abs(metrics.get("flow_imbalance", 0))
            if flow_imbalance > 0.3:
                confidence += 10
            elif flow_imbalance > 0.5:
                confidence += 20
            
            # Adjust based on gamma strength
            net_gamma = abs(metrics.get("net_gamma", 0))
            if net_gamma > 5000000:
                confidence += 10
            elif net_gamma > 10000000:
                confidence += 20
            
            # Clamp to 0-100
            return max(0, min(100, confidence))
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 50
    
    def _generate_description(self, gamma_state: GammaState, flow_state: FlowState, interaction_type: InteractionType) -> str:
        """Generate human-readable description"""
        descriptions = {
            InteractionType.RANGE_COMPRESSION: f"{gamma_state.value.title()} gamma with {flow_state.value.replace('_', ' ')} suggests range compression. Price likely to stay contained.",
            InteractionType.DOWNSIDE_ACCELERATION: f"{gamma_state.value.title()} gamma combined with {flow_state.value.replace('_', ' ')} indicates downside acceleration risk.",
            InteractionType.UPSIDE_BREAKOUT_RISK: f"{gamma_state.value.title()} gamma with {flow_state.value.replace('_', ' ')} creates upside breakout potential.",
            InteractionType.CHOPPY_MARKET: f"Mixed {gamma_state.value} gamma and {flow_state.value.replace('_', ' ')} signals choppy, directionless market.",
            InteractionType.MOMENTUM_BUILD: f"{gamma_state.value.title()} gamma with {flow_state.value.replace('_', ' ')} building momentum.",
            InteractionType.MEAN_REVERSION_SETUP: f"{gamma_state.value.title()} gamma and {flow_state.value.replace('_', ' ')} setting up mean reversion.",
            InteractionType.VOLATILITY_EXPANSION: f"{gamma_state.value.title()} gamma with {flow_state.value.replace('_', ' ')} suggests volatility expansion.",
            InteractionType.STRUCTURAL_STABILITY: f"{gamma_state.value.title()} gamma with {flow_state.value.replace('_', ' ')} indicates structural stability."
        }
        
        return descriptions.get(interaction_type, "Complex market structure detected.")
    
    def _generate_trading_implications(self, interaction_type: InteractionType) -> Dict[str, Any]:
        """Generate trading implications based on interaction type"""
        implications = {
            InteractionType.RANGE_COMPRESSION: {
                "strategy": "range_bound",
                "direction": "sideways",
                "volatility": "decreasing",
                "timeframe": "short_to_medium",
                "key_levels": "support_resistance"
            },
            InteractionType.DOWNSIDE_ACCELERATION: {
                "strategy": "bearish",
                "direction": "down",
                "volatility": "increasing",
                "timeframe": "short_term",
                "key_levels": "support_break"
            },
            InteractionType.UPSIDE_BREAKOUT_RISK: {
                "strategy": "bullish_breakout",
                "direction": "up",
                "volatility": "expanding",
                "timeframe": "immediate",
                "key_levels": "resistance_break"
            },
            InteractionType.CHOPPY_MARKET: {
                "strategy": "avoid_or_range",
                "direction": "uncertain",
                "volatility": "unpredictable",
                "timeframe": "very_short",
                "key_levels": "none_clear"
            },
            InteractionType.MOMENTUM_BUILD: {
                "strategy": "momentum",
                "direction": "trending",
                "volatility": "moderate",
                "timeframe": "medium",
                "key_levels": "trend_lines"
            },
            InteractionType.MEAN_REVERSION_SETUP: {
                "strategy": "mean_reversion",
                "direction": "counter_trend",
                "volatility": "normal",
                "timeframe": "short",
                "key_levels": "extremes"
            },
            InteractionType.VOLATILITY_EXPANSION: {
                "strategy": "volatility",
                "direction": "explosive",
                "volatility": "high",
                "timeframe": "very_short",
                "key_levels": "breakouts"
            },
            InteractionType.STRUCTURAL_STABILITY: {
                "strategy": "position_trading",
                "direction": "stable",
                "volatility": "low",
                "timeframe": "medium_to_long",
                "key_levels": "established"
            }
        }
        
        return implications.get(interaction_type, {
            "strategy": "cautious",
            "direction": "uncertain",
            "volatility": "unknown",
            "timeframe": "wait_for_clarity",
            "key_levels": "monitor"
        })
    
    def _generate_risk_factors(self, interaction_type: InteractionType, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate risk factors for current interaction"""
        base_risks = {
            "flow_imbalance_risk": abs(metrics.get("flow_imbalance", 0)) > 0.6,
            "gamma_flip_risk": metrics.get("distance_from_flip", 999) < 25,
            "regime_change_risk": metrics.get("regime_confidence", 50) < 60,
            "volatility_spike_risk": metrics.get("volatility_regime") in ["elevated", "extreme"]
        }
        
        interaction_specific_risks = {
            InteractionType.RANGE_COMPRESSION: {
                "range_break_risk": True,
                "false_breakout_risk": True
            },
            InteractionType.DOWNSIDE_ACCELERATION: {
                "cascade_risk": True,
                "liquidity_crunch_risk": True
            },
            InteractionType.UPSIDE_BREAKOUT_RISK: {
                "short_squeeze_risk": True,
                "exhaustion_risk": True
            },
            InteractionType.CHOPPY_MARKET: {
                "whipsaw_risk": True,
                "stop_hunting_risk": True
            },
            InteractionType.MOMENTUM_BUILD: {
                "exhaustion_risk": True,
                "reversal_risk": True
            },
            InteractionType.MEAN_REVERSION_SETUP: {
                "trend_continuation_risk": True,
                "timing_risk": True
            },
            InteractionType.VOLATILITY_EXPANSION: {
                "gap_risk": True,
                "liquidity_risk": True
            },
            InteractionType.STRUCTURAL_STABILITY: {
                "complacency_risk": True,
                "sudden_shock_risk": True
            }
        }
        
        risks = base_risks.copy()
        risks.update(interaction_specific_risks.get(interaction_type, {}))
        
        return risks
    
    def _generate_opportunities(self, interaction_type: InteractionType, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading opportunities"""
        opportunities = {
            InteractionType.RANGE_COMPRESSION: {
                "range_trading": True,
                "option_selling": True,
                "theta_capture": True
            },
            InteractionType.DOWNSIDE_ACCELERATION: {
                "put_buying": True,
                "short_selling": True,
                "volatility_buying": True
            },
            InteractionType.UPSIDE_BREAKOUT_RISK: {
                "call_buying": True,
                "breakout_trading": True,
                "momentum_playing": True
            },
            InteractionType.CHOPPY_MARKET: {
                "stay_flat": True,
                "scalping": True,
                "very_short_term": True
            },
            InteractionType.MOMENTUM_BUILD: {
                "trend_following": True,
                "pyramid_building": True,
                "partial_profits": True
            },
            InteractionType.MEAN_REVERSION_SETUP: {
                "contrarian_trading": True,
                "fading_extremes": True,
                "option_selling": True
            },
            InteractionType.VOLATILITY_EXPANSION: {
                "straddle_buying": True,
                "breakout_playing": True,
                "rapid_profits": True
            },
            InteractionType.STRUCTURAL_STABILITY: {
                "position_building": True,
                "carry_trades": True,
                "long_term_holds": True
            }
        }
        
        return opportunities.get(interaction_type, {
            "monitor_only": True,
            "wait_for_clarity": True
        })
    
    def _build_interaction_matrix(self) -> Dict[tuple, InteractionType]:
        """Build the gamma + flow interaction matrix"""
        matrix = {
            # Positive Gamma
            (GammaState.POSITIVE, FlowState.CALL_WRITING): InteractionType.RANGE_COMPRESSION,
            (GammaState.POSITIVE, FlowState.PUT_WRITING): InteractionType.MEAN_REVERSION_SETUP,
            (GammaState.POSITIVE, FlowState.CALL_BUYING): InteractionType.RANGE_COMPRESSION,
            (GammaState.POSITIVE, FlowState.PUT_BUYING): InteractionType.VOLATILITY_EXPANSION,
            (GammaState.POSITIVE, FlowState.BEARISH_BUILD): InteractionType.STRUCTURAL_STABILITY,
            (GammaState.POSITIVE, FlowState.BALANCED): InteractionType.STRUCTURAL_STABILITY,
            (GammaState.POSITIVE, FlowState.NEUTRAL): InteractionType.STRUCTURAL_STABILITY,
            
            # Negative Gamma
            (GammaState.NEGATIVE, FlowState.CALL_WRITING): InteractionType.CHOPPY_MARKET,
            (GammaState.NEGATIVE, FlowState.PUT_WRITING): InteractionType.DOWNSIDE_ACCELERATION,
            (GammaState.NEGATIVE, FlowState.CALL_BUYING): InteractionType.UPSIDE_BREAKOUT_RISK,
            (GammaState.NEGATIVE, FlowState.PUT_BUYING): InteractionType.DOWNSIDE_ACCELERATION,
            (GammaState.NEGATIVE, FlowState.BEARISH_BUILD): InteractionType.MOMENTUM_BUILD,
            (GammaState.NEGATIVE, FlowState.BALANCED): InteractionType.CHOPPY_MARKET,
            (GammaState.NEGATIVE, FlowState.NEUTRAL): InteractionType.CHOPPY_MARKET,
            
            # Neutral Gamma
            (GammaState.NEUTRAL, FlowState.CALL_WRITING): InteractionType.RANGE_COMPRESSION,
            (GammaState.NEUTRAL, FlowState.PUT_WRITING): InteractionType.RANGE_COMPRESSION,
            (GammaState.NEUTRAL, FlowState.CALL_BUYING): InteractionType.MOMENTUM_BUILD,
            (GammaState.NEUTRAL, FlowState.PUT_BUYING): InteractionType.MOMENTUM_BUILD,
            (GammaState.NEUTRAL, FlowState.BEARISH_BUILD): InteractionType.MOMENTUM_BUILD,
            (GammaState.NEUTRAL, FlowState.BALANCED): InteractionType.STRUCTURAL_STABILITY,
            (GammaState.NEUTRAL, FlowState.NEUTRAL): InteractionType.STRUCTURAL_STABILITY,
        }
        
        return matrix
    
    def _create_default_interaction(self) -> StructuralInteraction:
        """Create default interaction for error cases"""
        return StructuralInteraction(
            gamma_state=GammaState.NEUTRAL,
            flow_state=FlowState.NEUTRAL,
            interaction_type=InteractionType.STRUCTURAL_STABILITY,
            confidence=50,
            description="Market structure analysis unavailable.",
            trading_implications={"strategy": "cautious"},
            risk_factors={"analysis_error": True},
            opportunities={"monitor_only": True}
        )
    
    def format_for_frontend(self, interaction: StructuralInteraction) -> Dict[str, Any]:
        """Format interaction for frontend consumption"""
        return {
            "gamma_state": interaction.gamma_state.value,
            "flow_state": interaction.flow_state.value,
            "interaction_type": interaction.interaction_type.value,
            "confidence": interaction.confidence,
            "description": interaction.description,
            "trading_implications": interaction.trading_implications,
            "risk_factors": interaction.risk_factors,
            "opportunities": interaction.opportunities,
            "summary": {
                "primary_strategy": interaction.trading_implications.get("strategy", "cautious"),
                "direction": interaction.trading_implications.get("direction", "uncertain"),
                "risk_level": self._calculate_risk_level(interaction.risk_factors),
                "opportunity_score": self._calculate_opportunity_score(interaction.opportunities)
            }
        }
    
    def _calculate_risk_level(self, risk_factors: Dict[str, bool]) -> str:
        """Calculate overall risk level"""
        active_risks = sum(1 for risk in risk_factors.values() if risk)
        
        if active_risks >= 4:
            return "high"
        elif active_risks >= 2:
            return "medium"
        else:
            return "low"
    
    def _calculate_opportunity_score(self, opportunities: Dict[str, bool]) -> int:
        """Calculate opportunity score (0-100)"""
        active_opportunities = sum(1 for opp in opportunities.values() if opp)
        return min(100, active_opportunities * 20)
