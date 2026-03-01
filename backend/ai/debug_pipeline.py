"""
Debug AI Pipeline - Identify issues in pipeline execution
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from app.services.live_structural_engine import LiveMetrics
from ai.ai_orchestrator import run_ai_pipeline

def create_bullish_metrics():
    """Create strong bullish LiveMetrics"""
    return LiveMetrics(
        symbol="BANKNIFTY",
        spot=45000.0,
        expected_move=400.0,
        upper_1sd=45400.0,
        lower_1sd=44600.0,
        upper_2sd=45800.0,
        lower_2sd=44200.0,
        breach_probability=20.0,
        range_hold_probability=80.0,
        gamma_regime="positive",
        intent_score=55.0,
        support_level=44700.0,
        resistance_level=45300.0,
        volatility_regime="normal",
        oi_velocity=500.0,
        pcr=1.45,
        total_oi=800000,
        timestamp=datetime.now(timezone.utc),
        net_gamma=80000.0,
        gamma_flip_level=44900.0,
        distance_from_flip=100.0,
        call_oi_velocity=400.0,
        put_oi_velocity=200.0,
        flow_imbalance=0.20,
        flow_direction="call",
        structural_regime="bullish",
        regime_confidence=0.65,
        alerts=[],
        gamma_pressure_map={},
        flow_gamma_interaction={},
        regime_dynamics={},
        expiry_magnet_analysis={}
    )

def debug_pipeline():
    """Debug AI pipeline step by step"""
    print("🔍 Debugging AI Pipeline...")
    
    metrics = create_bullish_metrics()
    
    try:
        print("Step 1: Running AI pipeline...")
        result = run_ai_pipeline(metrics)
        
        if result:
            print("✅ Pipeline returned result:")
            print(f"   Symbol: {result.get('symbol', 'N/A')}")
            print(f"   Strategy: {result.get('strategy', 'N/A')}")
            print(f"   Option: {result.get('option', 'N/A')}")
            print(f"   Entry: {result.get('entry', 0)}")
            print(f"   Target: {result.get('target', 0)}")
            print(f"   Stoploss: {result.get('stoploss', 0)}")
            print(f"   Confidence: {result.get('confidence', 0)}")
            print(f"   Risk Status: {result.get('risk_status', 'UNKNOWN')}")
            print(f"   Regime: {result.get('regime', 'UNKNOWN')}")
            print(f"   Risk/Reward: {result.get('risk_reward', 0)}")
            print(f"   Explanation count: {len(result.get('explanation', []))}")
            
            return True
        else:
            print("❌ Pipeline returned None")
            return False
            
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_pipeline()
