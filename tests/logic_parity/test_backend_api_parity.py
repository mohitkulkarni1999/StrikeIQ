"""
Backend-API Logic Parity Test
Captures backend AI engine outputs and compares with API responses
"""

import sys
import os
import pytest
import requests
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Import AI engines and components
from ai.ai_extension_layer import LiveMetrics
from ai.liquidity_engine import LiquidityEngine
from ai.stoploss_hunt_engine import StoplossHuntEngine
from ai.smart_money_engine import SmartMoneyEngine
from ai.gamma_squeeze_engine import GammaSqueezeEngine
from ai.options_trap_engine import OptionsTrapEngine
from ai.dealer_gamma_engine import DealerGammaEngine
from ai.liquidity_vacuum_engine import LiquidityVacuumEngine
from ai.ai_extension_layer import AIExtensionLayer

@dataclass
class ParityTestData:
    """Test data for parity validation"""
    test_id: str
    live_metrics: LiveMetrics
    engine_outputs: Dict[str, Any]
    api_responses: Dict[str, Any]
    timestamp: datetime

@dataclass
class FieldComparison:
    """Field comparison result"""
    field_name: str
    backend_value: Any
    api_value: Any
    frontend_value: Any = None
    backend_api_match: bool
    api_frontend_match: bool
    backend_frontend_match: bool
    overall_match: bool

