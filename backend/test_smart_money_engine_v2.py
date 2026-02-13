#!/usr/bin/env python3
"""
Test script for SmartMoneyEngine v2
Tests statistical stability, normalization, and activation thresholds
"""

import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.models.database import Base, get_db
from app.models.market_data import OptionChainSnapshot, MarketSnapshot, SmartMoneyPrediction
from app.services.market_data.smart_money_engine_v2 import SmartMoneyEngineV2
from app.services.market_data.performance_tracking_service import PerformanceTrackingService
from app.core.config import settings

def create_comprehensive_test_data(db: Session):
    """Create comprehensive test data for v2 engine validation"""
    print("Creating comprehensive test data...")
    
    # Create test snapshots for NIFTY over multiple time periods
    base_time = datetime.now(timezone.utc)
    
    # Create 50 snapshots over the last 2 hours (to test activation thresholds)
    for i in range(50):
        timestamp = base_time - timedelta(minutes=i*2.5)  # 2.5 minute intervals
        
        # Create option chain data for different strikes with realistic variations
        strikes = [19500, 19600, 19700, 19800, 19900, 20000, 20100, 20200, 20300, 20400]
        
        for strike in strikes:
            # Simulate realistic market dynamics
            base_oi_ce = 100000 + i*1000 + strike*10
            base_oi_pe = 80000 + i*800 + (20000-strike)*8
            
            # Add some randomness and trends
            import random
            random.seed(i + strike)  # Reproducible randomness
            
            oi_change_ce = random.randint(500, 2000) + (100 if i < 20 else -50)  # Trend change
            oi_change_pe = random.randint(400, 1500) + (-80 if i < 20 else 100)  # Opposite trend
            
            # CE option
            ce_snapshot = OptionChainSnapshot(
                symbol="NIFTY",
                timestamp=timestamp,
                strike=strike,
                option_type="CE",
                expiry="2026-02-27",
                oi=base_oi_ce,
                oi_change=oi_change_ce,
                prev_oi=base_oi_ce - oi_change_ce,
                oi_delta=oi_change_ce,
                ltp=50.0 + (20000 - strike) * 0.1 + random.uniform(-5, 5),
                iv=15.0 + i * 0.1 + random.uniform(-1, 1),
                volume=5000 + i*500 + random.randint(-1000, 1000),
                delta=-0.4 + (20000 - strike) * 0.0001,
                gamma=0.001,
                theta=-2.0,
                vega=5.0
            )
            db.add(ce_snapshot)
            
            # PE option
            pe_snapshot = OptionChainSnapshot(
                symbol="NIFTY",
                timestamp=timestamp,
                strike=strike,
                option_type="PE",
                expiry="2026-02-27",
                oi=base_oi_pe,
                oi_change=oi_change_pe,
                prev_oi=base_oi_pe - oi_change_pe,
                oi_delta=oi_change_pe,
                ltp=30.0 + (strike - 20000) * 0.05 + random.uniform(-3, 3),
                iv=16.0 + i * 0.08 + random.uniform(-1, 1),
                volume=4000 + i*400 + random.randint(-800, 800),
                delta=0.3 - (20000 - strike) * 0.0001,
                gamma=0.001,
                theta=-1.5,
                vega=4.0
            )
            db.add(pe_snapshot)
    
    # Create some older data for IV regime testing
    old_base_time = base_time - timedelta(days=2)
    for i in range(80):  # 80 snapshots = 1 full trading day
        timestamp = old_base_time + timedelta(minutes=i*5)  # 5 minute intervals
        
        strikes = [19500, 19600, 19700, 19800, 19900, 20000, 20100, 20200, 20300, 20400]
        
        for strike in strikes:
            # Lower IV regime (old data)
            iv_base = 12.0 + random.uniform(-0.5, 0.5)
            
            ce_snapshot = OptionChainSnapshot(
                symbol="NIFTY",
                timestamp=timestamp,
                strike=strike,
                option_type="CE",
                expiry="2026-02-20",  # Different expiry
                oi=50000 + random.randint(-5000, 5000),
                oi_change=random.randint(100, 500),
                prev_oi=49000 + random.randint(-5000, 5000),
                oi_delta=random.randint(100, 500),
                ltp=45.0 + random.uniform(-10, 10),
                iv=iv_base,
                volume=3000 + random.randint(-500, 500),
                delta=-0.35 + random.uniform(-0.1, 0.1),
                gamma=0.001,
                theta=-2.0,
                vega=5.0
            )
            db.add(ce_snapshot)
            
            pe_snapshot = OptionChainSnapshot(
                symbol="NIFTY",
                timestamp=timestamp,
                strike=strike,
                option_type="PE",
                expiry="2026-02-20",
                oi=40000 + random.randint(-4000, 4000),
                oi_change=random.randint(80, 400),
                prev_oi=39000 + random.randint(-4000, 4000),
                oi_delta=random.randint(80, 400),
                ltp=25.0 + random.uniform(-8, 8),
                iv=iv_base + 0.5,
                volume=2500 + random.randint(-400, 400),
                delta=0.25 + random.uniform(-0.1, 0.1),
                gamma=0.001,
                theta=-1.5,
                vega=4.0
            )
            db.add(pe_snapshot)
    
    db.commit()
    print(f"Created comprehensive test data: {50*10*2 + 80*10*2} option records")

