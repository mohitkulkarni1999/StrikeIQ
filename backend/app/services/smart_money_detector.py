"""
Smart Money Detector
Detects call writing, put writing, and long/short buildup patterns
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class SmartMoneyResult:
    """Smart money activity analysis result"""
    symbol: str
    call_writing_detected: bool
    put_writing_detected: bool
    call_writing_strength: float  # 0-100
    put_writing_strength: float  # 0-100
    long_buildup_detected: bool
    short_buildup_detected: bool
    buildup_strength: float  # 0-100
    net_smart_money_flow: str  # "bullish", "bearish", "neutral"
    institutional_activity_score: float  # 0-100
    key_observations: List[str]
    timestamp: str

class SmartMoneyDetector:
    """
    Detects smart money activity from option chain patterns
    """
    
    def __init__(self):
        self.historical_data = {}  # Store historical patterns
        
    def compute(self, data: Dict[str, Any]) -> SmartMoneyResult:
        """
        Detect smart money activity from option chain data
        """
        try:
            symbol = data.get("symbol", "NIFTY")
            calls = data.get("calls", [])
            puts = data.get("puts", [])
            
            # Detect call writing
            call_writing_detected, call_writing_strength = self._detect_call_writing(calls)
            
            # Detect put writing
            put_writing_detected, put_writing_strength = self._detect_put_writing(puts)
            
            # Detect long/short buildup
            long_buildup_detected, short_buildup_detected, buildup_strength = self._detect_buildup(
                calls, puts
            )
            
            # Calculate net smart money flow
            net_flow = self._calculate_net_flow(
                call_writing_strength, put_writing_strength,
                long_buildup_detected, short_buildup_detected
            )
            
            # Calculate institutional activity score
            institutional_activity_score = self._calculate_institutional_score(
                call_writing_strength, put_writing_strength, buildup_strength
            )
            
            # Generate key observations
            key_observations = self._generate_observations(
                call_writing_detected, put_writing_detected,
                long_buildup_detected, short_buildup_detected,
                net_flow
            )
            
            return SmartMoneyResult(
                symbol=symbol,
                call_writing_detected=call_writing_detected,
                put_writing_detected=put_writing_detected,
                call_writing_strength=call_writing_strength,
                put_writing_strength=put_writing_strength,
                long_buildup_detected=long_buildup_detected,
                short_buildup_detected=short_buildup_detected,
                buildup_strength=buildup_strength,
                net_smart_money_flow=net_flow,
                institutional_activity_score=institutional_activity_score,
                key_observations=key_observations,
                timestamp=data.get("timestamp", "")
            )
            
        except Exception as e:
            logger.error(f"Error detecting smart money: {e}")
            # Return neutral result on error
            return SmartMoneyResult(
                symbol=data.get("symbol", "NIFTY"),
                call_writing_detected=False,
                put_writing_detected=False,
                call_writing_strength=0,
                put_writing_strength=0,
                long_buildup_detected=False,
                short_buildup_detected=False,
                buildup_strength=0,
                net_smart_money_flow="neutral",
                institutional_activity_score=0,
                key_observations=["Analysis unavailable"],
                timestamp=data.get("timestamp", "")
            )
    
    def _detect_call_writing(self, calls: List[Dict]) -> Tuple[bool, float]:
        """Detect call writing patterns"""
        try:
            if not calls:
                return False, 0
            
            # Look for high OI with low volume (writing pattern)
            writing_indicators = []
            
            for call in calls:
                oi = call.get("open_interest", 0)
                volume = call.get("volume", 0)
                last_price = call.get("last_price", 0)
                
                # Writing indicators:
                # 1. High OI but low volume
                # 2. Decreasing IV (premium pressure)
                # 3. OTM strikes with high OI
                
                if oi > 1000 and volume < oi * 0.1:
                    writing_strength = min((oi / 1000) * 50, 100)
                    writing_indicators.append(writing_strength)
            
            if writing_indicators:
                avg_strength = np.mean(writing_indicators)
                return avg_strength > 30, avg_strength
            
            return False, 0
            
        except Exception as e:
            logger.error(f"Error detecting call writing: {e}")
            return False, 0
    
    def _detect_put_writing(self, puts: List[Dict]) -> Tuple[bool, float]:
        """Detect put writing patterns"""
        try:
            if not puts:
                return False, 0
            
            # Look for high OI with low volume (writing pattern)
            writing_indicators = []
            
            for put in puts:
                oi = put.get("open_interest", 0)
                volume = put.get("volume", 0)
                last_price = put.get("last_price", 0)
                
                # Writing indicators:
                # 1. High OI but low volume
                # 2. Decreasing IV (premium pressure)
                # 3. OTM strikes with high OI
                
                if oi > 1000 and volume < oi * 0.1:
                    writing_strength = min((oi / 1000) * 50, 100)
                    writing_indicators.append(writing_strength)
            
            if writing_indicators:
                avg_strength = np.mean(writing_indicators)
                return avg_strength > 30, avg_strength
            
            return False, 0
            
        except Exception as e:
            logger.error(f"Error detecting put writing: {e}")
            return False, 0
    
    def _detect_buildup(self, calls: List[Dict], puts: List[Dict]) -> Tuple[bool, bool, float]:
        """Detect long/short buildup patterns"""
        try:
            if not calls or not puts:
                return False, False, 0
            
            # Calculate total OI changes
            call_oi_total = sum(call.get("open_interest", 0) for call in calls)
            put_oi_total = sum(put.get("open_interest", 0) for put in puts)
            
            # Calculate volume patterns
            call_volume_total = sum(call.get("volume", 0) for call in calls)
            put_volume_total = sum(put.get("volume", 0) for put in puts)
            
            # Long buildup: High call volume + increasing call OI
            long_buildup = (
                call_volume_total > put_volume_total * 1.5 and
                call_oi_total > put_oi_total * 1.2
            )
            
            # Short buildup: High put volume + increasing put OI
            short_buildup = (
                put_volume_total > call_volume_total * 1.5 and
                put_oi_total > call_oi_total * 1.2
            )
            
            # Calculate buildup strength
            volume_ratio = max(call_volume_total, put_volume_total) / min(call_volume_total, put_volume_total) if min(call_volume_total, put_volume_total) > 0 else 1
            buildup_strength = min(volume_ratio * 20, 100)
            
            return long_buildup, short_buildup, buildup_strength
            
        except Exception as e:
            logger.error(f"Error detecting buildup: {e}")
            return False, False, 0
    
    def _calculate_net_flow(self, call_strength: float, put_strength: float, long_buildup: bool, short_buildup: bool) -> str:
        """Calculate net smart money flow direction"""
        try:
            bullish_score = 0
            bearish_score = 0
            
            # Call writing is bearish
            bearish_score += call_strength * 0.6
            
            # Put writing is bullish
            bullish_score += put_strength * 0.6
            
            # Long buildup is bullish
            if long_buildup:
                bullish_score += 30
            
            # Short buildup is bearish
            if short_buildup:
                bearish_score += 30
            
            if bullish_score > bearish_score * 1.2:
                return "bullish"
            elif bearish_score > bullish_score * 1.2:
                return "bearish"
            else:
                return "neutral"
                
        except Exception as e:
            logger.error(f"Error calculating net flow: {e}")
            return "neutral"
    
    def _calculate_institutional_score(self, call_strength: float, put_strength: float, buildup_strength: float) -> float:
        """Calculate overall institutional activity score"""
        try:
            # Combine all indicators
            writing_score = max(call_strength, put_strength)
            combined_score = (writing_score + buildup_strength) / 2
            
            return min(combined_score, 100)
            
        except Exception as e:
            logger.error(f"Error calculating institutional score: {e}")
            return 0
    
    def _generate_observations(self, call_writing: bool, put_writing: bool, long_buildup: bool, short_buildup: bool, net_flow: str) -> List[str]:
        """Generate key observations for smart money activity"""
        observations = []
        
        if call_writing:
            observations.append("Call writing detected - potential bearish sentiment")
        
        if put_writing:
            observations.append("Put writing detected - potential bullish sentiment")
        
        if long_buildup:
            observations.append("Long buildup detected - bullish institutional activity")
        
        if short_buildup:
            observations.append("Short buildup detected - bearish institutional activity")
        
        if net_flow == "bullish":
            observations.append("Net smart money flow: BULLISH")
        elif net_flow == "bearish":
            observations.append("Net smart money flow: BEARISH")
        else:
            observations.append("Net smart money flow: NEUTRAL")
        
        return observations
