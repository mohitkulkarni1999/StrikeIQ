"""
Explanation Engine - Generates human readable explanations
Lightweight, optimized for Intel i5 CPU, 8GB RAM
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TradeExplanation:
    """Human readable trade explanation"""
    summary: str
    detailed_reasoning: str
    key_factors: List[str]
    risk_factors: List[str]

class ExplanationEngine:
    """
    Generates human readable explanations for trade suggestions
    Explains the reasoning behind AI decisions
    """
    
    def __init__(self):
        # Explanation templates for different strategies
        self.strategy_explanations = {
            "Long Call": {
                "template": "Bullish call option purchase based on {primary_signal}. {supporting_factors}",
                "key_factors": ["PCR bullishness", "Positive gamma", "Call flow dominance", "Support level proximity"]
            },
            "Long Put": {
                "template": "Bearish put option purchase based on {primary_signal}. {supporting_factors}",
                "key_factors": ["PCR bearishness", "Negative gamma", "Put flow dominance", "Resistance level proximity"]
            },
            "Bull Call Spread": {
                "template": "Moderately bullish call spread for defined risk. {primary_signal}. {supporting_factors}",
                "key_factors": ["Moderate PCR bullish", "Controlled gamma exposure", "Range-bound bias", "Risk-defined structure"]
            },
            "Bear Put Spread": {
                "template": "Moderately bearish put spread for defined risk. {primary_signal}. {supporting_factors}",
                "key_factors": ["Moderate PCR bearish", "Controlled gamma exposure", "Range-bound bias", "Risk-defined structure"]
            },
            "Iron Condor": {
                "template": "Neutral iron condor for range-bound income. {primary_signal}. {supporting_factors}",
                "key_factors": ["PCR neutrality", "Gamma balance", "Expected range hold", "Volatility optimization"]
            },
            "Straddle": {
                "template": "Volatility straddle for breakout potential. {primary_signal}. {supporting_factors}",
                "key_factors": ["High volatility environment", "Breakout probability", "Volume spike", "Expected move expansion"]
            },
            "Strangle": {
                "template": "Volatility strangle for directional uncertainty. {primary_signal}. {supporting_factors}",
                "key_factors": ["Moderate volatility", "Neutral bias with movement", "Cost efficiency", "Flexible strike selection"]
            }
        }
    
    def generate_explanation(self, metrics, formula_signals, strategy_choice, trade_suggestion) -> TradeExplanation:
        """
        Generate comprehensive explanation for trade suggestion
        """
        try:
            # Get strategy-specific template
            strategy_info = self.strategy_explanations.get(
                trade_suggestion.strategy, 
                {"template": "Trade based on {primary_signal}. {supporting_factors}", "key_factors": []}
            )
            
            # Identify primary signal
            primary_signal = self._identify_primary_signal(formula_signals, strategy_choice.market_bias)
            
            # Generate supporting factors
            supporting_factors = self._generate_supporting_factors(formula_signals, metrics, strategy_choice.market_bias)
            
            # Create summary
            summary = strategy_info["template"].format(
                primary_signal=primary_signal,
                supporting_factors=" ".join(supporting_factors[:2])  # Top 2 factors for summary
            )
            
            # Generate detailed reasoning
            detailed_reasoning = self._generate_detailed_reasoning(
                formula_signals, metrics, strategy_choice, trade_suggestion
            )
            
            # Identify key factors
            key_factors = self._identify_key_factors(formula_signals, metrics, strategy_choice.market_bias)
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(formula_signals, metrics, trade_suggestion)
            
            return TradeExplanation(
                summary=summary,
                detailed_reasoning=detailed_reasoning,
                key_factors=key_factors,
                risk_factors=risk_factors
            )
            
        except Exception as e:
            logger.error(f"Explanation generation error: {e}")
            return TradeExplanation(
                summary="Trade generated based on technical analysis",
                detailed_reasoning="Error generating detailed explanation",
                key_factors=["Technical analysis"],
                risk_factors=["Market risk"]
            )
    
    def _identify_primary_signal(self, formula_signals, market_bias: str) -> str:
        """Identify the primary driving signal"""
        try:
            # Check high-confidence signals first
            high_confidence_signals = []
            
            for formula_id, signal in formula_signals.items():
                if signal.confidence > 0.7 and signal.signal in ["BUY", "SELL"]:
                    high_confidence_signals.append((formula_id, signal))
            
            if high_confidence_signals:
                # Sort by confidence
                high_confidence_signals.sort(key=lambda x: x[1].confidence, reverse=True)
                top_signal = high_confidence_signals[0]
                
                formula_names = {
                    "F01": "PCR analysis",
                    "F02": "OI imbalance",
                    "F03": "Gamma regime",
                    "F06": "Delta imbalance",
                    "F10": "Flow imbalance"
                }
                
                formula_name = formula_names.get(top_signal[0], f"Formula {top_signal[0]}")
                return f"{formula_name}: {top_signal[1].reason}"
            
            # Fallback to market bias
            if market_bias == "bullish":
                return "Overall bullish market conditions"
            elif market_bias == "bearish":
                return "Overall bearish market conditions"
            else:
                return "Neutral market conditions with specific opportunities"
                
        except Exception as e:
            logger.error(f"Primary signal identification error: {e}")
            return "Technical analysis signals"
    
    def _generate_supporting_factors(self, formula_signals, metrics, market_bias: str) -> List[str]:
        """Generate list of supporting factors"""
        try:
            factors = []
            
            # Add key formula signals
            signal_descriptions = []
            
            for formula_id, signal in formula_signals.items():
                if signal.confidence > 0.6 and signal.signal in ["BUY", "SELL"]:
                    if formula_id == "F01":
                        signal_descriptions.append(f"PCR {signal.signal.lower()}")
                    elif formula_id == "F03":
                        signal_descriptions.append(f"{signal.signal} gamma")
                    elif formula_id == "F10":
                        signal_descriptions.append(f"Strong {signal.signal.lower()} flow")
            
            # Add market metrics
            if hasattr(metrics, 'volatility_regime'):
                if metrics.volatility_regime == "elevated":
                    factors.append("Elevated volatility supports option premiums")
                elif metrics.volatility_regime == "low":
                    factors.append("Low volatility provides cost efficiency")
            
            if hasattr(metrics, 'expected_move'):
                if metrics.expected_move > metrics.spot * 0.03:
                    factors.append("High expected move indicates potential breakout")
            
            # Add structural factors
            if hasattr(metrics, 'support_level') and hasattr(metrics, 'spot'):
                support_distance = (metrics.spot - metrics.support_level) / metrics.spot
                if support_distance < 0.02:
                    factors.append("Near strong support level")
            
            if hasattr(metrics, 'resistance_level') and hasattr(metrics, 'spot'):
                resistance_distance = (metrics.resistance_level - metrics.spot) / metrics.spot
                if resistance_distance < 0.02:
                    factors.append("Near resistance level")
            
            # Combine signal descriptions
            if signal_descriptions:
                factors.extend(signal_descriptions[:2])
            
            return factors[:4]  # Return top 4 factors
            
        except Exception as e:
            logger.error(f"Supporting factors generation error: {e}")
            return ["Technical analysis"]
    
    def _generate_detailed_reasoning(self, formula_signals, metrics, strategy_choice, trade_suggestion) -> str:
        """Generate detailed reasoning for the trade"""
        try:
            reasoning_parts = []
            
            # Market context
            market_bias = strategy_choice.market_bias
            reasoning_parts.append(f"Market Analysis: {market_bias.capitalize()} bias detected with {strategy_choice.confidence:.0%} confidence.")
            
            # Key signals breakdown
            active_signals = []
            for formula_id, signal in formula_signals.items():
                if signal.confidence > 0.5:
                    formula_names = {
                        "F01": "PCR", "F02": "OI Imbalance", "F03": "Gamma",
                        "F04": "Volume", "F05": "Expected Move", "F06": "Delta",
                        "F07": "Volatility", "F08": "OI Velocity", "F09": "Gamma Flip",
                        "F10": "Flow"
                    }
                    name = formula_names.get(formula_id, formula_id)
                    active_signals.append(f"{name}: {signal.reason}")
            
            if active_signals:
                reasoning_parts.append("Key Signals: " + "; ".join(active_signals[:3]))
            
            # Strategy rationale
            strategy_rationale = self._get_strategy_rationale(trade_suggestion.strategy, market_bias, metrics)
            reasoning_parts.append(f"Strategy Rationale: {strategy_rationale}")
            
            # Risk considerations
            risk_considerations = self._get_risk_considerations(trade_suggestion, metrics)
            reasoning_parts.append(f"Risk Considerations: {risk_considerations}")
            
            return " ".join(reasoning_parts)
            
        except Exception as e:
            logger.error(f"Detailed reasoning generation error: {e}")
            return "Trade based on comprehensive technical analysis and risk management principles."
    
    def _get_strategy_rationale(self, strategy: str, market_bias: str, metrics) -> str:
        """Get strategy-specific rationale"""
        try:
            rationales = {
                "Long Call": f"Direct bullish exposure with defined risk, suitable for {market_bias} market conditions",
                "Long Put": f"Direct bearish exposure with defined risk, suitable for {market_bias} market conditions",
                "Bull Call Spread": f"Defined-risk bullish position, capital efficient for moderate {market_bias} outlook",
                "Bear Put Spread": f"Defined-risk bearish position, capital efficient for moderate {market_bias} outlook",
                "Iron Condor": f"Income strategy for range-bound markets, benefits from time decay",
                "Straddle": f"Volatility play for significant price movement regardless of direction",
                "Strangle": f"Cost-effective volatility play with wider breakeven points"
            }
            
            return rationales.get(strategy, "Technical analysis-based strategy selection")
            
        except Exception as e:
            logger.error(f"Strategy rationale error: {e}")
            return "Strategy selected based on technical analysis"
    
    def _get_risk_considerations(self, trade_suggestion, metrics) -> str:
        """Get risk considerations for the trade"""
        try:
            risks = []
            
            # Strategy-specific risks
            if trade_suggestion.strategy in ["Long Call", "Long Put"]:
                risks.append("Time decay erosion of premium")
                risks.append("Maximum loss limited to premium paid")
            elif trade_suggestion.strategy in ["Bull Call Spread", "Bear Put Spread"]:
                risks.append("Limited profit potential")
                risks.append("Defined risk exposure")
            elif trade_suggestion.strategy == "Iron Condor":
                risks.append("Significant loss if range breaks")
                risks.append("Maximum loss defined by spread width")
            elif trade_suggestion.strategy in ["Straddle", "Strangle"]:
                risks.append("Time decay works against position")
                risks.append("Requires significant price movement")
            
            # Market risks
            if hasattr(metrics, 'volatility_regime'):
                if metrics.volatility_regime == "low":
                    risks.append("Low volatility may limit premium expansion")
                elif metrics.volatility_regime == "extreme":
                    risks.append("High volatility increases premium cost")
            
            return "; ".join(risks[:3])
            
        except Exception as e:
            logger.error(f"Risk considerations error: {e}")
            return "Standard market risks apply"
    
    def _identify_key_factors(self, formula_signals, metrics, market_bias: str) -> List[str]:
        """Identify key factors driving the decision"""
        try:
            factors = []
            
            # Top formula signals
            top_signals = sorted(
                [(fid, signal) for fid, signal in formula_signals.items() if signal.confidence > 0.6],
                key=lambda x: x[1].confidence,
                reverse=True
            )[:3]
            
            formula_names = {
                "F01": "PCR Analysis", "F02": "OI Imbalance", "F03": "Gamma Regime",
                "F04": "Volume Activity", "F05": "Expected Move", "F06": "Delta Flow",
                "F07": "Volatility Regime", "F08": "OI Velocity", "F09": "Gamma Flip",
                "F10": "Order Flow"
            }
            
            for formula_id, signal in top_signals:
                name = formula_names.get(formula_id, formula_id)
                factors.append(f"{name}: {signal.reason}")
            
            # Market structure factors
            if hasattr(metrics, 'support_level') and hasattr(metrics, 'spot'):
                support_distance = abs(metrics.spot - metrics.support_level) / metrics.spot
                if support_distance < 0.03:
                    factors.append(f"Support level at {metrics.support_level}")
            
            if hasattr(metrics, 'resistance_level') and hasattr(metrics, 'spot'):
                resistance_distance = abs(metrics.resistance_level - metrics.spot) / metrics.spot
                if resistance_distance < 0.03:
                    factors.append(f"Resistance level at {metrics.resistance_level}")
            
            return factors[:5]  # Return top 5 factors
            
        except Exception as e:
            logger.error(f"Key factors identification error: {e}")
            return ["Technical analysis"]
    
    def _identify_risk_factors(self, formula_signals, metrics, trade_suggestion) -> List[str]:
        """Identify risk factors for the trade"""
        try:
            risks = []
            
            # Signal conflicts
            buy_signals = sum(1 for s in formula_signals.values() if s.signal == "BUY" and s.confidence > 0.6)
            sell_signals = sum(1 for s in formula_signals.values() if s.signal == "SELL" and s.confidence > 0.6)
            
            if buy_signals > 0 and sell_signals > 0:
                risks.append("Mixed signals detected")
            
            # Low confidence signals
            low_confidence = [fid for fid, s in formula_signals.items() if s.confidence < 0.4]
            if len(low_confidence) > 5:
                risks.append("Multiple low-confidence indicators")
            
            # Market risks
            if hasattr(metrics, 'volatility_regime'):
                if metrics.volatility_regime == "extreme":
                    risks.append("Extreme volatility conditions")
                elif metrics.volatility_regime == "low":
                    risks.append("Low volatility may limit movement")
            
            # Strategy risks
            if trade_suggestion.strategy in ["Long Call", "Long Put"]:
                risks.append("Time decay risk")
            elif trade_suggestion.strategy == "Iron Condor":
                risks.append("Range breakout risk")
            elif trade_suggestion.strategy in ["Straddle", "Strangle"]:
                risks.append("Volatility contraction risk")
            
            # Position risks
            if trade_suggestion.confidence < 0.7:
                risks.append("Below-optimal confidence level")
            
            return risks[:4]  # Return top 4 risks
            
        except Exception as e:
            logger.error(f"Risk factors identification error: {e}")
            return ["Market risk"]