class BackendAPIParityTest:
    """Tests logic consistency between backend AI engines and API responses"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Initialize AI engines
        self.engines = {
            'liquidity': LiquidityEngine(),
            'stoploss_hunt': StoplossHuntEngine(),
            'smart_money': SmartMoneyEngine(),
            'gamma_squeeze': GammaSqueezeEngine(),
            'options_trap': OptionsTrapEngine(),
            'dealer_gamma': DealerGammaEngine(),
            'liquidity_vacuum': LiquidityVacuumEngine()
        }
        
        self.extension_layer = AIExtensionLayer()
        self.test_data: List[ParityTestData] = []
        self.comparisons: List[FieldComparison] = []
    
    def create_test_scenarios(self) -> List[LiveMetrics]:
        """Create diverse test scenarios for comprehensive testing"""
        scenarios = []
        
        # Scenario 1: Bullish Market
        scenarios.append(LiveMetrics(
            spot_price=45200,
            pcr=1.25,
            net_gamma=-35000,
            gamma_flip_level=45300,
            support=44900,
            resistance=45500,
            volatility_regime="HIGH",
            oi_change=750000,
            vwap=45150,
            change=200,
            change_percent=0.44,
            volume=1500000,
            market_status="TRADING",
            rsi=75,
            momentum_score=0.8,
            regime="BULLISH",
            total_call_oi=6000000,
            total_put_oi=4800000,
            atm_strike=45200,
            theta=0.06,
            delta=0.6,
            gamma=0.025,
            vega=0.18,
            iv=28.0,
            iv_regime="HIGH",
            pcr_shift_z=2.1,
            atm_straddle=250,
            straddle_change_normalized=0.15,
            oi_acceleration_ratio=1.4,
            expected_move=120,
            time_to_expiry=5,
            liquidity_score=0.9,
            market_bias="BULLISH",
            flow_gamma_interaction=0.4,
            gamma_pressure_map={"level": "HIGH", "pressure": -0.4},
            structural_alert_level="HIGH"
        ))
        
        # Scenario 2: Bearish Market
        scenarios.append(LiveMetrics(
            spot_price=44700,
            pcr=0.85,
            net_gamma=-15000,
            gamma_flip_level=44800,
            support=44500,
            resistance=44900,
            volatility_regime="MEDIUM",
            oi_change=-250000,
            vwap=44750,
            change=-300,
            change_percent=-0.67,
            volume=2000000,
            market_status="TRADING",
            rsi=25,
            momentum_score=0.2,
            regime="BEARISH",
            total_call_oi=3500000,
            total_put_oi=4100000,
            atm_strike=44700,
            theta=0.04,
            delta=0.4,
            gamma=0.015,
            vega=0.12,
            iv=20.0,
            iv_regime="MEDIUM",
            pcr_shift_z=-1.2,
            atm_straddle=180,
            straddle_change_normalized=-0.08,
            oi_acceleration_ratio=0.8,
            expected_move=80,
            time_to_expiry=8,
            liquidity_score=0.6,
            market_bias="BEARISH",
            flow_gamma_interaction=-0.2,
            gamma_pressure_map={"level": "MEDIUM", "pressure": 0.2},
            structural_alert_level="MEDIUM"
        ))
        
        # Scenario 3: Neutral/Sideways Market
        scenarios.append(LiveMetrics(
            spot_price=45000,
            pcr=1.02,
            net_gamma=-22000,
            gamma_flip_level=45050,
            support=44850,
            resistance=45150,
            volatility_regime="LOW",
            oi_change=100000,
            vwap=45000,
            change=0,
            change_percent=0.0,
            volume=800000,
            market_status="TRADING",
            rsi=50,
            momentum_score=0.5,
            regime="NEUTRAL",
            total_call_oi=4900000,
            total_put_oi=5000000,
            atm_strike=45000,
            theta=0.03,
            delta=0.5,
            gamma=0.02,
            vega=0.14,
            iv=16.0,
            iv_regime="LOW",
            pcr_shift_z=0.1,
            atm_straddle=150,
            straddle_change_normalized=0.02,
            oi_acceleration_ratio=1.0,
            expected_move=60,
            time_to_expiry=10,
            liquidity_score=0.7,
            market_bias="NEUTRAL",
            flow_gamma_interaction=0.0,
            gamma_pressure_map={"level": "LOW", "pressure": 0.0},
            structural_alert_level="LOW"
        ))
        
        # Scenario 4: Extreme Volatility
        scenarios.append(LiveMetrics(
            spot_price=45350,
            pcr=1.45,
            net_gamma=-42000,
            gamma_flip_level=45400,
            support=45000,
            resistance=45700,
            volatility_regime="EXTREME",
            oi_change=1200000,
            vwap=45280,
            change=350,
            change_percent=0.78,
            volume=3000000,
            market_status="TRADING",
            rsi=85,
            momentum_score=0.95,
            regime="BULLISH",
            total_call_oi=7000000,
            total_put_oi=4800000,
            atm_strike=45350,
            theta=0.08,
            delta=0.7,
            gamma=0.03,
            vega=0.22,
            iv=35.0,
            iv_regime="EXTREME",
            pcr_shift_z=3.2,
            atm_straddle=320,
            straddle_change_normalized=0.25,
            oi_acceleration_ratio=1.8,
            expected_move=180,
            time_to_expiry=3,
            liquidity_score=0.95,
            market_bias="BULLISH",
            flow_gamma_interaction=0.6,
            gamma_pressure_map={"level": "EXTREME", "pressure": -0.6},
            structural_alert_level="HIGH"
        ))
        
        # Scenario 5: Gamma Squeeze Setup
        scenarios.append(LiveMetrics(
            spot_price=44900,
            pcr=0.95,
            net_gamma=-8000,
            gamma_flip_level=44950,
            support=44700,
            resistance=45100,
            volatility_regime="HIGH",
            oi_change=500000,
            vwap=44920,
            change=-100,
            change_percent=-0.22,
            volume=1800000,
            market_status="TRADING",
            rsi=35,
            momentum_score=0.3,
            regime="BEARISH",
            total_call_oi=4200000,
            total_put_oi=4400000,
            atm_strike=44900,
            theta=0.05,
            delta=0.45,
            gamma=0.018,
            vega=0.16,
            iv=24.0,
            iv_regime="HIGH",
            pcr_shift_z=-0.5,
            atm_straddle=200,
            straddle_change_normalized=-0.05,
            oi_acceleration_ratio=1.1,
            expected_move=90,
            time_to_expiry=6,
            liquidity_score=0.75,
            market_bias="BEARISH",
            flow_gamma_interaction=-0.1,
            gamma_pressure_map={"level": "HIGH", "pressure": 0.1},
            structural_alert_level="MODERATE"
        ))
        
        return scenarios
    
    def run_ai_engines(self, metrics: LiveMetrics) -> Dict[str, Any]:
        """Run all AI engines and collect outputs"""
        engine_outputs = {}
        
        for name, engine in self.engines.items():
            try:
                if hasattr(engine, 'analyze'):
                    output = engine.analyze(metrics)
                elif hasattr(engine, 'detect_trap'):
                    output = engine.detect_trap(metrics)
                else:
                    continue
                
                engine_outputs[name] = output
                
            except Exception as e:
                engine_outputs[name] = {"error": str(e)}
        
        # Run extension layer
        try:
            extension_output = self.extension_layer.analyze_advanced_signals(metrics)
            engine_outputs['extension_layer'] = extension_output
        except Exception as e:
            engine_outputs['extension_layer'] = {"error": str(e)}
        
        return engine_outputs
    
    def extract_key_fields_from_engines(self, engine_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key fields from AI engine outputs"""
        fields = {
            'pcr': None,
            'net_gamma': None,
            'support': None,
            'resistance': None,
            'signal': None,
            'confidence': None
        }
        
        # Extract from individual engines
        for engine_name, output in engine_outputs.items():
            if isinstance(output, dict) and 'error' not in output:
                # Look for signal and confidence
                if 'signal' in output and fields['signal'] is None:
                    fields['signal'] = output['signal']
                
                if 'confidence' in output and fields['confidence'] is None:
                    fields['confidence'] = output['confidence']
        
        return fields
    
    def call_api_endpoints(self) -> Dict[str, Any]:
        """Call API endpoints and collect responses"""
        api_responses = {}
        
        try:
            # Get metrics
            metrics_response = self.session.get(f"{self.base_url}/metrics", timeout=10)
            if metrics_response.status_code == 200:
                api_responses['metrics'] = metrics_response.json()
            
            # Get signals
            signals_response = self.session.get(f"{self.base_url}/signals", timeout=10)
            if signals_response.status_code == 200:
                api_responses['signals'] = signals_response.json()
            
            # Get market state
            market_state_response = self.session.get(f"{self.base_url}/market-state", timeout=10)
            if market_state_response.status_code == 200:
                api_responses['market_state'] = market_state_response.json()
            
            # Get AI analysis
            ai_analysis_response = self.session.get(f"{self.base_url}/ai-analysis", timeout=10)
            if ai_analysis_response.status_code == 200:
                api_responses['ai_analysis'] = ai_analysis_response.json()
                
        except Exception as e:
            print(f"API call error: {e}")
        
        return api_responses
    
    def extract_key_fields_from_api(self, api_responses: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key fields from API responses"""
        fields = {
            'pcr': None,
            'net_gamma': None,
            'support': None,
            'resistance': None,
            'signal': None,
            'confidence': None
        }
        
        # Extract from metrics endpoint
        if 'metrics' in api_responses:
            metrics = api_responses['metrics']
            if 'pcr' in metrics:
                fields['pcr'] = metrics['pcr']
            if 'net_gamma' in metrics:
                fields['net_gamma'] = metrics['net_gamma']
            if 'support' in metrics:
                fields['support'] = metrics['support']
            if 'resistance' in metrics:
                fields['resistance'] = metrics['resistance']
        
        # Extract from signals endpoint
        if 'signals' in api_responses:
            signals = api_responses['signals']
            if 'signals' in signals and signals['signals']:
                first_signal = signals['signals'][0]
                if 'signal' in first_signal:
                    fields['signal'] = first_signal['signal']
                if 'confidence' in first_signal:
                    fields['confidence'] = first_signal['confidence']
        
        # Extract from market state
        if 'market_state' in api_responses:
            market_state = api_responses['market_state']
            if 'data' in market_state:
                data = market_state['data']
                if 'pcr' in data:
                    fields['pcr'] = data['pcr']
                if 'net_gamma' in data:
                    fields['net_gamma'] = data['net_gamma']
                if 'support' in data:
                    fields['support'] = data['support']
                if 'resistance' in data:
                    fields['resistance'] = data['resistance']
        
        # Extract from AI analysis
        if 'ai_analysis' in api_responses:
            ai_analysis = api_responses['ai_analysis']
            if 'analysis' in ai_analysis:
                analysis = ai_analysis['analysis']
                if 'signal' in analysis:
                    fields['signal'] = analysis['signal']
                if 'confidence' in analysis:
                    fields['confidence'] = analysis['confidence']
        
        return fields
    
    def compare_values(self, backend_value: Any, api_value: Any, field_name: str) -> bool:
        """Compare backend and API values with tolerance"""
        if backend_value is None or api_value is None:
            return backend_value == api_value
        
        # For numeric values, use tolerance
        if isinstance(backend_value, (int, float)) and isinstance(api_value, (int, float)):
            tolerance = 0.01  # 1% tolerance or 0.01 absolute
            return abs(backend_value - api_value) <= tolerance
        
        # For string values, exact match
        if isinstance(backend_value, str) and isinstance(api_value, str):
            return backend_value.strip() == api_value.strip()
        
        # Direct comparison for other types
        return backend_value == api_value
    
    def run_parity_test(self, test_id: str, metrics: LiveMetrics) -> ParityTestData:
        """Run parity test for a single scenario"""
        print(f"\n🔍 Running parity test {test_id}...")
        
        # Run AI engines
        engine_outputs = self.run_ai_engines(metrics)
        backend_fields = self.extract_key_fields_from_engines(engine_outputs)
        
        # Call API endpoints
        api_responses = self.call_api_endpoints()
        api_fields = self.extract_key_fields_from_api(api_responses)
        
        # Create test data
        test_data = ParityTestData(
            test_id=test_id,
            live_metrics=metrics,
            engine_outputs=engine_outputs,
            api_responses=api_responses,
            timestamp=datetime.now()
        )
        
        # Compare fields
        for field_name in ['pcr', 'net_gamma', 'support', 'resistance', 'signal', 'confidence']:
            backend_val = backend_fields.get(field_name)
            api_val = api_fields.get(field_name)
            
            match = self.compare_values(backend_val, api_val, field_name)
            
            comparison = FieldComparison(
                field_name=field_name,
                backend_value=backend_val,
                api_value=api_val,
                backend_api_match=match,
                api_frontend_match=False,  # Will be set in frontend test
                backend_frontend_match=False,  # Will be set in frontend test
                overall_match=match
            )
            
            self.comparisons.append(comparison)
            
            status = "✅ PASS" if match else "❌ FAIL"
            print(f"  {field_name}: Backend={backend_val}, API={api_val} -> {status}")
        
        return test_data
    
    def run_all_tests(self) -> List[ParityTestData]:
        """Run all parity tests"""
        print("🚀 Starting Backend-API Logic Parity Tests")
        print("=" * 60)
        
        scenarios = self.create_test_scenarios()
        self.test_data = []
        self.comparisons = []
        
        for i, metrics in enumerate(scenarios, 1):
            test_id = f"scenario_{i}"
            test_data = self.run_parity_test(test_id, metrics)
            self.test_data.append(test_data)
        
        return self.test_data
    
    def generate_comparison_table(self) -> str:
        """Generate comparison table for report"""
        table_lines = []
        table_lines.append("| Field | Backend | API | Status |")
        table_lines.append("| ----- | ------- | --- | ------ |")
        
        for comparison in self.comparisons:
            backend_val = comparison.backend_value if comparison.backend_value is not None else "N/A"
            api_val = comparison.api_value if comparison.api_value is not None else "N/A"
            status = "PASS" if comparison.backend_api_match else "FAIL"
            
            table_lines.append(f"| {comparison.field_name} | {backend_val} | {api_val} | {status} |")
        
        return "\n".join(table_lines)
    
    def save_test_data(self, filename: str = "backend_api_parity_data.json"):
        """Save test data for frontend comparison"""
        data_to_save = {
            "test_data": [],
            "comparisons": []
        }
        
        for test_data in self.test_data:
            # Convert LiveMetrics to dict for JSON serialization
            metrics_dict = {
                "spot_price": test_data.live_metrics.spot_price,
                "pcr": test_data.live_metrics.pcr,
                "net_gamma": test_data.live_metrics.net_gamma,
                "support": test_data.live_metrics.support,
                "resistance": test_data.live_metrics.resistance,
                "timestamp": test_data.timestamp.isoformat()
            }
            
            data_to_save["test_data"].append({
                "test_id": test_data.test_id,
                "live_metrics": metrics_dict,
                "backend_fields": self.extract_key_fields_from_engines(test_data.engine_outputs),
                "api_fields": self.extract_key_fields_from_api(test_data.api_responses)
            })
        
        for comparison in self.comparisons:
            data_to_save["comparisons"].append({
                "field_name": comparison.field_name,
                "backend_value": comparison.backend_value,
                "api_value": comparison.api_value,
                "backend_api_match": comparison.backend_api_match
            })
        
        with open(filename, 'w') as f:
            json.dump(data_to_save, f, indent=2)
        
        print(f"✅ Test data saved to {filename}")

def run_backend_api_parity_tests():
    """Run backend-API parity tests"""
    test_suite = BackendAPIParityTest()
    test_data = test_suite.run_all_tests()
    
    # Generate comparison table
    comparison_table = test_suite.generate_comparison_table()
    
    # Save test data for frontend comparison
    test_suite.save_test_data()
    
    return test_data, comparison_table

if __name__ == "__main__":
    test_data, comparison_table = run_backend_api_parity_tests()
    print("\n" + "=" * 60)
    print("Backend-API Parity Test Complete")
    print("=" * 60)
    print(comparison_table)