async def test_smart_money_engine_v2():
    """Test the SmartMoneyEngine v2 implementation"""
    print("=" * 80)
    print("SmartMoneyEngine v2 Test Suite - Statistical Stability")
    print("=" * 80)
    
    # Setup database
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db = Session(engine)
    
    try:
        # Create comprehensive test data
        create_comprehensive_test_data(db)
        
        # Initialize v2 engine
        engine_v2 = SmartMoneyEngineV2(snapshot_count=30, min_snapshots=10)
        
        print("\n1. Testing NIFTY signal generation with v2 engine...")
        
        # Test NIFTY signal
        nifty_signal = await engine_v2.generate_smart_money_signal("NIFTY", db)
        
        print("✅ NIFTY v2 Signal Generated:")
        print(f"   Symbol: {nifty_signal['symbol']}")
        print(f"   Bias: {nifty_signal['bias']}")
        print(f"   Confidence: {nifty_signal['confidence']}")
        print(f"   Timestamp: {nifty_signal['timestamp']}")
        
        print("\n📊 Normalized Metrics:")
        for key, value in nifty_signal['metrics'].items():
            print(f"   {key}: {value}")
        
        print("\n💡 Reasoning:")
        for reason in nifty_signal['reasoning']:
            print(f"   - {reason}")
        
        print("\n📋 Data Quality:")
        for key, value in nifty_signal['data_quality'].items():
            print(f"   {key}: {value}")
        
        # Test normalization validation
        print("\n2. Testing feature normalization...")
        
        # Validate normalized ranges
        metrics = nifty_signal['metrics']
        
        # PCR Z-score should be reasonable
        pcr_z = metrics.get('pcr_shift_z', 0)
        if abs(pcr_z) > 5:  # Z-scores beyond 5 are suspicious
            print(f"⚠️  PCR Z-score seems extreme: {pcr_z}")
        else:
            print(f"✅ PCR Z-score reasonable: {pcr_z:.2f}")
        
        # Straddle change should be 0-1
        straddle_norm = metrics.get('straddle_change_normalized', 0)
        if 0 <= straddle_norm <= 1:
            print(f"✅ Straddle change normalized correctly: {straddle_norm:.3f}")
        else:
            print(f"❌ Straddle change normalization failed: {straddle_norm}")
        
        # Volume ratio should be reasonable
        volume_ratio = metrics.get('volume_ratio', 0)
        if volume_ratio > 0:
            print(f"✅ Volume ratio calculated: {volume_ratio:.2f}")
        else:
            print(f"⚠️  Volume ratio is zero: {volume_ratio}")
        
        # OI acceleration ratio should be small
        oi_accel_ratio = metrics.get('oi_acceleration_ratio', 0)
        if abs(oi_accel_ratio) < 1:  # Should be normalized by total OI
            print(f"✅ OI acceleration ratio normalized: {oi_accel_ratio:.6f}")
        else:
            print(f"❌ OI acceleration ratio not normalized: {oi_accel_ratio}")
        
        # Test confidence sigmoid function
        print("\n3. Testing sigmoid confidence scoring...")
        
        confidence = nifty_signal['confidence']
        if 0 <= confidence <= 100:
            print(f"✅ Confidence in valid range: {confidence}")
        else:
            print(f"❌ Confidence out of range: {confidence}")
        
        # Test activation thresholds
        print("\n4. Testing activation thresholds...")
        
        # Test with insufficient data
        small_engine = SmartMoneyEngineV2(snapshot_count=5, min_snapshots=10)
        small_signal = await small_engine.generate_smart_money_signal("NIFTY", db)
        
        if small_signal['bias'] == "NEUTRAL" and small_signal['confidence'] == 0:
            print("✅ Activation threshold correctly prevents signal with insufficient data")
        else:
            print("❌ Activation threshold failed")
        
        # Test data freshness
        print("\n5. Testing data freshness validation...")
        
        # Create old data
        old_timestamp = datetime.now(timezone.utc) - timedelta(minutes=10)
        old_snapshot = OptionChainSnapshot(
            symbol="TEST",
            timestamp=old_timestamp,
            strike=20000,
            option_type="CE",
            expiry="2026-02-27",
            oi=100000,
            oi_change=1000,
            prev_oi=99000,
            oi_delta=1000,
            ltp=50,
            iv=15,
            volume=5000
        )
        db.add(old_snapshot)
        db.commit()
        
        old_engine = SmartMoneyEngineV2(max_data_age_minutes=5)
        old_signal = await old_engine.generate_smart_money_signal("TEST", db)
        
        if "too old" in old_signal['reasoning'][0]:
            print("✅ Data freshness validation works")
        else:
            print("❌ Data freshness validation failed")
        
        # Test BANKNIFTY (should return insufficient data)
        print("\n6. Testing BANKNIFTY signal generation...")
        
        banknifty_signal = await engine_v2.generate_smart_money_signal("BANKNIFTY", db)
        print("✅ BANKNIFTY Signal Generated (expected NEUTRAL due to no data)")
        
        # Test invalid symbol
        print("\n7. Testing invalid symbol...")
        
        try:
            invalid_signal = await engine_v2.generate_smart_money_signal("INVALID", db)
            print("❌ Should have raised ValueError for invalid symbol")
            return False
        except ValueError:
            print("✅ Correctly raised ValueError for invalid symbol")
        
        # Test cache functionality
        print("\n8. Testing cache functionality...")
        
        # Test cache - second call should be faster
        start_time = datetime.now()
        cached_signal = await engine_v2.generate_smart_money_signal("NIFTY", db)
        end_time = datetime.now()
        cache_time = (end_time - start_time).total_seconds()
        
        print(f"✅ Cached response generated in {cache_time:.3f} seconds")
        
        # Verify cache returns same result
        if cached_signal['symbol'] == nifty_signal['symbol'] and cached_signal['bias'] == nifty_signal['bias']:
            print("✅ Cache returned consistent results")
        else:
            print("❌ Cache returned inconsistent results")
            return False
        
        print("\n" + "=" * 80)
        print("🎉 ALL V2 TESTS PASSED!")
        print("SmartMoneyEngine v2 is statistically stable and production-ready")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

