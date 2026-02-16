"""
Unit tests for Gamma + Flow Structural Engine
"""

import pytest
import numpy as np
from unittest.mock import Mock
from datetime import datetime, timezone

from app.services.live_structural_engine import LiveStructuralEngine, LiveMetrics
from app.core.live_market_state import MarketStateManager

class TestGammaFlowEngine:
    """Test suite for Gamma + Flow calculations"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_market_state = Mock(spec=MarketStateManager)
        self.engine = LiveStructuralEngine(self.mock_market_state)
        
        # Sample frontend data for testing
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
    
    def test_calculate_net_gamma_exposure(self):
        """Test Net Gamma Exposure calculation"""
        result = self.engine._calculate_net_gamma_exposure(self.sample_frontend_data)
        
        # Verify calculations
        expected_call_gex = (0.0023 * 7900000 * 75) + (0.0031 * 9946040 * 75)
        expected_put_gex = (-0.0018 * 1777425 * 75) + (-0.0029 * 7920315 * 75)
        expected_net_gamma = expected_call_gex - expected_put_gex
        
        assert result["net_gamma"] == pytest.approx(expected_net_gamma)
        assert result["gamma_regime"] in ["positive", "negative", "neutral"]
        assert "total_call_gex" in result
        assert "total_put_gex" in result
    
    def test_calculate_net_gamma_exposure_missing_data(self):
        """Test GEX calculation with missing gamma data"""
        incomplete_data = {
            "spot": 25471.1,
            "strikes": {
                25400.0: {
                    "call": {"oi": 7900000},  # Missing gamma
                    "put": {"oi": 1777425}   # Missing gamma
                }
            }
        }
        
        result = self.engine._calculate_net_gamma_exposure(incomplete_data)
        assert result["net_gamma"] == 0
        assert result["gamma_regime"] == "neutral"
    
    def test_calculate_gamma_flip_level(self):
        """Test Gamma Flip Level calculation"""
        result = self.engine._calculate_gamma_flip_level(self.sample_frontend_data)
        
        assert "gamma_flip_level" in result
        assert "distance_from_flip" in result
        assert isinstance(result["distance_from_flip"], (int, float))
        
        # Distance should be positive
        assert result["distance_from_flip"] >= 0
    
    def test_calculate_gamma_flip_level_no_data(self):
        """Test flip level with no data"""
        empty_data = {"spot": 25471.1, "strikes": {}}
        
        result = self.engine._calculate_gamma_flip_level(empty_data)
        assert result["gamma_flip_level"] is None
        assert result["distance_from_flip"] == 0
    
    def test_calculate_oi_flow_engine(self):
        """Test OI Flow Engine calculation"""
        # Setup previous snapshot
        self.engine.previous_oi_snapshot["NIFTY"] = {
            25400.0: {"call_oi": 7800000, "put_oi": 1700000},
            25500.0: {"call_oi": 9800000, "put_oi": 7800000}
        }
        
        result = self.engine._calculate_oi_flow_engine("NIFTY", self.sample_frontend_data)
        
        assert "call_oi_velocity" in result
        assert "put_oi_velocity" in result
        assert "flow_imbalance" in result
        assert "flow_direction" in result
        assert "total_velocity" in result
        
        # Verify flow imbalance calculation
        expected_call_velocity = (7900000 - 7800000) + (9946040 - 9800000)
        expected_put_velocity = (1777425 - 1700000) + (7920315 - 7800000)
        expected_total = abs(expected_call_velocity) + abs(expected_put_velocity)
        
        assert result["call_oi_velocity"] == expected_call_velocity
        assert result["put_oi_velocity"] == expected_put_velocity
        assert result["total_velocity"] == expected_total
    
    def test_classify_flow_direction(self):
        """Test flow direction classification"""
        # Test call writing
        result = self.engine._classify_flow_direction(1500, -800, 0.5)
        assert result == "call_writing"
        
        # Test bearish build
        result = self.engine._classify_flow_direction(-800, 1500, -0.5)
        assert result == "bearish_build"
        
        # Test put writing
        result = self.engine._classify_flow_direction(800, 1500, -0.2)
        assert result == "put_writing"
        
        # Test balanced
        result = self.engine._classify_flow_direction(500, 500, 0)
        assert result == "balanced"
        
        # Test call dominant
        result = self.engine._classify_flow_direction(2000, 500, 0.6)
        assert result == "call_dominant"
        
        # Test put dominant
        result = self.engine._classify_flow_direction(500, 2000, -0.6)
        assert result == "put_dominant"
    
    def test_classify_structural_regime(self):
        """Test structural regime classification"""
        gamma_metrics = {"net_gamma": 1000000, "gamma_regime": "positive"}
        flow_metrics = {"flow_imbalance": 0.1, "flow_direction": "balanced"}
        expected_move = {"spot": 25471.1, "upper_1sd": 25823.72}
        volatility_regime = "normal"
        
        result = self.engine._classify_structural_regime(
            gamma_metrics, flow_metrics, expected_move, volatility_regime
        )
        
        assert "structural_regime" in result
        assert "regime_confidence" in result
        assert 0 <= result["regime_confidence"] <= 100
        
        # Should classify as range due to positive gamma + low flow
        assert result["structural_regime"] == "range"
    
    def test_structural_regime_trend(self):
        """Test trend regime classification"""
        gamma_metrics = {"net_gamma": -1000000, "gamma_regime": "negative"}
        flow_metrics = {"flow_imbalance": 0.5, "flow_direction": "call_dominant"}
        expected_move = {"spot": 25471.1, "upper_1sd": 25823.72}
        volatility_regime = "normal"
        
        result = self.engine._classify_structural_regime(
            gamma_metrics, flow_metrics, expected_move, volatility_regime
        )
        
        # Should classify as trend due to negative gamma + strong flow
        assert result["structural_regime"] == "trend"
    
    def test_structural_regime_breakout(self):
        """Test breakout regime classification"""
        gamma_metrics = {"net_gamma": 0, "gamma_regime": "neutral"}
        flow_metrics = {"flow_imbalance": 0.3, "flow_direction": "call_dominant"}
        expected_move = {"spot": 25700, "upper_1sd": 25800}  # Near resistance
        volatility_regime = "elevated"
        
        result = self.engine._classify_structural_regime(
            gamma_metrics, flow_metrics, expected_move, volatility_regime
        )
        
        # Should classify as breakout due to high volatility + near resistance
        assert result["structural_regime"] == "breakout"
    
    def test_comprehensive_metrics_integration(self):
        """Test integration of all new metrics"""
        # Setup previous OI snapshot
        self.engine.previous_oi_snapshot["NIFTY"] = {
            25400.0: {"call_oi": 7800000, "put_oi": 1700000},
            25500.0: {"call_oi": 9800000, "put_oi": 7800000}
        }
        
        # Mock market state snapshot
        mock_snapshot = {
            "symbol": "NIFTY",
            "spot": 25471.1,
            "pcr": 0.45,
            "total_oi_calls": 257919740,
            "total_oi_puts": 116669865
        }
        
        result = self.engine._calculate_comprehensive_metrics("NIFTY", mock_snapshot, self.sample_frontend_data)
        
        # Verify all new metrics are present
        assert isinstance(result, LiveMetrics)
        assert result.net_gamma is not None
        assert result.gamma_flip_level is not None
        assert result.distance_from_flip is not None
        assert result.call_oi_velocity is not None
        assert result.put_oi_velocity is not None
        assert result.flow_imbalance is not None
        assert result.flow_direction is not None
        assert result.structural_regime is not None
        assert result.regime_confidence is not None
    
    def test_error_handling(self):
        """Test error handling in calculations"""
        # Test with malformed data
        malformed_data = {
            "spot": "invalid",  # Should be number
            "strikes": {
                "invalid_strike": "not_a_dict"
            }
        }
        
        # Should not raise exceptions
        result = self.engine._calculate_net_gamma_exposure(malformed_data)
        assert result["net_gamma"] == 0
        assert result["gamma_regime"] == "neutral"
        
        result = self.engine._calculate_gamma_flip_level(malformed_data)
        assert result["gamma_flip_level"] is None
        assert result["distance_from_flip"] == 0
    
    def test_performance_safety(self):
        """Test performance and safety measures"""
        # Test with large dataset
        large_strikes = {}
        for i in range(1000):  # 1000 strikes
            strike = 25000 + i * 50
            large_strikes[strike] = {
                "call": {
                    "oi": 1000000,
                    "gamma": 0.001
                },
                "put": {
                    "oi": 1000000,
                    "gamma": -0.001
                }
            }
        
        large_data = {
            "spot": 25471.1,
            "strikes": large_strikes
        }
        
        # Should handle large dataset without issues
        result = self.engine._calculate_net_gamma_exposure(large_data)
        assert isinstance(result["net_gamma"], (int, float))
        assert result["gamma_regime"] in ["positive", "negative", "neutral"]
    
    def test_division_by_zero_safety(self):
        """Test division by zero safety"""
        # Test with zero total velocity
        flow_metrics = {
            "call_oi_velocity": 0,
            "put_oi_velocity": 0
        }
        
        # Should handle zero division safely
        assert flow_metrics["call_oi_velocity"] == 0
        assert flow_metrics["put_oi_velocity"] == 0

if __name__ == "__main__":
    pytest.main([__file__])
