import logging
from typing import Dict, Any, Optional
import json
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

class AIInterpreterService:
    
    def __init__(self):
        self.timeout = 10.0
        
    async def interpret_market(self, intelligence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpret market intelligence using AI.
        
        Args:
            intelligence: MarketIntelligence object with bias, volatility, liquidity, regime
            
        Returns:
            Structured interpretation JSON
        """
        try:
            # Validate input structure
            if not self._validate_intelligence(intelligence):
                logger.warning("Invalid intelligence structure received")
                return self._get_fallback_response()
            
            # Prepare controlled AI payload
            ai_payload = self._prepare_ai_payload(intelligence)
            
            # Call AI service (placeholder - will be implemented based on available provider)
            interpretation = await self._call_ai_service(ai_payload)
            
            # Validate and structure response
            return self._structure_response(interpretation)
            
        except Exception as e:
            logger.error(f"AI interpretation failed: {e}")
            return self._get_fallback_response()
    
    def _validate_intelligence(self, intelligence: Dict[str, Any]) -> bool:
        """Validate intelligence object structure."""
        # Check for required keys - be more flexible with validation
        if not isinstance(intelligence, dict):
            logger.warning("Invalid intelligence structure: not a dictionary")
            return False
        
        # Check for at least one of the main sections
        has_bias = "bias" in intelligence and isinstance(intelligence["bias"], dict)
        has_volatility = "volatility" in intelligence and isinstance(intelligence["volatility"], dict)
        has_liquidity = "liquidity" in intelligence and isinstance(intelligence["liquidity"], dict)
        
        # At least one section must be present
        if not (has_bias or has_volatility or has_liquidity):
            logger.warning("Invalid intelligence structure: missing required sections")
            return False
        
        return True
    
    def _prepare_ai_payload(self, intelligence: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare controlled payload for AI - only structured intelligence."""
        return {
            "bias": intelligence.get("bias", {}),
            "volatility": intelligence.get("volatility", {}),
            "liquidity": intelligence.get("liquidity", {}),
            "timestamp": intelligence.get("timestamp", datetime.now().isoformat()),
            "confidence": intelligence.get("confidence", 0.0)
        }
    
    async def _call_ai_service(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Call AI service for interpretation.
        For now, returns a rule-based interpretation until AI service is integrated.
        """
        try:
            # Extract key intelligence data
            bias = payload.get("bias", {})
            volatility = payload.get("volatility", {})
            liquidity = payload.get("liquidity", {})
            
            # Rule-based interpretation logic
            bias_score = bias.get("score", 0)
            bias_label = bias.get("label", "NEUTRAL")
            volatility_state = volatility.get("current", "normal")
            
            # Generate narrative based on bias and volatility
            if bias_score >= 70:
                narrative = f"Strong {bias_label} sentiment detected with {volatility_state} volatility. Market shows significant institutional positioning with high conviction."
                risk_context = "elevated"
                confidence_tone = "high"
            elif bias_score <= 30:
                narrative = f"Strong {bias_label} sentiment with {volatility_state} volatility. Market indicates defensive positioning with potential downside risk."
                risk_context = "elevated"
                confidence_tone = "high"
            else:
                narrative = f"Balanced market conditions with {volatility_state} volatility. Mixed signals suggest cautious positioning."
                risk_context = "moderate"
                confidence_tone = "medium"
            
            # Add liquidity context
            total_oi = liquidity.get("total_oi", 0)
            if total_oi > 0:
                liquidity_context = f"Market liquidity at {total_oi:,} shows {'high' if total_oi > 10000000 else 'moderate' if total_oi > 5000000 else 'normal'} participation."
            else:
                liquidity_context = "Limited liquidity data available."
            
            # Generate positioning context
            positioning_context = f"Current bias score of {bias_score}/100 suggests {'strong' if bias_score > 60 else 'moderate' if bias_score > 40 else 'weak'} market conviction."
            
            # Generate contradiction flags
            contradictions = []
            if bias_score > 60 and volatility_state == "low":
                contradictions.append("High bias score conflicts with low volatility regime")
            elif bias_score < 40 and volatility_state == "extreme":
                contradictions.append("Low bias score conflicts with extreme volatility regime")
            
            return {
                "narrative": narrative,
                "risk_context": risk_context,
                "positioning_context": positioning_context,
                "liquidity_context": liquidity_context,
                "contradiction_flags": contradictions,
                "confidence_tone": confidence_tone,
                "interpreted_at": datetime.now().isoformat(),
                "fallback": False
            }
            
        except Exception as e:
            logger.error(f"Rule-based interpretation failed: {e}")
            return self._get_fallback_response()
    
    def _structure_response(self, ai_response: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Structure AI response into required format."""
        if not ai_response:
            return self._get_fallback_response()
        
        try:
            # Extract structured fields from AI response
            return {
                "narrative": ai_response.get("narrative"),
                "risk_context": ai_response.get("risk_context"),
                "positioning_context": ai_response.get("positioning_context"),
                "contradiction_flags": ai_response.get("contradiction_flags", []),
                "confidence_tone": ai_response.get("confidence_tone", "cautious"),
                "interpreted_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to structure AI response: {e}")
            return self._get_fallback_response()
    
    def _get_fallback_response(self) -> Dict[str, Any]:
        """Return safe fallback response."""
        return {
            "narrative": None,
            "risk_context": None,
            "positioning_context": None,
            "contradiction_flags": [],
            "confidence_tone": "cautious",
            "interpreted_at": datetime.now().isoformat(),
            "fallback": True
        }

# Singleton instance
ai_interpreter_service = AIInterpreterService()
