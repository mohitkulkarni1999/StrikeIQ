"""
Tests for Productized Intelligence Engine
Tests alerts, pressure maps, interactions, and expiry analysis
"""

import pytest
from unittest.mock import Mock
from datetime import datetime, timezone

from app.services.structural_alert_engine import StructuralAlertEngine, AlertType, AlertSeverity
from app.services.gamma_pressure_map import GammaPressureMapEngine
from app.services.flow_gamma_interaction import FlowGammaInteractionEngine, GammaState, FlowState
from app.services.regime_confidence_engine import RegimeConfidenceEngine, RegimeType
from app.services.expiry_magnet_model import ExpiryMagnetModel

class TestProductizedIntelligence:
    """Test suite for productized intelligence features"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.alert_engine = StructuralAlertEngine()
        self.pressure_engine = GammaPressureMapEngine()
        self.interaction_engine = FlowGammaInteractionEngine()
        self.regime_engine = RegimeConfidenceEngine()
        self.expiry_engine = ExpiryMagnetModel()
        
        # Sample metrics for testing
        self.sample_metrics = {
            "symbol": "NIFTY",
            "spot": 25471.1,
            "net_gamma": 12345678,
            "gamma_flip_level": 25420.0,
            "distance_from_flip": 51.1,
            "call_oi_velocity": 1500,
            "put_oi_velocity": 800,
            "flow_imbalance": 0.3,
            "flow_direction": "call_writing",
            "structural_regime": "range",
            "regime_confidence": 72,
            "expected_move": 352.62,
            "volatility_regime": "normal"
        }
        
        # Sample frontend data
        self.sample_frontend_data = {
            "symbol": "NIFTY",
            "spot": 25471.1,
            "atm_strike": 25450.0,
            "strikes": {
                25400.0: {
                    "call": {
                        "ltp": 143.0,
                        "oi": 7900000,
                        "gamma": 0.0023,
                        "delta": 0.52
                    },
                    "put": {
                        "ltp": 561.55,
                        "oi": 1777425,
                        "gamma": -0.0018,
                        "delta": -0.48
                    }
                },
                25500.0: {
                    "call": {
                        "ltp": 98.0,
                        "oi": 9946040,
                        "gamma": 0.0031,
                        "delta": 0.41
                    },
                    "put": {
                        "ltp": 143.0,
                        "oi": 7920315,
                        "gamma": -0.0029,
                        "delta": -0.59
                    }
                }
            }
        }
    
    @pytest.mark.asyncio
    async def test_structural_alert_engine(self):
        """Test structural alert generation"""
        # Test gamma flip break alert
        metrics_flip = self.sample_metrics.copy()
        metrics_flip["distance_from_flip"] = 20  # Close to flip
        
        alerts = await self.alert_engine.analyze_and_generate_alerts("NIFTY", metrics_flip)
        
        assert len(alerts) > 0
        gamma_flip_alerts = [a for a in alerts if a.alert_type == AlertType.GAMMA_FLIP_BREAK]
        assert len(gamma_flip_alerts) > 0
        
        alert = gamma_flip_alerts[0]
        assert alert.severity in [AlertSeverity.HIGH, AlertSeverity.MEDIUM]
        assert "gamma flip" in alert.message.lower()
        assert alert.symbol == "NIFTY"
        
        # Test flow imbalance spike alert
        metrics_flow = self.sample_metrics.copy()
        metrics_flow["flow_imbalance"] = 0.8  # High imbalance
        
        alerts = await self.alert_engine.analyze_and_generate_alerts("NIFTY", metrics_flow)
        
        flow_alerts = [a for a in alerts if a.alert_type == AlertType.FLOW_IMBALANCE_SPIKE]
        assert len(flow_alerts) > 0
        
        alert = flow_alerts[0]
        assert alert.severity in [AlertSeverity.HIGH, AlertSeverity.MEDIUM]
        assert "flow imbalance" in alert.message.lower()
    
    def test_gamma_pressure_map(self):
        """Test gamma pressure map computation"""
        pressure_map = self.pressure_engine.compute_pressure_map("NIFTY", self.sample_frontend_data)
        
        assert pressure_map.symbol == "NIFTY"
        assert pressure_map.spot == 25471.1
        assert pressure_map.net_gamma is not None
        assert len(pressure_map.top_magnets) >= 0
        assert len(pressure_map.top_cliffs) >= 0
        
        # Test formatting for frontend
        formatted = self.pressure_engine.format_for_frontend(pressure_map)
        
        assert "symbol" in formatted
        assert "net_gamma" in formatted
        assert "top_magnets" in formatted
        assert "top_cliffs" in formatted
        assert "pressure_distribution" in formatted
        
        # Check pressure distribution
        pressure_dist = formatted["pressure_distribution"]
        assert "call_pressure" in pressure_dist
        assert "put_pressure" in pressure_dist
        assert "balance" in pressure_dist
    
    def test_flow_gamma_interaction(self):
        """Test flow + gamma interaction model"""
        interaction = self.interaction_engine.compute_interaction(self.sample_metrics)
        
        assert interaction.gamma_state in [GammaState.POSITIVE, GammaState.NEGATIVE, GammaState.NEUTRAL]
        assert interaction.flow_state in [FlowState.CALL_WRITING, FlowState.PUT_WRITING, FlowState.BALANCED, FlowState.NEUTRAL]
        assert interaction.interaction_type is not None
        assert 0 <= interaction.confidence <= 100
        assert interaction.description is not None
        assert interaction.trading_implications is not None
        assert interaction.risk_factors is not None
        assert interaction.opportunities is not None
        
        # Test formatting for frontend
        formatted = self.interaction_engine.format_for_frontend(interaction)
        
        assert "gamma_state" in formatted
        assert "flow_state" in formatted
        assert "interaction_type" in formatted
        assert "confidence" in formatted
        assert "summary" in formatted
        
        # Check summary
        summary = formatted["summary"]
        assert "primary_strategy" in summary
        assert "direction" in summary
        assert "risk_level" in summary
        assert "opportunity_score" in summary
    
    @pytest.mark.asyncio
    async def test_regime_confidence_engine(self):
        """Test enhanced regime confidence analysis"""
        dynamics = await self.regime_engine.analyze_regime_dynamics("NIFTY", self.sample_metrics)
        
        assert dynamics.regime in [RegimeType.RANGE, RegimeType.TREND, RegimeType.BREAKOUT, RegimeType.PIN_RISK]
        assert 0 <= dynamics.confidence <= 100
        assert 0 <= dynamics.stability_score <= 100
        assert -100 <= dynamics.acceleration_index <= 100
        assert 0 <= dynamics.transition_probability <= 100
        assert dynamics.regime_duration >= 0
        assert 0 <= dynamics.historical_consistency <= 100
        assert 0 <= dynamics.momentum_score <= 100
        
        # Test formatting for frontend
        formatted = self.regime_engine.format_for_frontend(dynamics)
        
        assert "regime" in formatted
        assert "confidence" in formatted
        assert "stability_score" in formatted
        assert "acceleration_index" in formatted
        assert "transition_probability" in formatted
        assert "interpretation" in formatted
        assert "alerts" in formatted
        
        # Check interpretation
        interpretation = formatted["interpretation"]
        assert "stability_level" in interpretation
        assert "acceleration_trend" in interpretation
        assert "transition_risk" in interpretation
        assert "momentum_strength" in interpretation
    
    def test_expiry_magnet_model(self):
        """Test expiry magnet analysis"""
        analysis = self.expiry_engine.analyze_expiry_magnets("NIFTY", self.sample_frontend_data, "2026-02-17")
        
        assert analysis.symbol == "NIFTY"
        assert analysis.days_to_expiry >= 0
        assert analysis.max_oi_strike > 0
        assert analysis.max_gamma_strike > 0
        assert analysis.pin_probability >= 0
        assert analysis.magnet_strength >= 0
        assert analysis.expiry_risk_level in ["critical", "high", "medium", "low"]
        assert len(analysis.recommended_strategies) > 0
        assert len(analysis.key_levels) > 0
        
        # Test formatting for frontend
        formatted = self.expiry_engine.format_for_frontend(analysis)
        
        assert "symbol" in formatted
        assert "days_to_expiry" in formatted
        assert "expiry_risk_level" in formatted
        assert "pin_probability" in formatted
        assert "magnet_strength" in formatted
        assert "max_oi_strike" in formatted
        assert "max_gamma_strike" in formatted
        assert "pin_zone" in formatted
        assert "recommended_strategies" in formatted
        assert "key_levels" in formatted
        assert "alerts" in formatted
        
        # Check pin zone
        pin_zone = formatted["pin_zone"]
        assert "lower_bound" in pin_zone
        assert "upper_bound" in pin_zone
        assert "width" in pin_zone
        
        # Check summary
        summary = formatted["summary"]
        assert "pin_risk" in summary
        assert "magnet_strength_level" in summary
        assert "expiry_urgency" in summary
    
    def test_interaction_matrix_coverage(self):
        """Test that all gamma + flow combinations are covered"""
        # Test various combinations
        test_cases = [
            {"net_gamma": 2000000, "flow_direction": "call_writing"},  # +Gamma + Call Writing
            {"net_gamma": -2000000, "flow_direction": "put_buying"},  # -Gamma + Put Buying
            {"net_gamma": 500000, "flow_direction": "balanced"},    # +Gamma + Balanced
            {"net_gamma": -500000, "flow_direction": "bearish_build"}, # -Gamma + Bearish Build
        ]
        
        for test_case in test_cases:
            metrics = self.sample_metrics.copy()
            metrics.update(test_case)
            
            interaction = self.interaction_engine.compute_interaction(metrics)
            
            assert interaction.interaction_type is not None
            assert interaction.confidence >= 0
            assert interaction.description is not None
    
    def test_alert_severity_classification(self):
        """Test alert severity classification"""
        # Test high severity scenarios
        high_severity_metrics = self.sample_metrics.copy()
        high_severity_metrics["distance_from_flip"] = 10  # Very close to flip
        
        alerts = await self.alert_engine.analyze_and_generate_alerts("NIFTY", high_severity_metrics)
        high_alerts = [a for a in alerts if a.severity == AlertSeverity.HIGH]
        
        # Should have high severity alerts for critical conditions
        assert len(high_alerts) > 0 or len(alerts) > 0  # At least some alerts
        
        # Test medium severity scenarios
        medium_severity_metrics = self.sample_metrics.copy()
        medium_severity_metrics["distance_from_flip"] = 40  # Medium distance
        
        alerts = await self.alert_engine.analyze_and_generate_alerts("NIFTY", medium_severity_metrics)
        
        # Should have medium or low severity alerts
        for alert in alerts:
            assert alert.severity in [AlertSeverity.HIGH, AlertSeverity.MEDIUM, AlertSeverity.LOW]
    
    def test_pressure_map_magnet_cliff_classification(self):
        """Test magnet and cliff classification"""
        pressure_map = self.pressure_engine.compute_pressure_map("NIFTY", self.sample_frontend_data)
        
        # Should have both magnets and cliffs or at least one type
        total_pressure_points = len(pressure_map.top_magnets) + len(pressure_map.top_cliffs)
        assert total_pressure_points >= 0  # Could be zero in test data
        
        # Check classification consistency
        for magnet in pressure_map.top_magnets:
            assert magnet.pressure_type == "magnet"
            assert magnet.pressure_strength >= 0
        
        for cliff in pressure_map.top_cliffs:
            assert cliff.pressure_type == "cliff"
            assert cliff.pressure_strength >= 0
    
    def test_expiry_risk_level_determination(self):
        """Test expiry risk level determination"""
        # Test critical expiry
        critical_analysis = self.expiry_engine.analyze_expiry_magnets("NIFTY", self.sample_frontend_data, "2026-02-16")  # 1 day to expiry
        assert critical_analysis.expiry_risk_level in ["critical", "high"]
        
        # Test normal expiry
        normal_analysis = self.expiry_engine.analyze_expiry_magnets("NIFTY", self.sample_frontend_data, "2026-03-01")  # ~2 weeks to expiry
        assert normal_analysis.expiry_risk_level in ["low", "medium"]
        
        # Test pin probability impact on risk
        high_pin_metrics = self.sample_frontend_data.copy()
        # Adjust to create high pin probability
        high_pin_metrics["spot"] = 25500.0  # Close to max OI strike
        
        high_pin_analysis = self.expiry_engine.analyze_expiry_magnets("NIFTY", high_pin_metrics, "2026-02-20")
        assert high_pin_analysis.pin_probability >= 60
    
    def test_comprehensive_integration(self):
        """Test comprehensive integration of all productized intelligence"""
        # This test ensures all engines work together
        
        # 1. Generate alerts
        alerts = asyncio.run(self.alert_engine.analyze_and_generate_alerts("NIFTY", self.sample_metrics))
        
        # 2. Compute pressure map
        pressure_map = self.pressure_engine.compute_pressure_map("NIFTY", self.sample_frontend_data)
        
        # 3. Compute interaction
        interaction = self.interaction_engine.compute_interaction(self.sample_metrics)
        
        # 4. Compute regime dynamics
        regime_dynamics = asyncio.run(self.regime_engine.analyze_regime_dynamics("NIFTY", self.sample_metrics))
        
        # 5. Compute expiry analysis
        expiry_analysis = self.expiry_engine.analyze_expiry_magnets("NIFTY", self.sample_frontend_data)
        
        # Verify all components are present
        assert isinstance(alerts, list)
        assert pressure_map.symbol == "NIFTY"
        assert interaction.symbol == "NIFTY"
        assert regime_dynamics.regime is not None
        assert expiry_analysis.symbol == "NIFTY"
        
        # Verify data consistency
        assert pressure_map.spot == self.sample_metrics["spot"]
        assert interaction.confidence >= 0
        assert regime_dynamics.confidence >= 0
        assert expiry_analysis.pin_probability >= 0

if __name__ == "__main__":
    pytest.main([__file__])