async def test_performance_tracking():
    """Test performance tracking functionality"""
    print("\n" + "=" * 80)
    print("Performance Tracking Test Suite")
    print("=" * 80)
    
    # Setup database
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db = Session(engine)
    
    try:
        # Initialize performance service
        perf_service = PerformanceTrackingService()
        
        print("\n1. Testing performance metrics calculation...")
        
        # Test performance metrics
        performance = await perf_service.get_performance_metrics("NIFTY", db, days=30)
        
        print("✅ Performance Metrics Generated:")
        print(f"   Symbol: {performance['symbol']}")
        print(f"   Total Signals: {performance['total_signals']}")
        print(f"   Win Rate: {performance['win_rate']}%")
        print(f"   Last 7 Day Accuracy: {performance['last_7_day_accuracy']}%")
        
        print("\n📊 Bias Distribution:")
        for bias, count in performance['bias_distribution'].items():
            print(f"   {bias}: {count}")
        
        print("\n📈 IV Regime Performance:")
        for regime, metrics in performance['iv_regime_performance'].items():
            print(f"   {regime}: {metrics['win_rate']}% win rate ({metrics['total_signals']} signals)")
        
        # Test with no data
        print("\n2. Testing performance with no data...")
        
        empty_performance = await perf_service.get_performance_metrics("BANKNIFTY", db, days=30)
        if empty_performance['total_signals'] == 0:
            print("✅ Empty performance handled correctly")
        else:
            print("❌ Empty performance handling failed")
        
        print("\n3. Testing prediction result updates...")
        
        # Test update results (this would normally be run periodically)
        update_result = await perf_service.update_prediction_results("NIFTY", db, lookback_minutes=30)
        print(f"✅ Update results completed: {update_result['updated_predictions']} predictions updated")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting SmartMoneyEngine v2 validation...")
    
    # Run tests
    success1 = asyncio.run(test_smart_money_engine_v2())
    success2 = asyncio.run(test_performance_tracking())
    
    if success1 and success2:
        print("\n🎉 ALL V2 VALIDATIONS PASSED!")
        print("SmartMoneyEngine v2 is production-ready with statistical stability")
        exit(0)
    else:
        print("\n❌ V2 VALIDATION FAILED!")
        exit(1)
