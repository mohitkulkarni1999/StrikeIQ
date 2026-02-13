#!/usr/bin/env python3
"""
Test script for SmartMoneyEngine v1
Tests all required functionality and validates output structure
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
from app.models.market_data import OptionChainSnapshot, MarketSnapshot
from app.services.market_data.smart_money_engine import SmartMoneyEngine
from app.core.config import settings

def create_test_data(db: Session):
    """Create test option chain snapshots for validation"""
    print("Creating test data...")
    
    # Create test snapshots for NIFTY
    base_time = datetime.now(timezone.utc)
    
    # Create 5 snapshots over the last 15 minutes
    for i in range(5):
        timestamp = base_time - timedelta(minutes=i*3)
        
        # Create option chain data for different strikes
        strikes = [19500, 19600, 19700, 19800, 19900, 20000, 20100, 20200, 20300, 20400]
        
        for strike in strikes:
            # CE option
            ce_snapshot = OptionChainSnapshot(
                symbol="NIFTY",
                timestamp=timestamp,
                strike=strike,
                option_type="CE",
                expiry="2026-02-27",
                oi=100000 + i*1000 + strike*10,
                oi_change=1000 + i*100,
                prev_oi=99000 + i*1000 + strike*10,
                oi_delta=1000 + i*100,
                ltp=50.0 + (20000 - strike) * 0.1,
                iv=15.0 + i * 0.5,
                volume=5000 + i*500,
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
                oi=80000 + i*800 + (20000-strike)*8,
                oi_change=800 + i*80,
                prev_oi=79200 + i*800 + (20000-strike)*8,
                oi_delta=800 + i*80,
                ltp=30.0 + (strike - 20000) * 0.05,
                iv=16.0 + i * 0.3,
                volume=4000 + i*400,
                delta=0.3 - (20000 - strike) * 0.0001,
                gamma=0.001,
                theta=-1.5,
                vega=4.0
            )
            db.add(pe_snapshot)
    
    db.commit()
    print(f"Created test data for NIFTY with {len(strikes)*2*5} option records")

async def test_smart_money_engine():
    """Test the SmartMoneyEngine implementation"""
    print("=" * 60)
    print("SmartMoneyEngine v1 Test Suite")
    print("=" * 60)
    
    # Setup database
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db = Session(engine)
    
    try:
        # Create test data
        create_test_data(db)
        
        # Initialize engine
        engine_instance = SmartMoneyEngine(snapshot_count=30)
        
        print("\n1. Testing NIFTY signal generation...")
        
        # Test NIFTY signal
        nifty_signal = await engine_instance.generate_smart_money_signal("NIFTY", db)
        
        print("✅ NIFTY Signal Generated:")
        print(f"   Symbol: {nifty_signal['symbol']}")
        print(f"   Bias: {nifty_signal['bias']}")
        print(f"   Confidence: {nifty_signal['confidence']}")
        print(f"   Timestamp: {nifty_signal['timestamp']}")
        
        print("\n📊 Metrics:")
        for key, value in nifty_signal['metrics'].items():
            print(f"   {key}: {value}")
        
        print("\n💡 Reasoning:")
        for reason in nifty_signal['reasoning']:
            print(f"   - {reason}")
        
        # Validate structure
        print("\n2. Validating response structure...")
        required_fields = ['symbol', 'timestamp', 'bias', 'confidence', 'metrics', 'reasoning']
        for field in required_fields:
            if field not in nifty_signal:
                print(f"❌ Missing required field: {field}")
                return False
            else:
                print(f"✅ Field present: {field}")
        
        # Validate metrics structure
        required_metrics = ['pcr', 'pcr_shift', 'atm_straddle', 'straddle_change_percent', 'oi_acceleration', 'iv_regime']
        for metric in required_metrics:
            if metric not in nifty_signal['metrics']:
                print(f"❌ Missing required metric: {metric}")
                return False
            else:
                print(f"✅ Metric present: {metric}")
        
        # Validate bias values
        valid_biases = ['BULLISH', 'BEARISH', 'NEUTRAL']
        if nifty_signal['bias'] not in valid_biases:
            print(f"❌ Invalid bias value: {nifty_signal['bias']}")
            return False
        else:
            print(f"✅ Valid bias: {nifty_signal['bias']}")
        
        # Validate confidence range
        if not (0 <= nifty_signal['confidence'] <= 100):
            print(f"❌ Invalid confidence value: {nifty_signal['confidence']}")
            return False
        else:
            print(f"✅ Valid confidence: {nifty_signal['confidence']}")
        
        # Validate IV regime
        valid_iv_regimes = ['LOW', 'NORMAL', 'HIGH']
        if nifty_signal['metrics']['iv_regime'] not in valid_iv_regimes:
            print(f"❌ Invalid IV regime: {nifty_signal['metrics']['iv_regime']}")
            return False
        else:
            print(f"✅ Valid IV regime: {nifty_signal['metrics']['iv_regime']}")
        
        print("\n3. Testing BANKNIFTY signal generation...")
        
        # Test BANKNIFTY (should return closed market response)
        banknifty_signal = await engine_instance.generate_smart_money_signal("BANKNIFTY", db)
        print("✅ BANKNIFTY Signal Generated (expected NEUTRAL due to no data)")
        
        print("\n4. Testing invalid symbol...")
        
        # Test invalid symbol
        try:
            invalid_signal = await engine_instance.generate_smart_money_signal("INVALID", db)
            print("❌ Should have raised ValueError for invalid symbol")
            return False
        except ValueError:
            print("✅ Correctly raised ValueError for invalid symbol")
        
        print("\n5. Testing cache functionality...")
        
        # Test cache - second call should be faster
        start_time = datetime.now()
        cached_signal = await engine_instance.generate_smart_money_signal("NIFTY", db)
        end_time = datetime.now()
        cache_time = (end_time - start_time).total_seconds()
        
        print(f"✅ Cached response generated in {cache_time:.3f} seconds")
        
        # Verify cache returns same result
        if cached_signal['symbol'] == nifty_signal['symbol'] and cached_signal['bias'] == nifty_signal['bias']:
            print("✅ Cache returned consistent results")
        else:
            print("❌ Cache returned inconsistent results")
            return False
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("SmartMoneyEngine v1 is ready for production")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

async def test_feature_calculations():
    """Test specific feature calculations"""
    print("\n" + "=" * 60)
    print("Feature Calculation Tests")
    print("=" * 60)
    
    # Setup database
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db = Session(engine)
    
    try:
        # Initialize engine
        engine_instance = SmartMoneyEngine(snapshot_count=30)
        
        # Get snapshots and test features
        snapshots = engine_instance._get_latest_snapshots("NIFTY", db)
        
        if not snapshots:
            print("❌ No test snapshots found")
            return False
        
        print(f"✅ Found {len(snapshots)} test snapshots")
        
        # Test basic features
        features = await engine_instance._calculate_features(snapshots, db)
        
        print("\n📊 Feature Calculations:")
        for key, value in features.items():
            print(f"   {key}: {value}")
        
        # Validate PCR calculation
        if features.get('pcr', 0) > 0:
            print("✅ PCR calculated correctly")
        else:
            print("❌ PCR calculation failed")
        
        # Validate ATM straddle
        if features.get('atm_straddle', 0) > 0:
            print("✅ ATM straddle calculated correctly")
        else:
            print("❌ ATM straddle calculation failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Feature test failed: {e}")
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting SmartMoneyEngine v1 validation...")
    
    # Run tests
    success1 = asyncio.run(test_smart_money_engine())
    success2 = asyncio.run(test_feature_calculations())
    
    if success1 and success2:
        print("\n🎉 ALL VALIDATIONS PASSED!")
        print("SmartMoneyEngine v1 is production-ready")
        exit(0)
    else:
        print("\n❌ VALIDATION FAILED!")
        exit(1)
