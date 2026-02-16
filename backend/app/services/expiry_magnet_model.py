"""
Expiry Magnet Model
Computes expiry-specific pin and magnet analysis for options trading
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class ExpiryAnalysis:
    """Complete expiry-specific analysis"""
    symbol: str
    days_to_expiry: int
    max_oi_strike: float
    max_gamma_strike: float
    max_oi_value: int
    max_gamma_value: float
    
    # Distance calculations
    distance_to_max_oi: float
    distance_to_max_gamma: float
    distance_to_atm: float
    
    # Magnet analysis
    pin_probability: float
    magnet_strength: float
    pin_zone: Tuple[float, float]  # (lower_bound, upper_bound)
    
    # Expiry-specific factors
    time_decay_factor: float
    gamma_concentration: float
    liquidity_profile: Dict[str, Any]
    
    # Trading implications
    expiry_risk_level: str
    recommended_strategies: List[str]
    key_levels: Dict[str, float]

class ExpiryMagnetModel:
    """
    Computes expiry-specific pin and magnet analysis
    Becomes insanely powerful near expiry days
    """
    
    def __init__(self):
        self.CONTRACT_MULTIPLIER = 75  # NFO options contract multiplier
        
        # Expiry thresholds
        self.CRITICAL_EXPIRY_DAYS = 3
        self.HIGH_RISK_EXPIRY_DAYS = 7
        self.NORMAL_EXPIRY_DAYS = 15
        
    def analyze_expiry_magnets(self, symbol: str, frontend_data: Dict[str, Any], expiry_date: str = None) -> ExpiryAnalysis:
        """
        Analyze expiry-specific magnets and pin risk
        """
        try:
            # Calculate days to expiry
            days_to_expiry = self._calculate_days_to_expiry(expiry_date)
            
            # Extract data
            spot = frontend_data.get("spot", 0)
            strikes = frontend_data.get("strikes", {})
            
            if not spot or not strikes:
                return self._create_default_analysis(symbol, days_to_expiry, spot)
            
            # Find max OI and gamma strikes
            max_oi_strike, max_oi_value = self._find_max_oi_strike(strikes)
            max_gamma_strike, max_gamma_value = self._find_max_gamma_strike(strikes)
            
            # Calculate distances
            distance_to_max_oi = abs(spot - max_oi_strike)
            distance_to_max_gamma = abs(spot - max_gamma_strike)
            distance_to_atm = abs(spot - self._find_atm_strike(strikes, spot))
            
            # Calculate pin probability
            pin_probability = self._calculate_pin_probability(
                spot, max_oi_strike, max_gamma_strike, days_to_expiry, strikes
            )
            
            # Calculate magnet strength
            magnet_strength = self._calculate_magnet_strength(
                max_oi_value, max_gamma_value, days_to_expiry
            )
            
            # Determine pin zone
            pin_zone = self._calculate_pin_zone(
                max_oi_strike, max_gamma_strike, days_to_expiry
            )
            
            # Calculate expiry-specific factors
            time_decay_factor = self._calculate_time_decay_factor(days_to_expiry)
            gamma_concentration = self._calculate_gamma_concentration(strikes, max_gamma_strike)
            liquidity_profile = self._analyze_liquidity_profile(strikes, days_to_expiry)
            
            # Determine risk level and strategies
            expiry_risk_level = self._determine_expiry_risk_level(days_to_expiry, pin_probability)
            recommended_strategies = self._get_recommended_strategies(
                expiry_risk_level, pin_probability, days_to_expiry
            )
            
            # Identify key levels
            key_levels = self._identify_key_levels(
                spot, max_oi_strike, max_gamma_strike, strikes
            )
            
            return ExpiryAnalysis(
                symbol=symbol,
                days_to_expiry=days_to_expiry,
                max_oi_strike=max_oi_strike,
                max_gamma_strike=max_gamma_strike,
                max_oi_value=max_oi_value,
                max_gamma_value=max_gamma_value,
                distance_to_max_oi=distance_to_max_oi,
                distance_to_max_gamma=distance_to_max_gamma,
                distance_to_atm=distance_to_atm,
                pin_probability=pin_probability,
                magnet_strength=magnet_strength,
                pin_zone=pin_zone,
                time_decay_factor=time_decay_factor,
                gamma_concentration=gamma_concentration,
                liquidity_profile=liquidity_profile,
                expiry_risk_level=expiry_risk_level,
                recommended_strategies=recommended_strategies,
                key_levels=key_levels
            )
            
        except Exception as e:
            logger.error(f"Error analyzing expiry magnets for {symbol}: {e}")
            return self._create_default_analysis(symbol, 0, frontend_data.get("spot", 0))
    
    def _calculate_days_to_expiry(self, expiry_date: str = None) -> int:
        """Calculate days to expiry"""
        try:
            if expiry_date:
                expiry_dt = datetime.strptime(expiry_date, "%Y-%m-%d").date()
                today = datetime.now(timezone.utc).date()
                return (expiry_dt - today).days
            else:
                # Default to 7 days if no expiry date provided
                return 7
        except Exception:
            return 7
    
    def _find_max_oi_strike(self, strikes: Dict[float, Dict]) -> Tuple[float, int]:
        """Find strike with maximum total OI"""
        max_oi = 0
        max_oi_strike = 0
        
        for strike, strike_data in strikes.items():
            call_oi = strike_data.get("call", {}).get("oi", 0)
            put_oi = strike_data.get("put", {}).get("oi", 0)
            total_oi = call_oi + put_oi
            
            if total_oi > max_oi:
                max_oi = total_oi
                max_oi_strike = strike
        
        return max_oi_strike, max_oi
    
    def _find_max_gamma_strike(self, strikes: Dict[float, Dict]) -> Tuple[float, float]:
        """Find strike with maximum gamma exposure"""
        max_gamma = 0
        max_gamma_strike = 0
        
        for strike, strike_data in strikes.items():
            call_data = strike_data.get("call", {})
            put_data = strike_data.get("put", {})
            
            # Calculate gamma exposure
            call_gex = 0
            put_gex = 0
            
            if call_data.get("gamma") and call_data.get("oi"):
                call_gex = abs(call_data["gamma"] * call_data["oi"] * self.CONTRACT_MULTIPLIER)
            
            if put_data.get("gamma") and put_data.get("oi"):
                put_gex = abs(put_data["gamma"] * put_data["oi"] * self.CONTRACT_MULTIPLIER)
            
            total_gamma = call_gex + put_gex
            
            if total_gamma > max_gamma:
                max_gamma = total_gamma
                max_gamma_strike = strike
        
        return max_gamma_strike, max_gamma
    
    def _find_atm_strike(self, strikes: Dict[float, Dict], spot: float) -> float:
        """Find ATM strike"""
        if not strikes:
            return spot
        
        return min(strikes.keys(), key=lambda x: abs(x - spot))
    
    def _calculate_pin_probability(self, spot: float, max_oi_strike: float, max_gamma_strike: float, 
                                 days_to_expiry: int, strikes: Dict[float, Dict]) -> float:
        """
        Calculate pin probability based on multiple factors
        """
        try:
            base_probability = 50  # Base 50%
            
            # Factor 1: Distance to max OI strike
            distance_to_oi = abs(spot - max_oi_strike)
            if distance_to_oi < 50:
                oi_factor = 30
            elif distance_to_oi < 100:
                oi_factor = 20
            elif distance_to_oi < 200:
                oi_factor = 10
            else:
                oi_factor = 0
            
            # Factor 2: Distance to max gamma strike
            distance_to_gamma = abs(spot - max_gamma_strike)
            if distance_to_gamma < 25:
                gamma_factor = 25
            elif distance_to_gamma < 50:
                gamma_factor = 15
            elif distance_to_gamma < 100:
                gamma_factor = 5
            else:
                gamma_factor = 0
            
            # Factor 3: Days to expiry (closer = higher pin probability)
            if days_to_expiry <= self.CRITICAL_EXPIRY_DAYS:
                expiry_factor = 20
            elif days_to_expiry <= self.HIGH_RISK_EXPIRY_DAYS:
                expiry_factor = 15
            elif days_to_expiry <= self.NORMAL_EXPIRY_DAYS:
                expiry_factor = 10
            else:
                expiry_factor = 5
            
            # Factor 4: OI concentration
            total_oi = sum(
                strike_data.get("call", {}).get("oi", 0) + 
                strike_data.get("put", {}).get("oi", 0)
                for strike_data in strikes.values()
            )
            
            if total_oi > 0:
                max_oi_total = strikes.get(max_oi_strike, {}).get("call", {}).get("oi", 0) + \
                             strikes.get(max_oi_strike, {}).get("put", {}).get("oi", 0)
                concentration_factor = (max_oi_total / total_oi) * 100
                concentration_factor = min(15, concentration_factor)
            else:
                concentration_factor = 0
            
            # Calculate final probability
            pin_probability = base_probability + oi_factor + gamma_factor + expiry_factor + concentration_factor
            return min(100, max(0, pin_probability))
            
        except Exception as e:
            logger.error(f"Error calculating pin probability: {e}")
            return 50
    
    def _calculate_magnet_strength(self, max_oi_value: int, max_gamma_value: float, days_to_expiry: int) -> float:
        """Calculate overall magnet strength"""
        try:
            # Normalize OI and gamma values
            oi_strength = min(50, max_oi_value / 1000000)  # Normalize to millions
            gamma_strength = min(50, max_gamma_value / 1000000)  # Normalize to millions
            
            # Time decay factor (closer to expiry = stronger magnet)
            if days_to_expiry <= self.CRITICAL_EXPIRY_DAYS:
                time_factor = 1.5
            elif days_to_expiry <= self.HIGH_RISK_EXPIRY_DAYS:
                time_factor = 1.2
            else:
                time_factor = 1.0
            
            magnet_strength = (oi_strength + gamma_strength) * time_factor
            return min(100, magnet_strength)
            
        except Exception as e:
            logger.error(f"Error calculating magnet strength: {e}")
            return 50
    
    def _calculate_pin_zone(self, max_oi_strike: float, max_gamma_strike: float, days_to_expiry: int) -> Tuple[float, float]:
        """Calculate pin zone bounds"""
        try:
            # Base zone width
            if days_to_expiry <= self.CRITICAL_EXPIRY_DAYS:
                base_width = 25  # Tight zone near expiry
            elif days_to_expiry <= self.HIGH_RISK_EXPIRY_DAYS:
                base_width = 50
            else:
                base_width = 75
            
            # If max OI and gamma strikes are close, center around them
            if abs(max_oi_strike - max_gamma_strike) < base_width:
                center = (max_oi_strike + max_gamma_strike) / 2
            else:
                # Use the stronger magnet as center
                center = max_oi_strike  # OI is typically stronger for pinning
            
            return (center - base_width/2, center + base_width/2)
            
        except Exception as e:
            logger.error(f"Error calculating pin zone: {e}")
            return (0, 0)
    
    def _calculate_time_decay_factor(self, days_to_expiry: int) -> float:
        """Calculate time decay factor (0-1, higher = more decay)"""
        if days_to_expiry <= 0:
            return 1.0
        elif days_to_expiry <= self.CRITICAL_EXPIRY_DAYS:
            return 0.9
        elif days_to_expiry <= self.HIGH_RISK_EXPIRY_DAYS:
            return 0.7
        elif days_to_expiry <= self.NORMAL_EXPIRY_DAYS:
            return 0.5
        else:
            return 0.3
    
    def _calculate_gamma_concentration(self, strikes: Dict[float, Dict], max_gamma_strike: float) -> float:
        """Calculate how concentrated gamma is around the max gamma strike"""
        try:
            total_gamma = 0
            nearby_gamma = 0
            
            for strike, strike_data in strikes.items():
                call_data = strike_data.get("call", {})
                put_data = strike_data.get("put", {})
                
                call_gex = 0
                put_gex = 0
                
                if call_data.get("gamma") and call_data.get("oi"):
                    call_gex = abs(call_data["gamma"] * call_data["oi"] * self.CONTRACT_MULTIPLIER)
                
                if put_data.get("gamma") and put_data.get("oi"):
                    put_gex = abs(put_data["gamma"] * put_data["oi"] * self.CONTRACT_MULTIPLIER)
                
                strike_gamma = call_gex + put_gex
                total_gamma += strike_gamma
                
                # Check if within 100 points of max gamma strike
                if abs(strike - max_gamma_strike) <= 100:
                    nearby_gamma += strike_gamma
            
            if total_gamma > 0:
                concentration = (nearby_gamma / total_gamma) * 100
                return min(100, concentration)
            
            return 0
            
        except Exception as e:
            logger.error(f"Error calculating gamma concentration: {e}")
            return 0
    
    def _analyze_liquidity_profile(self, strikes: Dict[float, Dict], days_to_expiry: int) -> Dict[str, Any]:
        """Analyze liquidity profile for expiry"""
        try:
            total_volume = 0
            total_oi = 0
            active_strikes = 0
            
            for strike_data in strikes.values():
                call_data = strike_data.get("call", {})
                put_data = strike_data.get("put", {})
                
                total_volume += call_data.get("volume", 0) + put_data.get("volume", 0)
                total_oi += call_data.get("oi", 0) + put_data.get("oi", 0)
                
                if (call_data.get("volume", 0) > 0 or put_data.get("volume", 0) > 0 or
                    call_data.get("oi", 0) > 0 or put_data.get("oi", 0) > 0):
                    active_strikes += 1
            
            # Liquidity classification
            if days_to_expiry <= self.CRITICAL_EXPIRY_DAYS:
                if total_volume > 1000000:  # High volume
                    liquidity_level = "very_high"
                elif total_volume > 500000:
                    liquidity_level = "high"
                elif total_volume > 100000:
                    liquidity_level = "medium"
                else:
                    liquidity_level = "low"
            else:
                if total_oi > 10000000:
                    liquidity_level = "very_high"
                elif total_oi > 5000000:
                    liquidity_level = "high"
                elif total_oi > 1000000:
                    liquidity_level = "medium"
                else:
                    liquidity_level = "low"
            
            return {
                "liquidity_level": liquidity_level,
                "total_volume": total_volume,
                "total_oi": total_oi,
                "active_strikes": active_strikes,
                "avg_volume_per_strike": total_volume / active_strikes if active_strikes > 0 else 0,
                "avg_oi_per_strike": total_oi / active_strikes if active_strikes > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing liquidity profile: {e}")
            return {"liquidity_level": "unknown"}
    
    def _determine_expiry_risk_level(self, days_to_expiry: int, pin_probability: float) -> str:
        """Determine overall expiry risk level"""
        if days_to_expiry <= self.CRITICAL_EXPIRY_DAYS:
            if pin_probability >= 70:
                return "critical"
            elif pin_probability >= 50:
                return "high"
            else:
                return "medium"
        elif days_to_expiry <= self.HIGH_RISK_EXPIRY_DAYS:
            if pin_probability >= 60:
                return "high"
            elif pin_probability >= 40:
                return "medium"
            else:
                return "low"
        else:
            if pin_probability >= 50:
                return "medium"
            else:
                return "low"
    
    def _get_recommended_strategies(self, risk_level: str, pin_probability: float, days_to_expiry: int) -> List[str]:
        """Get recommended trading strategies based on expiry analysis"""
        strategies = []
        
        if risk_level == "critical":
            strategies.extend([
                "avoid_directional_positions",
                "consider_straddles",
                "monitor_pin_zone_closely",
                "reduce_position_size"
            ])
        elif risk_level == "high":
            strategies.extend([
                "use_range_bound_strategies",
                "consider_iron_condors",
                "watch_for_breakouts",
                "tight_stops_required"
            ])
        elif risk_level == "medium":
            strategies.extend([
                "standard_options_strategies",
                "monitor_key_levels",
                "consider_theta_capture"
            ])
        else:
            strategies.extend([
                "normal_trading_approach",
                "focus_on_underlying_analysis",
                "standard_risk_management"
            ])
        
        # Add expiry-specific strategies
        if days_to_expiry <= self.CRITICAL_EXPIRY_DAYS:
            strategies.append("intraday_focus")
            strategies.append("avoid_overnight_risk")
        elif pin_probability >= 60:
            strategies.append("pin_risk_management")
        
        return strategies
    
    def _identify_key_levels(self, spot: float, max_oi_strike: float, max_gamma_strike: float, strikes: Dict[float, Dict]) -> Dict[str, float]:
        """Identify key levels for expiry trading"""
        key_levels = {
            "spot": spot,
            "max_oi_strike": max_oi_strike,
            "max_gamma_strike": max_gamma_strike
        }
        
        # Find support and resistance based on OI
        call_oi_by_strike = {}
        put_oi_by_strike = {}
        
        for strike, strike_data in strikes.items():
            call_oi_by_strike[strike] = strike_data.get("call", {}).get("oi", 0)
            put_oi_by_strike[strike] = strike_data.get("put", {}).get("oi", 0)
        
        # Find resistance (highest call OI above spot)
        resistance_candidates = [(strike, oi) for strike, oi in call_oi_by_strike.items() if strike > spot]
        if resistance_candidates:
            key_levels["resistance"] = max(resistance_candidates, key=lambda x: x[1])[0]
        
        # Find support (highest put OI below spot)
        support_candidates = [(strike, oi) for strike, oi in put_oi_by_strike.items() if strike < spot]
        if support_candidates:
            key_levels["support"] = max(support_candidates, key=lambda x: x[1])[0]
        
        return key_levels
    
    def _create_default_analysis(self, symbol: str, days_to_expiry: int, spot: float) -> ExpiryAnalysis:
        """Create default analysis for error cases"""
        return ExpiryAnalysis(
            symbol=symbol,
            days_to_expiry=days_to_expiry,
            max_oi_strike=spot,
            max_gamma_strike=spot,
            max_oi_value=0,
            max_gamma_value=0,
            distance_to_max_oi=0,
            distance_to_max_gamma=0,
            distance_to_atm=0,
            pin_probability=50,
            magnet_strength=50,
            pin_zone=(spot - 50, spot + 50),
            time_decay_factor=0.5,
            gamma_concentration=0,
            liquidity_profile={"liquidity_level": "unknown"},
            expiry_risk_level="medium",
            recommended_strategies=["cautious_approach"],
            key_levels={"spot": spot}
        )
    
    def format_for_frontend(self, analysis: ExpiryAnalysis) -> Dict[str, Any]:
        """Format expiry analysis for frontend consumption"""
        return {
            "symbol": analysis.symbol,
            "days_to_expiry": analysis.days_to_expiry,
            "expiry_risk_level": analysis.expiry_risk_level,
            "pin_probability": analysis.pin_probability,
            "magnet_strength": analysis.magnet_strength,
            
            # Key strikes
            "max_oi_strike": analysis.max_oi_strike,
            "max_gamma_strike": analysis.max_gamma_strike,
            "pin_zone": {
                "lower_bound": analysis.pin_zone[0],
                "upper_bound": analysis.pin_zone[1],
                "width": analysis.pin_zone[1] - analysis.pin_zone[0]
            },
            
            # Distances
            "distance_to_max_oi": analysis.distance_to_max_oi,
            "distance_to_max_gamma": analysis.distance_to_max_gamma,
            "distance_to_atm": analysis.distance_to_atm,
            
            # Expiry factors
            "time_decay_factor": analysis.time_decay_factor,
            "gamma_concentration": analysis.gamma_concentration,
            "liquidity_profile": analysis.liquidity_profile,
            
            # Trading guidance
            "recommended_strategies": analysis.recommended_strategies,
            "key_levels": analysis.key_levels,
            
            # Summary
            "summary": {
                "pin_risk": "high" if analysis.pin_probability >= 70 else "medium" if analysis.pin_probability >= 40 else "low",
                "magnet_strength_level": "strong" if analysis.magnet_strength >= 70 else "moderate" if analysis.magnet_strength >= 40 else "weak",
                "expiry_urgency": "critical" if analysis.days_to_expiry <= 3 else "high" if analysis.days_to_expiry <= 7 else "normal"
            },
            
            # Alerts
            "alerts": self._generate_expiry_alerts(analysis)
        }
    
    def _generate_expiry_alerts(self, analysis: ExpiryAnalysis) -> List[Dict[str, Any]]:
        """Generate expiry-specific alerts"""
        alerts = []
        
        # Critical expiry alert
        if analysis.days_to_expiry <= self.CRITICAL_EXPIRY_DAYS:
            alerts.append({
                "type": "critical_expiry",
                "severity": "high",
                "message": f"Critical expiry: {analysis.days_to_expiry} days remaining. Pin risk elevated."
            })
        
        # High pin probability alert
        if analysis.pin_probability >= 70:
            alerts.append({
                "type": "high_pin_probability",
                "severity": "high",
                "message": f"High pin probability ({analysis.pin_probability:.0f}%). Price may get pinned."
            })
        
        # Strong magnet alert
        if analysis.magnet_strength >= 80:
            alerts.append({
                "type": "strong_magnet",
                "severity": "medium",
                "message": f"Strong magnet detected. Price likely to gravitate to pin zone."
            })
        
        # Close to max OI alert
        if analysis.distance_to_max_oi <= 25:
            alerts.append({
                "type": "near_max_oi",
                "severity": "medium",
                "message": f"Spot very close to max OI strike ({analysis.distance_to_max_oi:.0f} points)."
            })
        
        return alerts
